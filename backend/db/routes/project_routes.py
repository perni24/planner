from starlette.responses import JSONResponse
from starlette.routing import Route

# Configurazione delle rotte
routes = [
    Route("/", endpoint=homepage)
]

async def homepage(request):
    return JSONResponse({'messaggio': 'Il backend del Planner è attivo!'})