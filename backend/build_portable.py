import os
import subprocess
from pathlib import Path


APP_NAME = "PlannerApp"


def run(command, cwd):
    subprocess.run(command, cwd=cwd, check=True)


def get_pyinstaller_path(backend_dir):
    if os.name == "nt":
        return backend_dir / "venv" / "Scripts" / "pyinstaller.exe"

    return backend_dir / "venv" / "bin" / "pyinstaller"


def get_npm_command():
    return "npm.cmd" if os.name == "nt" else "npm"


def main():
    backend_dir = Path(__file__).resolve().parent
    project_dir = backend_dir.parent
    frontend_dir = project_dir / "frontend"
    pyinstaller = get_pyinstaller_path(backend_dir)
    add_data_separator = ";" if os.name == "nt" else ":"

    if not pyinstaller.exists():
        raise RuntimeError(
            "PyInstaller non trovato. Installa PyInstaller nel venv del backend."
        )

    run([get_npm_command(), "run", "build"], cwd=frontend_dir)

    run(
        [
            str(pyinstaller),
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


if __name__ == "__main__":
    main()
