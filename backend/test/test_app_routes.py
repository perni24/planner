import asyncio
import json
import time
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from starlette.applications import Starlette

from config import APP_VERSION
from routes import app_routes
from routes.api import all_routes
from services import app_lifecycle, update_service


async def request_app(path, method="GET"):
    app = Starlette(routes=all_routes)
    messages = []
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"127.0.0.1:8000")],
        "server": ("127.0.0.1", 8000),
        "client": ("127.0.0.1", 12345),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    status = next(message["status"] for message in messages if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return status, body


def test_old_heartbeat_endpoint_is_removed_at_root_and_under_api():
    for prefix in ("", "/api"):
        status, _ = asyncio.run(request_app(f"{prefix}/app/heartbeat", "POST"))
        assert status == 404


def test_shutdown_still_calls_registered_callback_at_root_and_under_api():
    callback = Mock()
    with patch.object(app_lifecycle, "_shutdown_callback", callback):
        for prefix in ("", "/api"):
            status, body = asyncio.run(request_app(f"{prefix}/app/shutdown", "POST"))
            assert status == 200
            assert json.loads(body) == {"message": "shutdown requested"}
    assert callback.call_count == 2


def test_version_and_update_check_remain_available_without_heartbeat():
    update = {"update_available": False, "current_version": APP_VERSION}
    with patch.object(app_routes, "check_update", return_value=update) as check_update:
        for prefix in ("", "/api"):
            status, body = asyncio.run(request_app(f"{prefix}/app/version"))
            assert status == 200
            assert json.loads(body) == {"version": APP_VERSION}
            status, body = asyncio.run(request_app(f"{prefix}/app/check_update"))
            assert status == 200
            assert json.loads(body) == update
    assert check_update.call_count == 2


def test_update_check_does_not_block_other_requests():
    order = []

    def slow_check_update():
        time.sleep(0.5)
        order.append("check_update")
        return {"update_available": False}

    async def scenario():
        update_request = asyncio.create_task(request_app("/api/app/check_update"))
        await asyncio.sleep(0.05)
        status, _ = await request_app("/api/app/version")
        assert status == 200
        order.append("version")
        status, _ = await update_request
        assert status == 200

    with patch.object(app_routes, "check_update", slow_check_update):
        asyncio.run(scenario())
    # Se il controllo bloccasse il loop eventi, /version risponderebbe solo dopo.
    assert order == ["version", "check_update"]


def test_update_check_reports_network_errors_without_raising():
    errors = (
        URLError("no network"),
        HTTPError(update_service.GITHUB_LATEST_RELEASE_API, 503, "Unavailable", None, None),
        TimeoutError("read timed out"),
        ConnectionResetError("connection reset"),
        ValueError("invalid JSON"),
    )
    for error in errors:
        with patch.object(update_service, "get_latest_release", side_effect=error):
            result = update_service.check_update()
        assert result["update_available"] is False
        assert result["latest_version"] is None
        assert result["error"] == "Unable to check for updates"

    for release in ({}, {"tag_name": None}, {"tag_name": "v1.0.0-beta"}, []):
        with patch.object(update_service, "get_latest_release", return_value=release):
            assert update_service.check_update()["error"] == "Unable to check for updates"


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
