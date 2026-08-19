import ctypes
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
import zipfile
from pathlib import Path
import requests
from streamlit.web import cli as stcli
REPOSITORY = "17wadeche/QA_Tool"
LATEST_RELEASE_API = (
    f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
)
WINDOWS_ASSET_NAME = "QA-Monitoring-Tool-Windows.zip"
EXECUTABLE_NAME = "QA-Monitoring-Tool.exe"
MAX_UPDATE_SIZE = 500 * 1024 * 1024
UPDATE_CHECK_INTERVAL_SECONDS = 5 * 60
WEBSOCKET_PING_INTERVAL_SECONDS = 30
DISCONNECTED_SESSION_TTL_SECONDS = 24 * 60 * 60
def bundled_path(filename):
    base_directory = Path(
        getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    )
    return base_directory / filename
def installed_app_path(app_directory, filename):
    app_directory = Path(app_directory)
    candidates = (
        app_directory / filename,
        app_directory / "_internal" / filename,
    )
    return next((path for path in candidates if path.is_file()), candidates[0])
def show_message(title, message, flags=0):
    return ctypes.windll.user32.MessageBoxW(
        None,
        message,
        title,
        flags,
    )
def version_key(version):
    value = version.strip().lower().removeprefix("v")
    try:
        parts = tuple(int(part) for part in value.split("."))
        return parts + (0,) * (4 - len(parts))
    except ValueError:
        return ()
def versions_match(left, right):
    left_key = version_key(left)
    return bool(left_key) and left_key == version_key(right)
def find_windows_asset(release):
    return next(
        (
            asset
            for asset in release.get("assets", [])
            if asset.get("name") == WINDOWS_ASSET_NAME
        ),
        None,
    )
def safely_extract(archive_path, destination):
    destination = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            member_path = (destination / member.filename).resolve()
            if destination not in member_path.parents and member_path != destination:
                raise ValueError("Update archive contains an unsafe path")
        archive.extractall(destination)
def download_update(asset, destination):
    url = asset.get("browser_download_url", "")
    if not url:
        raise ValueError("Release asset has no download URL")
    expected_size = int(asset.get("size") or 0)
    if expected_size > MAX_UPDATE_SIZE:
        raise ValueError("Update archive is unexpectedly large")
    downloaded = 0
    with requests.get(url, stream=True, timeout=(10, 60)) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                downloaded += len(chunk)
                if downloaded > MAX_UPDATE_SIZE:
                    raise ValueError("Update archive is unexpectedly large")
                output.write(chunk)
    if expected_size and downloaded != expected_size:
        raise ValueError("Downloaded update size does not match the release")
def locate_extracted_app(destination):
    matches = list(destination.rglob(EXECUTABLE_NAME))
    if len(matches) != 1:
        raise ValueError("Update does not contain the expected application")
    return matches[0].parent
def powershell_literal(value):
    return "'" + str(value).replace("'", "''") + "'"
def install_and_restart(staged_app):
    install_directory = Path(sys.executable).resolve().parent
    updater_directory = Path(tempfile.mkdtemp(prefix="qa-monitoring-updater-"))
    script_path = updater_directory / "install-update.ps1"
    backup_directory = install_directory.with_name(install_directory.name + ".old")
    script = f"""
$ErrorActionPreference = 'Stop'
$processId = {os.getpid()}
$install = {powershell_literal(install_directory)}
$staged = {powershell_literal(staged_app)}
$backup = {powershell_literal(backup_directory)}
$updater = {powershell_literal(updater_directory)}
Wait-Process -Id $processId -ErrorAction SilentlyContinue
try {{
    if (Test-Path $backup) {{ Remove-Item $backup -Recurse -Force }}
    Move-Item $install $backup
    Move-Item $staged $install
    Start-Process (Join-Path $install {powershell_literal(EXECUTABLE_NAME)})
    Remove-Item $backup -Recurse -Force
}} catch {{
    if ((Test-Path $backup) -and -not (Test-Path $install)) {{
        Move-Item $backup $install
    }}
    Start-Process (Join-Path $install {powershell_literal(EXECUTABLE_NAME)})
}}
Remove-Item $updater -Recurse -Force
""".strip()
    script_path.write_text(script, encoding="utf-8")
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ],
        creationflags=creation_flags,
        close_fds=True,
        cwd=updater_directory,
    )
    os._exit(0)
def check_for_updates():
    workspace = None
    try:
        if not getattr(sys, "frozen", False) or os.name != "nt":
            return
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
        if not version_key(latest_version) > version_key(current_version):
            return
        asset = find_windows_asset(release)
        if not asset:
            return
        workspace = Path(tempfile.mkdtemp(prefix="qa-monitoring-update-"))
        archive_path = workspace / WINDOWS_ASSET_NAME
        extracted_path = workspace / "extracted"
        extracted_path.mkdir()
        download_update(asset, archive_path)
        safely_extract(archive_path, extracted_path)
        staged_app = locate_extracted_app(extracted_path)
        staged_version = installed_app_path(staged_app, "VERSION").read_text(
            encoding="utf-8"
        ).strip()
        if not versions_match(staged_version, latest_version):
            raise ValueError("Update version does not match release tag")
        install_and_restart(staged_app)
    except Exception as error:
        print(f"Automatic update check failed: {error}", file=sys.stderr)
        if workspace:
            shutil.rmtree(workspace, ignore_errors=True)
def monitor_for_updates():
    while True:
        check_for_updates()
        time.sleep(UPDATE_CHECK_INTERVAL_SECONDS)
def find_available_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
def open_browser_when_ready(port):
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
    threading.Thread(target=monitor_for_updates, daemon=True).start()
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
        f"--server.websocketPingInterval={WEBSOCKET_PING_INTERVAL_SECONDS}",
        f"--server.disconnectedSessionTTL={DISCONNECTED_SESSION_TTL_SECONDS}",
        "--browser.gatherUsageStats=false",
    ]
    stcli.main()
if __name__ == "__main__":
    main()