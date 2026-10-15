import os
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
    SERVER_GRACEFUL_SHUTDOWN_SECONDS,
    SERVER_SHUTDOWN_TIMEOUT_SECONDS,
    SERVER_STARTUP_TIMEOUT_SECONDS,
    WEBVIEW_GUI,
    ensure_default_locales,
    ensure_runtime_directories,
)
from db.db import init_db
from middleware.origin_guard import origin_guard
from routes.api import all_routes
from services.app_lifecycle import set_shutdown_callback
from services.event_service import close_subscribers
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
    ],
    lifespan=lifespan,
)


def initialize_runtime():
    """Prepara cartelle, lingue e database prima dell'avvio del server."""
    ensure_runtime_directories()
    ensure_default_locales()
    init_db()


def start_server():
    """Avvia il backend in un thread e la finestra nel thread principale."""
    index_path = os.path.join(FRONTEND_DIST_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise RuntimeError("Frontend build not found. Run 'npm run build' in frontend first.")

    import webview

    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        reload=RELOAD,
        timeout_graceful_shutdown=SERVER_GRACEFUL_SHUTDOWN_SECONDS,
    )
    server = uvicorn.Server(config)
    errors = []

    def run_backend():
        try:
            server.run()
        except BaseException as error:
            # Uvicorn solleva SystemExit anche quando la porta e gia occupata.
            errors.append(error)

    def request_stop():
        server.should_exit = True

    backend_thread = threading.Thread(target=run_backend, name="planner-backend", daemon=False)
    set_shutdown_callback(request_stop)
    try:
        backend_thread.start()
        wait_for_server(server, backend_thread, errors)
        window = webview.create_window(
            "Planner", APP_URL, width=1280, height=800, min_size=(800, 600)
        )
        window.events.closed += request_stop
        webview.start(gui=WEBVIEW_GUI, debug=DEBUG)
    finally:
        request_stop()
        if backend_thread.ident is not None:
            backend_thread.join(timeout=SERVER_SHUTDOWN_TIMEOUT_SECONDS)
        if backend_thread.is_alive():
            raise RuntimeError("Backend shutdown timed out; the server thread is still running.")
        set_shutdown_callback(None)

    if errors:
        raise RuntimeError("Backend stopped unexpectedly.") from errors[0]


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
    initialize_runtime()
    start_server()


if __name__ == "__main__":
    main()
