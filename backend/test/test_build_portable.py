import os
import runpy
import subprocess
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import build_portable as build


def expect_error(exception, operation):
    try:
        operation()
    except exception as error:
        return error
    raise AssertionError(f"Expected {exception.__name__}")


def make_bundle(root, platform="win32"):
    files = [
        "PlannerApp.exe" if platform == "win32" else "PlannerApp",
        "LICENSE", "THIRD_PARTY_NOTICES.md",
        "_internal/schema.sql", "_internal/frontend_dist/index.html",
        "_internal/locales/it.json", "_internal/locales/en.json",
        "_internal/db/migrations/001_example.sql",
        "_internal/db/migrations/legacy_add_subtasks.sql",
    ]
    if platform == "win32":
        files.extend([
            "_internal/webview/lib/Microsoft.Web.WebView2.Core.dll",
            "_internal/webview/lib/Microsoft.Web.WebView2.WinForms.dll",
            "_internal/webview/lib/runtimes/win-x64/native/WebView2Loader.dll",
            "_internal/webview/js/api.js",
            "_internal/pythonnet/runtime/Python.Runtime.dll",
        ])
    elif platform == "linux":
        files.extend(f"_internal/{relative}" for relative in build.LINUX_QT_REQUIRED_FILES)
        files.append("_internal/webview/js/api.js")
    for relative in files:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture", encoding="utf-8")
    if platform == "linux" and os.name != "nt":
        (root / "PlannerApp").chmod(0o755)
        (root / "_internal" / build.LINUX_QT_REQUIRED_FILES[0]).chmod(0o755)
    if platform == "linux":
        for name in build.LINUX_QT_DISTRIBUTIONS:
            relative = f"{name.lower().replace('-', '_')}-1.0.dist-info"
            info = root / "_internal" / relative
            info.mkdir(parents=True)
            (info / "METADATA").write_text(f"Name: {name}\nVersion: 1.0\n", encoding="utf-8")
            (info / "LICENSE").write_text("upstream license fixture", encoding="utf-8")
            (info / "RECORD").write_text(f"{relative}/LICENSE,,\n", encoding="utf-8")
        build.collect_linux_licenses(root)
    return root


def test_windows_arguments_collect_bridge_and_exclude_other_renderers():
    root = Path(__file__).resolve().parents[1]
    arguments = build.get_pyinstaller_arguments(root, root / "dist", "win32")
    assert "--onedir" in arguments and "--clean" in arguments
    assert "--console" in arguments and "--noupx" in arguments
    assert arguments[arguments.index("--collect-data") + 1] == "webview"
    excluded = [arguments[index + 1] for index, value in enumerate(arguments) if value == "--exclude-module"]
    assert set(excluded) == set(build.WINDOWS_EXCLUDED_MODULES)
    assert not {"clr", "pythonnet", "clr_loader", "webview.platforms.winforms", "webview.platforms.edgechromium"} & set(excluded)
    assert arguments[-1] == str(root / "main.py")


def test_windows_resources_do_not_include_database_or_profile_directory():
    root = Path(__file__).resolve().parents[1]
    arguments = build.get_pyinstaller_arguments(root, root / "dist", "win32")
    resources = [arguments[index + 1] for index, value in enumerate(arguments) if value == "--add-data"]
    assert resources == [
        f"{root / 'schema.sql'};.",
        f"{root / 'db' / 'migrations'};db/migrations",
        f"{root / 'locales'};locales",
        f"{root.parent / 'frontend' / 'dist'};frontend_dist",
    ]


def test_linux_does_not_receive_windows_renderer_exclusions():
    root = Path(__file__).resolve().parents[1]
    arguments = build.get_pyinstaller_arguments(root, root / "dist", "linux")
    excluded = [arguments[index + 1] for index, value in enumerate(arguments) if value == "--exclude-module"]
    assert set(excluded) == set(build.LINUX_EXCLUDED_MODULES)
    assert not {"PyQt6", "qtpy", "webview.platforms.qt", "PyQt6.QtQuick", "PyQt6.QtQml"} & set(excluded)
    assert "--console" not in arguments
    assert f"{root / 'db' / 'migrations'}:db/migrations" in arguments


