import os
import sqlite3

from config import DATA_DIR, DB_PATH, SCHEMA_PATH


def get_db_connection():
    """Ritorna una connessione al database pronta all'uso."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Cartella database creata in: {DATA_DIR}")

    if os.path.exists(DB_PATH):
        print(f"Il database esiste gia in: {DB_PATH}. Salto l'inizializzazione.")
        return

    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"File schema non trovato: {SCHEMA_PATH}")

    print(f"Creazione del database in: {DB_PATH}...")

    with sqlite3.connect(DB_PATH) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())

    print("Database inizializzato con successo!")


if __name__ == "__main__":
    init_db()
