import ctypes
import json
import locale
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import (
    DEFAULT_LOCALES_DIR,
    DESKTOP_LOG_BACKUP_COUNT,
    DESKTOP_LOG_MAX_BYTES,
    DESKTOP_LOG_PATH,
    FRONTEND_DIST_DIR,
    LOCALES_DIR,
)


LOGGER = logging.getLogger("planner.desktop")
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False

# Ultima risorsa se anche i dizionari esterni e quelli inclusi sono illeggibili.
FALLBACK_MESSAGES = {
    "desktop.errors.title": "Planner error",
    "desktop.errors.startup": "Planner could not start. Check the application folder and the log for details.",
    "desktop.errors.runtime": "The local server stopped unexpectedly. Planner will close. Check the log before restarting.",
    "desktop.errors.frontend": "The interface build is missing. Restore the complete portable folder or run npm run build in frontend during development.",
    "desktop.errors.renderer": "The application window could not start. Check the web renderer installation (WebView2 on Windows).",
    "desktop.errors.timeout": "Application startup exceeded its time limit. Check the log before restarting.",
    "desktop.errors.shutdown": "Planner is taking longer than expected to stop. It is still waiting for safe cleanup. Do not restart it until the process exits. Check the log for details.",
    "desktop.errors.log": "Technical details are available in:",
    "desktop.errors.console": "Technical details are available in the console. The log file could not be opened.",
}


def configure_desktop_logging():
    """Configura log limitati e mantiene la console se la cartella non e scrivibile."""
    for handler in list(LOGGER.handlers):
        LOGGER.removeHandler(handler)
        handler.close()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    if sys.stderr is not None:
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(formatter)
        LOGGER.addHandler(console)
    try:
        os.makedirs(os.path.dirname(DESKTOP_LOG_PATH), exist_ok=True)
        handler = RotatingFileHandler(
            DESKTOP_LOG_PATH,
            maxBytes=DESKTOP_LOG_MAX_BYTES,
            backupCount=DESKTOP_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        LOGGER.addHandler(handler)
    except OSError:
        LOGGER.warning("Unable to open desktop log file", exc_info=True)


def attach_backend_logging():
    """Collega il file dopo che Uvicorn ha configurato i propri logger."""
    logger = logging.getLogger("uvicorn.error")
    handlers = []
    for handler in LOGGER.handlers:
        if isinstance(handler, RotatingFileHandler) and handler not in logger.handlers:
            logger.addHandler(handler)
            handlers.append(handler)
    return handlers


def detach_backend_logging(handlers):
    logger = logging.getLogger("uvicorn.error")
    for handler in handlers:
        logger.removeHandler(handler)


def load_error_messages():
    """Non interroga il DB: deve funzionare anche dopo una migrazione fallita."""
    try:
        language = (locale.getlocale()[0] or "en").replace("-", "_").split("_")[0].lower()
    except (ValueError, TypeError):
        language = "en"
    if language not in ("it", "en"):
        language = "en"
    messages = FALLBACK_MESSAGES.copy()
    paths = dict.fromkeys(
        os.path.join(directory, f"{code}.json")
        for code in dict.fromkeys(("en", language))
        for directory in dict.fromkeys((DEFAULT_LOCALES_DIR, LOCALES_DIR))
    )
    for path in paths:
        try:
            with open(path, encoding="utf-8") as source:
                translations = json.load(source)
            if isinstance(translations, dict):
                for key in messages:
                    value = translations.get(key)
                    if isinstance(value, str) and value.strip():
                        messages[key] = value
        except (OSError, ValueError):
            continue
    return messages


def error_message_key(error, kind):
    if kind == "shutdown":
        return "desktop.errors.shutdown"
    if kind == "runtime":
        return "desktop.errors.runtime"
    if isinstance(error, TimeoutError):
        return "desktop.errors.timeout"
    if isinstance(error, FileNotFoundError) and error.filename == os.path.join(
        FRONTEND_DIST_DIR, "index.html"
    ):
        return "desktop.errors.frontend"
    if isinstance(error, ImportError) or type(error).__module__.startswith("webview"):
        return "desktop.errors.renderer"
    return "desktop.errors.startup"


def show_native_error(title, message):
    """Fallback Windows indipendente da PyWebView e da WebView2."""
    if sys.platform != "win32":
        return False
    message_box = ctypes.windll.user32.MessageBoxW
    message_box.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    message_box.restype = ctypes.c_int
    result = message_box(None, message, title, 0x10)
    return bool(result)


def report_desktop_error(error, kind="startup", window=None):
    """La segnalazione non deve mai sostituire l'errore che sta gestendo."""
    try:
        LOGGER.error("Desktop %s failure", kind, exc_info=(type(error), error, error.__traceback__))
        messages = load_error_messages()
        message = messages[error_message_key(error, kind)]
        file_handler = next(
            (handler for handler in LOGGER.handlers if isinstance(handler, RotatingFileHandler)),
            None,
        )
        if file_handler is not None:
            message += f"\n\n{messages['desktop.errors.log']}\n{file_handler.baseFilename}"
        else:
            message += f"\n\n{messages['desktop.errors.console']}"
        title = messages["desktop.errors.title"]
        if window is not None:
            try:
                window.create_confirmation_dialog(title, message)
                return
            except Exception:
                LOGGER.warning("Unable to show the webview error dialog", exc_info=True)
        try:
            if show_native_error(title, message):
                return
        except Exception:
            LOGGER.warning("Unable to show the native error dialog", exc_info=True)
        if sys.stderr is not None:
            print(f"{title}\n{message}", file=sys.stderr)
    except Exception:
        if sys.stderr is not None:
            try:
                print(f"Planner error: {error!r}", file=sys.stderr)
            except Exception:
                pass
