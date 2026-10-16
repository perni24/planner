import asyncio
import json
import unittest
from unittest.mock import Mock, patch

from starlette.applications import Starlette

from config import APP_VERSION
from routes import app_routes
from routes.api import all_routes
from services import app_lifecycle


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


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
