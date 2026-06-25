import os


def get_bool_env(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in ("1", "true", "yes", "on")


BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)

APP_ENV = os.getenv("APP_ENV", "development")
IS_DEVELOPMENT = APP_ENV == "development"
DEBUG = get_bool_env("DEBUG", IS_DEVELOPMENT)
RELOAD = get_bool_env("RELOAD", IS_DEVELOPMENT)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

DATA_DIR = os.path.join(BACKEND_DIR, "db")
DB_PATH = os.path.join(DATA_DIR, "planner.db")
SCHEMA_PATH = os.path.join(BACKEND_DIR, "schema.sql")
LOCALES_DIR = os.path.join(BACKEND_DIR, "locales")