def test_linux_arguments_collect_webengine_and_bridge():
    root = Path(__file__).resolve().parents[1]
    arguments = build.get_pyinstaller_arguments(root, root / "dist", "linux")
    hidden = [arguments[index + 1] for index, value in enumerate(arguments) if value == "--hidden-import"]
    assert set(hidden) == set(build.LINUX_HIDDEN_IMPORTS)
    assert arguments[arguments.index("--collect-data") + 1] == "webview"
    assert "--noupx" in arguments
    copied = [arguments[index + 1] for index, value in enumerate(arguments) if value == "--copy-metadata"]
    assert set(copied) == set(build.LINUX_QT_DISTRIBUTIONS)


def test_build_environment_selects_pyqt6_only_for_linux_without_mutating_parent():
    with patch.dict(os.environ, {"QT_API": "pyside6", "PLANNER_BUILD_TEST": "keep"}):
        environment = build.get_build_environment("linux")
        assert environment["QT_API"] == "pyqt6"
        assert environment["PLANNER_BUILD_TEST"] == "keep"
        assert os.environ["QT_API"] == "pyside6"
        assert build.get_build_environment("win32")["QT_API"] == "pyside6"


def test_linux_runtime_config_selects_same_qt_binding_as_build():
    with patch.dict(os.environ, {"QT_API": "pyside6"}), patch.object(build.sys, "platform", "linux"):
        config = runpy.run_path(str(Path(__file__).resolve().parents[1] / "config.py"))
        assert config["WEBVIEW_GUI"] == "qt"
        assert os.environ["QT_API"] == "pyqt6"


def test_destination_with_runtime_data_is_rejected_without_deleting_anything():
    with TemporaryDirectory(prefix="planner-build-data-") as directory:
        root = Path(directory)
        for relative in ("data/planner.db", "locales/it.json", "old.db", "old.sqlite3"):
            destination = root / relative.replace("/", "_")
            path = destination / relative
            path.parent.mkdir(parents=True)
            path.write_text("keep", encoding="utf-8")
            error = expect_error(RuntimeError, lambda: build.validate_destination(destination))
            assert "--dist-dir" in str(error)
            assert path.read_text(encoding="utf-8") == "keep"


def test_fresh_or_unused_build_destination_can_be_used():
    with TemporaryDirectory(prefix="planner-build-unused-") as directory:
        root = Path(directory) / build.APP_NAME
        build.validate_destination(root)
        make_bundle(root)
        build.validate_destination(root)


def test_bundle_validation_checks_javascript_and_native_dependencies():
    with TemporaryDirectory(prefix="planner-build-files-") as directory:
        root = make_bundle(Path(directory))
        build.validate_bundle(root, "win32")
        for relative in (
            "_internal/webview/js/api.js",
            "_internal/webview/lib/Microsoft.Web.WebView2.Core.dll",
            "_internal/webview/lib/runtimes/win-x64/native/WebView2Loader.dll",
            "_internal/pythonnet/runtime/Python.Runtime.dll",
        ):
            path = root / relative
            path.unlink()
            expect_error(RuntimeError, lambda: build.validate_bundle(root, "win32"))
            path.write_text("fixture", encoding="utf-8")


def test_linux_bundle_validation_checks_webengine_resources_and_bridge():
    with TemporaryDirectory(prefix="planner-build-qt-") as directory:
        root = make_bundle(Path(directory), "linux")
        build.validate_bundle(root, "linux")
        for relative in (*build.LINUX_QT_REQUIRED_FILES, "webview/js/api.js"):
            path = root / "_internal" / relative
            path.unlink()
            error = expect_error(RuntimeError, lambda: build.validate_bundle(root, "linux"))
            assert relative in str(error) or "webview/js/*.js" in str(error)
            path.write_text("fixture", encoding="utf-8")
            if relative == build.LINUX_QT_REQUIRED_FILES[0] and os.name != "nt":
                path.chmod(0o755)


@unittest.skipIf(os.name == "nt", "Executable permissions require a POSIX filesystem")
def test_linux_bundle_rejects_non_executable_app_and_helper():
    with TemporaryDirectory(prefix="planner-build-permissions-") as directory:
        root = make_bundle(Path(directory), "linux")
        for path in (root / "PlannerApp", root / "_internal" / build.LINUX_QT_REQUIRED_FILES[0]):
            path.chmod(0o644)
            error = expect_error(RuntimeError, lambda: build.validate_bundle(root, "linux"))
            assert "permission" in str(error)
            path.chmod(0o755)


