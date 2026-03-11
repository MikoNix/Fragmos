import sys
import os
import uuid
import json
import tempfile
import shutil
import time
import glob as globmod
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as stc

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

try:
    from request import MODELS, PRICE_PER_1K_TOKENS, CHARS_PER_TOKEN
except Exception:
    MODELS = {"YandexGPT 5.1 Pro RC": {"id": "placeholder", "desc": "Модель по умолчанию"}}
    PRICE_PER_1K_TOKENS = 2.0
    CHARS_PER_TOKEN = 4


_BUG_REPORTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Bug_reports")
)


def _estimate_cost(code: str) -> tuple[int, float]:
    """Возвращает (estimated_tokens, cost_rub)."""
    tokens = max(1, len(code) // CHARS_PER_TOKEN)
    cost   = tokens * PRICE_PER_1K_TOKENS / 1000
    return tokens, cost


# ── Папка сессии /temp/<session_id> ──────────────────────────────────────
def _session_dir() -> str:
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    session_id = st.session_state["session_id"]
    path = os.path.join(tempfile.gettempdir(), session_id)
    os.makedirs(path, exist_ok=True)
    return path


def _run_pipeline(code: str, session_dir: str, cfg_overrides: dict | None = None, model_id: str | None = None) -> tuple[str | None, float, str | None]:
    """Запускает pipeline и возвращает (xml_path, cost, error)."""
    try:
        import pipeline as _pl

        code_path = os.path.join(session_dir, "input.txt")
        xml_path  = os.path.join(session_dir, "result.xml")

        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)

        result, cost = _pl.run(code_path, xml_path, cfg_overrides=cfg_overrides, model_id=model_id)
        return result, cost, None

    except Exception as exc:
        return None, 0.0, str(exc)



# ── Поиск прошлых блок-схем в temp ──────────────────────────────────────
def _find_past_schemes() -> list[dict]:
    """Ищет result.xml файлы в подпапках temp и возвращает список."""
    tmp = tempfile.gettempdir()
    results = []
    for xml_path in globmod.glob(os.path.join(tmp, "*", "result.xml")):
        try:
            mtime = os.path.getmtime(xml_path)
            folder = os.path.basename(os.path.dirname(xml_path))
            # Пробуем прочитать начало файла для валидации
            with open(xml_path, "r", encoding="utf-8") as f:
                content = f.read()
            if len(content) > 50:  # не пустой файл
                ts = time.strftime("%d.%m %H:%M", time.localtime(mtime))
                short_id = folder[:8]
                results.append({
                    "name": f"Схема {short_id}",
                    "date": ts,
                    "path": xml_path,
                    "content": content,
                    "mtime": mtime,
                })
        except Exception:
            continue
    results.sort(key=lambda x: x["mtime"], reverse=True)
    return results[:10]  # последние 10


# ── Инициализация состояния ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Привет! Вставьте код, и я построю блок-схему. Можно на любом языке."}
    ]
if "xml_result" not in st.session_state:
    st.session_state["xml_result"] = None
if "xml_content" not in st.session_state:
    st.session_state["xml_content"] = None
if "generating" not in st.session_state:
    st.session_state["generating"] = False
if "last_code" not in st.session_state:
    st.session_state["last_code"] = None
if "api_cost" not in st.session_state:
    st.session_state["api_cost"] = None

# Настройки по умолчанию (из builder.DEFAULT_CFG)
_DEFAULT_SETTINGS = {
    "gap_y": 40,
    "if_branch_gap": 20,
    "if_branch_vgap": 15,
    "if_branch_min_gap": 40,
    "while_corridor_base": 80,
    "while_corridor_step": 20,
    "while_corridor_min": 30,
    "while_back_turn_gap": 20,
    "while_back_top_gap": 15,
    "show_bbox": True,
}

if "cfg_settings" not in st.session_state:
    st.session_state["cfg_settings"] = dict(_DEFAULT_SETTINGS)
if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = list(MODELS.keys())[0]


