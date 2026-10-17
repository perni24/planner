import importlib.util
import json
import socket
import sqlite3
import sys
import threading
import time
import unittest
from contextlib import ExitStack, asynccontextmanager, closing, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import MagicMock, Mock, call, patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse
from starlette.routing import Route

import config
import main as application
from db import db as database
from db.repositories import mcp_repo
from middleware.shutdown_guard import shutdown_guard
from routes import event_routes
from services import event_service
from services import operation_control


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
    shown = MagicMock()
    window = Mock()
    window.events.closed = closed
    window.events.shown = shown
    window.destroy.side_effect = lambda: closed.__iadd__.call_args.args[0]()
    webview = ModuleType("webview")
    webview.settings = {"ALLOW_DOWNLOADS": False, "OPEN_EXTERNAL_LINKS_IN_BROWSER": False}
    webview.create_window = Mock(return_value=window)

    def run_gui(monitor, **kwargs):
        shown.__iadd__.call_args.args[0]()
        watcher = threading.Thread(target=monitor)
        watcher.start()
        closed.__iadd__.call_args.args[0]()
        watcher.join(timeout=2)
        assert not watcher.is_alive()

    webview.start = Mock(side_effect=run_gui)

    with ExitStack() as patches:
        patches.enter_context(patch.dict(sys.modules, webview=webview))
        patches.enter_context(patch.object(application.os.path, "isfile", return_value=True))
        configuration = patches.enter_context(patch.object(application.uvicorn, "Config"))
        patches.enter_context(patch.object(application.uvicorn, "Server", return_value=server))
        shutdown = patches.enter_context(patch.object(application, "set_shutdown_callback"))
        report = patches.enter_context(patch.object(application, "report_desktop_error"))
        try:
            yield {
                "server": server,
                "config": configuration,
                "webview": webview,
                "closed": closed,
                "shown": shown,
                "window": window,
                "report": report,
                "shutdown": shutdown,
                "threads": backend_threads,
            }
        finally:
            server.should_exit = True
            for thread in backend_threads:
                thread.join(timeout=2)
                assert not thread.is_alive()
            operation_control.reset_operations()


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
    ), patch.object(application, "configure_desktop_logging"):
        application.main()
    assert operations.mock_calls == [call.initialize(), call.start()]


def test_failed_initialization_does_not_start_server():
    error = RuntimeError("Initialization failed")
    with patch.object(application, "initialize_runtime", side_effect=error), patch.object(
        application, "start_server"
    ) as start, patch.object(application, "configure_desktop_logging"), patch.object(
        application, "report_desktop_error"
    ) as report:
        assert application.main() == 1
        start.assert_not_called()
        report.assert_called_once_with(error)


def test_desktop_runs_backend_in_thread_and_stops_it_after_window_closes():
    with mocked_desktop() as mocks:
        assert application.start_server() == 0
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
        mocks["webview"].start.assert_called_once()
        assert callable(mocks["webview"].start.call_args.args[0])
        assert mocks["webview"].start.call_args.kwargs == {
            "gui": application.WEBVIEW_GUI,
            "debug": application.DEBUG,
            "private_mode": False,
            "storage_path": application.WEBVIEW_STORAGE_DIR,
        }
        assert mocks["webview"].settings["ALLOW_DOWNLOADS"] is True
        assert mocks["webview"].settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] is True
        mocks["report"].assert_not_called()
        mocks["closed"].__iadd__.assert_called_once()
        assert mocks["server"].should_exit is True
        assert len(mocks["threads"]) == 1
        assert mocks["threads"][0] is not threading.main_thread()
        assert not mocks["threads"][0].daemon
        assert not mocks["threads"][0].is_alive()
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
        error = expect_error(FileNotFoundError, application.start_server)
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


def test_shutdown_timeout_reports_once_and_waits_for_safe_thread_cleanup():
    with mocked_desktop() as mocks, patch.object(application, "SERVER_SHUTDOWN_TIMEOUT_SECONDS", 0.001):
        released = threading.Event()

        def backend_with_slow_cleanup():
            mocks["threads"].append(threading.current_thread())
            mocks["server"].started = True
            assert released.wait(timeout=2)

        def report(error, **kwargs):
            assert kwargs == {"kind": "shutdown"}
            assert mocks["threads"][0].is_alive()
            released.set()

        mocks["server"].run.side_effect = backend_with_slow_cleanup
        mocks["report"].side_effect = report
        # Evita un monitor simulato che attenda prima del join del coordinatore.
        mocks["webview"].start.side_effect = None
        assert application.start_server() == 1
        mocks["report"].assert_called_once()
        assert not mocks["threads"][0].is_alive()
        assert mocks["shutdown"].call_args_list[-1] == call(None)


