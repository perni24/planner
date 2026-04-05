import sqlite3
import os

# Ottiene il percorso assoluto della cartella 'backend'
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
# Definisce il percorso per la cartella 'db' e il file del database
DB_FOLDER = os.path.join(BACKEND_DIR, "db")
DB_NAME = os.path.join(DB_FOLDER, "planner.db")

def get_db_connection():
    """Ritorna una connessione al database pronta all'uso."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    # Crea la cartella 'db' se non esiste ancora
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)
        print(f"Cartella database creata in: {DB_FOLDER}")

    # Controlla se il file esiste già per evitare di sovrascrivere dati
    if os.path.exists(DB_NAME):
        print(f"Il database esiste già in: {DB_NAME}. Salto l'inizializzazione.")
        return

    print(f"Creazione del database in: {DB_NAME}...")

    # Connessione (crea il file se non esiste)
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Creazione Tabella
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attivita (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titolo TEXT NOT NULL,
                descrizione TEXT,
                scadenza TEXT,
                completato INTEGER DEFAULT 0
            )
        ''')

        conn.commit()

    print("Database inizializzato con successo!")

if __name__ == "__main__":
    inizializza_db()