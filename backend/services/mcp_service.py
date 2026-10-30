from mcp.server.mcpserver.exceptions import ToolError

from db.repositories import mcp_repo
from services import event_service
from validators.request_validator import validate_int, validate_text


MAX_BULK_AREAS = 50
MAX_BULK_PROJECTS = 50
MAX_BULK_TASKS = 50


def validate_optional_description(description):
    # Negli update None significa "lasciare invariata la descrizione": non va
    # passato a validate_text, che lo convertirebbe in "" svuotando il campo.
    if description is None:
        return None, None

    return validate_text(description, "description", required=False)


def get_all_areas() -> dict:
    areas = mcp_repo.get_all_areas()

    return {
        "area_count": len(areas),
        "areas": areas,
    }


def get_project_tasks(project_id) -> dict:
    project_id, error = validate_int(project_id, "project_id")

    if error:
        raise ToolError(error)

    existing_project_ids = mcp_repo.get_existing_project_ids([project_id])

    if project_id not in existing_project_ids:
        raise ToolError(f"Project not found: {project_id}.")

    tasks = mcp_repo.get_project_tasks(project_id)

    return {
        "project_id": project_id,
        "task_count": len(tasks),
        "tasks": tasks,
    }


def bulk_insert_area(names: list[str]) -> dict:
    if not names:
        raise ToolError("At least one area is required.")

    if len(names) > MAX_BULK_AREAS:
        raise ToolError(
            f"A maximum of {MAX_BULK_AREAS} areas can be created at once."
        )

    validated_names = []

    for name in names:
        validated_name, error = validate_text(name, "name")

        if error:
            raise ToolError(error)

        validated_names.append(validated_name)

    normalized_names = [name.casefold() for name in validated_names]

    if len(normalized_names) != len(set(normalized_names)):
        raise ToolError("The request contains duplicate area names.")

    inserted_ids = mcp_repo.bulk_insert_area(validated_names)

    event_service.publish({
        "entity": "area",
        "action": "created",
        "ids": inserted_ids,
    })

    return {
        "requested": len(validated_names),
        "created": len(inserted_ids),
        "area_ids": inserted_ids,
    }


def bulk_insert_project(projects: list[dict]) -> dict:
    if not projects:
        raise ToolError("At least one project is required.")

    if len(projects) > MAX_BULK_PROJECTS:
        raise ToolError(
            f"A maximum of {MAX_BULK_PROJECTS} projects can be created at once."
        )

    area_ids = []
    names = []
    descriptions = []

    for project in projects:
        area_id, error = validate_int(project.get("area_id"), "area_id")
        if error:
            raise ToolError(error)

        name, error = validate_text(project.get("name"), "name")
        if error:
            raise ToolError(error)

        description, error = validate_text(
            project.get("description"),
            "description",
            required=False,
        )
        if error:
            raise ToolError(error)

        area_ids.append(area_id)
        names.append(name)
        descriptions.append(description)

    existing_area_ids = mcp_repo.get_existing_area_ids(area_ids)
    missing_area_ids = sorted(set(area_ids) - existing_area_ids)

    if missing_area_ids:
        missing_ids = ", ".join(str(area_id) for area_id in missing_area_ids)
        raise ToolError(f"Areas not found: {missing_ids}.")

    inserted_ids = mcp_repo.bulk_insert_project(
        area_ids,
        names,
        descriptions,
    )

    event_service.publish({
        "entity": "project",
        "action": "created",
        "ids": inserted_ids,
    })

    return {
        "requested": len(projects),
        "created": len(inserted_ids),
        "project_ids": inserted_ids,
    }


def bulk_insert_task(tasks: list[dict]) -> dict:
    if not tasks:
        raise ToolError("At least one task is required.")

    if len(tasks) > MAX_BULK_TASKS:
        raise ToolError(
            f"A maximum of {MAX_BULK_TASKS} tasks can be created at once."
        )

    project_ids = []
    titles = []
    descriptions = []
    parent_ids = []

    for task in tasks:
        project_id, error = validate_int(task.get("project_id"), "project_id")
        if error:
            raise ToolError(error)

        title, error = validate_text(task.get("title"), "title")
        if error:
            raise ToolError(error)

        description, error = validate_text(
            task.get("description"),
            "description",
            required=False,
        )
        if error:
            raise ToolError(error)

        parent_id = task.get("parent_id")
        if parent_id is not None:
            parent_id, error = validate_int(parent_id, "parent_id")
            if error:
                raise ToolError(error)

        project_ids.append(project_id)
        titles.append(title)
        descriptions.append(description)
        parent_ids.append(parent_id)

    existing_project_ids = mcp_repo.get_existing_project_ids(project_ids)
    missing_project_ids = sorted(set(project_ids) - existing_project_ids)

    if missing_project_ids:
        missing_ids = ", ".join(
            str(project_id) for project_id in missing_project_ids
        )
        raise ToolError(f"Projects not found: {missing_ids}.")

    requested_parent_ids = {
        parent_id for parent_id in parent_ids if parent_id is not None
    }
    parent_tasks = mcp_repo.get_parent_tasks(requested_parent_ids)
    parent_tasks_by_id = {task["id"]: task for task in parent_tasks}
    missing_parent_ids = sorted(
        requested_parent_ids - set(parent_tasks_by_id)
    )

    if missing_parent_ids:
        missing_ids = ", ".join(
            str(parent_id) for parent_id in missing_parent_ids
        )
        raise ToolError(f"Parent tasks not found: {missing_ids}.")

    for project_id, parent_id in zip(project_ids, parent_ids, strict=True):
        if parent_id is None:
            continue

        parent_task = parent_tasks_by_id[parent_id]

        if parent_task["project_id"] != project_id:
            raise ToolError(
                f"Parent task {parent_id} belongs to a different project."
            )

        if parent_task["parent_id"] is not None:
            raise ToolError(
                f"Task {parent_id} cannot be a parent because it is a subtask."
            )

    inserted_ids = mcp_repo.bulk_insert_task(
        project_ids,
        titles,
        descriptions,
        parent_ids,
    )

    event_service.publish({
        "entity": "task",
        "action": "created",
        "ids": inserted_ids,
    })

    return {
        "requested": len(tasks),
        "created": len(inserted_ids),
        "task_ids": inserted_ids,
    }


