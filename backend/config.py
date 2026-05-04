import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)

DATA_DIR = os.path.join(BACKEND_DIR, "db")
DB_PATH = os.path.join(DATA_DIR, "planner.db")
SCHEMA_PATH = os.path.join(BACKEND_DIR, "schema.sql")
LOCALES_DIR = os.path.join(PROJECT_DIR, "locales")
