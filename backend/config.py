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

APP_ENV = os.getenv("APP_ENV", "production" if IS_FROZEN else "development")
IS_DEVELOPMENT = APP_ENV == "development"
IS_PRODUCTION = APP_ENV == "production"

DEBUG = get_bool_env("DEBUG", IS_DEVELOPMENT)
RELOAD = False if IS_FROZEN else get_bool_env("RELOAD", IS_DEVELOPMENT)

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

if IS_FROZEN:
    APP_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, "_MEIPASS", APP_DIR)

    DATA_DIR = os.path.join(APP_DIR, "data")
    DB_PATH = os.path.join(DATA_DIR, "planner.db")
    SCHEMA_PATH = os.path.join(BUNDLE_DIR, "schema.sql")
    LOCALES_DIR = os.path.join(APP_DIR, "locales")
    DEFAULT_LOCALES_DIR = os.path.join(BUNDLE_DIR, "locales")
    FRONTEND_DIST_DIR = os.path.join(BUNDLE_DIR, "frontend_dist")
else:
    APP_DIR = BACKEND_DIR
    BUNDLE_DIR = BACKEND_DIR

    DATA_DIR = os.path.join(BACKEND_DIR, "db")
    DB_PATH = os.path.join(DATA_DIR, "planner.db")
    SCHEMA_PATH = os.path.join(BACKEND_DIR, "schema.sql")
    LOCALES_DIR = os.path.join(BACKEND_DIR, "locales")
    DEFAULT_LOCALES_DIR = LOCALES_DIR
    FRONTEND_DIST_DIR = os.path.join(PROJECT_DIR, "frontend", "dist")


def ensure_runtime_directories():
    for directory in (DATA_DIR, LOCALES_DIR):
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
