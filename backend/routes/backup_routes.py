import asyncio
import os
from datetime import datetime
from tempfile import TemporaryDirectory

from anyio import CancelScope
from starlette.concurrency import run_in_threadpool
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

from config import DATA_DIR, DB_PATH
from db.db import backup_database


async def download_backup(request):
    if not os.path.isfile(DB_PATH):
        return JSONResponse({"error": "database not found"}, status_code=404)

    backup_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    async def send_backup(scope, receive, send):
        # La risposta ASGI mantiene la copia fino alla fine dell'invio, anche in errore.
        with TemporaryDirectory(prefix="planner-backup-", dir=DATA_DIR) as directory:
            backup_path = os.path.join(directory, "planner.db")
            backup_task = asyncio.create_task(run_in_threadpool(backup_database, backup_path))
            try:
                await asyncio.shield(backup_task)
            except asyncio.CancelledError:
                # Prima della pulizia attendi che il worker abbia chiuso SQLite.
                with CancelScope(shield=True):
                    await backup_task
                raise
            response = FileResponse(
                backup_path,
                filename=f"planner_backup_{backup_date}.db",
                media_type="application/octet-stream",
                headers={"Cache-Control": "no-store"},
            )
            # Il file va letto prima della pulizia, non delegato al server con pathsend.
            response_scope = dict(scope)
            response_scope["extensions"] = {
                name: value
                for name, value in scope.get("extensions", {}).items()
                if name != "http.response.pathsend"
            }
            await response(response_scope, receive, send)

    return send_backup


routes = [
    Route("/download", endpoint=download_backup),
]