@st.dialog("Удаление блок-схемы")
def _confirm_delete_dialog(scheme_name: str, scheme_path: str):
    """Модальное окно подтверждения удаления."""
    st.markdown(f"Вы уверены, что хотите удалить **{scheme_name}**?")
    st.caption("Это действие нельзя отменить.")
    dcols = st.columns(2)
    with dcols[0]:
        if st.button("Да, удалить", use_container_width=True, type="primary", key="modal_del_yes"):
            folder = os.path.dirname(scheme_path)
            shutil.rmtree(folder, ignore_errors=True)
            st.rerun()
    with dcols[1]:
        if st.button("Отмена", use_container_width=True, key="modal_del_no"):
            st.rerun()


@st.dialog("Инструкция", width="large")
def _instructions_dialog():
    st.markdown("""
### Как пользоваться генератором блок-схем

**1. Вставьте код в чат**
Поддерживаются любые языки программирования: Python, C/C++, Java, JavaScript, C# и другие.
Вставьте функцию, класс или целую программу — AI сам разберётся со структурой.

**2. AI анализирует код**
Нейросеть переводит код в промежуточный JSON-формат, который описывает логику:
операции, условия, циклы, ввод/вывод. Это занимает несколько секунд.

**3. Получите блок-схему**
После генерации доступны действия:
- **Скачать** — сохранить XML-файл для draw.io
- **Открыть в Draw.io** — открыть редактор прямо на странице без загрузки файла
- **Сгенерировать заново** — повторить генерацию с теми же настройками

**Настройки генерации**
В блоке «Настройки генерации» можно настроить отступы, зазоры и отображение блоков схемы.
Изменения применяются при следующей генерации.

**Выбор модели**
Разные модели дают разное качество перевода кода. Оценка стоимости отображается
автоматически на основе длины кода.

**Баг-репорт**
Если схема построена неверно — нажмите «Баг-репорт» в сообщении чата.
Опишите ошибку, и отчёт сохранится автоматически.
""")


def _drawio_embed_html(xml_content: str) -> str:
    """Возвращает HTML для встраивания draw.io с заданным XML."""
    xml_json = json.dumps(xml_content)
    return f"""<!DOCTYPE html>
    <html><head><style>
      body{{margin:0;overflow:hidden;background:#1e1e1e;}}
      iframe{{border:none;display:block;width:100%;height:100%;}}
      html,body{{height:100%;}}
    </style></head>
    <body>
    <iframe id="f" src="https://embed.diagrams.net/?proto=json&spin=1&noExitBtn=1&dark=1"></iframe>
    <script>
    var xml = {xml_json};
    var f = document.getElementById('f');
    window.addEventListener('message', function(e) {{
      if (e.source !== f.contentWindow) return;
      try {{
        var msg = JSON.parse(e.data);
        if (msg.event === 'init') {{
          f.contentWindow.postMessage(JSON.stringify({{action:'load', xml:xml}}), '*');
        }}
      }} catch(ex) {{}}
    }});
    </script>
    </body></html>"""



