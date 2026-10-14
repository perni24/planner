import asyncio
import json
import re
import sqlite3
import threading
import unittest
from contextlib import closing, contextmanager, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from starlette.applications import Starlette
from starlette.routing import Mount

from db import db as database
from routes import backup_routes


@contextmanager
def isolated_database():
    with TemporaryDirectory(prefix="planner-backup-test-") as directory:
        root = Path(directory)
        with patch.multiple(
            database,
            DATA_DIR=str(root),
            DB_PATH=str(root / "planner.db"),
            MIGRATION_BACKUPS_DIR=str(root / "migration_backups"),
        ), patch.multiple(
            backup_routes,
            DATA_DIR=str(root),
            DB_PATH=str(root / "planner.db"),
        ), redirect_stdout(StringIO()):
            database.init_db()
            yield root


async def request_backup(method="GET", headers=(), on_send=None, extensions=None):
    app = Starlette(routes=[Mount("/api/backup", routes=backup_routes.routes)])
    messages = []
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": "/api/backup/download",
        "raw_path": b"/api/backup/download",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"127.0.0.1:8000"), *headers],
        "server": ("127.0.0.1", 8000),
        "client": ("127.0.0.1", 12345),
        "extensions": extensions or {},
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        if on_send:
            on_send(message)
        messages.append(message)

    await app(scope, receive, send)
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return start["status"], dict(start["headers"]), body


def assert_no_temporary_backups(root):
    assert not list(root.glob("planner-backup-*"))


def test_download_returns_valid_snapshot_and_cleans_temporary_files():
    with isolated_database() as root:
        with closing(database.get_db_connection()) as conn:
            conn.execute("UPDATE areas SET name = 'Original area'")
            conn.execute("INSERT INTO projects (area_id, name) VALUES (1, 'Project')")
            conn.execute("INSERT INTO tasks (project_id, title) VALUES (1, 'Task')")
            conn.commit()
            version = conn.execute("PRAGMA user_version").fetchone()[0]
        status, headers, body = asyncio.run(request_backup())
        assert status == 200
        assert headers[b"content-type"] == b"application/octet-stream"
        assert headers[b"cache-control"] == b"no-store"
        assert re.fullmatch(
            rb'attachment; filename="planner_backup_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.db"',
            headers[b"content-disposition"],
        )
        assert int(headers[b"content-length"]) == len(body)
        received = root / "received.db"
        received.write_bytes(body)
        with closing(sqlite3.connect(received)) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert not conn.execute("PRAGMA foreign_key_check").fetchall()
            assert conn.execute("PRAGMA user_version").fetchone()[0] == version
            assert conn.execute("SELECT name FROM areas").fetchone()[0] == "Original area"
            assert conn.execute("SELECT title FROM tasks").fetchone()[0] == "Task"
            assert conn.execute(
                "SELECT 1 FROM sqlite_master WHERE name = 'trg_recreate_last_area'"
            ).fetchone() is not None
        assert_no_temporary_backups(root)


def test_download_includes_committed_wal_data():
    with isolated_database() as root:
        with closing(database.get_db_connection()) as writer:
            assert writer.execute("PRAGMA journal_mode = WAL").fetchone()[0] == "wal"
            writer.execute("PRAGMA wal_autocheckpoint = 0")
            writer.execute("UPDATE areas SET name = 'WAL area'")
            writer.commit()
            assert Path(str(root / "planner.db") + "-wal").stat().st_size > 0
            status, _, body = asyncio.run(request_backup())
            assert status == 200
            received = root / "received.db"
            received.write_bytes(body)
            with closing(sqlite3.connect(received)) as conn:
                assert conn.execute("SELECT name FROM areas").fetchone()[0] == "WAL area"
                assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert_no_temporary_backups(root)


