import sqlite3
import unittest
from contextlib import ExitStack, closing, contextmanager, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from db import db as database
from db.repositories import area_repo, mcp_repo, project_repo, setting_repo, task_repo


REPOSITORIES = (area_repo, project_repo, task_repo, setting_repo, mcp_repo)
CUSTOM_COLORS = {
    "background": "#111111",
    "foreground": "#eeeeee",
    "card": "#222222",
    "border": "#333333",
    "hover": "#444444",
    "hoverText": "#ffffff",
}


def assert_connections_closed(connections):
    for conn in connections:
        try:
            conn.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            continue
        raise AssertionError("Repository left a database connection open")


@contextmanager
def isolated_database():
    with TemporaryDirectory(prefix="planner-repositories-") as directory:
        root = Path(directory)
        connections = []

        def tracked_connection():
            conn = database.get_db_connection()
            connections.append(conn)
            return conn

        with patch.multiple(
            database,
            DATA_DIR=str(root),
            DB_PATH=str(root / "planner.db"),
            MIGRATION_BACKUPS_DIR=str(root / "migration_backups"),
        ), redirect_stdout(StringIO()), ExitStack() as patches:
            database.init_db()
            for repository in REPOSITORIES:
                patches.enter_context(patch.object(repository, "get_db_connection", tracked_connection))
            try:
                yield connections
            finally:
                try:
                    assert_connections_closed(connections)
                finally:
                    for conn in connections:
                        conn.close()


def seed_projects_and_tasks():
    projects = [
        project_repo.insert_project(1, "First project", "First description"),
        project_repo.insert_project(1, "Second project", "Second description"),
    ]
    tasks = [
        task_repo.insert_task(project_id, f"Task {index}", "Description")
        for index, project_id in enumerate(projects)
    ]
    return projects, tasks


def snapshot():
    with closing(database.get_db_connection()) as conn:
        return {
            table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY id")]
            for table in ("areas", "projects", "tasks", "settings")
        }


def expect_error(exception, operation, *args):
    try:
        operation(*args)
    except exception:
        return
    raise AssertionError(f"Expected {exception.__name__}")


def test_area_crud_commits_and_closes_connections():
    with isolated_database():
        assert len(area_repo.get_all_areas()) == 1
        area_id = area_repo.insert_area("Second area")
        assert isinstance(area_id, int)
        assert area_repo.update_area(area_id, "Renamed area") == 1
        assert any(area["name"] == "Renamed area" for area in area_repo.get_all_areas())
        assert area_repo.delete_area(area_id) == 1
        assert area_repo.delete_area(area_id) == 0
        assert area_repo.update_area(area_id, "Missing area") == 0
        assert len(area_repo.get_all_areas()) == 1


def test_project_crud_returns_materialized_data_and_closes_connections():
    with isolated_database():
        project_id = project_repo.insert_project(1, "Project", "Description")
        assert project_repo.get_all_projects()[0]["id"] == project_id
        assert project_repo.get_projects_by_area(1)[0]["name"] == "Project"
        assert project_repo.get_project(project_id)["description"] == "Description"
        assert project_repo.update_project(project_id, "Renamed", "Updated description") == 1
        assert project_repo.get_project(project_id)["name"] == "Renamed"
        assert project_repo.delete_project(project_id) == 1
        assert project_repo.get_project(project_id) is None
        assert project_repo.get_projects_by_area(1) == []
        assert project_repo.update_project(project_id, "Missing", "Description") == 0
        assert project_repo.delete_project(project_id) == 0


