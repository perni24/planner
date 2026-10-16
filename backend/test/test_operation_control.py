import asyncio
import sqlite3
import threading
import time
import unittest
from contextlib import closing
from queue import ShutDown
from unittest.mock import Mock, patch

from db import db as database
from db import migration_runner
from db.repositories import mcp_repo
from middleware.shutdown_guard import shutdown_guard
from services import app_lifecycle, event_service, operation_control
from test_backup import isolated_database, assert_no_temporary_backups, request_backup


def expect_error(exception, operation):
    try:
        operation()
    except exception as error:
        return error
    raise AssertionError(f"Expected {exception.__name__}")


def test_repeated_shutdown_requests_do_not_extend_grace_period():
    with patch.object(operation_control.time, "monotonic", return_value=10):
        operation_control.request_stop()
    with patch.object(operation_control.time, "monotonic", return_value=12):
        operation_control.request_stop()
    with patch.object(operation_control.time, "monotonic", return_value=13):
        assert operation_control.is_stopping()
        expect_error(InterruptedError, operation_control.check_operation)


def test_shutdown_without_registered_callback_never_forces_process_exit():
    with patch.object(app_lifecycle, "_shutdown_callback", None), patch("os._exit") as exit_process:
        app_lifecycle.request_shutdown()
        exit_process.assert_not_called()
    callback = Mock()
    with patch.object(app_lifecycle, "_shutdown_callback", callback):
        app_lifecycle.request_shutdown()
    callback.assert_called_once_with()


def test_nested_deadlines_keep_the_shorter_outer_limit():
    with operation_control.operation_scope(0.005):
        with operation_control.operation_scope(60):
            time.sleep(0.01)
            expect_error(TimeoutError, operation_control.check_operation)
    operation_control.check_operation()


def test_shutdown_rejects_new_connections_but_allows_existing_short_transaction():
    with isolated_database():
        with closing(database.get_db_connection()) as conn, conn:
            conn.execute("INSERT INTO areas (name) VALUES ('Committed before stop')")
            operation_control.request_stop()
            expect_error(InterruptedError, database.get_db_connection)
        operation_control.reset_operations()
        with closing(database.get_db_connection()) as conn:
            assert conn.execute("SELECT count(*) FROM areas").fetchone()[0] == 2
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


LONG_QUERY = """
    WITH RECURSIVE numbers(n) AS (
        VALUES (1) UNION ALL SELECT n + 1 FROM numbers WHERE n < 100000000
    ) SELECT sum(n) FROM numbers
"""


def test_sqlite_progress_handler_bounds_long_queries_and_rolls_back_writes():
    with isolated_database():
        with patch.object(database, "DATABASE_OPERATION_TIMEOUT_SECONDS", 0.01):
            with closing(database.get_db_connection()) as conn:
                try:
                    with conn:
                        conn.execute("INSERT INTO areas (name) VALUES ('Must roll back')")
                        conn.execute(LONG_QUERY).fetchone()
                except sqlite3.OperationalError as error:
                    assert error.sqlite_errorcode == sqlite3.SQLITE_INTERRUPT
                else:
                    raise AssertionError("Expected SQL deadline cancellation")
        with closing(database.get_db_connection()) as conn:
            assert conn.execute("SELECT count(*) FROM areas").fetchone()[0] == 1
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_shutdown_cancels_an_active_sqlite_query_in_another_thread():
    with isolated_database(), patch.object(operation_control, "SHUTDOWN_OPERATION_GRACE_SECONDS", 0):
        entered = threading.Event()
        errors = []

        def run_query():
            try:
                with closing(database.get_db_connection()) as conn, conn:
                    conn.execute("INSERT INTO areas (name) VALUES ('Must roll back')")
                    conn.set_trace_callback(lambda sql: entered.set() if "WITH RECURSIVE" in sql else None)
                    conn.execute(LONG_QUERY).fetchone()
            except Exception as error:
                errors.append(error)

        worker = threading.Thread(target=run_query)
        worker.start()
        try:
            assert entered.wait(timeout=2)
            operation_control.request_stop()
        finally:
            worker.join(timeout=3)
        assert not worker.is_alive()
        assert len(errors) == 1 and errors[0].sqlite_errorcode == sqlite3.SQLITE_INTERRUPT
        operation_control.reset_operations()
        with closing(database.get_db_connection()) as conn:
            assert conn.execute("SELECT count(*) FROM areas").fetchone()[0] == 1


def test_locked_database_respects_busy_timeout():
    with isolated_database(), patch.object(database, "SQLITE_BUSY_TIMEOUT_SECONDS", 0.05):
        with closing(database.get_db_connection()) as holder, closing(database.get_db_connection()) as waiter:
            holder.execute("BEGIN IMMEDIATE")
            start = time.monotonic()
            error = expect_error(sqlite3.OperationalError, lambda: waiter.execute("BEGIN IMMEDIATE"))
            assert error.sqlite_errorcode == sqlite3.SQLITE_BUSY
            assert time.monotonic() - start < 1
            holder.rollback()


