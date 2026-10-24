import os
import shutil
import sys


def get_bool_env(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in ("1", "true", "yes", "on")


IS_FROZEN = getattr(sys, "frozen", False)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)

APP_VERSION = "0.1.0"
GITHUB_REPO = os.getenv("GITHUB_REPO", "perni24/planner")
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
GITHUB_LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

APP_ENV = os.getenv("APP_ENV", "production" if IS_FROZEN else "development")
IS_DEVELOPMENT = APP_ENV == "development"
IS_PRODUCTION = APP_ENV == "production"

DEBUG = get_bool_env("DEBUG", IS_DEVELOPMENT)
# Il reload di Uvicorn non e compatibile con il ciclo di vita della finestra desktop.
RELOAD = False

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

APP_HOST = "127.0.0.1" if HOST in ("0.0.0.0", "::") else HOST
APP_URL = f"http://{APP_HOST}:{PORT}"
# Su Linux si forza Qt: senza indicazione pywebview prova prima GTK, che usa il
# WebKitGTK di sistema invece del motore incluso nel pacchetto portable.
WEBVIEW_GUI = {"win32": "edgechromium", "linux": "qt"}.get(sys.platform)
if sys.platform == "linux":
    # Mantiene il binding usato nella build anche con QT_API esterno differente.
    os.environ["QT_API"] = "pyqt6"
SERVER_STARTUP_TIMEOUT_SECONDS = 15
SERVER_GRACEFUL_SHUTDOWN_SECONDS = 5
SERVER_SHUTDOWN_TIMEOUT_SECONDS = 10
# La cancellazione SQLite precede la scadenza delle richieste ASGI (5 secondi).
SHUTDOWN_OPERATION_GRACE_SECONDS = 3
SQLITE_BUSY_TIMEOUT_SECONDS = 1
DATABASE_OPERATION_TIMEOUT_SECONDS = 30
DATABASE_PROGRESS_STEPS = 1000
RUNTIME_INITIALIZATION_TIMEOUT_SECONDS = 120

# Valori ammessi nell'header Host (senza porta), contro il DNS rebinding.
# Se HOST viene cambiato per raggiungere l'app con un altro nome o IP, quel valore
# viene ammesso; con 0.0.0.0 o :: restano ammessi solo i nomi locali.
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

if HOST not in ("0.0.0.0", "::", *ALLOWED_HOSTS):
    ALLOWED_HOSTS.append(HOST)

if IS_FROZEN:
    APP_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, "_MEIPASS", APP_DIR)

    DATA_DIR = os.path.join(APP_DIR, "data")
    DB_PATH = os.path.join(DATA_DIR, "planner.db")
    SCHEMA_PATH = os.path.join(BUNDLE_DIR, "schema.sql")
    MIGRATIONS_DIR = os.path.join(BUNDLE_DIR, "db", "migrations")
    LOCALES_DIR = os.path.join(APP_DIR, "locales")
    DEFAULT_LOCALES_DIR = os.path.join(BUNDLE_DIR, "locales")
    FRONTEND_DIST_DIR = os.path.join(BUNDLE_DIR, "frontend_dist")
else:
    APP_DIR = BACKEND_DIR
    BUNDLE_DIR = BACKEND_DIR

    DATA_DIR = os.path.join(BACKEND_DIR, "db")
    DB_PATH = os.path.join(DATA_DIR, "planner.db")
    SCHEMA_PATH = os.path.join(BACKEND_DIR, "schema.sql")
    MIGRATIONS_DIR = os.path.join(BACKEND_DIR, "db", "migrations")
    LOCALES_DIR = os.path.join(BACKEND_DIR, "locales")
    DEFAULT_LOCALES_DIR = LOCALES_DIR
    FRONTEND_DIST_DIR = os.path.join(PROJECT_DIR, "frontend", "dist")

MIGRATION_BACKUPS_DIR = os.path.join(DATA_DIR, "migration_backups")
WEBVIEW_STORAGE_DIR = os.path.join(DATA_DIR, "webview")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
DESKTOP_LOG_PATH = os.path.join(LOGS_DIR, "planner.log")
DESKTOP_LOG_MAX_BYTES = 1_000_000
DESKTOP_LOG_BACKUP_COUNT = 3


def ensure_runtime_directories():
    for directory in (DATA_DIR, LOCALES_DIR, WEBVIEW_STORAGE_DIR):
        os.makedirs(directory, exist_ok=True)


def ensure_default_locales():
    if not IS_FROZEN or not os.path.isdir(DEFAULT_LOCALES_DIR):
        return

    os.makedirs(LOCALES_DIR, exist_ok=True)

    for filename in os.listdir(DEFAULT_LOCALES_DIR):
        if not filename.endswith(".json"):
            continue

        source_path = os.path.join(DEFAULT_LOCALES_DIR, filename)
        target_path = os.path.join(LOCALES_DIR, filename)

        if not os.path.exists(target_path):
            shutil.copy2(source_path, target_path)