def test_runtime_initialization_deadline_prevents_database_start():
    with patch.object(application, "RUNTIME_INITIALIZATION_TIMEOUT_SECONDS", 0.001), patch.object(
        application, "ensure_runtime_directories", side_effect=lambda: time.sleep(0.01)
    ), patch.object(application, "ensure_default_locales") as locales, patch.object(
        application, "init_db"
    ) as database:
        expect_error(TimeoutError, application.initialize_runtime)
        locales.assert_not_called()
        database.assert_not_called()


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
        def shutdown_from_api(monitor, **kwargs):
            mocks["shown"].__iadd__.call_args.args[0]()
            mocks["shutdown"].call_args_list[0].args[0]()
            assert mocks["server"].should_exit is True
            monitor()

        mocks["webview"].start.side_effect = shutdown_from_api
        assert application.start_server() == 0
        mocks["window"].destroy.assert_called_once_with()
        mocks["report"].assert_not_called()
        assert not mocks["threads"][0].is_alive()


def test_config_disables_reload_even_when_requested_in_environment():
    with patch.dict("os.environ", RELOAD="1"):
        spec = importlib.util.spec_from_file_location("planner_config_test", config.__file__)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.RELOAD is False


def test_runtime_creates_profile_directory_without_overwriting_existing_data():
    with TemporaryDirectory(prefix="planner-profile-test-") as directory:
        root = Path(directory)
        profile = root / "data" / "webview"
        with patch.multiple(
            config,
            DATA_DIR=str(root / "data"),
            LOCALES_DIR=str(root / "locales"),
            WEBVIEW_STORAGE_DIR=str(profile),
        ):
            config.ensure_runtime_directories()
            assert profile.is_dir()
            marker = profile / "existing-profile"
            marker.write_text("keep", encoding="utf-8")
            config.ensure_runtime_directories()
            assert marker.read_text(encoding="utf-8") == "keep"


def test_development_profile_is_inside_development_data_directory():
    with patch.object(sys, "frozen", False, create=True):
        spec = importlib.util.spec_from_file_location("planner_development_config_test", config.__file__)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    assert Path(module.WEBVIEW_STORAGE_DIR) == Path(module.BACKEND_DIR) / "db" / "webview"


def test_portable_profile_is_beside_executable_and_not_inside_bundle():
    with TemporaryDirectory(prefix="planner-portable-profile-test-") as directory:
        root = Path(directory)
        with patch.object(sys, "frozen", True, create=True), patch.object(
            sys, "executable", str(root / "PlannerApp.exe")
        ), patch.object(sys, "_MEIPASS", str(root / "_internal"), create=True):
            spec = importlib.util.spec_from_file_location("planner_portable_config_test", config.__file__)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        assert Path(module.WEBVIEW_STORAGE_DIR) == root / "data" / "webview"
        module.ensure_runtime_directories()
        assert (root / "data" / "webview").is_dir()
        assert not (root / "_internal").exists()


def test_invalid_profile_directory_stops_initialization_before_database_access():
    with TemporaryDirectory(prefix="planner-profile-error-test-") as directory:
        root = Path(directory)
        profile = root / "webview"
        profile.write_text("not a directory", encoding="utf-8")
        with patch.multiple(
            config, DATA_DIR=str(root / "data"), LOCALES_DIR=str(root / "locales"),
            WEBVIEW_STORAGE_DIR=str(profile),
        ), patch.object(application, "init_db") as init_db:
            expect_error(FileExistsError, application.initialize_runtime)
            init_db.assert_not_called()


def test_runtime_backend_failure_is_reported_once_and_closes_window():
    for failure in (None, RuntimeError("Simulated backend crash")):
        with mocked_desktop() as mocks:
            fail = threading.Event()

            def crash_backend():
                mocks["threads"].append(threading.current_thread())
                mocks["server"].started = True
                assert fail.wait(timeout=2)
                if failure is not None:
                    raise failure

            def run_gui(monitor, **kwargs):
                mocks["shown"].__iadd__.call_args.args[0]()
                fail.set()
                monitor()

            mocks["server"].run.side_effect = crash_backend
            mocks["webview"].start.side_effect = run_gui
            assert application.start_server() == 1
            mocks["window"].destroy.assert_called_once_with()
            mocks["report"].assert_called_once()
            call_args = mocks["report"].call_args
            assert call_args.kwargs == {"kind": "runtime", "window": mocks["window"]}
            assert call_args.args[0].__cause__ is failure


