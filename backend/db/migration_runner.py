import os
import sqlite3
from contextlib import closing
from datetime import datetime

from config import DATABASE_OPERATION_TIMEOUT_SECONDS, SQLITE_BUSY_TIMEOUT_SECONDS
from services.operation_control import check_operation, operation_deadline


MIGRATION_FILES = (
    "001_fix_subtask_delete.sql",
    "002_recreate_last_area.sql",
)


def load_migrations(directory):
    migrations = []

    for version, filename in enumerate(MIGRATION_FILES, start=1):
        check_operation()
        if not filename.startswith(f"{version:03d}_") or not filename.endswith(".sql"):
            raise RuntimeError(f"Invalid migration filename: {filename}")

        with open(os.path.join(directory, filename), "r", encoding="utf-8") as file:
            migrations.append((version, filename, file.read()))

    return migrations


def get_schema_version(conn):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def validate_schema_version(version, latest_version):
    if version < 0 or version > latest_version:
        raise RuntimeError(
            f"Unsupported database schema version {version}; "
            f"this app supports versions 0 through {latest_version}."
        )


def authorize_script(action, first_argument, second_argument, database, source):
    if action in (sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_SAVEPOINT):
        return sqlite3.SQLITE_DENY
    if (
        action == sqlite3.SQLITE_PRAGMA
        and first_argument.lower() == "user_version"
        and second_argument is not None
    ):
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def execute_script(conn, script):
    # executescript() farebbe commit implicito; complete_statement mantiene
    # intatti anche i trigger e le stringhe che contengono punti e virgola.
    statement = ""
    conn.set_authorizer(authorize_script)
    try:
        for part in script.split(";"):
            check_operation()
            statement += part + ";"
            if sqlite3.complete_statement(statement):
                conn.execute(statement)
                statement = ""
        if statement.strip():
            conn.execute(statement)
    finally:
        conn.set_authorizer(None)


def create_migration_backup(conn, directory, version):
    deadline = operation_deadline(DATABASE_OPERATION_TIMEOUT_SECONDS)
    check_operation(deadline)
    os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(directory, f"planner_v{version}_{timestamp}.db")

    def progress(status, remaining, total):
        check_operation(deadline)

    try:
        with closing(sqlite3.connect(path, timeout=SQLITE_BUSY_TIMEOUT_SECONDS)) as backup_conn:
            conn.backup(backup_conn, pages=256, progress=progress, sleep=0.05)
    except BaseException:
        if os.path.exists(path):
            os.remove(path)
        raise

    print(f"Backup prima delle migrazioni creato in: {path}")
    return path


def apply_migrations(conn, migrations, directory):
    latest_version = len(migrations)

    for version, filename, script in migrations:
        try:
            check_operation()
            conn.execute("BEGIN IMMEDIATE")
            current_version = get_schema_version(conn)
            validate_schema_version(current_version, latest_version)

            if current_version >= version:
                conn.rollback()
                continue
            if current_version != version - 1:
                raise RuntimeError(f"Missing migration before schema version {version}")

            # I DB senza versione includono sia v0.0.1 (senza subtask) sia v0.1.0.
            if version == 1:
                columns = conn.execute("PRAGMA table_info(tasks)").fetchall()
                if not columns:
                    raise RuntimeError("Unsupported legacy database: tasks table is missing")
                if not any(column[1] == "parent_id" for column in columns):
                    legacy_path = os.path.join(directory, "legacy_add_subtasks.sql")
                    with open(legacy_path, "r", encoding="utf-8") as file:
                        execute_script(conn, file.read())

            execute_script(conn, script)
            conn.execute(f"PRAGMA user_version = {version}")
            check_operation()
            conn.commit()
            print(f"Migrazione applicata: {filename} (schema {version})")
        except Exception as error:
            conn.rollback()
            raise RuntimeError(f"Database migration failed: {filename}") from error
