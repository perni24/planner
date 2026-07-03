from starlette.responses import JSONResponse
from starlette.routing import Route

from config import APP_VERSION
from services.app_lifecycle import register_heartbeat, request_shutdown
from services.update_service import check_update


async def heartbeat(request):
    register_heartbeat()
    return JSONResponse({"status": "alive"})


async def shutdown(request):
    request_shutdown()
    return JSONResponse({"message": "shutdown requested"})


async def version(request):
    return JSONResponse({"version": APP_VERSION})


async def check_app_update(request):
    return JSONResponse(check_update())


routes = [
    Route("/heartbeat", endpoint=heartbeat, methods=["POST"]),
    Route("/shutdown", endpoint=shutdown, methods=["POST"]),
    Route("/version", endpoint=version),
    Route("/check_update", endpoint=check_app_update),
]