def bulk_update_project(projects: list[dict]) -> dict:
    if not projects:
        raise ToolError("At least one project is required.")

    if len(projects) > MAX_BULK_PROJECTS:
        raise ToolError(
            f"A maximum of {MAX_BULK_PROJECTS} projects can be updated at once."
        )

    project_ids = []
    names = []
    descriptions = []

    for project in projects:
        project_id, error = validate_int(project.get("id"), "id")
        if error:
            raise ToolError(error)

        name, error = validate_text(project.get("name"), "name")
        if error:
            raise ToolError(error)

        description, error = validate_optional_description(project.get("description"))
        if error:
            raise ToolError(error)

        project_ids.append(project_id)
        names.append(name)
        descriptions.append(description)

    if len(project_ids) != len(set(project_ids)):
        raise ToolError("The request contains duplicate project IDs.")

    existing_project_ids = mcp_repo.get_existing_project_ids(project_ids)
    missing_project_ids = sorted(set(project_ids) - existing_project_ids)

    if missing_project_ids:
        missing_ids = ", ".join(
            str(project_id) for project_id in missing_project_ids
        )
        raise ToolError(f"Projects not found: {missing_ids}.")

    updated_ids = mcp_repo.bulk_update_project(
        project_ids,
        names,
        descriptions,
    )

    event_service.publish({
        "entity": "project",
        "action": "updated",
        "ids": updated_ids,
    })

    return {
        "requested": len(projects),
        "updated": len(updated_ids),
        "project_ids": updated_ids,
    }


def bulk_update_task(tasks: list[dict]) -> dict:
    if not tasks:
        raise ToolError("At least one task is required.")

    if len(tasks) > MAX_BULK_TASKS:
        raise ToolError(
            f"A maximum of {MAX_BULK_TASKS} tasks can be updated at once."
        )

    task_ids = []
    titles = []
    descriptions = []

    for task in tasks:
        task_id, error = validate_int(task.get("id"), "id")
        if error:
            raise ToolError(error)

        title, error = validate_text(task.get("title"), "title")
        if error:
            raise ToolError(error)

        description, error = validate_optional_description(task.get("description"))
        if error:
            raise ToolError(error)

        task_ids.append(task_id)
        titles.append(title)
        descriptions.append(description)

    if len(task_ids) != len(set(task_ids)):
        raise ToolError("The request contains duplicate task IDs.")

    existing_task_ids = mcp_repo.get_existing_task_ids(task_ids)
    missing_task_ids = sorted(set(task_ids) - existing_task_ids)

    if missing_task_ids:
        missing_ids = ", ".join(str(task_id) for task_id in missing_task_ids)
        raise ToolError(f"Tasks not found: {missing_ids}.")

    updated_ids = mcp_repo.bulk_update_task(
        task_ids,
        titles,
        descriptions,
    )

    event_service.publish({
        "entity": "task",
        "action": "updated",
        "ids": updated_ids,
    })

    return {
        "requested": len(tasks),
        "updated": len(updated_ids),
        "task_ids": updated_ids,
    }


