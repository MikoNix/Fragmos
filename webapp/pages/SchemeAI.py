import sys
import os
import uuid
import tempfile
import base64
import zlib
import urllib.parse

import streamlit as st
import streamlit.components.v1 as components

from pages.modules import util_sidebar

# ── Настройка страницы ────────────────────────────────────────────────────
st.set_page_config(page_title="Генератор блок-схем", layout="wide", initial_sidebar_state="expanded")
util_sidebar()

# ── Путь к модулям fragmos ────────────────────────────────────────────────
_FRAGMOS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "fragmos")
)
if _FRAGMOS_DIR not in sys.path:
    sys.path.insert(0, _FRAGMOS_DIR)


# ── Папка сессии /temp/<session_id> ──────────────────────────────────────
def _session_dir() -> str:
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    session_id = st.session_state["session_id"]
    path = os.path.join(tempfile.gettempdir(), session_id)
    os.makedirs(path, exist_ok=True)
    return path


def _run_pipeline(code: str, session_dir: str) -> tuple[str | None, str | None]:
    """Запускает pipeline и возвращает (xml_path, error)."""
    try:
        import pipeline as _pl

        code_path = os.path.join(session_dir, "input.txt")
        xml_path  = os.path.join(session_dir, "result.xml")

        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)

        result = _pl.run(code_path, xml_path)
        return result, None

    except Exception as exc:
        return None, str(exc)


# ── draw.io ссылка ───────────────────────────────────────────────────────
def _make_drawio_url(xml_content: str) -> str:
    xml_bytes = xml_content.encode("utf-8")
    compressed = zlib.compress(xml_bytes, 9)
    b64 = base64.urlsafe_b64encode(compressed).decode("ascii")
    return f"https://app.diagrams.net/#R{urllib.parse.quote(b64, safe='')}"


# ── Анимация загрузки (iframe, прозрачный фон, справа) ───────────────────
LOADER_HTML = """<!DOCTYPE html>
<html>
<head>
<meta name="color-scheme" content="light dark">
<style>
html,body{margin:0;padding:0;background:transparent;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}

.wrap{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:20px}

/* Текст */
.title{font-size:15px;font-weight:700;color:#e6edf3;text-align:center}
.sub{font-size:12px;color:#8b949e;text-align:center}

/* Точки */
.dots{display:flex;gap:8px;justify-content:center;margin-top:4px}
.dot{width:7px;height:7px;border-radius:50%;animation:bounce 1.4s ease-in-out infinite}
.dot:nth-child(1){background:#a371f7;animation-delay:0s}
.dot:nth-child(2){background:#58a6ff;animation-delay:.2s}
.dot:nth-child(3){background:#ff7b72;animation-delay:.4s}
@keyframes bounce{0%,100%{transform:translateY(0);opacity:.4}50%{transform:translateY(-8px);opacity:1}}

/* SVG блоки */
.glow{animation:pulse 2.4s ease-in-out infinite}
.g1{animation-delay:0s}
.g2{animation-delay:.4s}
.g3{animation-delay:.8s}
.g4{animation-delay:1.2s}
@keyframes pulse{0%,100%{opacity:.65;filter:drop-shadow(0 0 2px rgba(163,113,247,.2))}50%{opacity:1;filter:drop-shadow(0 0 10px rgba(163,113,247,.5))}}

/* Бегущие пунктиры */
.dash{stroke-dasharray:6 4;animation:flow 1.5s linear infinite}
@keyframes flow{to{stroke-dashoffset:-20}}

/* Меняющийся текст внутри блока процесса */
.cycle text{animation:swapText 6s steps(1) infinite}
.t1{animation-delay:0s !important}
.t2{animation-delay:2s !important}
.t3{animation-delay:4s !important}

.phase{animation:phaseIn 6s steps(1) infinite}
.p1{animation-delay:0s}
.p2{animation-delay:2s}
.p3{animation-delay:4s}
@keyframes phaseIn{0%{opacity:1}33.33%{opacity:0}100%{opacity:0}}
</style>
</head>
<body>
<div class="wrap">
    <div>
        <div class="title">Строим блок-схему</div>
        <div class="sub">Анализируем структуру кода...</div>
        <div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
    </div>
    <svg width="180" height="260" viewBox="0 0 180 260" fill="none">
        <!-- Начало -->
        <g class="glow g1">
            <rect x="40" y="6" width="100" height="32" rx="16" fill="#a371f7" stroke="#8b5cf6" stroke-width="1.5"/>
            <text x="90" y="27" text-anchor="middle" fill="#fff" font-size="11" font-weight="700" font-family="sans-serif">Начало</text>
        </g>
        <line class="dash" x1="90" y1="38" x2="90" y2="60" stroke="#a371f7" stroke-width="1.5"/>

        <!-- Процесс (меняющийся текст) -->
        <g class="glow g2">
            <rect x="25" y="60" width="130" height="32" rx="5" fill="#58a6ff" stroke="#2d8ef3" stroke-width="1.5"/>
            <text class="phase p1" x="90" y="81" text-anchor="middle" fill="#fff" font-size="11" font-weight="700" font-family="sans-serif">Чтение кода</text>
            <text class="phase p2" x="90" y="81" text-anchor="middle" fill="#fff" font-size="11" font-weight="700" font-family="sans-serif">Построение</text>
            <text class="phase p3" x="90" y="81" text-anchor="middle" fill="#fff" font-size="11" font-weight="700" font-family="sans-serif">Оптимизация</text>
        </g>
        <line class="dash" x1="90" y1="92" x2="90" y2="114" stroke="#58a6ff" stroke-width="1.5"/>

        <!-- if ромб -->
        <g class="glow g3">
            <rect x="55" y="114" width="70" height="70" rx="5" fill="#f85149" stroke="#d13438" stroke-width="1.5" transform="rotate(45 90 149)"/>
            <text x="90" y="154" text-anchor="middle" fill="#fff" font-size="13" font-weight="700" font-family="sans-serif">if?</text>
            <!-- Ветвления -->
            <text x="38" y="148" text-anchor="middle" fill="#3fb950" font-size="9" font-weight="700" font-family="sans-serif">Да</text>
            <text x="142" y="148" text-anchor="middle" fill="#ffa657" font-size="9" font-weight="700" font-family="sans-serif">Нет</text>
        </g>
        <line class="dash" x1="90" y1="184" x2="90" y2="200" stroke="#f85149" stroke-width="1.5"/>
        <!-- Ветка влево -->
        <line class="dash" x1="55" y1="149" x2="20" y2="149" stroke="#3fb950" stroke-width="1"/>
        <line class="dash" x1="20" y1="149" x2="20" y2="200" stroke="#3fb950" stroke-width="1"/>
        <line class="dash" x1="20" y1="200" x2="90" y2="200" stroke="#3fb950" stroke-width="1"/>
        <!-- Ветка вправо -->
        <line class="dash" x1="125" y1="149" x2="160" y2="149" stroke="#ffa657" stroke-width="1"/>
        <line class="dash" x1="160" y1="149" x2="160" y2="200" stroke="#ffa657" stroke-width="1"/>
        <line class="dash" x1="160" y1="200" x2="90" y2="200" stroke="#ffa657" stroke-width="1"/>

        <!-- Процесс 2 -->
        <g class="glow g2" style="animation-delay:1s">
            <rect x="25" y="200" width="130" height="28" rx="5" fill="#58a6ff" stroke="#2d8ef3" stroke-width="1.5"/>
            <text x="90" y="219" text-anchor="middle" fill="#fff" font-size="10" font-weight="700" font-family="sans-serif">Генерация XML</text>
        </g>
        <line class="dash" x1="90" y1="228" x2="90" y2="240" stroke="#58a6ff" stroke-width="1.5"/>

        <!-- Конец -->
        <g class="glow g4">
            <rect x="40" y="240" width="100" height="18" rx="9" fill="#a371f7" stroke="#8b5cf6" stroke-width="1.5"/>
            <text x="90" y="253" text-anchor="middle" fill="#fff" font-size="9" font-weight="700" font-family="sans-serif">Готово</text>
        </g>
    </svg>
</div>
</body>
</html>"""


