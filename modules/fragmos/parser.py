"""
parser.py — Трансформирует унифицированный AST (от ast_generators) в список nodes
для Builder, применяя режим отображения из modes/modes.yaml.
"""

from builder import DEFAULT_CFG
from modes import get_mode


# ═══════════════════════════════════════════════════════════════════════════
# ЕДИНАЯ ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════════════

def parse_ast_to_flowchart(ast_dict: dict, mode_id: str = 'default') -> tuple[dict, list]:
    """
    Преобразует унифицированный AST в (cfg, nodes) для Builder.

    Args:
        ast_dict: {'type': 'program', 'body': [...], 'metadata': {...}}
        mode_id:  ID режима из modes.yaml ('default' | 'loopLimit')

    Returns:
        (cfg, nodes) — конфигурация и список блоков для Builder.

    Raises:
        ValueError: если mode_id не найден.
    """
    mode = get_mode(mode_id)
    cfg = dict(DEFAULT_CFG)
    converter = _Converter(mode)
    nodes = converter.convert_program(ast_dict)
    return cfg, nodes


# ═══════════════════════════════════════════════════════════════════════════
# КОНВЕРТЕР
# ═══════════════════════════════════════════════════════════════════════════

class _Converter:
    def __init__(self, mode: dict):
        self._blocks = mode['blocks']

    # ── top level ─────────────────────────────────────────────────────────

    def convert_program(self, ast_dict: dict) -> list:
        """Конвертирует program-узел. Каждая function_def → START…STOP."""
        nodes = []
        for node in ast_dict.get('body', []):
            nodes.extend(self._convert(node))
        # Если нет function_def — оборачиваем всё в START/STOP сами
        if not any(n.get('type') == 'start' for n in nodes):
            nodes = [{'type': 'start', 'value': ''}] + nodes + [{'type': 'stop', 'value': ''}]
        return nodes

    # ── dispatcher ────────────────────────────────────────────────────────

    def _convert(self, node: dict) -> list:
        t = node.get('type')
        if t == 'function_def':
            return self._function(node)
        if t == 'class_def':
            return self._class_def(node)
        if t == 'if' or t == 'try':
            return [self._if_node(node)]
        if t == 'for':
            return self._for(node)
        if t == 'while':
            return self._while(node)
        if t == 'return':
            return [{'type': 'stop', 'value': node.get('value', '')}]
        if t == 'assignment':
            return [{'type': 'execute', 'value': node.get('value', '')}]
        if t == 'call':
            return [{'type': 'process', 'value': node.get('value', '')}]
        if t == 'io':
            return [{'type': 'io', 'value': node.get('value', '')}]
        if t == 'expression':
            return [{'type': 'execute', 'value': node.get('value', '')}]
        return []

    def _convert_body(self, body: list) -> list:
        result = []
        for node in body:
            result.extend(self._convert(node))
        return result

    # ── function_def ──────────────────────────────────────────────────────

    def _function(self, node: dict) -> list:
        name = node.get('value', node.get('name', ''))
        body = node.get('body', [])
        nodes = [{'type': 'start', 'value': name}]
        body_nodes = self._convert_body(body)
        # Если тело не заканчивается stop — добавляем
        has_stop = body_nodes and body_nodes[-1].get('type') == 'stop'
        nodes.extend(body_nodes)
        if not has_stop:
            nodes.append({'type': 'stop', 'value': f'конец {node.get("name", "")}'})
        return nodes

    # ── class_def ─────────────────────────────────────────────────────────

    def _class_def(self, node: dict) -> list:
        """Разворачиваем методы класса как обычные function_def."""
        nodes = []
        for child in node.get('body', []):
            if child.get('type') == 'function_def':
                nodes.extend(self._function(child))
        return nodes

    # ── if / try ──────────────────────────────────────────────────────────

    def _if_node(self, node: dict) -> dict:
        condition = node.get('value', '')
        children = self._convert_body(node.get('body', []))
        else_children = self._convert_body(node.get('else_body', []))
        return {
            'type': 'if',
            'value': condition,
            'children': children,
            'else_children': else_children,
        }

    # ── for ───────────────────────────────────────────────────────────────

    def _for(self, node: dict) -> list:
        header = node.get('value', '')
        body = self._convert_body(node.get('body', []))
        block_type = self._blocks.get('for', 'for_default')

        if block_type == 'loop_limit':
            return [
                {'type': 'loop_limit_start', 'value': header},
                *body,
                {'type': 'loop_limit_end', 'value': header},
            ]
        # default: for_default (шестиугольник) с children
        return [{'type': 'for_default', 'value': header, 'children': body}]

    # ── while ─────────────────────────────────────────────────────────────

    def _while(self, node: dict) -> list:
        condition = node.get('value', '')
        body = self._convert_body(node.get('body', []))
        block_type = self._blocks.get('while', 'while')

        if block_type == 'loop_limit':
            return [
                {'type': 'loop_limit_start', 'value': condition},
                *body,
                {'type': 'loop_limit_end', 'value': condition},
            ]
        # default: while (ромб с возвратной стрелкой) с children
        return [{'type': 'while', 'value': condition, 'children': body}]
