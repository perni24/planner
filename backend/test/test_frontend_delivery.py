import asyncio
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from starlette.applications import Starlette

import main as application


async def request_frontend(path, method="GET", headers=()):
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    app = Starlette(routes=application.create_routes())
    await app({
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1", "method": method, "scheme": "http",
        "path": path, "raw_path": path.encode(), "query_string": b"",
        "root_path": "", "headers": list(headers),
        "server": ("127.0.0.1", 8000), "client": ("127.0.0.1", 12345),
    }, receive, send)
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return start["status"], dict(start["headers"]), body


def test_html_is_never_cached_at_root_explicit_index_or_react_routes():
    with TemporaryDirectory(prefix="planner-frontend-") as directory:
        content = b"<!doctype html><div id='root'>Current build</div>"
        Path(directory, "index.html").write_bytes(content)
        with patch.object(application, "FRONTEND_DIST_DIR", directory):
            for path in ("/", "/index.html", "/tasks/5", "/settings", "/calendar"):
                status, headers, body = asyncio.run(request_frontend(path))
                assert status == 200, path
                assert headers[b"cache-control"] == b"no-store", path
                assert body == content, path
                status, headers, body = asyncio.run(request_frontend(path, "HEAD"))
                assert status == 200 and body == b"", path
                assert headers[b"cache-control"] == b"no-store"


def test_new_build_is_returned_even_with_previous_cache_validators():
    with TemporaryDirectory(prefix="planner-frontend-") as directory:
        index = Path(directory, "index.html")
        index.write_text("Previous build", encoding="utf-8")
        with patch.object(application, "FRONTEND_DIST_DIR", directory):
            _, previous_headers, _ = asyncio.run(request_frontend("/"))
            index.write_text("Updated build with new asset names", encoding="utf-8")
            status, headers, body = asyncio.run(request_frontend("/", headers=[
                (b"if-none-match", previous_headers[b"etag"]),
                (b"if-modified-since", previous_headers[b"last-modified"]),
            ]))
            assert status == 200
            assert body == b"Updated build with new asset names"
            assert headers[b"cache-control"] == b"no-store"


def test_assets_and_rest_routes_are_not_replaced_by_react_html():
    with TemporaryDirectory(prefix="planner-frontend-") as directory:
        Path(directory, "index.html").write_text("Frontend", encoding="utf-8")
        Path(directory, "assets").mkdir()
        Path(directory, "assets", "index-current.js").write_text("Current JavaScript", encoding="utf-8")
        with patch.object(application, "FRONTEND_DIST_DIR", directory), patch(
            "routes.task_routes.taskRepo.get_all_tasks", return_value=[]
        ):
            for prefix in ("", "/api"):
                status, headers, body = asyncio.run(request_frontend(f"{prefix}/tasks/get_all_tasks"))
                assert status == 200 and json.loads(body) == []
                assert headers[b"content-type"].startswith(b"application/json")
            assert asyncio.run(request_frontend("/api/tasks/5"))[0] == 404
            status, headers, body = asyncio.run(request_frontend("/assets/index-current.js"))
            assert status == 200 and body == b"Current JavaScript"
            assert b"cache-control" not in headers


def test_window_url_changes_only_with_the_build_and_keeps_same_origin():
    with TemporaryDirectory(prefix="planner-frontend-") as directory:
        index = Path(directory, "index.html")
        index.write_text("First build", encoding="utf-8")
        with patch.object(application, "APP_URL", "http://127.0.0.1:8000"):
            first = application.get_frontend_url(index)
            assert first == application.get_frontend_url(index)
            index.write_text("Next build", encoding="utf-8")
            second = application.get_frontend_url(index)
            assert second != first
            for value in (first, second):
                url = urlsplit(value)
                assert (url.scheme, url.netloc, url.path) == ("http", "127.0.0.1:8000", "/")
                assert len(parse_qs(url.query)["frontend"][0]) == 16


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