def test_task_crud_and_completion_keep_transaction_behavior():
    with isolated_database():
        project_id = project_repo.insert_project(1, "Project", "Description")
        parent_id = task_repo.insert_task(project_id, "Parent", "Description")
        assert len(task_repo.get_all_tasks()) == 1
        assert task_repo.get_task(parent_id)["project_id"] == project_id
        assert task_repo.has_subtasks(parent_id) is False
        child_id = task_repo.insert_task(project_id, "Child", "Description", parent_id)
        assert task_repo.has_subtasks(parent_id) is True
        assert task_repo.update_task(child_id, "Renamed child", "Updated description") == 1
        assert task_repo.update_status_task(child_id) == 1
        tasks = {task["id"]: task for task in task_repo.get_tasks_by_project(project_id)}
        assert tasks[parent_id]["completed"] == tasks[child_id]["completed"] == 1
        assert tasks[child_id]["title"] == "Renamed child"
        assert task_repo.delete_task(child_id) == 1
        assert task_repo.delete_task(parent_id) == 1
        assert task_repo.get_task(parent_id) is None
        assert task_repo.has_subtasks(parent_id) is False
        assert task_repo.update_task(parent_id, "Missing", "Description") == 0
        assert task_repo.update_status_task(parent_id) == 0
        assert task_repo.delete_task(parent_id) == 0


def test_settings_updates_and_empty_results_close_connections():
    with isolated_database():
        assert setting_repo.get_current_language() == "it"
        setting_repo.update_language("en")
        setting_repo.update_theme("custom", CUSTOM_COLORS)
        settings = setting_repo.get_all_settings()
        assert settings["language"] == setting_repo.get_current_language() == "en"
        assert settings["theme"] == "custom"
        assert settings["custom_background"] == CUSTOM_COLORS["background"]
        assert settings["custom_hover_text"] == CUSTOM_COLORS["hoverText"]
        with closing(database.get_db_connection()) as conn:
            conn.execute("DELETE FROM settings")
            conn.commit()
        assert setting_repo.get_all_settings() is None
        assert setting_repo.get_current_language() == "it"


def test_rest_errors_close_connections_without_changing_data():
    with isolated_database() as connections:
        projects, tasks = seed_projects_and_tasks()
        operations = (
            (sqlite3.IntegrityError, area_repo.insert_area, (None,)),
            (sqlite3.IntegrityError, area_repo.update_area, (1, None)),
            (sqlite3.IntegrityError, project_repo.insert_project, (9999, "Invalid", "Description")),
            (sqlite3.IntegrityError, project_repo.update_project, (projects[0], None, "Description")),
            (sqlite3.IntegrityError, task_repo.insert_task, (9999, "Invalid", "Description")),
            (sqlite3.IntegrityError, task_repo.update_task, (tasks[0], None, "Description")),
            (sqlite3.IntegrityError, setting_repo.update_language, (None,)),
            (sqlite3.IntegrityError, setting_repo.update_theme, (None, CUSTOM_COLORS)),
            (KeyError, setting_repo.update_theme, ("custom", {})),
        )
        before = snapshot()
        for exception, operation, args in operations:
            expect_error(exception, operation, *args)
            assert snapshot() == before
            assert_connections_closed(connections)


def test_mcp_readers_return_data_after_connections_are_closed():
    with isolated_database():
        projects, tasks = seed_projects_and_tasks()
        child_id = task_repo.insert_task(projects[0], "Child", "Description", tasks[0])
        assert mcp_repo.get_all_areas()[0]["id"] == 1
        assert {project["id"] for project in mcp_repo.get_all_projects()} == set(projects)
        assert len(mcp_repo.get_project_tasks(projects[0])) == 2
        assert mcp_repo.get_project_tasks(9999) == []
        assert mcp_repo.get_existing_area_ids([1, 9999]) == {1}
        assert mcp_repo.get_existing_project_ids([*projects, 9999]) == set(projects)
        assert mcp_repo.get_existing_task_ids([*tasks, child_id, 9999]) == {*tasks, child_id}
        assert mcp_repo.get_task_ids_with_subtasks(tasks) == {tasks[0]}
        assert mcp_repo.get_parent_tasks([tasks[0]]) == [
            {"id": tasks[0], "project_id": projects[0], "parent_id": None}
        ]


