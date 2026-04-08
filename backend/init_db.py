import os
import sqlite3

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BACKEND_DIR, "db")
DB_NAME = os.path.join(DB_FOLDER, "planner.db")
SCHEMA_PATH = os.path.join(BACKEND_DIR, "schema.sql")


def get_db_connection():
    """Ritorna una connessione al database pronta all'uso."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)
        print(f"Cartella database creata in: {DB_FOLDER}")

    if os.path.exists(DB_NAME):
        print(f"Il database esiste gia in: {DB_NAME}. Salto l'inizializzazione.")
        return

    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"File schema non trovato: {SCHEMA_PATH}")

    print(f"Creazione del database in: {DB_NAME}...")

    with sqlite3.connect(DB_NAME) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())

    print("Database inizializzato con successo!")


if __name__ == "__main__":
    init_db()
