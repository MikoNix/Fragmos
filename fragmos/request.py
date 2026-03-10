import openai


def request(code_path):
    """
    Читает код из файла, отправляет в YandexGPT и возвращает .frg текст.
    """
    with open(code_path, "r", encoding="utf-8") as f:
        code = f.read()

    client = openai.OpenAI(
        api_key="1",
        base_url="https://ai.api.cloud.yandex.net/v1",
        project="1"
    )

    response = client.responses.create(
        prompt={
            "id": "fvt60bpn6f51khbi7jjt",
        },
        input=code,
    )

    return response.output_text
