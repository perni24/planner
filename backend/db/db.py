import os
import sqlite3
from contextlib import closing

from config import (
    DATA_DIR, DB_PATH, MIGRATION_BACKUPS_DIR, MIGRATIONS_DIR, SCHEMA_PATH,
    DATABASE_OPERATION_TIMEOUT_SECONDS, DATABASE_PROGRESS_STEPS, SQLITE_BUSY_TIMEOUT_SECONDS,
)
from services.operation_control import (
    cancellation_requested, check_operation, is_stopping, operation_deadline,
)
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
    if is_stopping():
        raise InterruptedError("Application is shutting down; no new database operations allowed")
    deadline = operation_deadline(DATABASE_OPERATION_TIMEOUT_SECONDS)
    check_operation(deadline)
    conn = sqlite3.connect(DB_PATH, timeout=SQLITE_BUSY_TIMEOUT_SECONDS)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.set_progress_handler(
            lambda: int(cancellation_requested(deadline)), DATABASE_PROGRESS_STEPS
        )
    except BaseException:
        conn.close()
        raise
    return conn


def backup_database(destination_path):
    deadline = operation_deadline(DATABASE_OPERATION_TIMEOUT_SECONDS)

    def progress(status, remaining, total):
        check_operation(deadline)

    with closing(get_db_connection()) as source:
        with closing(sqlite3.connect(destination_path, timeout=SQLITE_BUSY_TIMEOUT_SECONDS)) as destination:
            source.backup(destination, pages=256, progress=progress, sleep=0.05)


def init_db():
    check_operation()
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
                check_operation()
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
