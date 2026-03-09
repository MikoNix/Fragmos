import sys
import os
import uuid
import tempfile
import threading
import time

import streamlit as st

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


# ── CSS-анимация спиннера ─────────────────────────────────────────────────
SPINNER_CSS = """
<style>
.frag-spinner-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 18px;
    padding: 40px 0;
}
.frag-spinner {
    width: 56px;
    height: 56px;
    border: 5px solid #30363d;
    border-top: 5px solid #a371f7;
    border-radius: 50%;
    animation: frag-spin 0.9s linear infinite;
}
@keyframes frag-spin {
    to { transform: rotate(360deg); }
}
.frag-spinner-label {
    color: #8b949e;
    font-size: 15px;
    letter-spacing: 0.04em;
}
.frag-dot {
    display: inline-block;
    animation: frag-blink 1.4s infinite both;
}
.frag-dot:nth-child(2) { animation-delay: 0.2s; }
.frag-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes frag-blink {
    0%, 80%, 100% { opacity: 0; }
    40%           { opacity: 1; }
}
</style>
"""

SPINNER_HTML = """
<div class="frag-spinner-wrap">
    <div class="frag-spinner"></div>
    <div class="frag-spinner-label">
        Генерация блок-схемы<span class="frag-dot">.</span><span class="frag-dot">.</span><span class="frag-dot">.</span>
    </div>
</div>
"""


# ── UI ───────────────────────────────────────────────────────────────────
st.markdown("## Генератор блок-схем")
st.markdown("Вставьте код в поле ниже и нажмите **Сгенерировать** — AI построит блок-схему в формате draw.io.")

code_input = st.text_area(
    label="Ваш код",
    placeholder="# Вставьте сюда код на любом языке...",
    height=320,
    key="code_input",
)

generate_btn = st.button("Сгенерировать", type="primary", use_container_width=True)

st.divider()

result_placeholder = st.empty()

# ── Логика генерации ─────────────────────────────────────────────────────
if generate_btn:
    if not code_input.strip():
        st.warning("Введите код перед генерацией.")
    else:
        # Сбрасываем прошлый результат
        st.session_state.pop("xml_result", None)
        st.session_state.pop("xml_error", None)

        session_dir = _session_dir()

        # Показываем спиннер
        st.markdown(SPINNER_CSS, unsafe_allow_html=True)
        spinner_slot = result_placeholder.empty()
        spinner_slot.markdown(SPINNER_HTML, unsafe_allow_html=True)

        xml_path, error = _run_pipeline(code_input, session_dir)

        # Убираем спиннер
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

        st.success("Блок-схема успешно сгенерирована!")

        col_dl, col_copy = st.columns(2, gap="small")

        with col_dl:
            st.download_button(
                label="Скачать .xml (draw.io)",
                data=xml_content.encode("utf-8"),
                file_name="flowchart.xml",
                mime="application/xml",
                use_container_width=True,
            )

        with col_copy:
            copy_btn = st.button("Копировать содержимое", use_container_width=True, key="copy_btn")

        if copy_btn:
            st.code(xml_content, language="xml")
            st.info("Выделите текст выше (Ctrl+A) и скопируйте (Ctrl+C).")

    else:
        st.error("Файл не найден. Попробуйте сгенерировать снова.")
