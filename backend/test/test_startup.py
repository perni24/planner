import importlib.util
import json
import socket
import sys
import threading
import time
import unittest
from contextlib import ExitStack, asynccontextmanager, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import MagicMock, Mock, call, patch
from urllib.request import Request, urlopen

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

import config
import main as application
from db import db as database
from routes import event_routes
from services import event_service


@contextmanager
def mocked_desktop():
    server = Mock(started=False, should_exit=False)
    backend_threads = []

    def run_backend():
        backend_threads.append(threading.current_thread())
        server.started = True
        while not server.should_exit:
            time.sleep(0.001)

    server.run.side_effect = run_backend
    closed = MagicMock()
    window = Mock()
    window.events.closed = closed
    webview = ModuleType("webview")
    webview.create_window = Mock(return_value=window)
    webview.start = Mock(side_effect=lambda **kwargs: closed.__iadd__.call_args.args[0]())

    with ExitStack() as patches:
        patches.enter_context(patch.dict(sys.modules, webview=webview))
        patches.enter_context(patch.object(application.os.path, "isfile", return_value=True))
        configuration = patches.enter_context(patch.object(application.uvicorn, "Config"))
        patches.enter_context(patch.object(application.uvicorn, "Server", return_value=server))
        shutdown = patches.enter_context(patch.object(application, "set_shutdown_callback"))
        heartbeat = patches.enter_context(patch("services.app_lifecycle.start_heartbeat_monitor"))
        try:
            yield {
                "server": server,
                "config": configuration,
                "webview": webview,
                "closed": closed,
                "shutdown": shutdown,
                "heartbeat": heartbeat,
                "threads": backend_threads,
            }
        finally:
            server.should_exit = True
            for thread in backend_threads:
                thread.join(timeout=2)
                assert not thread.is_alive()


def expect_error(exception, operation):
    try:
        operation()
    except exception as error:
        return error
    raise AssertionError(f"Expected {exception.__name__}")


def test_initialize_runtime_preserves_preparation_order():
    operations = Mock()
    with patch.multiple(
        application,
        ensure_runtime_directories=operations.directories,
        ensure_default_locales=operations.locales,
        init_db=operations.database,
    ):
        application.initialize_runtime()
    assert operations.mock_calls == [call.directories(), call.locales(), call.database()]


def test_main_prepares_runtime_before_starting_server():
    operations = Mock()
    with patch.multiple(
        application,
        initialize_runtime=operations.initialize,
        start_server=operations.start,
    ):
        application.main()
    assert operations.mock_calls == [call.initialize(), call.start()]


def test_failed_initialization_does_not_start_server():
    error = RuntimeError("Initialization failed")
    with patch.object(application, "initialize_runtime", side_effect=error), patch.object(
        application, "start_server"
    ) as start:
        assert expect_error(RuntimeError, application.main) is error
        start.assert_not_called()


def test_desktop_runs_backend_in_thread_and_stops_it_after_window_closes():
    with mocked_desktop() as mocks:
        application.start_server()
        mocks["config"].assert_called_once_with(
            application.app,
            host=application.HOST,
            port=application.PORT,
            reload=False,
            timeout_graceful_shutdown=application.SERVER_GRACEFUL_SHUTDOWN_SECONDS,
        )
        mocks["webview"].create_window.assert_called_once_with(
            "Planner", application.APP_URL, width=1280, height=800, min_size=(800, 600)
        )
        mocks["webview"].start.assert_called_once_with(
            gui=application.WEBVIEW_GUI, debug=application.DEBUG
        )
        mocks["closed"].__iadd__.assert_called_once()
        assert mocks["server"].should_exit is True
        assert len(mocks["threads"]) == 1
        assert mocks["threads"][0] is not threading.main_thread()
        assert not mocks["threads"][0].daemon
        assert not mocks["threads"][0].is_alive()
        mocks["heartbeat"].assert_not_called()
        assert mocks["shutdown"].call_args_list[-1] == call(None)


def test_window_opens_on_main_thread_only_after_backend_is_ready():
    with mocked_desktop() as mocks:
        def create_window(*args, **kwargs):
            assert threading.current_thread() is threading.main_thread()
            assert mocks["server"].started
            assert mocks["threads"][0].is_alive()
            return mocks["webview"].create_window.return_value

        mocks["webview"].create_window.side_effect = create_window
        mocks["webview"].start.side_effect = None
        application.start_server()


def test_missing_frontend_does_not_start_backend_or_open_window():
    with mocked_desktop() as mocks, patch.object(
        application.os.path, "isfile", return_value=False
    ):
        error = expect_error(RuntimeError, application.start_server)
        assert "npm run build" in str(error)
        mocks["config"].assert_not_called()
        mocks["server"].run.assert_not_called()
        mocks["webview"].create_window.assert_not_called()


def test_backend_bind_failure_does_not_open_a_window_on_another_service():
    with mocked_desktop() as mocks:
        failure = SystemExit(1)
        mocks["server"].run.side_effect = failure
        error = expect_error(RuntimeError, application.start_server)
        assert error.__cause__ is failure
        mocks["webview"].create_window.assert_not_called()
        assert mocks["server"].should_exit


def test_backend_startup_timeout_requests_shutdown():
    with mocked_desktop() as mocks, patch.object(
        application, "SERVER_STARTUP_TIMEOUT_SECONDS", 0.01
    ):
        def never_ready():
            mocks["threads"].append(threading.current_thread())
            while not mocks["server"].should_exit:
                time.sleep(0.001)

        mocks["server"].run.side_effect = never_ready
        expect_error(TimeoutError, application.start_server)
        mocks["webview"].create_window.assert_not_called()
        assert not mocks["threads"][0].is_alive()


