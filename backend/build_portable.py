import os
import shutil
import subprocess
import sys
from pathlib import Path


APP_NAME = "PlannerApp"


def run(command, cwd):
    subprocess.run(command, cwd=cwd, check=True)


def get_pyinstaller_command(backend_dir):
    if os.name == "nt":
        pyinstaller = backend_dir / "venv" / "Scripts" / "pyinstaller.exe"
    else:
        pyinstaller = backend_dir / "venv" / "bin" / "pyinstaller"

    if pyinstaller.exists():
        return [str(pyinstaller)]

    return [sys.executable, "-m", "PyInstaller"]


def get_npm_command():
    return "npm.cmd" if os.name == "nt" else "npm"


def main():
    backend_dir = Path(__file__).resolve().parent
    project_dir = backend_dir.parent
    frontend_dir = project_dir / "frontend"
    pyinstaller_command = get_pyinstaller_command(backend_dir)
    add_data_separator = ";" if os.name == "nt" else ":"

    run([get_npm_command(), "run", "build"], cwd=frontend_dir)

    run(
        [
            *pyinstaller_command,
            "--noconfirm",
            "--onedir",
            "--name",
            APP_NAME,
            "--add-data",
            f"schema.sql{add_data_separator}.",
            "--add-data",
            f"locales{add_data_separator}locales",
            "--add-data",
            f"../frontend/dist{add_data_separator}frontend_dist",
            "main.py",
        ],
        cwd=backend_dir,
    )

    portable_dir = backend_dir / "dist" / APP_NAME
    license_path = project_dir / "LICENSE"
    third_party_notices_path = project_dir / "THIRD_PARTY_NOTICES.md"

    if not license_path.is_file():
        raise FileNotFoundError(f"File LICENSE non trovato: {license_path}")

    if not third_party_notices_path.is_file():
        raise FileNotFoundError(
            f"File THIRD_PARTY_NOTICES.md non trovato: {third_party_notices_path}"
        )

    shutil.copy2(
        license_path,
        portable_dir / "LICENSE",
    )

    shutil.copy2(
        third_party_notices_path,
        portable_dir / "THIRD_PARTY_NOTICES.md",
    )


if __name__ == "__main__":
    main()
