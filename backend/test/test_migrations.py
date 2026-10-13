import re
import shutil
import sqlite3
import unittest
from contextlib import closing, contextmanager, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from db import db as database
from db import migration_runner


SCHEMA_PATH = Path(database.SCHEMA_PATH)
MIGRATIONS_DIR = Path(database.MIGRATIONS_DIR)


@contextmanager
def isolated_database():
    with TemporaryDirectory(prefix="planner-migrations-") as directory:
        root = Path(directory)
        with patch.multiple(
            database,
            DATA_DIR=str(root),
            DB_PATH=str(root / "planner.db"),
            MIGRATION_BACKUPS_DIR=str(root / "migration_backups"),
        ), redirect_stdout(StringIO()):
            yield root


def seed_legacy_database(with_subtasks=True):
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    schema = schema.replace(
        "AND EXISTS (SELECT 1 FROM tasks WHERE parent_id = OLD.parent_id)\n", ""
    )
    if not with_subtasks:
        schema = re.sub(r"CREATE TRIGGER .*?END;", "", schema, flags=re.DOTALL)
        schema = schema.replace("    parent_id INTEGER,\n", "")
        schema = schema.replace(
            "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,\n"
            "    FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE",
            "FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE",
        )
        schema = schema.replace(" AND t.parent_id IS NULL", "")

    with closing(database.get_db_connection()) as conn:
        conn.executescript(schema)
        conn.execute("INSERT INTO projects (id, area_id, name) VALUES (3, 1, 'Project')")
        conn.execute(
            "INSERT INTO tasks (id, project_id, title) VALUES (41, 3, 'Parent')"
        )
        if with_subtasks:
            conn.execute(
                "INSERT INTO tasks (id, project_id, parent_id, title) "
                "VALUES (42, 3, 41, 'Subtask')"
            )
        conn.execute("UPDATE settings SET language = 'en', theme = 'dark'")
        conn.commit()


def snapshot(conn):
    result = {
        table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY id")]
        for table in ("areas", "projects", "settings", "calendar")
    }
    result["tasks"] = [tuple(row) for row in conn.execute(
        "SELECT id, project_id, title, description, completed, created_at, updated_at "
        "FROM tasks ORDER BY id"
    )]
    return result


def expect_error(exception, operation):
    try:
        operation()
    except exception as error:
        return error
    raise AssertionError(f"Expected {exception.__name__}")


def test_new_database_and_repeated_startup():
    with isolated_database() as root:
        database.init_db()
        with closing(database.get_db_connection()) as conn:
            assert migration_runner.get_schema_version(conn) == 1
            before = snapshot(conn)
            assert len(before["areas"]) == len(before["settings"]) == 1
        database.init_db()
        with closing(database.get_db_connection()) as conn:
            assert snapshot(conn) == before
        assert not (root / "migration_backups").exists()


def test_legacy_migration_preserves_data_and_creates_backup():
    with isolated_database() as root:
        seed_legacy_database()
        with closing(database.get_db_connection()) as conn:
            before = snapshot(conn)
            old_trigger = conn.execute(
                "SELECT sql FROM sqlite_master WHERE name = 'trg_subtask_after_delete'"
            ).fetchone()[0]
        database.init_db()
        with closing(database.get_db_connection()) as conn:
            assert snapshot(conn) == before
            assert migration_runner.get_schema_version(conn) == 1
            trigger = conn.execute(
                "SELECT sql FROM sqlite_master WHERE name = 'trg_subtask_after_delete'"
            ).fetchone()[0]
            assert "AND EXISTS" in trigger
        backups = list((root / "migration_backups").glob("*.db"))
        assert len(backups) == 1
        with closing(sqlite3.connect(backups[0])) as conn:
            assert snapshot(conn) == before
            assert migration_runner.get_schema_version(conn) == 0
            assert conn.execute(
                "SELECT sql FROM sqlite_master WHERE name = 'trg_subtask_after_delete'"
            ).fetchone()[0] == old_trigger
        database.init_db()
        assert list((root / "migration_backups").glob("*.db")) == backups


def test_deleting_last_subtask_keeps_parent_open():
    with isolated_database():
        seed_legacy_database()
        database.init_db()
        with closing(database.get_db_connection()) as conn:
            conn.execute("DELETE FROM tasks WHERE id = 42")
            assert conn.execute("SELECT completed FROM tasks WHERE id = 41").fetchone()[0] == 0
            conn.commit()


def test_deleting_open_subtask_completes_parent_with_completed_child():
    with isolated_database():
        seed_legacy_database()
        database.init_db()
        with closing(database.get_db_connection()) as conn:
            conn.execute(
                "INSERT INTO tasks (project_id, parent_id, title, completed) "
                "VALUES (3, 41, 'Completed child', 1)"
            )
            conn.execute("DELETE FROM tasks WHERE id = 42")
            assert conn.execute("SELECT completed FROM tasks WHERE id = 41").fetchone()[0] == 1
            conn.commit()