def test_writes_during_transfer_do_not_change_snapshot():
    with isolated_database() as root:
        def update_source(message):
            if message["type"] == "http.response.start":
                with closing(database.get_db_connection()) as conn:
                    conn.execute("UPDATE areas SET name = 'Changed during download'")
                    conn.commit()

        status, _, body = asyncio.run(request_backup(on_send=update_source))
        assert status == 200
        received = root / "received.db"
        received.write_bytes(body)
        with closing(sqlite3.connect(received)) as conn:
            assert conn.execute("SELECT name FROM areas").fetchone()[0] == "utente"
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        with closing(database.get_db_connection()) as conn:
            assert conn.execute("SELECT name FROM areas").fetchone()[0] == "Changed during download"
        assert_no_temporary_backups(root)


def test_missing_database_returns_404_without_creating_files():
    with isolated_database() as root:
        Path(database.DB_PATH).unlink()
        status, _, body = asyncio.run(request_backup())
        assert status == 404
        assert json.loads(body) == {"error": "database not found"}
        assert not Path(database.DB_PATH).exists()
        assert_no_temporary_backups(root)


def test_failed_snapshot_creation_cleans_partial_file():
    with isolated_database() as root:
        def fail_backup(destination):
            Path(destination).write_bytes(b"partial backup")
            raise sqlite3.OperationalError("simulated backup failure")

        with patch.object(backup_routes, "backup_database", fail_backup):
            try:
                asyncio.run(request_backup())
            except sqlite3.OperationalError:
                pass
            else:
                raise AssertionError("Expected backup failure")
        assert_no_temporary_backups(root)
        with closing(database.get_db_connection()) as conn:
            assert conn.execute("SELECT COUNT(*) FROM areas").fetchone()[0] == 1


def test_failed_transfer_cleans_temporary_file():
    with isolated_database() as root:
        def disconnect(message):
            if message["type"] == "http.response.body":
                raise OSError("simulated client disconnect")

        try:
            asyncio.run(request_backup(on_send=disconnect))
        except OSError:
            pass
        else:
            raise AssertionError("Expected transfer failure")
        assert_no_temporary_backups(root)


def test_cancelled_backup_waits_for_worker_before_cleanup():
    with isolated_database() as root:
        started = threading.Event()
        release = threading.Event()
        original_backup = backup_routes.backup_database

        def slow_backup(destination):
            started.set()
            if not release.wait(timeout=5):
                raise AssertionError("Backup worker was not released")
            original_backup(destination)

        async def cancel_request():
            task = asyncio.create_task(request_backup())
            try:
                assert await asyncio.to_thread(started.wait, 5)
                task.cancel()
                await asyncio.sleep(0)
                assert not task.done()
            finally:
                release.set()
            try:
                await task
            except asyncio.CancelledError:
                pass
            else:
                raise AssertionError("Expected request cancellation")

        with patch.object(backup_routes, "backup_database", slow_backup):
            asyncio.run(cancel_request())
        assert_no_temporary_backups(root)


def test_simultaneous_downloads_use_independent_temporary_files():
    with isolated_database() as root:
        paths = []
        lock = threading.Lock()
        original_backup = backup_routes.backup_database

        def record_backup(destination):
            with lock:
                paths.append(destination)
            original_backup(destination)

        async def download_twice():
            return await asyncio.gather(request_backup(), request_backup())

        with patch.object(backup_routes, "backup_database", record_backup):
            responses = asyncio.run(download_twice())
        assert len(set(paths)) == 2
        assert all(status == 200 for status, _, _ in responses)
        assert all(body.startswith(b"SQLite format 3\0") for _, _, body in responses)
        assert_no_temporary_backups(root)


def test_head_and_invalid_ranges_clean_temporary_files():
    with isolated_database() as root:
        status, headers, body = asyncio.run(request_backup(method="HEAD"))
        assert status == 200 and body == b""
        assert int(headers[b"content-length"]) > 0
        assert_no_temporary_backups(root)
        for value, expected_status in ((b"invalid", 400), (b"bytes=999999999-", 416)):
            status, _, _ = asyncio.run(request_backup(headers=[(b"range", value)]))
            assert status == expected_status
            assert_no_temporary_backups(root)


def test_pathsend_extension_does_not_outlive_temporary_file():
    with isolated_database() as root:
        status, _, body = asyncio.run(request_backup(extensions={"http.response.pathsend": {}}))
        assert status == 200 and body.startswith(b"SQLite format 3\0")
        assert_no_temporary_backups(root)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
