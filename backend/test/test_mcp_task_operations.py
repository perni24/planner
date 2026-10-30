import unittest
from contextlib import closing
from unittest.mock import Mock, patch

from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.mcpserver.utilities.func_metadata import func_metadata
from pydantic import ValidationError

from db import db as database
from db.repositories import mcp_repo, project_repo, task_repo
from integration.mcp.mcp_tools import register_mcp_tools
from services import mcp_service
from test_repositories import expect_error, isolated_database, snapshot


def stored_task(task_id):
    return next((task for task in task_repo.get_all_tasks() if task["id"] == task_id), None)


def seed_tasks():
    project = project_repo.insert_project(1, "Project", "Description")
    other_project = project_repo.insert_project(1, "Other", "Description")
    first = task_repo.insert_task(project, "First", "First parent")
    second = task_repo.insert_task(project, "Second", "Second parent")
    other = task_repo.insert_task(other_project, "Other", "Other parent")
    opened = task_repo.insert_task(project, "Open child", "Keep description", first)
    completed = task_repo.insert_task(project, "Completed child", "Keep too", first)
    task_repo.update_status_task(completed)
    destination_child = task_repo.insert_task(project, "Destination child", "", second)
    task_repo.update_status_task(destination_child)
    return project, first, second, other, opened, completed, destination_child


def test_delete_requires_explicit_consent_for_parent_and_child_batch():
    with isolated_database(), patch.object(mcp_service.event_service, "publish") as publish:
        _, first, _, _, opened, _, _ = seed_tasks()
        before = snapshot()
        for tasks in ([{"id": first}], [{"id": first}, {"id": opened}]):
            expect_error(ToolError, mcp_service.bulk_delete_task, tasks)
            assert snapshot() == before
        for consent in (1, "true", "yes", None):
            expect_error(ToolError, mcp_service.bulk_delete_task, [{"id": first}], consent)
        publish.assert_not_called()


def test_delete_cascade_returns_unique_ids_and_publishes_after_commit():
    for child_first in (False, True):
        with isolated_database():
            _, first, second, _, opened, completed, _ = seed_tasks()
            ids = [opened, first] if child_first else [first, opened]
            events = []

            def on_publish(event):
                assert stored_task(first) is None
                assert stored_task(opened) is None
                assert stored_task(completed) is None
                assert stored_task(second) is not None
                events.append(event)

            with patch.object(mcp_service.event_service, "publish", on_publish):
                result = mcp_service.bulk_delete_task([{"id": value} for value in ids], True)
            assert result == {
                "requested": 2, "deleted": 3, "requested_task_ids": ids,
                "task_ids": sorted([first, opened, completed]), "parent_ids": [],
            }
            assert events == [{"entity": "task", "action": "deleted", "ids": result["task_ids"]}]
            with closing(database.get_db_connection()) as conn:
                assert not conn.execute("PRAGMA foreign_key_check").fetchall()


def test_delete_leaf_recalculates_surviving_parent():
    with isolated_database(), patch.object(mcp_service.event_service, "publish"):
        _, first, _, other, opened, _, _ = seed_tasks()
        result = mcp_service.bulk_delete_task([{"id": opened}, {"id": other}])
        assert result["deleted"] == 2
        assert result["parent_ids"] == [first]
        assert stored_task(first)["completed"] == 1


def test_delete_last_open_child_keeps_parent_open():
    with isolated_database(), patch.object(mcp_service.event_service, "publish"):
        project, first, _, _, opened, completed, _ = seed_tasks()
        mcp_service.bulk_delete_task([{"id": completed}])
        mcp_service.bulk_delete_task([{"id": opened}])
        assert stored_task(first)["completed"] == 0
        assert not task_repo.has_subtasks(first)
        assert project_repo.get_project(project)["total_tasks"] == 2


