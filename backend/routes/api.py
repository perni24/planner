from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
# Importiamo le rotte dei progetti
from .project_routes import routes as project_routes
from .setting_routes import routes as setting_routes

# Endpoint generico per lo stato del server
async def health_check(request):
    return JSONResponse({'status': 'online'})

# Raggruppiamo tutte le rotte dell'applicazione
all_routes = [
    Route("/", endpoint=health_check),
    # Monta le rotte dei progetti sotto il prefisso /projects
    Mount("/projects", routes=project_routes),
    Mount("/settings", routes=setting_routes)
]
