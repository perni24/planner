import asyncio
from contextlib import contextmanager, redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from starlette.requests import Request

from db import db as database
from db.repositories import setting_repo
from routes import locale_routes, setting_routes
from services import locale_service, operation_control
from validators.settings_validator import (
    ALLOWED_THEMES,
    COLOR_KEYS,
    validate_language_settings,
    validate_theme_settings,
)


COLORS = {key: "#12Ab34" for key in COLOR_KEYS}


@contextmanager
def isolated_locales():
    with TemporaryDirectory(prefix="planner-settings-locales-") as directory:
        external = Path(directory) / "external"
        bundled = Path(directory) / "bundled"
        external.mkdir()
        bundled.mkdir()
        with patch.multiple(locale_service, LOCALES_DIR=str(external), DEFAULT_LOCALES_DIR=str(bundled)):
            yield external, bundled


def write_dictionary(directory, language, text="Translation"):
    path = directory / f"{language}.json"
    path.write_text(json.dumps({"settings.title": text}), encoding="utf-8")
    return path


async def invoke(endpoint, payload=None, raw_body=None):
    body = json.dumps(payload).encode() if raw_body is None else raw_body

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request({
        "type": "http", "method": "POST", "path": "/test",
        "headers": [], "query_string": b"",
    }, receive)
    return await endpoint(request)


def test_theme_validation_accepts_all_modes_and_preserves_color_values():
    for theme in ALLOWED_THEMES:
        values, error = validate_theme_settings({"theme": theme, "custom_colors": COLORS})
        assert error is None
        assert values == {"theme": theme, "custom_colors": COLORS}
        assert values["custom_colors"] is not COLORS


def test_theme_validation_rejects_non_objects_and_unknown_modes():
    for data in (None, [], True, 1, "dark", {}):
        values, error = validate_theme_settings(data)
        assert values is None and error
    for theme in (None, True, 1, [], {}, "", "blue", "Dark", " dark "):
        values, error = validate_theme_settings({"theme": theme, "custom_colors": COLORS})
        assert values is None and "theme" in error


def test_color_validation_requires_exact_object_keys():
    invalid = [None, [], "#123456", True, 7, {}, {**COLORS, "unexpected": "#123456"}]
    invalid.extend({key: value for key, value in COLORS.items() if key != missing} for missing in COLOR_KEYS)
    for colors in invalid:
        values, error = validate_theme_settings({"theme": "custom", "custom_colors": colors})
        assert values is None and "custom_colors" in error


def test_every_color_requires_six_hex_digits():
    for key in COLOR_KEYS:
        for value in (None, True, 7, [], {}, "", "red", "#123", "#12345678", "123456", "#GGGGGG", " #123456", "#123456\n"):
            values, error = validate_theme_settings({"theme": "custom", "custom_colors": {**COLORS, key: value}})
            assert values is None and f"custom_colors.{key}" in error


def test_language_validation_accepts_custom_and_regional_dictionaries():
    with isolated_locales() as (external, bundled):
        for language in ("it", "en", "fr", "pt-BR"):
            write_dictionary(external, language)
            assert validate_language_settings({"language": language}) == ({"language": language}, None)
        assert locale_service.get_available_languages() == ["en", "fr", "it", "pt-BR"]


def test_language_codes_and_missing_dictionaries_are_rejected():
    with isolated_locales() as (external, bundled):
        write_dictionary(external, "it")
        for language in (None, True, 7, [], {}, "", "../it", "it/..", "it.json", "IT", "en-us", "it\n", "zz"):
            values, error = validate_language_settings({"language": language})
            assert values is None and "language" in error
        for data in (None, [], True, 7, "it", {}):
            values, error = validate_language_settings(data)
            assert values is None and error


def test_invalid_json_dictionaries_are_rejected_and_not_listed():
    invalid = (b"not JSON", b"[]", b"{}", b"null", b'{"key": 1}', b'{"key": null}', b'{"key": {}}', b'{"": "text"}', b"\xff")
    with isolated_locales() as (external, bundled):
        for content in invalid:
            (external / "fr.json").write_bytes(content)
            values, error = validate_language_settings({"language": "fr"})
            assert values is None and "dictionary" in error
            assert locale_service.get_available_languages() == []
        (external / "fr.json").unlink()
        (external / "fr.json").mkdir()
        assert locale_service.get_available_languages() == []


def test_unreadable_dictionary_is_rejected():
    with patch("services.locale_service.open", side_effect=PermissionError("unreadable"), create=True):
        values, error = validate_language_settings({"language": "it"})
        assert values is None and "dictionary" in error