def test_database_without_subtasks_is_upgraded():
    with isolated_database():
        seed_legacy_database(with_subtasks=False)
        with closing(database.get_db_connection()) as conn:
            before = snapshot(conn)
        database.init_db()
        with closing(database.get_db_connection()) as conn:
            assert snapshot(conn) == before
            assert conn.execute("SELECT parent_id FROM tasks WHERE id = 41").fetchone()[0] is None
            conn.execute(
                "INSERT INTO tasks (project_id, parent_id, title) VALUES (3, 41, 'Child')"
            )
            assert conn.execute("SELECT total_tasks FROM v_projects_status WHERE id = 3").fetchone()[0] == 1
            parent_fk = [row for row in conn.execute("PRAGMA foreign_key_list(tasks)") if row[3] == "parent_id"]
            assert len(parent_fk) == 1 and parent_fk[0][6] == "CASCADE"
            conn.execute("DELETE FROM tasks WHERE id = 41")
            assert conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0
            conn.commit()


def test_failed_migration_rolls_back_trigger_and_version():
    with isolated_database() as root:
        seed_legacy_database()
        scripts = root / "scripts"
        scripts.mkdir()
        (scripts / "001_fail.sql").write_text(
            "DROP TRIGGER trg_subtask_after_delete;\n"
            "CREATE TABLE migration_probe(id INTEGER);\n"
            "INSERT INTO missing_table VALUES (1);\n",
            encoding="utf-8",
        )
        with closing(database.get_db_connection()) as conn:
            before = snapshot(conn)
            trigger = conn.execute(
                "SELECT sql FROM sqlite_master WHERE name = 'trg_subtask_after_delete'"
            ).fetchone()[0]
        with patch.object(database, "MIGRATIONS_DIR", str(scripts)), patch.object(
            migration_runner, "MIGRATION_FILES", ("001_fail.sql",)
        ):
            expect_error(RuntimeError, database.init_db)
        with closing(database.get_db_connection()) as conn:
            assert snapshot(conn) == before
            assert migration_runner.get_schema_version(conn) == 0
            assert conn.execute(
                "SELECT sql FROM sqlite_master WHERE name = 'trg_subtask_after_delete'"
            ).fetchone()[0] == trigger
            assert conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'migration_probe'").fetchone() is None


def test_migrations_run_in_order_and_retry_only_failed_step():
    with isolated_database() as root:
        seed_legacy_database()
        scripts = root / "scripts"
        scripts.mkdir()
        shutil.copy2(MIGRATIONS_DIR / "001_fix_subtask_delete.sql", scripts)
        second_script = scripts / "002_add_notes.sql"
        second_script.write_text(
            "CREATE TABLE notes(note TEXT); INSERT INTO missing_table VALUES (1);",
            encoding="utf-8",
        )
        with patch.object(database, "MIGRATIONS_DIR", str(scripts)), patch.object(
            migration_runner,
            "MIGRATION_FILES",
            ("001_fix_subtask_delete.sql", "002_add_notes.sql"),
        ):
            expect_error(RuntimeError, database.init_db)
            with closing(database.get_db_connection()) as conn:
                assert migration_runner.get_schema_version(conn) == 1
                assert conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'notes'").fetchone() is None
            second_script.write_text(
                "CREATE TABLE notes(note TEXT); INSERT INTO notes VALUES ('a;b');",
                encoding="utf-8",
            )
            database.init_db()
            database.init_db()
            with closing(database.get_db_connection()) as conn:
                assert migration_runner.get_schema_version(conn) == 2
                assert conn.execute("SELECT note FROM notes").fetchall()[0][0] == "a;b"


def test_newer_schema_is_rejected_without_changes():
    with isolated_database() as root:
        seed_legacy_database()
        with closing(database.get_db_connection()) as conn:
            conn.execute("PRAGMA user_version = 2")
            before = snapshot(conn)
        expect_error(RuntimeError, database.init_db)
        with closing(database.get_db_connection()) as conn:
            assert migration_runner.get_schema_version(conn) == 2
            assert snapshot(conn) == before
        assert not (root / "migration_backups").exists()


def test_missing_script_does_not_create_database():
    with isolated_database():
        with patch.object(database, "MIGRATIONS_DIR", "missing-migration-directory"):
            expect_error(FileNotFoundError, database.init_db)
        assert not Path(database.DB_PATH).exists()


def test_failed_initialization_can_be_retried():
    with isolated_database() as root:
        faulty_schema = root / "faulty_schema.sql"
        faulty_schema.write_text(
            "CREATE TABLE partial(id INTEGER); INSERT INTO missing_table VALUES (1);",
            encoding="utf-8",
        )
        with patch.object(database, "SCHEMA_PATH", str(faulty_schema)):
            expect_error(sqlite3.Error, database.init_db)
        with closing(database.get_db_connection()) as conn:
            assert migration_runner.get_schema_version(conn) == 0
            assert conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table'").fetchone() is None
        database.init_db()
        with closing(database.get_db_connection()) as conn:
            assert migration_runner.get_schema_version(conn) == 1


def test_scripts_cannot_commit_or_change_schema_version():
    for forbidden_sql in ("COMMIT;", "PRAGMA user_version = 99;"):
        with closing(sqlite3.connect(":memory:")) as conn:
            conn.execute("BEGIN IMMEDIATE")
            expect_error(
                sqlite3.Error,
                lambda: migration_runner.execute_script(
                    conn, "CREATE TABLE probe(id INTEGER);" + forbidden_sql
                ),
            )
            conn.rollback()
            assert conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'probe'").fetchone() is None
            assert migration_runner.get_schema_version(conn) == 0


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