def test_closing_window_while_crash_dialog_is_open_reports_only_once():
    with mocked_desktop() as mocks, patch.object(application, "configure_desktop_logging"), patch.object(
        application, "initialize_runtime"
    ):
        crash = threading.Event()
        dialog_open = threading.Event()
        dialog_dismissed = threading.Event()
        watchers = []

        def crash_backend():
            mocks["threads"].append(threading.current_thread())
            mocks["server"].started = True
            assert crash.wait(timeout=2)
            raise RuntimeError("Simulated backend crash")

        def blocking_dialog(*args, **kwargs):
            # Il messaggio resta aperto finche l'utente non lo chiude.
            if kwargs.get("window") is not None:
                dialog_open.set()
                assert dialog_dismissed.wait(timeout=5)

        def close_window_while_dialog_is_open(monitor, **kwargs):
            mocks["shown"].__iadd__.call_args.args[0]()
            watcher = threading.Thread(target=monitor)
            watchers.append(watcher)
            watcher.start()
            crash.set()
            assert dialog_open.wait(timeout=2)
            # L'utente chiude la finestra principale invece di premere OK.
            mocks["closed"].__iadd__.call_args.args[0]()

        mocks["server"].run.side_effect = crash_backend
        mocks["webview"].start.side_effect = close_window_while_dialog_is_open
        mocks["report"].side_effect = blocking_dialog
        try:
            assert application.main() == 1
            assert dialog_open.is_set() and not dialog_dismissed.is_set()
        finally:
            dialog_dismissed.set()
            for watcher in watchers:
                watcher.join(timeout=2)
                assert not watcher.is_alive()

        # Un solo messaggio, di tipo runtime: nessun secondo "errore di avvio" da main().
        mocks["report"].assert_called_once()
        assert mocks["report"].call_args.kwargs == {"kind": "runtime", "window": mocks["window"]}


def test_renderer_failure_cancels_monitor_before_window_is_shown():
    with mocked_desktop() as mocks:
        watchers = []

        def fail_before_shown(monitor, **kwargs):
            watcher = threading.Thread(target=monitor)
            watchers.append(watcher)
            watcher.start()
            raise RuntimeError("Native window could not be created")

        mocks["webview"].start.side_effect = fail_before_shown
        expect_error(RuntimeError, application.start_server)
        for watcher in watchers:
            watcher.join(timeout=1)
            assert not watcher.is_alive()
        mocks["window"].destroy.assert_not_called()
        mocks["report"].assert_not_called()


def test_keyboard_interrupt_returns_cancel_status_without_error_dialog():
    with patch.object(application, "configure_desktop_logging"), patch.object(
        application, "initialize_runtime", side_effect=KeyboardInterrupt
    ), patch.object(application, "report_desktop_error") as report:
        assert application.main() == 130
        report.assert_not_called()


def test_main_reports_startup_error_once_and_returns_failure_status():
    error = RuntimeError("Cannot start server")
    with patch.object(application, "configure_desktop_logging"), patch.object(
        application, "initialize_runtime"
    ), patch.object(application, "start_server", side_effect=error), patch.object(
        application, "report_desktop_error"
    ) as report:
        assert application.main() == 1
        report.assert_called_once_with(error)