def test_language_loading_prefers_external_then_bundled_selected_dictionary():
    with isolated_locales() as (external, bundled), patch.object(locale_service, "get_current_language", return_value="fr"):
        external_path = write_dictionary(external, "fr", "External French")
        write_dictionary(bundled, "fr", "Bundled French")
        write_dictionary(external, "it", "Italian")
        assert locale_service.load_language()["settings.title"] == "External French"
        external_path.write_text("broken JSON", encoding="utf-8")
        assert locale_service.load_language()["settings.title"] == "Bundled French"
        assert external_path.read_text(encoding="utf-8") == "broken JSON"


def test_deleted_selected_dictionary_falls_back_without_changing_files_or_settings():
    with isolated_locales() as (external, bundled), patch.object(locale_service, "get_current_language", return_value="fr") as current:
        french = write_dictionary(external, "fr")
        write_dictionary(external, "it", "Italian")
        write_dictionary(bundled, "en", "English")
        assert validate_language_settings({"language": "fr"})[1] is None
        french.unlink()
        before = {path: path.read_bytes() for path in external.glob("*.json")}
        with patch.object(setting_repo, "update_language") as update:
            assert locale_service.load_language()["settings.title"] == "Italian"
            update.assert_not_called()
        assert {path: path.read_bytes() for path in external.glob("*.json")} == before
        assert current.return_value == "fr"
        (external / "it.json").write_text("[]", encoding="utf-8")
        assert locale_service.load_language()["settings.title"] == "English"


def test_invalid_saved_code_uses_default_and_all_missing_dictionaries_return_503():
    with isolated_locales() as (external, bundled), patch.object(locale_service, "get_current_language", return_value="../../bad"):
        path = write_dictionary(bundled, "it", "Bundled Italian")
        assert locale_service.load_language()["settings.title"] == "Bundled Italian"
        path.unlink()
        response = asyncio.run(invoke(locale_routes.load_language))
        assert response.status_code == 503
        assert json.loads(response.body) == {"error": "No usable language dictionary is available"}


def test_missing_locales_directory_returns_empty_language_list():
    with isolated_locales() as (external, bundled):
        external.rmdir()
        assert locale_service.get_available_languages() == []


def test_settings_routes_reject_malformed_json_and_non_object_payloads_before_writes():
    with patch.object(setting_routes, "settingRepo") as repository:
        for endpoint in (setting_routes.update_language, setting_routes.update_theme):
            for body in (b"{", b"\xff", b"[]", b"null", b'"text"', b"7", b"false"):
                response = asyncio.run(invoke(endpoint, raw_body=body))
                assert response.status_code == 400
                assert isinstance(json.loads(response.body)["error"], str)
        assert repository.mock_calls == []


def test_settings_routes_validate_then_write_only_complete_values():
    with isolated_locales() as (external, bundled), patch.object(setting_routes, "settingRepo") as repository:
        write_dictionary(external, "pt-BR")
        response = asyncio.run(invoke(setting_routes.update_language, {"language": "pt-BR"}))
        assert response.status_code == 200
        repository.update_language.assert_called_once_with("pt-BR")
        for theme in ALLOWED_THEMES:
            response = asyncio.run(invoke(setting_routes.update_theme, {"theme": theme, "custom_colors": COLORS}))
            assert response.status_code == 200
            repository.update_theme.assert_called_with(theme, COLORS)


def test_invalid_settings_leave_database_values_unchanged():
    with isolated_locales(), TemporaryDirectory(prefix="planner-settings-db-") as directory:
        root = Path(directory)
        with patch.multiple(database, DATA_DIR=str(root), DB_PATH=str(root / "planner.db"), MIGRATION_BACKUPS_DIR=str(root / "backups")), redirect_stdout(StringIO()):
            database.init_db()
            before = setting_repo.get_all_settings()
            for endpoint, payload in (
                (setting_routes.update_language, {"language": "zz"}),
                (setting_routes.update_language, {"language": ["it"]}),
                (setting_routes.update_theme, {"theme": "blue", "custom_colors": COLORS}),
                (setting_routes.update_theme, {"theme": "custom", "custom_colors": {"background": "#123456"}}),
                (setting_routes.update_theme, {"theme": "custom", "custom_colors": {**COLORS, "card": "invalid"}}),
            ):
                response = asyncio.run(invoke(endpoint, payload))
                assert response.status_code == 400
                assert setting_repo.get_all_settings() == before
            response = asyncio.run(invoke(setting_routes.update_theme, {"theme": "custom", "custom_colors": COLORS}))
            assert response.status_code == 200
            after = setting_repo.get_all_settings()
            assert after["theme"] == "custom"
            assert after["custom_hover_text"] == COLORS["hoverText"]


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function, setUp=operation_control.reset_operations, tearDown=operation_control.reset_operations)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