# ── UI ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="margin-bottom:20px;">'
    '<h2 style="font-size:24px;font-weight:700;color:#e6edf3;margin:0 0 6px;">Генератор блок-схем</h2>'
    '<p style="font-size:13px;color:#8b949e;margin:0;">Вставьте код — AI построит блок-схему, которую можно сразу открыть в draw.io</p>'
    '<div style="height:1px;background:linear-gradient(90deg,#a371f7,#30363d,transparent);margin-top:14px;"></div>'
    '</div>',
    unsafe_allow_html=True,
)

# Поле ввода слева (60% ширины)
col_input, col_space = st.columns([3, 2], gap="large")

with col_input:
    code_input = st.text_area(
        label="Ваш код",
        placeholder="# Вставьте сюда код на любом языке...",
        height=300,
        key="code_input",
        label_visibility="collapsed",
    )
    generate_btn = st.button("Сгенерировать блок-схему", type="primary", use_container_width=True)

result_placeholder = st.empty()

# ── Логика генерации ─────────────────────────────────────────────────────
if generate_btn:
    if not code_input.strip():
        st.warning("Введите код перед генерацией.")
    else:
        st.session_state.pop("xml_result", None)
        st.session_state.pop("xml_error", None)

        session_dir = _session_dir()

        spinner_slot = result_placeholder.empty()
        with spinner_slot.container():
            components.html(LOADER_HTML, height=300)

        xml_path, error = _run_pipeline(code_input, session_dir)

        spinner_slot.empty()

        if error:
            st.session_state["xml_error"] = error
        else:
            st.session_state["xml_result"] = xml_path


# ── Вывод результата ─────────────────────────────────────────────────────
if "xml_error" in st.session_state:
    st.error(f"Ошибка генерации:\n\n```\n{st.session_state['xml_error']}\n```")

if "xml_result" in st.session_state:
    xml_path = st.session_state["xml_result"]

    if xml_path and os.path.exists(xml_path):
        with open(xml_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        drawio_url = _make_drawio_url(xml_content)

        st.success("Блок-схема успешно сгенерирована!")

        col1, col2, col3 = st.columns(3, gap="small")

        with col1:
            st.download_button(
                label="Скачать .xml",
                data=xml_content.encode("utf-8"),
                file_name="flowchart.xml",
                mime="application/xml",
                use_container_width=True,
            )

        with col2:
            st.link_button("Открыть в draw.io", drawio_url, use_container_width=True)

        with col3:
            if st.button("Показать XML", use_container_width=True, key="show_xml_btn"):
                st.session_state["show_xml"] = not st.session_state.get("show_xml", False)

        if st.session_state.get("show_xml", False):
            st.code(xml_content, language="xml")

    else:
        st.error("Файл не найден. Попробуйте сгенерировать снова.")
