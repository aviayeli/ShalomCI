"""Build the ShalomCI Windows desktop executable with PyInstaller (V3-compliant).

Must be run natively on Windows (PyInstaller does not cross-compile) via:
    uv run python build.py

pyinstaller is a uv-managed dev dependency (see pyproject.toml), so it is
never installed globally, per the V3 packaging rule.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SEP = ";" if os.name == "nt" else ":"  # PyInstaller --add-data separator is OS-specific

CMD = [
    "uv",
    "run",
    "pyinstaller",
    "--onedir",
    "--windowed",
    "--name",
    "ShalomCI",
    "--icon",
    "Icon.ico",
    "--collect-all",
    "streamlit",
    "--copy-metadata",
    "streamlit",
    "--copy-metadata",
    "altair",
    "--add-data",
    f"src{SEP}src",
    "run_desktop.py",
]

if __name__ == "__main__":
    if os.name != "nt":
        print("Warning: PyInstaller cannot cross-compile a Windows .exe from this OS.", file=sys.stderr)
    subprocess.run(CMD, cwd=ROOT, check=True)