def test_mcp_empty_id_lists_do_not_open_connections():
    with isolated_database() as connections:
        for operation in (
            mcp_repo.get_existing_area_ids,
            mcp_repo.get_existing_project_ids,
            mcp_repo.get_existing_task_ids,
            mcp_repo.get_task_ids_with_subtasks,
        ):
            assert operation([]) == set()
        assert mcp_repo.get_parent_tasks([]) == []
        assert connections == []


def test_mcp_bulk_writes_keep_automatic_commit():
    with isolated_database():
        area_ids = mcp_repo.bulk_insert_area(["First area", "Second area"])
        assert len(area_ids) == 2
        assert set(area_ids) <= mcp_repo.get_existing_area_ids(area_ids)
        project_ids = mcp_repo.bulk_insert_project(area_ids, ["First", "Second"], ["A", "B"])
        task_ids = mcp_repo.bulk_insert_task(project_ids, ["Task A", "Task B"], ["A", "B"], [None, None])
        assert mcp_repo.get_existing_task_ids(task_ids) == set(task_ids)
        assert mcp_repo.bulk_update_project(project_ids, ["Changed A", "Changed B"], ["C", "D"]) == project_ids
        assert mcp_repo.bulk_update_task(task_ids, ["Changed task A", "Changed task B"], ["C", "D"]) == task_ids
        assert mcp_repo.bulk_set_task_completed(task_ids, [True, False]) == task_ids
        assert project_repo.get_project(project_ids[0])["name"] == "Changed A"
        tasks = task_repo.get_all_tasks()
        assert {task["title"] for task in tasks} == {"Changed task A", "Changed task B"}
        assert {task["id"]: task["completed"] for task in tasks} == {
            task_ids[0]: 1, task_ids[1]: 0,
        }


def test_mcp_bulk_insert_errors_roll_back_partial_batches():
    with isolated_database() as connections:
        projects, _ = seed_projects_and_tasks()
        operations = (
            (mcp_repo.bulk_insert_area, (["Valid", None],)),
            (mcp_repo.bulk_insert_project, ([1, 9999], ["Valid", "Invalid"], ["A", "B"])),
            (mcp_repo.bulk_insert_task, ([projects[0], 9999], ["Valid", "Invalid"], ["A", "B"], [None, None])),
        )
        before = snapshot()
        for operation, args in operations:
            expect_error(sqlite3.IntegrityError, operation, *args)
            assert snapshot() == before
            assert_connections_closed(connections)


def test_mcp_bulk_update_errors_roll_back_partial_batches():
    with isolated_database() as connections:
        projects, tasks = seed_projects_and_tasks()
        operations = (
            (sqlite3.IntegrityError, mcp_repo.bulk_update_project, (projects, ["Changed", None], ["C", "D"])),
            (sqlite3.IntegrityError, mcp_repo.bulk_update_task, (tasks, ["Changed", None], ["C", "D"])),
            (TypeError, mcp_repo.bulk_set_task_completed, (tasks, [True, object()])),
        )
        before = snapshot()
        for exception, operation, args in operations:
            expect_error(exception, operation, *args)
            assert snapshot() == before
            assert_connections_closed(connections)


def test_mcp_mismatched_bulk_lengths_roll_back_and_close():
    with isolated_database() as connections:
        projects, tasks = seed_projects_and_tasks()
        operations = (
            (mcp_repo.bulk_insert_project, ([1, 1], ["Partial"], ["A", "B"])),
            (mcp_repo.bulk_insert_task, (projects, ["Partial"], ["A", "B"], [None, None])),
            (mcp_repo.bulk_update_project, (projects, ["Partial"], ["C", "D"])),
            (mcp_repo.bulk_update_task, (tasks, ["Partial"], ["C", "D"])),
            (mcp_repo.bulk_set_task_completed, (tasks, [True])),
        )
        before = snapshot()
        for operation, args in operations:
            expect_error(ValueError, operation, *args)
            assert snapshot() == before
            assert_connections_closed(connections)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