def test_bulk_cancellation_rolls_back_every_item():
    with isolated_database(), patch.object(operation_control, "SHUTDOWN_OPERATION_GRACE_SECONDS", 0):
        def names():
            yield "First"
            yield "Second"
            operation_control.request_stop()
            yield "Cancelled"

        expect_error(InterruptedError, lambda: mcp_repo.bulk_insert_area(names()))
        operation_control.reset_operations()
        assert [area["name"] for area in mcp_repo.get_all_areas()] == ["utente"]


def test_backup_retry_on_locked_database_has_a_deadline_and_cleans_partial_copy():
    with isolated_database() as root, patch.object(database, "DATABASE_OPERATION_TIMEOUT_SECONDS", 0.05):
        with closing(database.get_db_connection()) as holder:
            holder.execute("BEGIN EXCLUSIVE")
            expect_error(TimeoutError, lambda: asyncio.run(request_backup()))
            holder.rollback()
        assert_no_temporary_backups(root)
        with closing(database.get_db_connection()) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_shutdown_cancels_a_retrying_backup_and_waits_for_worker_cleanup():
    with isolated_database() as root, patch.object(operation_control, "SHUTDOWN_OPERATION_GRACE_SECONDS", 0):
        errors = []
        entered = threading.Event()
        original_check = database.check_operation
        checks = 0

        def progress_check(deadline=None):
            nonlocal checks
            checks += 1
            if checks > 1:
                entered.set()
            original_check(deadline)

        def download():
            try:
                asyncio.run(request_backup())
            except InterruptedError as error:
                errors.append(error)

        worker = threading.Thread(target=download)
        with closing(database.get_db_connection()) as holder:
            holder.execute("BEGIN EXCLUSIVE")
            with patch.object(database, "check_operation", progress_check):
                worker.start()
                try:
                    assert entered.wait(timeout=2)
                    operation_control.request_stop()
                    worker.join(timeout=3)
                    assert not worker.is_alive()
                    assert len(errors) == 1
                finally:
                    holder.rollback()
                    worker.join(timeout=3)
        assert_no_temporary_backups(root)


def test_cancelled_migration_backup_removes_incomplete_file():
    with isolated_database() as root, closing(database.get_db_connection()) as conn:
        with patch.object(migration_runner, "check_operation", side_effect=[None, TimeoutError("timeout")]):
            expect_error(TimeoutError, lambda: migration_runner.create_migration_backup(
                conn, root / "migration_backups", 2
            ))
        assert not list((root / "migration_backups").glob("*.db"))
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_cancelled_migration_rolls_back_schema_data_and_version():
    with isolated_database(), closing(database.get_db_connection()) as conn:
        migrations = [(3, "003_test.sql", "CREATE TABLE cancelled(id); INSERT INTO areas(name) VALUES('Cancelled');")]
        conn.execute("PRAGMA user_version = 2")
        # Le prime due migrazioni vengono saltate; la terza viene interrotta prima del commit.
        migrations = [(1, "001.sql", ""), (2, "002.sql", ""), *migrations]
        check = operation_control.check_operation

        def cancel_before_commit():
            if conn.execute("PRAGMA user_version").fetchone()[0] == 3:
                raise TimeoutError("Migration deadline reached")
            check()

        with patch.object(migration_runner, "check_operation", side_effect=cancel_before_commit):
            expect_error(RuntimeError, lambda: migration_runner.apply_migrations(conn, migrations, ""))
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
        assert not conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'cancelled'").fetchone()
        assert conn.execute("SELECT count(*) FROM areas").fetchone()[0] == 1
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_shutdown_guard_rejects_new_requests_without_calling_application():
    called = Mock()
    messages = []

    async def app(scope, receive, send):
        called()

    async def send(message):
        messages.append(message)

    operation_control.request_stop()
    asyncio.run(shutdown_guard(app)({"type": "http"}, None, send))
    called.assert_not_called()
    assert messages[0]["status"] == 503


def test_subscribing_after_stop_returns_closed_queue_without_registering_reader():
    operation_control.request_stop()
    subscriber = event_service.subscribe()
    assert subscriber not in event_service._subscribers
    expect_error(ShutDown, subscriber.get_nowait)


def test_shutdown_guard_returns_504_for_operation_deadline_before_headers():
    messages = []

    async def app(scope, receive, send):
        raise TimeoutError("Operation deadline reached")

    async def send(message):
        messages.append(message)

    asyncio.run(shutdown_guard(app)({"type": "http"}, None, send))
    assert messages[0]["status"] == 504


def test_shutdown_guard_does_not_send_a_second_response_after_headers():
    messages = []

    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        raise TimeoutError("Transfer deadline reached")

    async def send(message):
        messages.append(message)

    expect_error(TimeoutError, lambda: asyncio.run(shutdown_guard(app)({"type": "http"}, None, send)))
    assert len(messages) == 1
    assert messages[0]["status"] == 200


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(
            function,
            setUp=operation_control.reset_operations,
            tearDown=operation_control.reset_operations,
        )
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
