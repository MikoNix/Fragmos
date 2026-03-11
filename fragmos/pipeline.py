"""
pipeline.py — полный пайплайн: код → .json → .xml

Использование:
    python pipeline.py <файл с кодом> [выход.xml]

Пример:
    python pipeline.py code.txt
    python pipeline.py code.txt result.xml
"""

import os
import sys

from request import request
from builder import generate


def run(code_path, out_xml=None, cfg_overrides=None, model_id=None):
    """
    Запускает полный пайплайн:
      1. request  — отправляет код в AI, получает JSON, сохраняет .json файл
      2. builder  — читает .json файл, генерирует .xml блок-схему

    cfg_overrides — словарь с переопределениями настроек (необязательно)
    model_id      — id промпта YandexGPT (необязательно)

    Возвращает (путь к .xml, стоимость_₽).
    """
    # ── Шаг 1: request ───────────────────────────────────────────────────
    print(f"[1/2] Отправка кода в AI: {code_path}")
    json_text, cost = request(code_path, model_id=model_id)

    base = os.path.splitext(code_path)[0]
    json_path = base + ".json"

    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_text)

    print(f"      Сохранён .json файл: {json_path}")
    print(f"      Стоимость генерации: {cost:.2f} ₽")

    # ── Шаг 2: builder ───────────────────────────────────────────────────
    print(f"[2/2] Генерация блок-схемы...")
    xml_path = generate(json_path, out_xml, cfg_overrides=cfg_overrides)

    return xml_path, cost


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python pipeline.py <файл с кодом> [выход.xml]")
        sys.exit(1)

    code_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None

    result, cost = run(code_file, out_file)
    print(f"\nГотово! Блок-схема: {result}")
    print(f"Стоимость: {cost:.2f} ₽")
