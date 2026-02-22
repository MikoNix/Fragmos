#!/usr/bin/env python3
"""
serve_drawio.py — раздаёт папку через localhost.run (SSH туннель, без регистрации)
и выводит ссылки draw.io в консоль. При добавлении файлов ссылки обновляются.

Требования: только стандартный SSH (уже есть в Codespaces)
    pip install watchdog   # опционально, для автообновления

Запуск:
    python serve_drawio.py              # папка ./diagrams, порт 8765
    python serve_drawio.py ./my_folder
    python serve_drawio.py ./my_folder 9000
"""

import sys
import re
import time
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import quote
import os   
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

PORT   = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
FOLDER = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path("./fragmos").resolve()

PUBLIC_URL = ""


# ─── HTTP-сервер ──────────────────────────────────────────────────────────────

class CORSHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FOLDER), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), CORSHandler)
    server.serve_forever()


# ─── Вывод ссылок ─────────────────────────────────────────────────────────────

def print_links():
    if not PUBLIC_URL:
        return
    files = sorted(FOLDER.glob("**/*.xml"))
    if not files:
        print("\n📂 Нет .xml файлов в папке. Положи файл — ссылки появятся автоматически.\n")
        return

    print(f"\n{'─'*62}")
    print(f"  🌐  {PUBLIC_URL}")
    print(f"{'─'*62}")
    for f in files:
        rel        = f.relative_to(FOLDER)
        file_url   = f"{PUBLIC_URL}/{quote(str(rel))}"
        drawio_url = f"https://app.diagrams.net/?url={quote(file_url, safe='')}"
        print(f"\n  📄  {rel}")
        print(f"      draw.io → {drawio_url}")
    print(f"\n{'─'*62}\n")


# ─── localhost.run туннель ────────────────────────────────────────────────────

def start_tunnel():
    """
    Запускает SSH туннель через localhost.run.
    Парсит публичный URL из вывода и обновляет PUBLIC_URL.
    """
    global PUBLIC_URL

    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "-R", f"80:localhost:{PORT}",
        "nokey@localhost.run",
        "--",
        "--output=json",
    ]

    print(f"⏳ Поднимаю туннель через localhost.run...")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for line in proc.stdout:
        line = line.strip()

        # localhost.run выводит URL в строке вида:
        # https://xxxx.lhr.life
        # или в JSON: {"address": "xxxx.lhr.life", ...}
        import json as _json
        try:
            data = _json.loads(line)
            addr = data.get("address") or data.get("url") or ""
            if addr:
                if not addr.startswith("http"):
                    addr = "https://" + addr
                PUBLIC_URL = addr.rstrip("/")
                print(f"✅ Туннель активен: {PUBLIC_URL}\n")
                print_links()
                continue
        except _json.JSONDecodeError:
            pass

        # Fallback: ищем URL в обычном тексте
        m = re.search(r"https?://[a-z0-9\-]+\.lhr\.life", line)
        if m and not PUBLIC_URL:
            PUBLIC_URL = m.group(0).rstrip("/")
            print(f"✅ Туннель активен: {PUBLIC_URL}\n")
            print_links()

        # Показываем прочие сообщения от SSH (ошибки и т.п.)
        elif line and "lhr.life" not in line and PUBLIC_URL == "":
            print(f"  ssh: {line}")

    proc.wait()
    if proc.returncode and proc.returncode != 0:
        print(f"\n⚠️  SSH туннель завершился (код {proc.returncode}). Перезапусти скрипт.")


# ─── Watchdog ─────────────────────────────────────────────────────────────────

class DrawioWatcher(FileSystemEventHandler):
    def __init__(self):
        self._timer = None

    def _schedule(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(1.0, print_links)
        self._timer.start()

    def on_created(self, event):
        if event.src_path.endswith(".xml"):
            print(f"✅ Новый файл: {Path(event.src_path).name}")
            os.system(f"clear")
            self._schedule()

    def on_deleted(self, event):
        if event.src_path.endswith(".xml"):
            print(f"🗑  Удалён: {Path(event.src_path).name}")
            self._schedule()

    def on_moved(self, event):
        if event.dest_path.endswith(".xml") or event.src_path.endswith(".xml"):
            print(f"✏️  Переименован: {Path(event.src_path).name} → {Path(event.dest_path).name}")
            self._schedule()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    FOLDER.mkdir(parents=True, exist_ok=True)

    # HTTP-сервер в фоне
    threading.Thread(target=run_server, daemon=True).start()

    # Watchdog
    if HAS_WATCHDOG:
        observer = Observer()
        observer.schedule(DrawioWatcher(), str(FOLDER), recursive=True)
        observer.start()
        print(f"👀 Слежу за папкой: {FOLDER}")
    else:
        print(f"⚠️  pip install watchdog — для автообновления ссылок при добавлении файлов")

    # Туннель в фоне (он сам напечатает ссылки когда поднимется)
    tunnel_thread = threading.Thread(target=start_tunnel, daemon=True)
    tunnel_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановлено.")
        if HAS_WATCHDOG:
            observer.stop()
            observer.join()


if __name__ == "__main__":
    main()