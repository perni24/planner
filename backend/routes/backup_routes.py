import os
from datetime import datetime

from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

from config import DB_PATH


async def download_backup(request):
    if not os.path.exists(DB_PATH):
        return JSONResponse({"error": "database not found"}, status_code=404)

    backup_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    return FileResponse(
        DB_PATH,
        filename=f"planner_backup_{backup_date}.db",
        media_type="application/octet-stream",
    )


routes = [
    Route("/download", endpoint=download_backup),
]