def bulk_set_task_completed(tasks: list[dict]) -> dict:
    if not tasks:
        raise ToolError("At least one task is required.")

    if len(tasks) > MAX_BULK_TASKS:
        raise ToolError(
            f"A maximum of {MAX_BULK_TASKS} tasks can be updated at once."
        )

    task_ids = []
    completeds = []

    for task in tasks:
        task_id, error = validate_int(task.get("id"), "id")
        if error:
            raise ToolError(error)

        completed = task.get("completed")
        if not isinstance(completed, bool):
            raise ToolError("The completed field must be a boolean.")

        task_ids.append(task_id)
        completeds.append(completed)

    if len(task_ids) != len(set(task_ids)):
        raise ToolError("The request contains duplicate task IDs.")

    existing_task_ids = mcp_repo.get_existing_task_ids(task_ids)
    missing_task_ids = sorted(set(task_ids) - existing_task_ids)

    if missing_task_ids:
        missing_ids = ", ".join(str(task_id) for task_id in missing_task_ids)
        raise ToolError(f"Tasks not found: {missing_ids}.")

    # Lo stato delle task con subtask e calcolato dai trigger del database:
    # una modifica diretta verrebbe annullata pur risultando aggiornata.
    parent_task_ids = sorted(mcp_repo.get_task_ids_with_subtasks(task_ids))

    if parent_task_ids:
        parent_ids = ", ".join(str(task_id) for task_id in parent_task_ids)
        raise ToolError(
            f"Tasks with subtasks cannot be updated directly: {parent_ids}. "
            "Their status is derived from their subtasks: update the subtasks instead."
        )

    updated_ids = mcp_repo.bulk_set_task_completed(
        task_ids,
        completeds,
    )

    event_service.publish({
        "entity": "task",
        "action": "updated",
        "ids": updated_ids,
    })

    return {
        "requested": len(tasks),
        "updated": len(updated_ids),
        "task_ids": updated_ids,
    }


def validate_task_batch(tasks, label):
    if not isinstance(tasks, list) or not tasks:
        raise ToolError(f"{label} must be a non-empty list.")
    if len(tasks) > MAX_BULK_TASKS:
        raise ToolError(f"A maximum of {MAX_BULK_TASKS} {label} can be processed at once.")
    ids = []
    for task in tasks:
        if not isinstance(task, dict):
            raise ToolError(f"Each item in {label} must be an object.")
        task_id, error = validate_int(task.get("id"), "id")
        if error:
            raise ToolError(error)
        ids.append(task_id)
    if len(ids) != len(set(ids)):
        raise ToolError("The request contains duplicate task IDs.")
    return ids


def bulk_delete_task(tasks: list[dict], include_subtasks=False) -> dict:
    if not isinstance(include_subtasks, bool):
        raise ToolError("include_subtasks must be a boolean.")
    ids = validate_task_batch(tasks, "tasks")
    missing = sorted(set(ids) - mcp_repo.get_existing_task_ids(ids))
    if missing:
        raise ToolError("Tasks not found: " + ", ".join(map(str, missing)) + ".")
    if not include_subtasks:
        parents = sorted(mcp_repo.get_task_ids_with_subtasks(ids))
        if parents:
            raise ToolError(
                "Tasks with subtasks require include_subtasks=true: "
                + ", ".join(map(str, parents)) + "."
            )
    try:
        result = mcp_repo.bulk_delete_task(ids, include_subtasks)
    except ValueError as error:
        raise ToolError(str(error)) from error
    event_service.publish({"entity": "task", "action": "deleted", "ids": result["deleted_ids"]})
    return {
        "requested": len(ids), "deleted": len(result["deleted_ids"]),
        "requested_task_ids": ids, "task_ids": result["deleted_ids"],
        "parent_ids": result["parent_ids"],
    }


def bulk_move_subtask(subtasks: list[dict]) -> dict:
    ids = validate_task_batch(subtasks, "subtasks")
    parent_ids = []
    for task in subtasks:
        parent_id, error = validate_int(task.get("parent_id"), "parent_id")
        if error:
            raise ToolError(error)
        parent_ids.append(parent_id)
    rows = mcp_repo.get_tasks_by_ids(set(ids) | set(parent_ids))
    by_id = {row["id"]: row for row in rows}
    missing = sorted((set(ids) | set(parent_ids)) - set(by_id))
    if missing:
        raise ToolError("Tasks not found: " + ", ".join(map(str, missing)) + ".")
    nested_sources = mcp_repo.get_task_ids_with_subtasks(ids)
    for task_id, parent_id in zip(ids, parent_ids, strict=True):
        source, target = by_id[task_id], by_id[parent_id]
        if task_id == parent_id:
            raise ToolError("A subtask cannot be its own parent.")
        if source["parent_id"] is None or task_id in nested_sources:
            raise ToolError(f"Task {task_id} must be a subtask without children.")
        if target["parent_id"] is not None:
            raise ToolError(f"Destination task {parent_id} must be a top-level task.")
        if source["project_id"] != target["project_id"]:
            raise ToolError("Subtask and destination must belong to the same project.")
    try:
        result = mcp_repo.bulk_move_subtask(ids, parent_ids)
    except ValueError as error:
        raise ToolError(str(error)) from error
    if result["moved_ids"]:
        event_service.publish({
            "entity": "task", "action": "updated",
            "ids": sorted(set(result["moved_ids"]) | set(result["parent_ids"])),
        })
    return {
        "requested": len(ids), "moved": len(result["moved_ids"]),
        "task_ids": result["moved_ids"], "unchanged_ids": result["unchanged_ids"],
        "parent_ids": result["parent_ids"],
    }
