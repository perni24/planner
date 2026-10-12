from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

from config import IS_DEVELOPMENT

# Solo i metodi che modificano dati vengono controllati. GET e HEAD restano liberi:
# senza CORS un altro sito puo inviarli ma non puo leggerne la risposta.
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
LOOPBACK_HOSTNAMES = {"127.0.0.1", "localhost", "::1"}


def is_allowed_origin(origin, host):
    # Stessa origine: la pagina e servita dal backend stesso.
    if host and origin == f"http://{host}":
        return True

    # In sviluppo il frontend gira su Vite (es. http://localhost:5173) e le richieste
    # arrivano tramite il proxy, che conserva l'Origin della pagina.
    if IS_DEVELOPMENT:
        return urlsplit(origin).hostname in LOOPBACK_HOSTNAMES

    return False


def is_cross_site_request(headers):
    origin = headers.get("origin")

    if origin is not None:
        return not is_allowed_origin(origin, headers.get("host"))

    # Senza Origin la richiesta arriva da un client non browser (client MCP, curl,
    # file .http). Per sicurezza si controlla anche Sec-Fetch-Site, che i browser
    # moderni inviano sempre.
    return headers.get("sec-fetch-site") == "cross-site"


def origin_guard(app):
    """Blocca le richieste che modificano dati inviate da pagine di altri siti (CSRF)."""

    async def middleware(scope, receive, send):
        if (
            scope["type"] == "http"
            and scope["method"] in UNSAFE_METHODS
            and is_cross_site_request(Headers(scope=scope))
        ):
            response = JSONResponse(
                {"error": "Cross-origin request blocked"},
                status_code=403,
            )
            await response(scope, receive, send)
            return

        await app(scope, receive, send)

    return middleware
