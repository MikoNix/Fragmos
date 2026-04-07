from tree_sitter_languages import get_parser as _get_ts_parser
from .base import ASTGenerator

_IO_METHODS = {'write', 'writeline', 'readline', 'read', 'readalltext', 'readalllines'}

_parser = None


def _parser_instance():
    global _parser
    if _parser is None:
        _parser = _get_ts_parser('c_sharp')
    return _parser


class CSharpAST(ASTGenerator):
    """C# AST generator using tree-sitter."""

    def generate(self, code: str) -> dict:
        print("[DEBUG] CSharpAST.generate called")
        tree = _parser_instance().parse(bytes(code, 'utf-8'))
        root = tree.root_node
        if root.has_error:
            raise SyntaxError("C# syntax error in source code")
        return {
            "type": "program",
            "body": self._visit_block(root),
            "metadata": {"language": "csharp"},
        }

    # ── helpers ──────────────────────────────────────────────────────────────

    def _t(self, node) -> str:
        return node.text.decode('utf-8')

    def _field(self, node, name):
        return node.child_by_field_name(name)

    def _visit_block(self, node) -> list:
        result = []
        for child in node.named_children:
            v = self._visit(child)
            if v is not None:
                if isinstance(v, list):
                    result.extend(v)
                else:
                    result.append(v)
        return result

    # ── node visitors ─────────────────────────────────────────────────────────

    def _visit(self, node) -> dict | list | None:
        t = node.type
        if t == 'class_declaration':
            return self._visit_class(node)
        if t == 'method_declaration':
            return self._visit_method(node)
        if t == 'constructor_declaration':
            return self._visit_constructor(node)
        if t in ('block', 'declaration_list'):
            return self._visit_block(node)
        if t == 'if_statement':
            return self._visit_if(node)
        if t == 'for_statement':
            return self._visit_for(node)
        if t == 'foreach_statement':
            return self._visit_foreach(node)
        if t == 'while_statement':
            return self._visit_while(node)
        if t == 'return_statement':
            return self._visit_return(node)
        if t == 'try_statement':
            return self._visit_try(node)
        if t == 'expression_statement':
            return self._visit_expression(node)
        if t == 'local_variable_declaration':
            return {'type': 'assignment', 'value': self._t(node).rstrip(';')}
        if t == 'local_declaration_statement':
            inner = node.named_children[0] if node.named_children else None
            if inner:
                return {'type': 'assignment', 'value': self._t(inner).rstrip(';')}
        return None

    def _visit_class(self, node) -> dict:
        name_node = self._field(node, 'name')
        name = self._t(name_node) if name_node else ''
        body_node = self._field(node, 'body')
        return {
            'type': 'class_def',
            'name': name,
            'value': name,
            'body': self._visit_block(body_node) if body_node else [],
        }

    def _visit_method(self, node) -> dict:
        name_node = self._field(node, 'name')
        name = self._t(name_node) if name_node else ''
        params_node = self._field(node, 'parameters')
        params = self._t(params_node) if params_node else '()'
        body_node = self._field(node, 'body')
        return {
            'type': 'function_def',
            'name': name,
            'value': f'{name}{params}',
            'body': self._visit_block(body_node) if body_node else [],
        }

    def _visit_constructor(self, node) -> dict:
        name_node = self._field(node, 'name')
        name = self._t(name_node) if name_node else ''
        params_node = self._field(node, 'parameters')
        params = self._t(params_node) if params_node else '()'
        body_node = self._field(node, 'body')
        return {
            'type': 'function_def',
            'name': name,
            'value': f'{name}{params}',
            'body': self._visit_block(body_node) if body_node else [],
        }

    def _visit_if(self, node) -> dict:
        cond_node = self._field(node, 'condition')
        condition = self._t(cond_node) if cond_node else ''
        cons_node = self._field(node, 'consequence')
        body = self._visit_block(cons_node) if cons_node else []
        else_body = []
        alt_node = self._field(node, 'alternative')
        if alt_node is not None:
            if alt_node.type == 'if_statement':
                else_body = [self._visit_if(alt_node)]
            else:
                else_body = self._visit_block(alt_node)
        return {
            'type': 'if',
            'value': condition,
            'body': body,
            'else_body': else_body,
        }

    def _visit_for(self, node) -> dict:
        init = self._field(node, 'initializer')
        cond = self._field(node, 'condition')
        upd = self._field(node, 'update')
        parts = []
        if init:
            parts.append(self._t(init).rstrip(';'))
        if cond:
            parts.append(self._t(cond))
        if upd:
            parts.append(self._t(upd))
        header = '; '.join(parts)
        body_node = self._field(node, 'body')
        return {
            'type': 'for',
            'value': header,
            'body': self._visit_block(body_node) if body_node else [],
        }

    def _visit_foreach(self, node) -> dict:
        type_node = self._field(node, 'type')
        name_node = self._field(node, 'left')
        in_node = self._field(node, 'right')
        parts = []
        if type_node:
            parts.append(self._t(type_node))
        if name_node:
            parts.append(self._t(name_node))
        header = ' '.join(parts)
        if in_node:
            header = f'{header} in {self._t(in_node)}'
        body_node = self._field(node, 'body')
        return {
            'type': 'for',
            'value': header,
            'body': self._visit_block(body_node) if body_node else [],
        }

    def _visit_while(self, node) -> dict:
        cond_node = self._field(node, 'condition')
        condition = self._t(cond_node) if cond_node else ''
        body_node = self._field(node, 'body')
        return {
            'type': 'while',
            'value': condition,
            'body': self._visit_block(body_node) if body_node else [],
        }

    def _visit_return(self, node) -> dict:
        val = self._t(node).rstrip(';')
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
            elif child.type == 'catch_clause':
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
        text = self._t(child).rstrip(';')
        if child.type == 'invocation_expression':
            func_node = child.child_by_field_name('function')
            func_name = self._t(func_node).split('.')[-1].lower() if func_node else ''
            if func_name in _IO_METHODS or 'console' in self._t(child).lower():
                return {'type': 'io', 'value': text}
            return {'type': 'call', 'value': text}
        if child.type == 'assignment_expression':
            return {'type': 'assignment', 'value': text}
        return {'type': 'expression', 'value': text}