def test_bundle_validation_checks_resources_licenses_and_migrations():
    with TemporaryDirectory(prefix="planner-build-resources-") as directory:
        root = make_bundle(Path(directory))
        for relative in (
            "LICENSE", "THIRD_PARTY_NOTICES.md", "_internal/schema.sql",
            "_internal/frontend_dist/index.html", "_internal/locales/en.json",
            "_internal/db/migrations/001_example.sql",
        ):
            path = root / relative
            path.unlink()
            expect_error(RuntimeError, lambda: build.validate_bundle(root, "win32"))
            path.write_text("fixture", encoding="utf-8")


def test_missing_license_stops_before_any_build_command():
    with TemporaryDirectory(prefix="planner-build-license-") as directory, patch.object(build, "run") as run:
        root = Path(directory)
        expect_error(FileNotFoundError, lambda: build.build_app(root / "backend", root / "output"))
        run.assert_not_called()


def test_bundle_rejects_development_database_logs_and_profile():
    with TemporaryDirectory(prefix="planner-build-private-") as directory:
        root = make_bundle(Path(directory))
        for relative in ("data", "db/planner.db", "db/logs", "db/webview"):
            path = root / "_internal" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("private", encoding="utf-8")
            expect_error(RuntimeError, lambda: build.validate_bundle(root, "win32"))
            path.unlink()


def test_cli_accepts_a_separate_output_directory():
    with patch.object(build, "build_app") as build_app:
        build.main(["--dist-dir", "dist/windows-check"])
    assert build_app.call_args.args[1] == Path("dist/windows-check").resolve()


def test_used_portable_folder_stops_before_any_build_command():
    with TemporaryDirectory(prefix="planner-build-protect-") as directory, patch.object(build, "run") as run:
        root = Path(directory)
        (root / "output" / build.APP_NAME / "data").mkdir(parents=True)
        expect_error(RuntimeError, lambda: build.build_app(root / "backend", root / "output"))
        run.assert_not_called()


def test_build_copies_notices_and_validates_selected_destination():
    with TemporaryDirectory(prefix="planner-build-flow-") as directory:
        root = Path(directory)
        backend = root / "backend"
        backend.mkdir()
        (root / "LICENSE").write_text("license", encoding="utf-8")
        (root / "THIRD_PARTY_NOTICES.md").write_text("notices", encoding="utf-8")
        output = root / "output"

        def run(command, cwd, env=None):
            if command[-1] == str(backend / "main.py"):
                make_bundle(output / build.APP_NAME)

        with patch.object(build, "run", side_effect=run) as commands, patch.object(
            build, "get_pyinstaller_command", return_value=["pyinstaller"]
        ), patch.object(build.sys, "platform", "win32"), redirect_stdout(StringIO()):
            build.build_app(backend, output)
        assert commands.call_count == 2
        assert commands.call_args_list[0].kwargs["cwd"] == root / "frontend"
        assert (output / build.APP_NAME / "LICENSE").read_text(encoding="utf-8") == "license"
        assert (output / build.APP_NAME / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8") == "notices"


def test_linux_build_passes_binding_environment_and_validates_bundle():
    with TemporaryDirectory(prefix="planner-build-linux-flow-") as directory:
        root = Path(directory)
        backend = root / "backend"
        backend.mkdir()
        (root / "LICENSE").write_text("license", encoding="utf-8")
        (root / "THIRD_PARTY_NOTICES.md").write_text("notices", encoding="utf-8")
        output = root / "output"

        def run(command, cwd, env=None):
            if command[-1] == str(backend / "main.py"):
                assert env["QT_API"] == "pyqt6"
                make_bundle(output / build.APP_NAME, "linux")

        with patch.object(build, "run", side_effect=run) as commands, patch.object(
            build, "get_pyinstaller_command", return_value=["pyinstaller"]
        ), patch.object(build.sys, "platform", "linux"), patch.object(build.os, "access", return_value=True), redirect_stdout(StringIO()):
            build.build_app(backend, output)
        assert commands.call_count == 2
        assert (output / build.APP_NAME / "PlannerApp").is_file()


def test_frontend_build_error_prevents_pyinstaller_and_copying():
    with TemporaryDirectory(prefix="planner-build-failure-") as directory:
        root = Path(directory)
        (root / "LICENSE").write_text("license", encoding="utf-8")
        (root / "THIRD_PARTY_NOTICES.md").write_text("notices", encoding="utf-8")
        failure = subprocess.CalledProcessError(1, "npm")
        with patch.object(build, "run", side_effect=failure) as run:
            assert expect_error(subprocess.CalledProcessError, lambda: build.build_app(
                root / "backend", root / "output"
            )) is failure
        run.assert_called_once()
        assert not (root / "output").exists()


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
