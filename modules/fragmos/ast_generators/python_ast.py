from tree_sitter_languages import get_parser as _get_ts_parser
from .base import ASTGenerator

_IO_FUNCS = {'print', 'input', 'open', 'write', 'read', 'readline', 'readlines'}

_parser = None


def _parser_instance():
    global _parser
    if _parser is None:
        _parser = _get_ts_parser('python')
    return _parser


class PythonAST(ASTGenerator):
    """Python AST generator using tree-sitter."""

    def generate(self, code: str) -> dict:
        print("[DEBUG] PythonAST.generate called")
        tree = _parser_instance().parse(bytes(code, 'utf-8'))
        root = tree.root_node
        if root.has_error:
            raise SyntaxError("Python syntax error in source code")
        return {
            "type": "program",
            "body": self._visit_block(root),
            "metadata": {"language": "python"},
        }

    # ── helpers ──────────────────────────────────────────────────────────────

    def _t(self, node) -> str:
        return node.text.decode('utf-8')

    def _field(self, node, name):
        return node.child_by_field_name(name)

    def _visit_block(self, node) -> list:
        """Walk named children of a block/module node."""
        result = []
        for child in node.named_children:
            v = self._visit(child)
            if v is not None:
                result.append(v)
        return result

    # ── node visitors ─────────────────────────────────────────────────────────

    def _visit(self, node) -> dict | None:
        t = node.type
        if t == 'function_definition':
            return self._visit_function(node)
        if t == 'class_definition':
            return self._visit_class(node)
        if t == 'if_statement':
            return self._visit_if(node)
        if t == 'for_statement':
            return self._visit_for(node)
        if t == 'while_statement':
            return self._visit_while(node)
        if t == 'return_statement':
            return self._visit_return(node)
        if t == 'try_statement':
            return self._visit_try(node)
        if t == 'expression_statement':
            return self._visit_expression(node)
        if t in ('assignment', 'augmented_assignment'):
            return {'type': 'assignment', 'value': self._t(node)}
        if t == 'decorated_definition':
            for child in node.named_children:
                if child.type in ('function_definition', 'class_definition'):
                    return self._visit(child)
        # skip: imports, comments, pass, break, continue, annotations
        return None

    def _visit_function(self, node) -> dict:
        name = self._t(self._field(node, 'name'))
        params = self._t(self._field(node, 'parameters'))
        body_node = self._field(node, 'body')
        return {
            'type': 'function_def',
            'name': name,
            'value': f'{name}{params}',
            'body': self._visit_block(body_node),
        }

    def _visit_class(self, node) -> dict:
        name = self._t(self._field(node, 'name'))
        body_node = self._field(node, 'body')
        return {
            'type': 'class_def',
            'name': name,
            'value': name,
            'body': self._visit_block(body_node) if body_node else [],
        }

    def _visit_if(self, node) -> dict:
        condition = self._t(self._field(node, 'condition'))
        body = self._visit_block(self._field(node, 'consequence'))
        # tree-sitter-python: all elif/else are flat children of if_statement
        alternatives = [c for c in node.named_children
                        if c.type in ('elif_clause', 'else_clause')]
        else_body = self._build_elif_chain(alternatives)
        return {
            'type': 'if',
            'value': condition,
            'body': body,
            'else_body': else_body,
        }

    def _build_elif_chain(self, alternatives: list) -> list:
        if not alternatives:
            return []
        first = alternatives[0]
        rest = alternatives[1:]
        if first.type == 'elif_clause':
            condition = self._t(self._field(first, 'condition'))
            body = self._visit_block(self._field(first, 'consequence'))
            return [{'type': 'if', 'value': condition, 'body': body,
                     'else_body': self._build_elif_chain(rest)}]
        if first.type == 'else_clause':
            return self._visit_block(self._field(first, 'body'))
        return []

    def _visit_for(self, node) -> dict:
        left = self._t(self._field(node, 'left'))
        right = self._t(self._field(node, 'right'))
        body = self._visit_block(self._field(node, 'body'))
        return {
            'type': 'for',
            'value': f'{left} in {right}',
            'body': body,
        }

    def _visit_while(self, node) -> dict:
        condition = self._t(self._field(node, 'condition'))
        body = self._visit_block(self._field(node, 'body'))
        return {
            'type': 'while',
            'value': condition,
            'body': body,
        }

    def _visit_return(self, node) -> dict:
        val = self._t(node)
        if val.startswith('return '):
            val = val[7:]
        elif val == 'return':
            val = ''
        return {'type': 'return', 'value': val}

    def _visit_try(self, node) -> dict:
        body = []
        except_body = []
        for child in node.named_children:
            if child.type == 'block' and not body:
                body = self._visit_block(child)
            elif child.type == 'except_clause':
                blk = child.child_by_field_name('body')
                if blk:
                    except_body.extend(self._visit_block(blk))
        return {
            'type': 'try',
            'value': 'try',
            'body': body,
            'else_body': except_body,
        }

    def _visit_expression(self, node) -> dict | None:
        child = node.named_children[0] if node.named_children else None
        if child is None:
            return None
        if child.type == 'call':
            func_node = child.child_by_field_name('function')
            func_name = self._t(func_node).split('.')[-1] if func_node else ''
            if func_name in _IO_FUNCS:
                return {'type': 'io', 'value': self._t(child)}
            return {'type': 'call', 'value': self._t(child)}
        if child.type in ('assignment', 'augmented_assignment'):
            return {'type': 'assignment', 'value': self._t(child)}
        return {'type': 'expression', 'value': self._t(child)}
