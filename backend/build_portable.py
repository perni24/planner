import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


APP_NAME = "PlannerApp"
WINDOWS_EXCLUDED_MODULES = (
    "webview.platforms.qt",
    "webview.platforms.gtk",
    "webview.platforms.cocoa",
    "webview.platforms.android",
    "webview.platforms.cef",
    "PyQt5",
    "PyQt6",
    "PySide2",
    "PySide6",
    "qtpy",
    "gi",
    "cefpython3",
)


def run(command, cwd):
    subprocess.run(command, cwd=cwd, check=True)


def get_pyinstaller_command(backend_dir):
    if os.name == "nt":
        pyinstaller = backend_dir / ".venv" / "Scripts" / "pyinstaller.exe"
    else:
        pyinstaller = backend_dir / ".venv" / "bin" / "pyinstaller"

    if pyinstaller.exists():
        return [str(pyinstaller)]

    return [sys.executable, "-m", "PyInstaller"]


def get_npm_command():
    return "npm.cmd" if os.name == "nt" else "npm"


def get_pyinstaller_arguments(backend_dir, dist_dir, platform=None):
    platform = sys.platform if platform is None else platform
    separator = ";" if platform == "win32" else ":"
    arguments = [
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name", APP_NAME,
        "--distpath", str(dist_dir),
    ]
    if platform == "win32":
        # Rende esplicita la raccolta del bridge JS oltre alle DLL gestite dagli hook.
        arguments.extend(["--console", "--noupx", "--collect-data", "webview"])
        for module in WINDOWS_EXCLUDED_MODULES:
            arguments.extend(["--exclude-module", module])

    resources = (
        (backend_dir / "schema.sql", "."),
        (backend_dir / "db" / "migrations", "db/migrations"),
        (backend_dir / "locales", "locales"),
        (backend_dir.parent / "frontend" / "dist", "frontend_dist"),
    )
    for source, destination in resources:
        arguments.extend(["--add-data", f"{source}{separator}{destination}"])
    arguments.append(str(backend_dir / "main.py"))
    return arguments


def validate_destination(portable_dir):
    if portable_dir.is_symlink() or portable_dir.is_junction():
        raise RuntimeError(f"Build destination must not be a symbolic link: {portable_dir}")
    runtime_paths = [portable_dir / name for name in ("data", "locales")]
    runtime_paths.extend(portable_dir.glob("*.db*"))
    runtime_paths.extend(portable_dir.glob("*.sqlite*"))
    if any(path.exists() for path in runtime_paths):
        raise RuntimeError(
            f"Build destination contains runtime data: {portable_dir}. "
            "Use --dist-dir with a different output directory or move the used "
            "portable folder first. Existing data will not be deleted."
        )


def validate_bundle(portable_dir, platform=None):
    platform = sys.platform if platform is None else platform
    internal = portable_dir / "_internal"
    executable = "PlannerApp.exe" if platform == "win32" else APP_NAME
    required = [
        portable_dir / executable,
        portable_dir / "LICENSE",
        portable_dir / "THIRD_PARTY_NOTICES.md",
        internal / "schema.sql",
        internal / "frontend_dist" / "index.html",
        internal / "locales" / "it.json",
        internal / "locales" / "en.json",
        internal / "db" / "migrations" / "legacy_add_subtasks.sql",
    ]
    missing = [str(path.relative_to(portable_dir)) for path in required if not path.is_file()]
    if not any((internal / "db" / "migrations").glob("[0-9][0-9][0-9]_*.sql")):
        missing.append("db/migrations/*.sql")
    if platform == "win32":
        for relative in (
            "webview/lib/Microsoft.Web.WebView2.Core.dll",
            "webview/lib/Microsoft.Web.WebView2.WinForms.dll",
            "pythonnet/runtime/Python.Runtime.dll",
        ):
            if not (internal / relative).is_file():
                missing.append(relative)
        if not any((internal / "webview" / "js").rglob("*.js")):
            missing.append("webview/js/*.js")
        if not any((internal / "webview" / "lib" / "runtimes").rglob("WebView2Loader.dll")):
            missing.append("webview/lib/runtimes/**/WebView2Loader.dll")
    for relative in ("data", "db/planner.db", "db/logs", "db/webview"):
        if (internal / relative).exists():
            raise RuntimeError(f"Runtime data must not be included in the bundle: {relative}")
    if missing:
        raise RuntimeError("Incomplete portable bundle: " + ", ".join(missing))
    validate_destination(portable_dir)


def build_app(backend_dir, dist_dir):
    project_dir = backend_dir.parent
    frontend_dir = project_dir / "frontend"
    portable_dir = dist_dir / APP_NAME
    validate_destination(portable_dir)
    license_path = project_dir / "LICENSE"
    third_party_notices_path = project_dir / "THIRD_PARTY_NOTICES.md"

    if not license_path.is_file():
        raise FileNotFoundError(f"File LICENSE non trovato: {license_path}")

    if not third_party_notices_path.is_file():
        raise FileNotFoundError(
            f"File THIRD_PARTY_NOTICES.md non trovato: {third_party_notices_path}"
        )

    run([get_npm_command(), "run", "build"], cwd=frontend_dir)
    run(
        [*get_pyinstaller_command(backend_dir), *get_pyinstaller_arguments(backend_dir, dist_dir)],
        cwd=backend_dir,
    )

    shutil.copy2(
        license_path,
        portable_dir / "LICENSE",
    )

    shutil.copy2(
        third_party_notices_path,
        portable_dir / "THIRD_PARTY_NOTICES.md",
    )
    validate_bundle(portable_dir)
    print(f"Portable build ready: {portable_dir}")


def main(argv=None):
    backend_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Build the portable Planner desktop app.")
    parser.add_argument(
        "--dist-dir", type=Path, default=backend_dir / "dist",
        help="Output parent directory (default: backend/dist).",
    )
    args = parser.parse_args(argv)
    build_app(backend_dir, args.dist_dir.resolve())


if __name__ == "__main__":
    main()