@st.dialog("Баг-репорт", width="large")
def _bug_report_dialog():
    session_id  = st.session_state.get("session_id", "unknown")
    last_code   = st.session_state.get("last_code", "")
    cfg         = st.session_state.get("cfg_settings", {})
    model_name  = st.session_state.get("selected_model", "unknown")

    # Читаем JSON-ответ нейросети из session dir
    ai_json = ""
    try:
        s_dir = os.path.join(tempfile.gettempdir(), session_id)
        j_path = os.path.join(s_dir, "input.json")
        if os.path.exists(j_path):
            with open(j_path, encoding="utf-8") as _f:
                ai_json = _f.read()
    except Exception:
        pass

    st.markdown(f"**UUID сессии:** `{session_id}`  \n**Модуль:** SchemeAI  \n**Модель:** {model_name}")
    st.divider()
    description = st.text_area("Опишите ошибку", placeholder="Что пошло не так? Какой блок построен неверно?", height=120)

    if st.button("Отправить отчёт", type="primary", use_container_width=True):
        if not description.strip():
            st.warning("Пожалуйста, опишите ошибку.")
            return

        ts_str  = time.strftime("%Y%m%d-%H%M%S")
        short   = session_id[:8]
        fname   = f"SchemeAI-{short}-{ts_str}.md"

        cfg_md = "\n".join(f"- {k}: `{v}`" for k, v in cfg.items())

        md = f"""# Bug Report: SchemeAI-{short}-{ts_str}

## Модуль
SchemeAI

## UUID сессии
`{session_id}`

## Дата
{time.strftime("%Y-%m-%d %H:%M:%S")}

## Модель
{model_name}

## Описание ошибки
{description}

## Запрос пользователя (код)
```
{last_code}
```

## Ответ нейросети (JSON)
```json
{ai_json}
```

## Настройки генерации
{cfg_md}
"""
        os.makedirs(_BUG_REPORTS_DIR, exist_ok=True)
        fpath = os.path.join(_BUG_REPORTS_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as _f:
            _f.write(md)

        st.success(f"Отчёт сохранён: `{fname}`")


# ── Описания настроек для тултипов ───────────────────────────────────────
_SETTING_HELP = {
    "gap_y": "Вертикальный зазор между элементами блок-схемы (в пикселях)",
    "if_branch_gap": "Горизонтальное расстояние от края ромба IF до центра ветки",
    "if_branch_vgap": "Вертикальный зазор от низа ромба IF до первого блока ветки",
    "if_branch_min_gap": "Минимальный зазор между bounding-box-ами веток IF",
    "while_corridor_base": "Базовая ширина коридора для возвратной стрелки WHILE/FOR",
    "while_corridor_step": "Уменьшение коридора на каждый уровень вложенности",
    "while_corridor_min": "Минимальная ширина коридора WHILE/FOR",
    "while_back_turn_gap": "Вертикальный зазор от последнего блока до перемычки возврата",
    "while_back_top_gap": "Вертикальный зазор от линии коридора до верха ромба",
    "show_bbox": "Показывать цветные области вокруг IF / WHILE / FOR блоков",
}

_SETTING_LABELS = {
    "gap_y": "Вертикальный зазор",
    "if_branch_gap": "IF: отступ ветки",
    "if_branch_vgap": "IF: верт. зазор",
    "if_branch_min_gap": "IF: мин. зазор веток",
    "while_corridor_base": "Цикл: коридор (база)",
    "while_corridor_step": "Цикл: шаг коридора",
    "while_corridor_min": "Цикл: мин. коридор",
    "while_back_turn_gap": "Цикл: зазор возврата",
    "while_back_top_gap": "Цикл: зазор сверху",
    "show_bbox": "Показывать BBox",
}

_SETTING_RANGES = {
    "gap_y": (10, 100),
    "if_branch_gap": (5, 80),
    "if_branch_vgap": (5, 60),
    "if_branch_min_gap": (10, 120),
    "while_corridor_base": (20, 200),
    "while_corridor_step": (5, 60),
    "while_corridor_min": (10, 80),
    "while_back_turn_gap": (5, 60),
    "while_back_top_gap": (5, 60),
}


# ── Загрузка HTML анимации из файла ──────────────────────────────────────
_ANIM_FILE = Path(__file__).resolve().parent.parent / "static" / "html" / "loading_anim.html"
_LOADING_ANIM_HTML = _ANIM_FILE.read_text(encoding="utf-8") if _ANIM_FILE.exists() else "<p>Loading...</p>"


# ── CSS стили для страницы (из файла) ────────────────────────────────────
_CSS_FILE = Path(__file__).resolve().parent.parent / "static" / "css" / "scheme_ai.css"
_page_css = _CSS_FILE.read_text(encoding="utf-8") if _CSS_FILE.exists() else ""

st.markdown(
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />',
    unsafe_allow_html=True,
)
st.markdown(
    f"<style>\n{_page_css}\n</style>",
    unsafe_allow_html=True,
)


# ── Заголовок ────────────────────────────────────────────────────────────
st.markdown(
    '<div class="page-header">'
    '<h2>Генератор блок-схем</h2>'
    '<p>Вставьте код в чат — AI построит блок-схему, которую можно сразу открыть в draw.io</p>'
    '<div class="header-line"></div>'
    '</div>',
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════
# LAYOUT: LEFT (chat) | RIGHT (animation + history)
# ══════════════════════════════════════════════════════════════════════════
has_result = st.session_state["xml_content"] is not None

col_chat, col_right = st.columns([3, 2], gap="medium")

# ── ПРАВАЯ КОЛОНКА ───────────────────────────────────────────────────────
with col_right:

    # --- Анимация / результат ---
    if st.session_state.get("generating"):
        st.markdown(
            '<div class="right-panel-title">'
            '<span class="material-symbols-outlined">auto_awesome</span>'
            'Генерация...'
            '</div>',
            unsafe_allow_html=True,
        )
        stc.html(_LOADING_ANIM_HTML, height=420)

    elif has_result:
        st.markdown(
            '<div class="right-panel-title">'
            '<span class="material-symbols-outlined">check_circle</span>'
            'Блок-схема готова'
            '</div>',
            unsafe_allow_html=True,
        )

        act_cols = st.columns(2)
        with act_cols[0]:
            st.download_button(
                label="Скачать XML",
                data=st.session_state["xml_content"].encode("utf-8"),
                file_name="flowchart.xml",
                mime="application/xml",
                use_container_width=True,
                icon=":material/download:",
            )
        with act_cols[1]:
            if st.button("Draw.io", use_container_width=True, icon=":material/open_in_new:", key="drawio_btn"):
                stc.html('<script>parent.document.getElementById("drawio-editor").scrollIntoView({behavior:"smooth"});</script>', height=0)


        act_cols2 = st.columns(2)
        with act_cols2[0]:
            st.button(
                "Сохранить",
                use_container_width=True,
                icon=":material/cloud_upload:",
                key="save_server_btn",
            )
        with act_cols2[1]:
            if st.button("Сбросить", use_container_width=True, icon=":material/restart_alt:", key="reset_btn"):
                st.session_state["xml_result"] = None
                st.session_state["xml_content"] = None
                st.session_state["messages"] = [
                    {"role": "assistant", "content": "Привет! Вставьте код, и я построю блок-схему."}
                ]
                st.rerun()
    else:
        st.markdown(
            '<div style="text-align:center;padding:60px 20px;color:#484f58;">'
            '<span class="material-symbols-outlined" style="font-size:48px;display:block;margin-bottom:12px;color:#30363d">schema</span>'
            '<p style="font-size:14px;margin:0">Отправьте код в чат, чтобы сгенерировать блок-схему</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # --- Кнопка перегенерации ---
    if st.session_state.get("last_code") and not st.session_state.get("generating"):
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        if st.button("Сгенерировать заново", use_container_width=True, icon=":material/refresh:", key="regen_btn"):
            code = st.session_state["last_code"]
            display_content = f"```\n{code}\n```"
            st.session_state["messages"].append({"role": "user", "content": display_content})
            st.session_state["messages"].append({
                "role": "assistant",
                "content": "Перегенерация...",
                "is_status": True,
            })
            st.session_state["generating"] = True
            st.session_state["pending_code"] = code
            st.rerun()

    # --- История прошлых блок-схем (всегда внизу) ---
    st.markdown(
        '<div class="right-panel-title" style="margin-top:16px">'
        '<span class="material-symbols-outlined">history</span>'
        'Прошлые блок-схемы'
        '</div>',
        unsafe_allow_html=True,
    )

    past_schemes = _find_past_schemes()

    if past_schemes:
        for idx_s, scheme in enumerate(past_schemes):
            with st.container(border=True):
                h_cols = st.columns([3, 1, 1, 1], gap="small")
                with h_cols[0]:
                    st.markdown(
                        f'<div class="history-name">{scheme["name"]}</div>'
                        f'<div class="history-date">{scheme["date"]}</div>',
                        unsafe_allow_html=True,
                    )
                with h_cols[1]:
                    st.download_button(
                        label="",
                        data=scheme["content"].encode("utf-8"),
                        file_name=f'{scheme["name"]}.xml',
                        mime="application/xml",
                        use_container_width=True,
                        icon=":material/download:",
                        key=f"hist_dl_{idx_s}",
                    )
                with h_cols[2]:
                    if st.button("", use_container_width=True, icon=":material/open_in_new:", key=f"hist_drawio_{idx_s}"):
                        st.session_state["xml_content"] = scheme["content"]
                        st.rerun()
                with h_cols[3]:
                    if st.button("", use_container_width=True, icon=":material/delete:", key=f"hist_del_{idx_s}"):
                        _confirm_delete_dialog(scheme["name"], scheme["path"])
    else:
        st.markdown(
            '<p style="font-size:12px;color:#484f58;text-align:center;padding:12px 0">'
            'Пока нет сохранённых схем</p>',
            unsafe_allow_html=True,
        )


# ── ЛЕВАЯ КОЛОНКА (ЧАТ) — input внутри контейнера ───────────────────────
with col_chat:

    chat_box = st.container(height=560, border=True)

    with chat_box:
        for msg in st.session_state["messages"]:
            role = msg["role"]
            with st.chat_message(role, avatar=":material/smart_toy:" if role == "assistant" else None):
                st.markdown(msg["content"])

                if msg.get("has_result") and st.session_state["xml_content"]:
                    xml_c = st.session_state["xml_content"]
                    bcols = st.columns(2)
                    with bcols[0]:
                        st.download_button(
                            label="Скачать",
                            data=xml_c.encode("utf-8"),
                            file_name="flowchart.xml",
                            mime="application/xml",
                            use_container_width=True,
                            icon=":material/download:",
                            key=f"dl_{msg.get('ts', 0)}",
                        )
                    with bcols[1]:
                        if st.button(
                            "Баг-репорт",
                            use_container_width=True,
                            icon=":material/bug_report:",
                            key=f"bug_{msg.get('ts', 0)}",
                        ):
                            _bug_report_dialog()

    # Поле ввода ПОД контейнером чата — всегда внизу
    user_input = st.chat_input("Вставьте код или напишите сообщение...")

    # --- Выбор модели + оценка стоимости ---
    model_names = list(MODELS.keys())
    selected_model_name = st.selectbox(
        "Модель",
        options=model_names,
        index=model_names.index(st.session_state["selected_model"])
              if st.session_state["selected_model"] in model_names else 0,
        key="model_selectbox",
    )
    st.session_state["selected_model"] = selected_model_name

    _lc = st.session_state.get("last_code")
    _mc = MODELS[selected_model_name]
    _real_cost = st.session_state.get("api_cost")
    if _real_cost:
        st.caption(f"{_mc['desc']} · Последняя генерация: {_real_cost:.4f} ₽")
    elif _lc:
        _tok, _cost = _estimate_cost(_lc)
        st.caption(f"{_mc['desc']} · ~{_tok} токенов · ≈{_cost:.4f} ₽")
    else:
        st.caption(_mc["desc"])

    # --- Кнопка инструкции ---
    if st.button(":material/help: Инструкция", key="instructions_btn"):
        _instructions_dialog()


# ── ВСТРОЕННЫЙ РЕДАКТОР Draw.io (под основным лейаутом) ────────────────────
if has_result and st.session_state["xml_content"]:
    st.markdown('<div id="drawio-editor"></div>', unsafe_allow_html=True)

    editor_cols = st.columns([6, 1])
    with editor_cols[0]:
        st.markdown(
            '<div class="right-panel-title" style="margin-top:20px">'
            '<span class="material-symbols-outlined">edit_note</span>'
            'Редактор Draw.io'
            '</div>',
            unsafe_allow_html=True,
        )
    with editor_cols[1]:
        with st.popover(":material/settings:", use_container_width=True):
            if "editor_height" not in st.session_state:
                st.session_state["editor_height"] = 1100
            st.session_state["editor_height"] = st.slider(
                "Высота редактора",
                min_value=300,
                max_value=1200,
                value=st.session_state["editor_height"],
                step=50,
                key="_editor_height_slider",
            )

    stc.html(_drawio_embed_html(st.session_state["xml_content"]), height=st.session_state.get("editor_height", 600), scrolling=False)


# ── НАСТРОЙКИ (под чатом, в expander с обводкой) ─────────────────────────
with st.expander(":material/tune: Настройки генерации", expanded=False):
    cfg = st.session_state["cfg_settings"]

    cfg["show_bbox"] = st.toggle(
        _SETTING_LABELS["show_bbox"],
        value=cfg["show_bbox"],
        help=_SETTING_HELP["show_bbox"],
        key="toggle_show_bbox",
    )

    st.divider()

    slider_keys = [
        "gap_y", "if_branch_gap", "if_branch_vgap", "if_branch_min_gap",
        "while_corridor_base", "while_corridor_step", "while_corridor_min",
        "while_back_turn_gap", "while_back_top_gap",
    ]

    for i in range(0, len(slider_keys), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx_k = i + j
            if idx_k >= len(slider_keys):
                break
            key = slider_keys[idx_k]
            lo, hi = _SETTING_RANGES[key]
            with col:
                cfg[key] = st.slider(
                    _SETTING_LABELS[key],
                    min_value=lo,
                    max_value=hi,
                    value=cfg[key],
                    help=_SETTING_HELP[key],
                    key=f"slider_{key}",
                )

    st.session_state["cfg_settings"] = cfg


# ── ОБРАБОТКА ВВОДА (двухфазная) ─────────────────────────────────────────
if user_input:
    # Оборачиваем ввод в блок кода чтобы Streamlit не интерпретировал содержимое
    display_content = f"```\n{user_input}\n```"
    st.session_state["messages"].append({"role": "user", "content": display_content})
    st.session_state["messages"].append({
        "role": "assistant",
        "content": "Упаковываем данные...",
        "is_status": True,
    })
    st.session_state["generating"] = True
    st.session_state["pending_code"] = user_input
    st.session_state["last_code"] = user_input
    st.rerun()

if st.session_state.get("generating") and st.session_state.get("pending_code"):
    code = st.session_state.pop("pending_code")

    session_dir = _session_dir()
    selected_model = st.session_state.get("selected_model", list(MODELS.keys())[0])
    model_id = MODELS.get(selected_model, {}).get("id")
    xml_path, cost, error = _run_pipeline(code, session_dir, st.session_state["cfg_settings"], model_id=model_id)

    st.session_state["generating"] = False
    st.session_state["api_cost"] = cost

    st.session_state["messages"] = [
        m for m in st.session_state["messages"] if not m.get("is_status")
    ]

    if error:
        st.session_state["messages"].append({
            "role": "assistant",
            "content": f"Ошибка генерации:\n```\n{error}\n```",
        })
        st.session_state["xml_result"] = None
        st.session_state["xml_content"] = None
    else:
        xml_content = ""
        if xml_path and os.path.exists(xml_path):
            with open(xml_path, "r", encoding="utf-8") as f:
                xml_content = f.read()

        st.session_state["xml_result"] = xml_path
        st.session_state["xml_content"] = xml_content

        cost_text = f" (стоимость: {cost:.4f} ₽)" if cost else ""
        ts = int(time.time() * 1000)
        st.session_state["messages"].append({
            "role": "assistant",
            "content": f"Блок-схема успешно сгенерирована!{cost_text}",
            "has_result": True,
            "ts": ts,
        })

    st.rerun()
