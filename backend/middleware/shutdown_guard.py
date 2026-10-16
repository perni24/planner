import sqlite3

from starlette.responses import JSONResponse

from config import DATABASE_OPERATION_TIMEOUT_SECONDS
from services.operation_control import is_stopping, operation_scope


def shutdown_guard(app):
    async def middleware(scope, receive, send):
        if scope["type"] != "http":
            return await app(scope, receive, send)
        if is_stopping():
            response = JSONResponse({"error": "Application is shutting down"}, status_code=503)
            return await response(scope, receive, send)

        response_started = False

        async def tracked_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            with operation_scope(DATABASE_OPERATION_TIMEOUT_SECONDS):
                await app(scope, receive, tracked_send)
        except (InterruptedError, TimeoutError, sqlite3.OperationalError) as error:
            if response_started or (
                isinstance(error, sqlite3.OperationalError)
                and getattr(error, "sqlite_errorcode", None) != sqlite3.SQLITE_INTERRUPT
            ):
                raise
            status = 503 if is_stopping() else 504
            response = JSONResponse(
                {"error": "Application is shutting down" if status == 503 else "Database operation timed out"},
                status_code=status,
            )
            await response(scope, receive, send)

    return middleware
