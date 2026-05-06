from starlette.responses import JSONResponse
from starlette.routing import Route
import services.locale_service as localeService

async def get_available_languages(request):
    languages = localeService.get_available_languages()
    return JSONResponse(languages)

async def load_language(request):
    language = localeService.load_language()
    return JSONResponse(language)

routes = [
    Route("/get_available_languages", endpoint=get_available_languages),
    Route("/load_language", endpoint=load_language)
]