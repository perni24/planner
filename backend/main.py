import errno
import os
import sys
import threading
import time

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse
from starlette.routing import Route
import uvicorn
from config import (
    ALLOWED_HOSTS,
    APP_URL,
    DEBUG,
    FRONTEND_DIST_DIR,
    HOST,
    PORT,
    RELOAD,
    RUNTIME_INITIALIZATION_TIMEOUT_SECONDS,
    SERVER_GRACEFUL_SHUTDOWN_SECONDS,
    SERVER_SHUTDOWN_TIMEOUT_SECONDS,
    SERVER_STARTUP_TIMEOUT_SECONDS,
    WEBVIEW_GUI,
    WEBVIEW_STORAGE_DIR,
    ensure_default_locales,
    ensure_runtime_directories,
)
from db.db import init_db
from middleware.origin_guard import origin_guard
from middleware.shutdown_guard import shutdown_guard
from routes.api import all_routes
from services.app_lifecycle import set_shutdown_callback
from services.desktop_error_service import (
    attach_backend_logging,
    configure_desktop_logging,
    detach_backend_logging,
    report_desktop_error,
)
from services.event_service import close_subscribers
from services import operation_control
from contextlib import asynccontextmanager
from starlette.routing import Mount

from integration.mcp.server import mcp_app, planner_mcp

@asynccontextmanager
async def lifespan(app):
    async with planner_mcp.session_manager.run():
        try:
            yield
        finally:
            close_subscribers()

async def serve_frontend(request):
    path = request.path_params.get("path", "")
    frontend_dir = os.path.abspath(FRONTEND_DIST_DIR)
    requested_path = os.path.abspath(os.path.join(frontend_dir, path))

    is_frontend_file = (
        os.path.commonpath([frontend_dir, requested_path]) == frontend_dir
        and os.path.isfile(requested_path)
    )

    if is_frontend_file:
        return FileResponse(requested_path)

    return FileResponse(os.path.join(frontend_dir, "index.html"))


def create_routes():
    routes = [*all_routes, Mount("/mcp", app=mcp_app),]
    index_path = os.path.join(FRONTEND_DIST_DIR, "index.html")

    if os.path.isfile(index_path):
        routes.append(Route("/{path:path}", endpoint=serve_frontend))

    return routes


app = Starlette(
    debug=DEBUG,
    routes=create_routes(),
    middleware=[
        Middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS),
        Middleware(origin_guard),
        Middleware(shutdown_guard),
    ],
    lifespan=lifespan,
)


def initialize_runtime():
    """Prepara cartelle, lingue e database prima dell'avvio del server."""
    with operation_control.operation_scope(RUNTIME_INITIALIZATION_TIMEOUT_SECONDS):
        ensure_runtime_directories()
        operation_control.check_operation()
        ensure_default_locales()
        operation_control.check_operation()
        init_db()
        operation_control.check_operation()


def start_server():
    """Avvia il backend in un thread e la finestra nel thread principale."""
    operation_control.reset_operations()
    index_path = os.path.join(FRONTEND_DIST_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise FileNotFoundError(
            errno.ENOENT,
            "Frontend build not found. Run 'npm run build' in frontend first.",
            index_path,
        )

    import webview

    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True

    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        reload=RELOAD,
        timeout_graceful_shutdown=SERVER_GRACEFUL_SHUTDOWN_SECONDS,
    )
    log_handlers = attach_backend_logging()
    server = uvicorn.Server(config)
    errors = []
    backend_finished = threading.Event()
    stop_requested = threading.Event()
    unexpected_stop = threading.Event()
    window_shown = threading.Event()
    window_closed = threading.Event()
    monitor_cancelled = threading.Event()
    failure_reported = threading.Event()

    def run_backend():
        try:
            server.run()
        except BaseException as error:
            # Uvicorn solleva SystemExit anche quando la porta e gia occupata.
            errors.append(error)
        finally:
            if not stop_requested.is_set():
                unexpected_stop.set()
            backend_finished.set()

    def request_stop():
        operation_control.request_stop()
        stop_requested.set()
        server.should_exit = True
        close_subscribers()

    def on_window_closed():
        window_closed.set()
        request_stop()

    def watch_backend():
        while not backend_finished.wait(0.1):
            if monitor_cancelled.is_set():
                return
        while not window_shown.wait(0.1):
            if monitor_cancelled.is_set():
                return
        if monitor_cancelled.is_set() or window_closed.is_set():
            return
        if unexpected_stop.is_set():
            error = RuntimeError("Backend stopped unexpectedly.")
            error.__cause__ = errors[0] if errors else None
            report_desktop_error(error, kind="runtime", window=window)
            failure_reported.set()
        try:
            window.destroy()
        except Exception as error:
            report_desktop_error(error, kind="runtime")
            failure_reported.set()

    backend_thread = threading.Thread(target=run_backend, name="planner-backend", daemon=False)
    set_shutdown_callback(request_stop)
    try:
        backend_thread.start()
        wait_for_server(server, backend_thread, errors)
        window = webview.create_window(
            "Planner", APP_URL, width=1280, height=800, min_size=(800, 600)
        )
        window.events.shown += window_shown.set
        window.events.closed += on_window_closed
        webview.start(
            watch_backend,
            gui=WEBVIEW_GUI,
            debug=DEBUG,
            private_mode=False,
            storage_path=WEBVIEW_STORAGE_DIR,
        )
    finally:
        monitor_cancelled.set()
        request_stop()
        if backend_thread.ident is not None:
            backend_thread.join(timeout=SERVER_SHUTDOWN_TIMEOUT_SECONDS)
        if backend_thread.is_alive():
            error = RuntimeError(
                "Backend shutdown timed out; waiting for cooperative cleanup. "
                "Do not restart Planner until the process exits."
            )
            report_desktop_error(error, kind="shutdown")
            failure_reported.set()
            # Nessuna terminazione forzata: il thread puo avere una transazione aperta.
            backend_thread.join()
        set_shutdown_callback(None)
        detach_backend_logging(log_handlers)

    if unexpected_stop.is_set() and not failure_reported.is_set():
        error = errors[0] if errors else None
        raise RuntimeError("Backend stopped unexpectedly.") from error
    if errors and not failure_reported.is_set():
        raise RuntimeError("Backend stopped unexpectedly.") from errors[0]
    return 1 if failure_reported.is_set() else 0


def wait_for_server(server, backend_thread, errors):
    """Attende il nostro server, senza fidarsi di altri servizi sulla stessa porta."""
    deadline = time.monotonic() + SERVER_STARTUP_TIMEOUT_SECONDS
    while not server.started:
        if not backend_thread.is_alive():
            error = errors[0] if errors else None
            raise RuntimeError("Backend failed to start. Check the server logs.") from error
        if time.monotonic() >= deadline:
            raise TimeoutError("Backend startup timed out.")
        time.sleep(0.05)

    if not backend_thread.is_alive() or server.should_exit:
        error = errors[0] if errors else None
        raise RuntimeError("Backend stopped before the window could be opened.") from error


def main():
    try:
        operation_control.reset_operations()
        configure_desktop_logging()
        initialize_runtime()
        return start_server()
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        report_desktop_error(error)
        return 1


if __name__ == "__main__":
    sys.exit(main())