def test_invalid_batches_do_not_write_or_publish():
    with isolated_database(), patch.object(mcp_service.event_service, "publish") as publish:
        _, first, second, _, opened, _, _ = seed_tasks()
        before = snapshot()
        cases = (
            (mcp_service.bulk_delete_task, []),
            (mcp_service.bulk_delete_task, [{"id": opened}] * 51),
            (mcp_service.bulk_delete_task, [{"id": opened}] * 2),
            (mcp_service.bulk_delete_task, [{"id": opened}, {"id": 9999}]),
            (mcp_service.bulk_move_subtask, []),
            (mcp_service.bulk_move_subtask, [{"id": opened, "parent_id": second}] * 51),
            (mcp_service.bulk_move_subtask, [{"id": opened, "parent_id": second}] * 2),
            (mcp_service.bulk_move_subtask, [{"id": opened, "parent_id": second}, {"id": first, "parent_id": second}]),
        )
        for operation, payload in cases:
            expect_error(ToolError, operation, payload)
            assert snapshot() == before
        publish.assert_not_called()


def test_move_preserves_content_and_recalculates_both_parents():
    with isolated_database():
        project, first, second, _, opened, _, _ = seed_tasks()
        before = stored_task(opened)
        events = []

        def on_publish(event):
            assert stored_task(opened)["parent_id"] == second
            assert stored_task(first)["completed"] == 1
            assert stored_task(second)["completed"] == 0
            events.append(event)

        with patch.object(mcp_service.event_service, "publish", on_publish):
            result = mcp_service.bulk_move_subtask([{"id": opened, "parent_id": second}])
        assert result == {
            "requested": 1, "moved": 1, "task_ids": [opened],
            "unchanged_ids": [], "parent_ids": sorted([first, second]),
        }
        after = stored_task(opened)
        for field in ("id", "project_id", "title", "description", "completed", "created_at"):
            assert after[field] == before[field]
        assert events == [{"entity": "task", "action": "updated", "ids": sorted([opened, first, second])}]
        assert project_repo.get_project(project)["completed_tasks"] == 1


def test_move_last_child_preserves_old_parent_state():
    for completed_state in (0, 1):
        with isolated_database(), patch.object(mcp_service.event_service, "publish"):
            _, first, second, _, opened, completed, _ = seed_tasks()
            task_repo.delete_task(completed)
            if completed_state:
                task_repo.update_status_task(opened)
            assert stored_task(first)["completed"] == completed_state
            mcp_service.bulk_move_subtask([{"id": opened, "parent_id": second}])
            assert stored_task(first)["completed"] == completed_state
            assert not task_repo.has_subtasks(first)
            assert stored_task(second)["completed"] == completed_state


def test_move_to_current_parent_does_not_write_or_publish():
    with isolated_database(), patch.object(mcp_service.event_service, "publish") as publish:
        _, first, _, _, opened, _, _ = seed_tasks()
        before = snapshot()
        result = mcp_service.bulk_move_subtask([{"id": opened, "parent_id": first}])
        assert result == {
            "requested": 1, "moved": 0, "task_ids": [],
            "unchanged_ids": [opened], "parent_ids": [],
        }
        assert snapshot() == before
        publish.assert_not_called()


def test_move_rejects_self_nested_cross_project_missing_and_main_tasks():
    with isolated_database(), patch.object(mcp_service.event_service, "publish") as publish:
        _, first, second, other, opened, completed, _ = seed_tasks()
        before = snapshot()
        for source, target in (
            (opened, opened), (opened, completed), (opened, other),
            (opened, 9999), (9999, second), (first, second),
        ):
            expect_error(ToolError, mcp_service.bulk_move_subtask, [{"id": source, "parent_id": target}])
            assert snapshot() == before
        publish.assert_not_called()


def test_move_rejects_legacy_subtask_with_children():
    with isolated_database(), patch.object(mcp_service.event_service, "publish") as publish:
        project, _, second, _, opened, _, _ = seed_tasks()
        task_repo.insert_task(project, "Legacy nested", "", opened)
        before = snapshot()
        expect_error(ToolError, mcp_service.bulk_move_subtask, [{"id": opened, "parent_id": second}])
        assert snapshot() == before
        publish.assert_not_called()


def test_delete_rechecks_consent_if_child_appears_after_service_validation():
    with isolated_database(), patch.object(mcp_service.event_service, "publish") as publish:
        _, _, _, other, _, _, _ = seed_tasks()
        original = mcp_repo.bulk_delete_task

        def concurrent_child(ids, consent):
            parent = stored_task(other)
            task_repo.insert_task(parent["project_id"], "Concurrent child", "", other)
            return original(ids, consent)

        with patch.object(mcp_repo, "bulk_delete_task", concurrent_child):
            expect_error(ToolError, mcp_service.bulk_delete_task, [{"id": other}])
        assert stored_task(other) is not None
        assert task_repo.has_subtasks(other)
        publish.assert_not_called()


