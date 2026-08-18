import ctypes
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
import requests
from streamlit.web import cli as stcli
REPOSITORY = "17wadeche/QA_Tool"
RELEASES_URL = f"https://github.com/{REPOSITORY}/releases/latest"
LATEST_RELEASE_API = (
    f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
)
def bundled_path(filename):
    base_directory = Path(
        getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    )
    return base_directory / filename
def show_message(title, message, flags=0):
    return ctypes.windll.user32.MessageBoxW(
        None,
        message,
        title,
        flags,
    )
def check_for_updates():
    try:
        version_file = bundled_path("VERSION")
        current_version = version_file.read_text(
            encoding="utf-8"
        ).strip()
        response = requests.get(
            LATEST_RELEASE_API,
            headers={"Accept": "application/vnd.github+json"},
            timeout=5,
        )
        response.raise_for_status()
        release = response.json()
        latest_version = str(release.get("tag_name", "")).strip()
        if (
            current_version
            and latest_version
            and latest_version != current_version
        ):
            result = show_message(
                "QA Monitoring Tool Update",
                (
                    f"A newer version is available.\n\n"
                    f"Installed: {current_version}\n"
                    f"Available: {latest_version}\n\n"
                    f"Open the download page?"
                ),
                4 | 32,  # Yes/No with question icon
            )
            if result == 6:
                webbrowser.open(
                    release.get("html_url", RELEASES_URL)
                )
    except Exception:
        pass
def find_available_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
def open_browser_when_ready(port):
    for _ in range(60):
        try:
            with socket.create_connection(
                ("127.0.0.1", port),
                timeout=0.5,
            ):
                webbrowser.open(f"http://localhost:{port}")
                return
        except OSError:
            time.sleep(0.5)
def main():
    app_path = bundled_path("app.py")
    if not app_path.exists():
        show_message(
            "QA Monitoring Tool",
            f"Application file was not found:\n{app_path}",
            16,
        )
        raise SystemExit(1)
    check_for_updates()
    port = find_available_port()
    threading.Thread(
        target=open_browser_when_ready,
        args=(port,),
        daemon=True,
    ).start()
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["QA_MONITORING_DESKTOP"] = "1"
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--global.developmentMode=false",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    stcli.main()
if __name__ == "__main__":
    main()