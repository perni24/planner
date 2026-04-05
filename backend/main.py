from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from init_db import init_db, get_db_connection

async def homepage(request):
    return JSONResponse({'messaggio': 'Il backend del Planner è attivo!'})

# Configurazione delle rotte
routes = [
    Route("/", endpoint=homepage)
]

# Configurazione del Middleware CORS
# allow_origins=["*"] permette a qualsiasi frontend di connettersi (ottimo per lo sviluppo)
middleware = [
    Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
]

app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == "__main__":
    # Inizializza il DB all'avvio
    init_db()
    # Avvia il server
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)