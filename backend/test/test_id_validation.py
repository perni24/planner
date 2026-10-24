import asyncio
import json
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlencode

from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.mcpserver.utilities.func_metadata import func_metadata
from pydantic import ValidationError
from starlette.requests import Request

from integration.mcp.mcp_tools import register_mcp_tools
from integration.mcp.models import CreateProject, CreateTask, SetTaskCompleted, UpdateProject, UpdateTask
from routes import area_routes, project_routes, task_routes
from services import mcp_service
from validators.request_validator import SQLITE_MAX_INTEGER, validate_int, validate_payload


INVALID_IDS = (True, False, 1.0, 1.9, float("inf"), float("nan"), None, [], {}, b"7", 0, -1, SQLITE_MAX_INTEGER + 1, 10**30)


def expect_error(exception, operation):
    try:
        operation()
    except exception as error:
        return error
    raise AssertionError(f"Expected {exception.__name__}")


async def invoke_route(endpoint, payload=None, query=None):
    async def receive():
        return {"type": "http.request", "body": json.dumps(payload).encode(), "more_body": False}

    request = Request({
        "type": "http", "method": "POST" if payload is not None else "GET",
        "path": "/test", "headers": [], "query_string": urlencode(query or {}).encode(),
    }, receive)
    return await endpoint(request)


def test_validate_int_accepts_integer_ids_and_rest_numeric_strings():
    for value in (1, 7, SQLITE_MAX_INTEGER, "1", "7", " 7 ", str(SQLITE_MAX_INTEGER)):
        result, error = validate_int(value, "project_id")
        assert error is None
        assert type(result) is int
        assert result == int(value)


def test_validate_int_rejects_coercions_missing_values_and_out_of_range_ids():
    for value in (*INVALID_IDS, "", "1.9", "1.0", "true", "abc", "0", "-1", str(10**30)):
        result, error = validate_int(value, "task_id")
        assert result is None, repr(value)
        assert error and "task_id" in error, repr(value)


def test_all_payload_id_fields_use_shared_validation():
    for field in ("id", "area_id", "project_id", "task_id", "parent_id"):
        assert validate_payload({field: "7"}, [field]) == ({field: 7}, None)
        for value in INVALID_IDS:
            if field == "parent_id" and value is None:
                continue
            result, error = validate_payload({field: value}, [field])
            assert result is None and field in error, (field, repr(value))
    assert validate_payload({}, ["parent_id"]) == ({"parent_id": None}, None)
    assert validate_payload({"parent_id": None}, ["parent_id"]) == ({"parent_id": None}, None)


def test_rest_write_routes_reject_invalid_ids_before_repository_access():
    cases = (
        (area_routes, "areaRepo", area_routes.update_area, "id", {"name": "Area"}),
        (area_routes, "areaRepo", area_routes.delete_area, "id", {}),
        (project_routes, "projectRepo", project_routes.insert_project, "area_id", {"name": "Project"}),
        (project_routes, "projectRepo", project_routes.update_project, "project_id", {"name": "Project"}),
        (project_routes, "projectRepo", project_routes.delete_project, "project_id", {}),
        (task_routes, "taskRepo", task_routes.insert_task, "project_id", {"title": "Task"}),
        (task_routes, "taskRepo", task_routes.insert_task, "parent_id", {"project_id": 7, "title": "Task"}),
        (task_routes, "taskRepo", task_routes.update_task, "task_id", {"title": "Task"}),
        (task_routes, "taskRepo", task_routes.update_status_task, "task_id", {}),
        (task_routes, "taskRepo", task_routes.delete_task, "task_id", {}),
    )
    for module, alias, endpoint, field, payload in cases:
        with patch.object(module, alias) as repository:
            for value in (True, False, 1.0, 1.9, 0, -1, SQLITE_MAX_INTEGER + 1):
                response = asyncio.run(invoke_route(endpoint, {**payload, field: value}))
                assert response.status_code == 400, (endpoint.__name__, field, value)
                assert field in json.loads(response.body)["error"]
            assert repository.mock_calls == []


