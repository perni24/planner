import os
import sqlite3
from contextlib import closing

from config import DATA_DIR, DB_PATH, MIGRATION_BACKUPS_DIR, MIGRATIONS_DIR, SCHEMA_PATH
from db.migration_runner import (
    apply_migrations,
    create_migration_backup,
    execute_script,
    get_schema_version,
    load_migrations,
    validate_schema_version,
)


def get_db_connection():
    """Ritorna una connessione al database pronta all'uso."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Cartella database creata in: {DATA_DIR}")

    migrations = load_migrations(MIGRATIONS_DIR)
    latest_version = len(migrations)

    with closing(get_db_connection()) as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            version = get_schema_version(conn)
            validate_schema_version(version, latest_version)
            has_tables = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' LIMIT 1"
            ).fetchone()

            if not has_tables:
                if version != 0:
                    raise RuntimeError("Database has a schema version but no tables")

                print(f"Creazione del database in: {DB_PATH}...")
                with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
                    execute_script(conn, schema_file.read())
                conn.execute(f"PRAGMA user_version = {latest_version}")
                conn.commit()
                print(f"Database inizializzato con successo (schema {latest_version})!")
                return

            conn.rollback()
        except Exception:
            conn.rollback()
            raise

        if version < latest_version:
            create_migration_backup(conn, MIGRATION_BACKUPS_DIR, version)
        apply_migrations(conn, migrations, MIGRATIONS_DIR)
        print(f"Database pronto in: {DB_PATH} (schema {get_schema_version(conn)}).")


if __name__ == "__main__":
    init_db()
