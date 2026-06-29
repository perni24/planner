import os
import threading
import webbrowser

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.routing import Route
import uvicorn
from config import (
    DEBUG,
    FRONTEND_DIST_DIR,
    HOST,
    IS_PRODUCTION,
    PORT,
    RELOAD,
    ensure_default_locales,
    ensure_runtime_directories,
)
from db.db import init_db
from routes.api import all_routes


# Configurazione del Middleware CORS
# allow_origins=["*"] permette a qualsiasi frontend di connettersi (ottimo per lo sviluppo)
middleware = [
    Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
]


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
    routes = [*all_routes]
    index_path = os.path.join(FRONTEND_DIST_DIR, "index.html")

    if os.path.isfile(index_path):
        routes.append(Route("/{path:path}", endpoint=serve_frontend))

    return routes


def open_browser():
    browser_host = "127.0.0.1" if HOST in ("0.0.0.0", "::") else HOST
    webbrowser.open(f"http://{browser_host}:{PORT}")


app = Starlette(debug=DEBUG, routes=create_routes(), middleware=middleware)

if __name__ == "__main__":
    ensure_runtime_directories()
    ensure_default_locales()
    # Inizializza il DB all'avvio
    init_db()

    if IS_PRODUCTION and not RELOAD:
        threading.Timer(1.0, open_browser).start()

    # Avvia il server
    if RELOAD:
        uvicorn.run("main:app", host=HOST, port=PORT, reload=RELOAD)
    else:
        uvicorn.run(app, host=HOST, port=PORT, reload=RELOAD)
