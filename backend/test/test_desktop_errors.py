import errno
import json
import logging
import unittest
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from services import desktop_error_service as errors


@contextmanager
def isolated_logging():
    previous = errors.LOGGER.handlers[:]
    errors.LOGGER.handlers = []
    console = StringIO()
    with TemporaryDirectory(prefix="planner-error-test-") as directory:
        path = Path(directory) / "logs" / "planner.log"
        with patch.object(errors, "DESKTOP_LOG_PATH", str(path)), patch.object(
            errors.sys, "stderr", console
        ), patch.object(errors, "show_native_error", return_value=False):
            try:
                yield path, console
            finally:
                for handler in list(errors.LOGGER.handlers):
                    logging.getLogger("uvicorn.error").removeHandler(handler)
                    errors.LOGGER.removeHandler(handler)
                    handler.close()
                errors.LOGGER.handlers = previous


def test_report_writes_traceback_and_log_location_without_gui():
    with isolated_logging() as (path, console):
        errors.configure_desktop_logging()
        with patch.object(errors.locale, "getlocale", return_value=("en_US", "UTF-8")):
            try:
                raise ValueError("Original failure details")
            except ValueError as original:
                errors.report_desktop_error(original)
        text = path.read_text(encoding="utf-8")
        assert "Traceback" in text
        assert "Original failure details" in text
        assert str(path) in console.getvalue()


def test_log_rotation_keeps_only_configured_backups():
    with isolated_logging() as (path, console), patch.multiple(
        errors, DESKTOP_LOG_MAX_BYTES=180, DESKTOP_LOG_BACKUP_COUNT=2
    ):
        errors.configure_desktop_logging()
        for index in range(12):
            errors.LOGGER.error("Rotation test %s: %s", index, "x" * 100)
        assert path.is_file()
        assert Path(f"{path}.1").is_file()
        assert Path(f"{path}.2").is_file()
        assert not Path(f"{path}.3").exists()


def test_unwritable_log_directory_keeps_console_fallback():
    with isolated_logging() as (path, console), patch.object(
        errors.os, "makedirs", side_effect=PermissionError("Read-only folder")
    ):
        errors.configure_desktop_logging()
        errors.report_desktop_error(RuntimeError("Original error"))
        assert not path.exists()
        assert "Read-only folder" in console.getvalue()
        assert "Original error" in console.getvalue()


def test_failed_webview_and_native_dialog_do_not_hide_original_error():
    window = Mock()
    window.create_confirmation_dialog.side_effect = RuntimeError("Dialog failed")
    with isolated_logging() as (path, console), patch.object(
        errors, "show_native_error", side_effect=OSError("Native dialog failed")
    ):
        errors.configure_desktop_logging()
        errors.report_desktop_error(ValueError("Original error"), window=window)
        text = path.read_text(encoding="utf-8")
        assert "Original error" in text
        assert "Dialog failed" in text
        assert "Native dialog failed" in text
        assert "Planner" in console.getvalue()


def test_working_webview_dialog_does_not_open_native_dialog():
    window = Mock()
    with isolated_logging(), patch.object(errors, "show_native_error") as native:
        errors.configure_desktop_logging()
        errors.report_desktop_error(RuntimeError("Server failed"), kind="runtime", window=window)
        window.create_confirmation_dialog.assert_called_once()
        native.assert_not_called()


def test_missing_or_invalid_dictionaries_keep_emergency_messages():
    with TemporaryDirectory(prefix="planner-error-locale-test-") as directory:
        root = Path(directory)
        (root / "en.json").write_text("not JSON", encoding="utf-8")
        (root / "it.json").write_text("[]", encoding="utf-8")
        with patch.multiple(errors, DEFAULT_LOCALES_DIR=directory, LOCALES_DIR=directory), patch.object(
            errors.locale, "getlocale", return_value=("it_IT", "UTF-8")
        ):
            assert errors.load_error_messages() == errors.FALLBACK_MESSAGES


def test_italian_messages_override_defaults_and_ignore_invalid_values():
    with TemporaryDirectory(prefix="planner-error-locale-test-") as directory:
        root = Path(directory)
        (root / "it.json").write_text(json.dumps({
            "desktop.errors.title": "Errore di prova",
            "desktop.errors.runtime": 123,
        }), encoding="utf-8")
        with patch.multiple(errors, DEFAULT_LOCALES_DIR=directory, LOCALES_DIR=directory), patch.object(
            errors.locale, "getlocale", return_value=("it_IT", "UTF-8")
        ):
            messages = errors.load_error_messages()
            assert messages["desktop.errors.title"] == "Errore di prova"
            assert messages["desktop.errors.runtime"] == errors.FALLBACK_MESSAGES["desktop.errors.runtime"]


def test_native_fallback_uses_windows_api_without_importing_webview():
    with patch.object(errors.sys, "platform", "win32"), patch.object(
        errors.ctypes, "windll", create=True
    ) as windows:
        windows.user32.MessageBoxW.return_value = 1
        assert errors.show_native_error("Title", "Message")
        windows.user32.MessageBoxW.assert_called_once_with(None, "Message", "Title", 0x10)


def test_backend_logs_share_rotating_file_and_can_be_detached():
    with isolated_logging() as (path, console):
        errors.configure_desktop_logging()
        handlers = errors.attach_backend_logging()
        logging.getLogger("uvicorn.error").error("Backend startup failed")
        assert "Backend startup failed" in path.read_text(encoding="utf-8")
        errors.detach_backend_logging(handlers)
        assert all(handler not in logging.getLogger("uvicorn.error").handlers for handler in handlers)


def test_error_categories_distinguish_frontend_timeout_and_runtime():
    missing = FileNotFoundError(
        errno.ENOENT, "Missing interface", str(Path(errors.FRONTEND_DIST_DIR) / "index.html")
    )
    assert errors.error_message_key(missing, "startup") == "desktop.errors.frontend"
    assert errors.error_message_key(TimeoutError(), "startup") == "desktop.errors.timeout"
    assert errors.error_message_key(ImportError(), "startup") == "desktop.errors.renderer"
    assert errors.error_message_key(RuntimeError(), "runtime") == "desktop.errors.runtime"
    assert errors.error_message_key(RuntimeError(), "shutdown") == "desktop.errors.shutdown"


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
