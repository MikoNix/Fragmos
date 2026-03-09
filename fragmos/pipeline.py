"""
pipeline.py — полный пайплайн: код → .frg → .xml

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


def run(code_path, out_xml=None):
    """
    Запускает полный пайплайн:
      1. request  — отправляет код в AI, получает .frg текст, сохраняет .frg файл
      2. builder  — читает .frg файл, генерирует .xml блок-схему

    Возвращает путь к готовому .xml файлу.
    """
    # ── Шаг 1: request ───────────────────────────────────────────────────
    print(f"[1/2] Отправка кода в AI: {code_path}")
    frg_text = request(code_path)

    base = os.path.splitext(code_path)[0]
    frg_path = base + ".frg"

    with open(frg_path, "w", encoding="utf-8") as f:
        f.write(frg_text)

    print(f"      Сохранён .frg файл: {frg_path}")

    # ── Шаг 2: builder ───────────────────────────────────────────────────
    print(f"[2/2] Генерация блок-схемы...")
    xml_path = generate(frg_path, out_xml)

    return xml_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python pipeline.py <файл с кодом> [выход.xml]")
        sys.exit(1)

    code_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None

    result = run(code_file, out_file)
    print(f"\nГотово! Блок-схема: {result}")