def test_rest_queries_preserve_string_ids_and_reject_overflow():
    cases = (
        (project_routes, "projectRepo", project_routes.get_projects_by_area, "area_id", "get_projects_by_area"),
        (project_routes, "projectRepo", project_routes.get_project, "project_id", "get_project"),
        (task_routes, "taskRepo", task_routes.get_tasks_by_project, "project_id", "get_tasks_by_project"),
    )
    for module, alias, endpoint, field, method in cases:
        with patch.object(module, alias) as repository:
            for value in (str(SQLITE_MAX_INTEGER + 1), "1.9", "true", "0"):
                response = asyncio.run(invoke_route(endpoint, query={field: value}))
                assert response.status_code == 400
            assert repository.mock_calls == []
            getattr(repository, method).return_value = []
            response = asyncio.run(invoke_route(endpoint, query={field: str(SQLITE_MAX_INTEGER)}))
            assert response.status_code == 200
            getattr(repository, method).assert_called_once_with(SQLITE_MAX_INTEGER)


def test_mcp_models_reject_id_coercions_and_publish_sqlite_bounds():
    cases = (
        (CreateProject, "area_id", {"name": "Project"}),
        (CreateTask, "project_id", {"title": "Task"}),
        (CreateTask, "parent_id", {"project_id": 7, "title": "Task"}),
        (UpdateProject, "id", {"name": "Project"}),
        (UpdateTask, "id", {"title": "Task"}),
        (SetTaskCompleted, "id", {"completed": True}),
    )
    for model, field, payload in cases:
        for value in (*INVALID_IDS, "7"):
            if field == "parent_id" and value is None:
                continue
            expect_error(ValidationError, lambda: model.model_validate({**payload, field: value}))
        for value in (1, SQLITE_MAX_INTEGER):
            assert getattr(model.model_validate({**payload, field: value}), field) == value
            assert getattr(model.model_validate_json(json.dumps({**payload, field: value})), field) == value
        schema = model.model_json_schema()["properties"][field]
        if field == "parent_id":
            schema = next(item for item in schema["anyOf"] if item["type"] == "integer")
        assert schema["type"] == "integer"
        assert schema["exclusiveMinimum"] == 0
        assert schema["maximum"] == SQLITE_MAX_INTEGER
    assert CreateTask(project_id=7, title="Task").parent_id is None


def test_mcp_read_tool_preserves_strict_id_validation_in_sdk_arguments():
    functions = {}

    def capture(function):
        functions[function.__name__] = function
        return function

    registry = Mock()
    registry.tool.return_value = capture
    register_mcp_tools(registry)
    metadata = func_metadata(functions["get_project_tasks"])
    for value in (*INVALID_IDS, "7"):
        expect_error(ValidationError, lambda: metadata.validate_arguments({"project_id": value}))
    assert metadata.validate_arguments({"project_id": SQLITE_MAX_INTEGER}) == {"project_id": SQLITE_MAX_INTEGER}


def test_mcp_services_reject_invalid_ids_before_queries_or_events():
    cases = (
        (mcp_service.get_project_tasks, lambda value: value),
        (mcp_service.bulk_insert_project, lambda value: [{"area_id": value, "name": "Project"}]),
        (mcp_service.bulk_insert_task, lambda value: [{"project_id": value, "title": "Task"}]),
        (mcp_service.bulk_insert_task, lambda value: [{"project_id": 7, "parent_id": value, "title": "Task"}]),
        (mcp_service.bulk_update_project, lambda value: [{"id": value, "name": "Project"}]),
        (mcp_service.bulk_update_task, lambda value: [{"id": value, "title": "Task"}]),
        (mcp_service.bulk_set_task_completed, lambda value: [{"id": value, "completed": True}]),
    )
    with patch.object(mcp_service, "mcp_repo") as repository, patch.object(mcp_service.event_service, "publish") as publish:
        for operation, arguments in cases:
            for value in (True, False, 1.0, 1.9, 0, SQLITE_MAX_INTEGER + 1):
                expect_error(ToolError, lambda: operation(arguments(value)))
        assert repository.mock_calls == []
        publish.assert_not_called()


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(function)
        for name, function in globals().items()
        if name.startswith("test_") and callable(function)
    )


if __name__ == "__main__":
    unittest.main()
