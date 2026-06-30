from starlette.responses import JSONResponse
from starlette.routing import Route

from services.app_lifecycle import register_heartbeat, request_shutdown


async def heartbeat(request):
    register_heartbeat()
    return JSONResponse({"status": "alive"})


async def shutdown(request):
    request_shutdown()
    return JSONResponse({"message": "shutdown requested"})


routes = [
    Route("/heartbeat", endpoint=heartbeat, methods=["POST"]),
    Route("/shutdown", endpoint=shutdown, methods=["POST"]),
]