def test_move_rechecks_destination_if_it_changes_after_service_validation():
    with isolated_database(), patch.object(mcp_service.event_service, "publish") as publish:
        _, _, second, other, opened, _, _ = seed_tasks()
        original = mcp_repo.bulk_move_subtask

        def concurrent_change(ids, parents):
            with closing(database.get_db_connection()) as conn, conn:
                conn.execute("UPDATE tasks SET project_id = ? WHERE id = ?", (stored_task(other)["project_id"], second))
            return original(ids, parents)

        before = stored_task(opened)
        with patch.object(mcp_repo, "bulk_move_subtask", concurrent_change):
            expect_error(ToolError, mcp_service.bulk_move_subtask, [{"id": opened, "parent_id": second}])
        assert stored_task(opened) == before
        publish.assert_not_called()


def test_repository_errors_roll_back_entire_move_batch_and_parent_states():
    with isolated_database():
        _, _, second, other, opened, completed, _ = seed_tasks()
        before = snapshot()
        expect_error(ValueError, mcp_repo.bulk_move_subtask, [opened, completed], [second, other])
        assert snapshot() == before
        expect_error(ValueError, mcp_repo.bulk_move_subtask, [opened, completed], [second])
        assert snapshot() == before


def test_cancellation_rolls_back_new_bulk_operations_before_commit():
    with isolated_database(), patch.object(mcp_service.event_service, "publish") as publish:
        _, _, second, _, opened, completed, _ = seed_tasks()
        before = snapshot()
        cases = (
            (mcp_service.bulk_delete_task, [{"id": opened}, {"id": completed}]),
            (mcp_service.bulk_move_subtask, [{"id": opened, "parent_id": second}, {"id": completed, "parent_id": second}]),
        )
        for operation, payload in cases:
            for cancelled_check in (2, 3):
                calls = 0

                def cancel():
                    nonlocal calls
                    calls += 1
                    if calls == cancelled_check:
                        raise InterruptedError("Test cancellation")

                with patch.object(mcp_repo, "check_operation", cancel):
                    expect_error(InterruptedError, operation, payload)
                assert snapshot() == before
        publish.assert_not_called()


def registered_tools():
    functions = {}

    def capture(function):
        functions[function.__name__] = function
        return function

    registry = Mock()
    registry.tool.return_value = capture
    register_mcp_tools(registry)
    return functions


def test_new_tool_schemas_enforce_bounds_strict_ids_and_consent():
    functions = registered_tools()
    for name, field, item in (
        ("bulk_delete_task", "tasks", {"id": 1}),
        ("bulk_move_subtask", "subtasks", {"id": 1, "parent_id": 2}),
    ):
        metadata = func_metadata(functions[name])
        schema = metadata.arg_model.model_json_schema()["properties"][field]
        assert schema["minItems"] == 1 and schema["maxItems"] == 50
        for payload in ([], [item] * 51):
            expect_error(ValidationError, metadata.validate_arguments, {field: payload})
        for key in item:
            for value in (True, 1.0, "1", 0, -1, 2**63, None):
                expect_error(ValidationError, metadata.validate_arguments, {field: [{**item, key: value}]})
    metadata = func_metadata(functions["bulk_delete_task"])
    for value in (1, "true", "yes", None):
        expect_error(ValidationError, metadata.validate_arguments, {"tasks": [{"id": 1}], "include_subtasks": value})


def test_registered_tools_execute_validated_models_through_service():
    functions = registered_tools()
    with isolated_database(), patch.object(mcp_service.event_service, "publish"):
        _, first, second, _, opened, _, _ = seed_tasks()
        move = functions["bulk_move_subtask"]
        result = move(**func_metadata(move).validate_arguments({"subtasks": [{"id": opened, "parent_id": second}]}))
        assert result["moved"] == 1
        delete = functions["bulk_delete_task"]
        result = delete(**func_metadata(delete).validate_arguments({"tasks": [{"id": first}], "include_subtasks": True}))
        assert result["deleted"] == 2


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
