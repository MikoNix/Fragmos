import openai
import re
import time


# ── Тарифы ───────────────────────────────────────────────────────────────
# Обновить согласно актуальным тарифам Yandex Cloud Foundation Models:
# https://yandex.cloud/ru/docs/foundation-models/pricing
PRICE_PER_1K_TOKENS = 0.82  # ₽ за 1000 токенов (вход + выход)
CHARS_PER_TOKEN     = 1    # ~4 символа на токен для кода


# ── Доступные модели ──────────────────────────────────────────────────────
# Ключ   — отображаемое название
# id     — идентификатор промпта в YandexGPT
# desc   — описание для UI
MODELS = {
    "Bauman 19.701": {
        "id":   "fvt60bpn6f51khbi7jjt",
        "desc": "",
    },
    "GU 19.701": {
        "id":   "fvtttdmeunp9a9e48npi",
        "desc": "",
    },
}


def request(code_path, model_id=None):
    """
    Читает код из файла, отправляет в YandexGPT и возвращает (JSON-текст, стоимость_₽).
    model_id — id промпта; если None, берётся первая модель из MODELS.
    """
    with open(code_path, "r", encoding="utf-8") as f:
        code = f.read()

    prompt_id = model_id or next(iter(MODELS.values()))["id"]

    client = openai.OpenAI(
        api_key="1",
        base_url="https://ai.api.cloud.yandex.net/v1",
        project="1"
    )

    resp = client.responses.create(
        prompt={"id": prompt_id},
        input=code,
        background=True,
    )

    # Опрашиваем статус до завершения
    while True:
        status = client.responses.retrieve(resp.id)
        if status.status in ("completed", "failed", "cancelled"):
            break
        time.sleep(2)

    if status.status != "completed":
        raise ValueError(f"AI запрос завершился со статусом: {status.status}")

    text = (status.output_text or "").strip()

    # Убираем markdown-обёртку ```json ... ``` если нейронка её добавила
    text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    if not text:
        raise ValueError("AI вернул пустой ответ")
    if not text.startswith('['):
        raise ValueError(f"AI вернул не JSON-массив. Начало ответа: {text[:300]!r}")

    # Считаем стоимость по usage из ответа
    cost = 0.0
    usage = getattr(status, "usage", None)
    if usage:
        total_tokens = getattr(usage, "total_tokens", 0)
        cost = (total_tokens / 1000) * PRICE_PER_1K_TOKENS

    return text, cost
