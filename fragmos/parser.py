import re
import os
import sys


# ═══════════════════════════════════════════════════════════════════════════
# ПАРСЕР .frg → (cfg, nodes)
# ═══════════════════════════════════════════════════════════════════════════

# Типы конфиг-параметров для приведения значений
_CFG_TYPES = {
    'gap_y':               int,
    'if_branch_gap':       int,
    'if_branch_vgap':      int,
    'if_branch_min_gap':   int,
    'while_corridor_base': int,
    'while_corridor_step': int,
    'while_corridor_min':  int,
    'while_back_turn_gap': int,
    'while_back_top_gap':  int,
    'show_bbox':           lambda v: v.strip().lower() in ('true', '1', 'yes'),
}

# Простые блоки: ключевое слово → type
_SIMPLE_KEYWORDS = {
    'START':      'start',
    'STOP':       'stop',
    'EXEC':       'execute',
    'PROCESS':    'process',
    'IO':         'io',
    'LOOP_START': 'loop_limit_start',
    'LOOP_END':   'loop_limit_end',
}


def parse_frg(text, base_cfg=None):
    """
    Парсит текст .frg файла.
    Возвращает (cfg, nodes):
      cfg   — словарь конфигурации (DEFAULT_CFG + переопределения из CONFIG)
      nodes — список узлов для Renderer
    """
    from builder import DEFAULT_CFG
    cfg = dict(base_cfg or DEFAULT_CFG)

    lines = _preprocess(text)
    i = 0

    if i < len(lines) and _kw(lines[i]) == 'CONFIG':
        i += 1
        i, cfg = _parse_config(lines, i, cfg)

    nodes, i = _parse_nodes(lines, i, stop_on=frozenset())
    return cfg, nodes


def parse_frg_file(path, base_cfg=None):
    """Читает файл по пути и парсит его."""
    with open(path, encoding='utf-8') as f:
        return parse_frg(f.read(), base_cfg)


# ── Вспомогательные функции ──────────────────────────────────────────────

def _preprocess(text):
    """Убирает пустые строки и комментарии (#...)."""
    result = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        # inline-комментарий вне кавычек
        result.append(_strip_inline_comment(line))
    return result


def _strip_inline_comment(line):
    """Убирает # комментарий, если он не внутри кавычек."""
    in_q = False
    for idx, ch in enumerate(line):
        if ch == '"':
            in_q = not in_q
        elif ch == '#' and not in_q:
            return line[:idx].rstrip()
    return line


def _kw(line):
    """Возвращает первое слово строки в верхнем регистре (без двоеточия)."""
    return line.split()[0].upper().rstrip(':')


def _val(line, lineno=None):
    """Извлекает строку в двойных кавычках; поддерживает экранирование \\\"."""
    m = re.search(r'"((?:[^"\\]|\\.)*)"', line)
    if not m:
        loc = f" (строка ~{lineno})" if lineno else ""
        raise SyntaxError(f"Ожидалось значение в кавычках{loc}: {line!r}")
    return m.group(1).replace('\\"', '"')


# ── CONFIG ───────────────────────────────────────────────────────────────

def _parse_config(lines, i, cfg):
    """Парсит тело CONFIG: ... END."""
    while i < len(lines):
        if _kw(lines[i]) == 'END':
            i += 1
            break
        if '=' in lines[i]:
            key, _, raw_val = lines[i].partition('=')
            key = key.strip()
            val = raw_val.strip()
            if key in _CFG_TYPES:
                cfg[key] = _CFG_TYPES[key](val)
            else:
                raise SyntaxError(f"Неизвестный параметр конфигурации: {key!r}")
        i += 1
    return i, cfg


# ── Основной парсер узлов ────────────────────────────────────────────────

def _parse_nodes(lines, i, stop_on):
    """
    Рекурсивно парсит последовательность узлов.
    Останавливается на ключевом слове из stop_on или при конце файла.
    Возвращает (nodes, i), где i указывает на строку-стоп (не потребляет её).
    """
    nodes = []
    while i < len(lines):
        kw = _kw(lines[i])

        if kw in stop_on:
            break

        if kw in _SIMPLE_KEYWORDS:
            nodes.append({'type': _SIMPLE_KEYWORDS[kw], 'value': _val(lines[i], i)})
            i += 1

        elif kw == 'IF':
            node, i = _parse_if(lines, i)
            nodes.append(node)

        elif kw == 'WHILE':
            value = _val(lines[i], i)
            i += 1
            children, i = _parse_nodes(lines, i, stop_on=frozenset({'END'}))
            _expect(lines, i, 'END')
            i += 1
            nodes.append({'type': 'while', 'value': value, 'children': children})

        elif kw == 'FOR':
            value = _val(lines[i], i)
            i += 1
            children, i = _parse_nodes(lines, i, stop_on=frozenset({'END'}))
            _expect(lines, i, 'END')
            i += 1
            nodes.append({'type': 'for_default', 'value': value, 'children': children})

        elif kw == 'CONFIG':
            raise SyntaxError("Блок CONFIG должен быть в начале файла")

        else:
            raise SyntaxError(f"Неизвестное ключевое слово: {lines[i]!r}")

    return nodes, i


def _parse_if(lines, i):
    """
    Парсит IF блок:
        IF "условие"
          YES:
            ...
          NO:
            ...
        END
    """
    value = _val(lines[i], i)
    i += 1

    yes_children = []
    no_children  = []

    while i < len(lines):
        kw = _kw(lines[i])

        if kw == 'END':
            i += 1
            break

        elif kw == 'YES':
            i += 1
            yes_children, i = _parse_nodes(
                lines, i, stop_on=frozenset({'NO', 'END'}))

        elif kw == 'NO':
            i += 1
            no_children, i = _parse_nodes(
                lines, i, stop_on=frozenset({'END'}))

        else:
            raise SyntaxError(
                f"Внутри IF ожидалось YES:, NO: или END, получено: {lines[i]!r}")

    return {
        'type':          'if',
        'value':         value,
        'children':      yes_children,
        'else_children': no_children,
    }, i


def _expect(lines, i, keyword):
    """Проверяет, что строка i содержит нужное ключевое слово."""
    if i >= len(lines) or _kw(lines[i]) != keyword:
        got = lines[i] if i < len(lines) else 'конец файла'
        raise SyntaxError(f"Ожидалось {keyword!r}, получено: {got!r}")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python parser.py <файл.frg>")
        sys.exit(1)

    path = sys.argv[1]
    cfg, nodes = parse_frg_file(path)

    print("=== CFG ===")
    for k, v in cfg.items():
        print(f"  {k} = {v!r}")

    print("\n=== NODES ===")
    import pprint
    pprint.pprint(nodes)