def test_renderer_failure_stops_backend_and_propagates_error():
    with mocked_desktop() as mocks:
        error = RuntimeError("Renderer not available")
        mocks["webview"].start.side_effect = error
        assert expect_error(RuntimeError, application.start_server) is error
        assert not mocks["threads"][0].is_alive()


def test_window_creation_failure_stops_backend():
    with mocked_desktop() as mocks:
        error = RuntimeError("Window creation failed")
        mocks["webview"].create_window.side_effect = error
        assert expect_error(RuntimeError, application.start_server) is error
        mocks["webview"].start.assert_not_called()
        assert not mocks["threads"][0].is_alive()


def test_shutdown_route_callback_requests_backend_stop():
    with mocked_desktop() as mocks:
        def shutdown_from_api(**kwargs):
            mocks["shutdown"].call_args_list[0].args[0]()
            assert mocks["server"].should_exit is True

        mocks["webview"].start.side_effect = shutdown_from_api
        application.start_server()
        assert not mocks["threads"][0].is_alive()


def test_config_disables_reload_even_when_requested_in_environment():
    with patch.dict("os.environ", RELOAD="1"):
        spec = importlib.util.spec_from_file_location("planner_config_test", config.__file__)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.RELOAD is False


def test_import_does_not_prepare_runtime_or_start_application():
    targets = (
        "config.ensure_runtime_directories",
        "config.ensure_default_locales",
        "db.db.init_db",
        "uvicorn.run",
        "uvicorn.Server",
        "threading.Thread",
        "services.app_lifecycle.set_shutdown_callback",
        "services.app_lifecycle.start_heartbeat_monitor",
    )
    with ExitStack() as patches:
        mocks = [patches.enter_context(patch(target)) for target in targets]
        patches.enter_context(patch.dict(sys.modules, webview=None))
        spec = importlib.util.spec_from_file_location("planner_import_test", application.__file__)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for operation in mocks:
            operation.assert_not_called()


def test_real_server_serves_health_and_closes_an_open_sse_connection():
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            event_service.close_subscribers()

    async def health(request):
        return JSONResponse({"status": "online"})

    app = Starlette(
        routes=[Route("/api/health", health), *event_routes.routes],
        lifespan=lifespan,
    )
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    closed = MagicMock()
    window = Mock()
    window.events.closed = closed
    webview = ModuleType("webview")
    webview.create_window = Mock(return_value=window)
    stream = None

    def visit_and_close(**kwargs):
        nonlocal stream
        with urlopen(f"{url}/api/health", timeout=2) as response:
            assert response.status == 200
        stream = urlopen(f"{url}/events", timeout=2)
        assert stream.status == 200
        closed.__iadd__.call_args.args[0]()

    webview.start = Mock(side_effect=visit_and_close)
    try:
        with patch.dict(sys.modules, webview=webview), patch.multiple(
            application,
            app=app,
            HOST="127.0.0.1",
            PORT=port,
            APP_URL=url,
            SERVER_GRACEFUL_SHUTDOWN_SECONDS=0.1,
        ), patch.object(application.os.path, "isfile", return_value=True):
            application.start_server()
        assert not any(thread.name == "planner-backend" for thread in threading.enumerate())
        with socket.socket() as probe:
            probe.settimeout(1)
            assert probe.connect_ex(("127.0.0.1", port)) != 0
    finally:
        if stream is not None:
            stream.close()
        event_service.close_subscribers()


def test_real_application_serves_rest_and_mcp_using_temporary_database():
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    webview = ModuleType("webview")
    webview.create_window = Mock(return_value=MagicMock())

    def use_rest_and_mcp(**kwargs):
        with urlopen(f"{url}/api/areas/get_all_areas", timeout=3) as response:
            areas = json.load(response)
            assert len(areas) == 1
            assert areas[0]["name"] == "utente"

        def rpc(method, params, identifier, protocol=None):
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Origin": url,
            }
            if protocol:
                headers["MCP-Protocol-Version"] = protocol
            request = Request(
                f"{url}/mcp/",
                data=json.dumps({
                    "jsonrpc": "2.0", "id": identifier, "method": method, "params": params
                }).encode(),
                headers=headers,
            )
            with urlopen(request, timeout=3) as response:
                payload = json.load(response)
                assert "error" not in payload, payload
                return payload["result"]

        initialization = rpc("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "planner-startup-test", "version": "1.0"},
        }, 1)
        protocol = initialization["protocolVersion"]
        tools = rpc("tools/list", {}, 2, protocol)
        assert any(tool["name"] == "get_all_areas" for tool in tools["tools"])
        result = rpc("tools/call", {"name": "get_all_areas", "arguments": {}}, 3, protocol)
        assert not result.get("isError", False), result
        content = json.loads(result["content"][0]["text"])
        assert content["area_count"] == 1

    webview.start = Mock(side_effect=use_rest_and_mcp)
    with TemporaryDirectory(prefix="planner-desktop-test-") as directory:
        root = Path(directory)
        with patch.multiple(
            database,
            DATA_DIR=str(root),
            DB_PATH=str(root / "planner.db"),
            MIGRATION_BACKUPS_DIR=str(root / "migration_backups"),
        ), patch.dict(sys.modules, webview=webview), patch.multiple(
            application, HOST="127.0.0.1", PORT=port, APP_URL=url,
        ), patch.object(application.os.path, "isfile", return_value=True):
            database.init_db()
            application.start_server()
    assert not any(thread.name == "planner-backend" for thread in threading.enumerate())


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
