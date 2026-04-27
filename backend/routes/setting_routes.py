from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.setting_repo as settingRepo

async def get_all_settings(request):
    settings = settingRepo.get_all_settings()
    return JSONResponse(settings)

routes = [
    Route("/get_all_settings", endpoint=get_all_settings)
]