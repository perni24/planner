import json

from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.setting_repo as settingRepo
from validators.settings_validator import validate_language_settings, validate_theme_settings

async def get_all_settings(request):
    settings = settingRepo.get_all_settings()
    return JSONResponse(settings)

async def update_language(request):
    try:
        data = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse({"error": "Request body must contain valid JSON"}, status_code=400)
    values, error = validate_language_settings(data)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    settingRepo.update_language(values["language"])
    return JSONResponse({"message": "Language update successful"})

async def update_theme(request):
    try:
        data = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse({"error": "Request body must contain valid JSON"}, status_code=400)
    values, error = validate_theme_settings(data)
    if error:
        return JSONResponse({"error": error}, status_code=400)
    settingRepo.update_theme(values["theme"], values["custom_colors"])
    return JSONResponse({"message": "theme update successful"})

routes = [
    Route("/get_all_settings", endpoint=get_all_settings),
    Route("/update_language", endpoint=update_language, methods=["POST"]),
    Route("/update_theme", endpoint=update_theme, methods=["POST"])
]
