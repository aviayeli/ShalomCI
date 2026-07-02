"""Standalone desktop entry-point for packaging ShalomCI with PyInstaller (--onedir).

Launches the existing Streamlit GUI (src/gui/app.py) programmatically on a
dynamically allocated localhost port and opens it in the user's default
browser. Does not modify any existing application files.
"""

import multiprocessing
import socket
import sys
import threading
import webbrowser
from pathlib import Path

APP_PATH = str(Path(__file__).resolve().parent / "src" / "gui" / "app.py")


def find_free_port() -> int:
    """Return an available, open TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        return sock.getsockname()[1]


def open_browser_when_ready(port: int, delay: float = 2.0) -> None:
    """Open the default browser to the local Streamlit server after a short delay."""
    timer = threading.Timer(delay, lambda: webbrowser.open(f"http://localhost:{port}"))
    timer.daemon = True
    timer.start()


def launch_streamlit(port: int) -> None:
    """Launch the existing Streamlit app programmatically on the given port."""
    import streamlit.web.cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        APP_PATH,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--server.address",
        "localhost",
    ]
    sys.exit(stcli.main())


def main() -> None:
    port = find_free_port()
    open_browser_when_ready(port)
    launch_streamlit(port)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
