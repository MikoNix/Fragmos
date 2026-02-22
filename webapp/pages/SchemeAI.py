import streamlit as st
import tempfile
import os
import base64
from pages.fragmos import *

from pages.modules import util_sidebar
util_sidebar()

# ── стили ────────────────────────────────────────────────────


# ── заголовок ────────────────────────────────────────────────
st.markdown("""
<div class="bock-header">
    <div class="bock-title">Bock <span>→</span> draw.io</div>
    <div class="bock-sub">Вставьте Bock-код и получите блок-схему в формате draw.io</div>
</div>
""", unsafe_allow_html=True)

# ── пример кода ──────────────────────────────────────────────
EXAMPLE = '''\
function example {
    input >> "a,b";
    sum = a + b;
    if (sum > 10) {
        output >> "big";
    }
    else {
        output >> "small";
    }
    output >> "done";
}
'''

# ── форма ────────────────────────────────────────────────────
col_code, col_action = st.columns([3, 1], gap="large")

with col_code:
    source = st.text_area(
        "Bock-код",
        value=st.session_state.get("bock_source", EXAMPLE),
        height=360,
        placeholder="function myFunc { ... }",
        key="bock_source_input",
    )

with col_action:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    filename = st.text_input(
        "Имя файла",
        value="diagram",
        help="Без расширения — .drawio добавится автоматически",
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    compile_btn = st.button("⚡ Скомпилировать", use_container_width=True)

# ── компиляция ────────────────────────────────────────────────
if compile_btn:
    if not source.strip():
        st.markdown('<div class="status-err">⚠ Введите Bock-код</div>', unsafe_allow_html=True)
    else:
        try:
            safe_name = (filename.strip() or "diagram").replace(" ", "_")
            if not safe_name.endswith(".drawio"):
                safe_name += ".drawio"

            with tempfile.TemporaryDirectory() as tmpdir:
                out_path = os.path.join(tmpdir, safe_name)
                compile(source, out_path)

                with open(out_path, "rb") as f:
                    file_bytes = f.read()

            # Base64 для ссылки
            b64 = base64.b64encode(file_bytes).decode()
            href = f"data:application/octet-stream;base64,{b64}"

            st.markdown(f"""
            <div class="status-ok">✓ Скомпилировано успешно</div>
            <div class="download-card">
                <div>
                    <div class="download-label">Готовый файл</div>
                    <div class="download-filename">{safe_name}</div>
                </div>
                <a class="download-btn" href="{href}" download="{safe_name}">
                    ↓ Скачать
                </a>
            </div>
            <div style="margin-top:0.6rem; color:#4b5563; font-size:0.78rem;">
                Откройте на <a href="https://app.diagrams.net/" target="_blank"
                style="color:#5affe0; text-decoration:none;">app.diagrams.net</a> — 
                файл загрузится автоматически через File → Import.
            </div>
            """, unsafe_allow_html=True)

            # Также стандартная кнопка Streamlit как запасной вариант
            st.download_button(
                label="↓ Скачать (альтернатива)",
                data=file_bytes,
                file_name=safe_name,
                mime="application/octet-stream",
                use_container_width=True,
            )

        except SyntaxError as e:
            st.markdown(f'<div class="status-err">Синтаксическая ошибка: {e}</div>',
                        unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="status-err">Ошибка компиляции: {e}</div>',
                        unsafe_allow_html=True)

# ── подсказка ────────────────────────────────────────────────
with st.expander("📖 Синтаксис fragmos"):
    st.code("""\
function имя_функции {
    input >> "переменная";
    переменная = выражение;
    if (условие) {
        output >> "результат";
    }
    else {
        output >> "иначе";
    }
    output >> "итог";
}
""", language="javascript")