def test_import_does_not_prepare_runtime_or_start_application():
    targets = (
        "config.ensure_runtime_directories",
        "config.ensure_default_locales",
        "db.db.init_db",
        "uvicorn.run",
        "uvicorn.Server",
        "threading.Thread",
        "services.app_lifecycle.set_shutdown_callback",
        "services.desktop_error_service.configure_desktop_logging",
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
    window.events.shown = MagicMock()
    webview = ModuleType("webview")
    webview.settings = {}
    webview.create_window = Mock(return_value=window)
    stream = None

    def visit_and_close(monitor, **kwargs):
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
    webview.settings = {}
    window = MagicMock()
    shown = MagicMock()
    window.events.shown = shown
    webview.create_window = Mock(return_value=window)
    client_threads = []
    mcp_started = threading.Event()
    cancelled = threading.Event()

    def pending_bulk(names):
        try:
            with closing(database.get_db_connection()) as conn, conn:
                conn.execute("INSERT INTO areas (name) VALUES ('Uncommitted MCP area')")
                mcp_started.set()
                conn.execute(
                    "WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n "
                    "WHERE x<100000000) SELECT sum(x) FROM n"
                ).fetchone()
        except sqlite3.OperationalError as error:
            assert error.sqlite_errorcode == sqlite3.SQLITE_INTERRUPT
            cancelled.set()
            raise

    def use_rest_and_mcp(monitor, **kwargs):
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
        request = Request(
            f"{url}/api/areas/insert_area", data=b'{"name":"Saved REST area"}',
            headers={"Origin": url, "Content-Type": "application/json"},
        )
        with urlopen(request, timeout=3) as response:
            assert response.status == 200
        result = rpc("tools/call", {
            "name": "bulk_insert_area", "arguments": {"areas": [{"name": "Saved MCP area"}]},
        }, 4, protocol)
        assert not result.get("isError", False), result

        def run_pending_mcp():
            try:
                # Il repository viene sostituito solo per simulare SQL molto lungo.
                with patch.object(mcp_repo, "bulk_insert_area", pending_bulk):
                    rpc("tools/call", {
                        "name": "bulk_insert_area", "arguments": {"areas": [{"name": "Pending"}]},
                    }, 5, protocol)
            except (OSError, ValueError):
                pass  # La connessione puo essere chiusa da Uvicorn durante lo stop.

        client = threading.Thread(target=run_pending_mcp)
        client_threads.append(client)
        client.start()
        assert mcp_started.wait(timeout=3)
        shown.__iadd__.call_args.args[0]()
        request = Request(f"{url}/api/app/shutdown", data=b"", headers={"Origin": url})
        with urlopen(request, timeout=3) as response:
            assert response.status == 200
        monitor()
        window.destroy.assert_called_once_with()

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
        ), patch.object(operation_control, "SHUTDOWN_OPERATION_GRACE_SECONDS", 0.05), patch.object(
            application.os.path, "isfile", return_value=True
        ):
            database.init_db()
            application.start_server()
            for client in client_threads:
                client.join(timeout=3)
                assert not client.is_alive()
            assert cancelled.is_set()
            with closing(sqlite3.connect(root / "planner.db")) as conn:
                assert [row[0] for row in conn.execute("SELECT name FROM areas ORDER BY id")] == [
                    "utente", "Saved REST area", "Saved MCP area",
                ]
                assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not any(thread.name == "planner-backend" for thread in threading.enumerate())


def test_window_close_cancels_inflight_rest_write_and_releases_port():
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    entered = threading.Event()
    statuses = []
    closed = MagicMock()
    window = Mock()
    window.events.closed = closed
    window.events.shown = MagicMock()
    webview = ModuleType("webview")
    webview.settings = {}
    webview.create_window = Mock(return_value=window)

    async def slow_write(request):
        with closing(database.get_db_connection()) as conn, conn:
            conn.execute("INSERT INTO areas (name) VALUES ('Uncommitted REST area')")
            entered.set()
            conn.execute(
                "WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n "
                "WHERE x<100000000) SELECT sum(x) FROM n"
            ).fetchone()
        return JSONResponse({"saved": True})

    def client_request():
        try:
            with urlopen(Request(f"{url}/write", data=b""), timeout=5) as response:
                statuses.append(response.status)
        except HTTPError as error:
            statuses.append(error.code)
            error.close()

    client = threading.Thread(target=client_request)

    def close_during_write(monitor, **kwargs):
        client.start()
        assert entered.wait(timeout=3)
        closed.__iadd__.call_args.args[0]()

    webview.start = Mock(side_effect=close_during_write)
    app = Starlette(
        routes=[Route("/write", slow_write, methods=["POST"])],
        middleware=[Middleware(shutdown_guard)],
    )
    with TemporaryDirectory(prefix="planner-rest-stop-") as directory:
        root = Path(directory)
        with patch.multiple(
            database, DATA_DIR=str(root), DB_PATH=str(root / "planner.db"),
            MIGRATION_BACKUPS_DIR=str(root / "backups"),
        ), patch.dict(sys.modules, webview=webview), patch.multiple(
            application, app=app, HOST="127.0.0.1", PORT=port, APP_URL=url,
        ), patch.object(operation_control, "SHUTDOWN_OPERATION_GRACE_SECONDS", 0.05), patch.object(
            application.os.path, "isfile", return_value=True
        ):
            database.init_db()
            try:
                assert application.start_server() == 0
            finally:
                if client.ident is not None:
                    client.join(timeout=5)
            assert not client.is_alive()
            assert statuses == [503]
            with closing(sqlite3.connect(root / "planner.db")) as conn:
                assert conn.execute("SELECT count(*) FROM areas").fetchone()[0] == 1
                assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert not any(thread.name == "planner-backend" for thread in threading.enumerate())
    with socket.socket() as probe:
        probe.settimeout(1)
        assert probe.connect_ex(("127.0.0.1", port)) != 0


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(
            function,
            setUp=operation_control.reset_operations,
            tearDown=operation_control.reset_operations,
        )
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
