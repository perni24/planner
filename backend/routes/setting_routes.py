from starlette.responses import JSONResponse
from starlette.routing import Route
import db.repositories.setting_repo as settingRepo

async def get_all_settings(request):
    settings = settingRepo.get_all_settings()
    return JSONResponse(settings)

async def update_language(request):
    data = await request.json()
    language = data.get("language")
    if not language:
        return JSONResponse({"error": "language obbligatoria"}, status_code=400)
    settingRepo.update_language(language)
    return JSONResponse({"message": "Language update successful"})

async def update_theme(request):
    data = await request.json()
    theme = data.get("theme")
    custom_colors = data.get("custom_colors")
    if not theme:
        return JSONResponse({"error": "theme obbligatorio"}, status_code=400)
    if not custom_colors:
        return JSONResponse({"error": "custom_colors obbligatorio"}, status_code=400)
    settingRepo.update_theme(theme, custom_colors)
    return JSONResponse({"message": "theme update successful"})

routes = [
    Route("/get_all_settings", endpoint=get_all_settings),
    Route("/update_language", endpoint=update_language, methods=["POST"]),
    Route("/update_theme", endpoint=update_theme, methods=["POST"])
]