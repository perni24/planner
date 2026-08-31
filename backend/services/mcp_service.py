from db.repositories import mcp_repo
from services import event_service
from validators.request_validator import validate_int, validate_text


MAX_BULK_AREAS = 50
MAX_BULK_PROJECTS = 50
MAX_BULK_TASKS = 50


def get_all_areas() -> dict:
    areas = mcp_repo.get_all_areas()

    return {
        "area_count": len(areas),
        "areas": areas,
    }


def get_project_tasks(project_id) -> dict:
    project_id, error = validate_int(project_id, "project_id")

    if error:
        raise ValueError(error)

    existing_project_ids = mcp_repo.get_existing_project_ids([project_id])

    if project_id not in existing_project_ids:
        raise ValueError(f"Progetto non trovato: {project_id}.")

    tasks = mcp_repo.get_project_tasks(project_id)

    return {
        "project_id": project_id,
        "task_count": len(tasks),
        "tasks": tasks,
    }


def bulk_insert_area(names: list[str]) -> dict:
    if not names:
        raise ValueError("Inserire almeno un'area.")

    if len(names) > MAX_BULK_AREAS:
        raise ValueError(
            f"Puoi creare al massimo {MAX_BULK_AREAS} aree."
        )

    validated_names = []

    for name in names:
        validated_name, error = validate_text(name, "name")

        if error:
            raise ValueError(error)

        validated_names.append(validated_name)

    normalized_names = [name.casefold() for name in validated_names]

    if len(normalized_names) != len(set(normalized_names)):
        raise ValueError("La richiesta contiene nomi duplicati.")

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
        raise ValueError("Inserire almeno un progetto.")

    if len(projects) > MAX_BULK_PROJECTS:
        raise ValueError(
            f"Puoi creare al massimo {MAX_BULK_PROJECTS} progetti."
        )

    area_ids = []
    names = []
    descriptions = []

    for project in projects:
        area_id, error = validate_int(project.get("area_id"), "area_id")
        if error:
            raise ValueError(error)

        name, error = validate_text(project.get("name"), "name")
        if error:
            raise ValueError(error)

        description, error = validate_text(
            project.get("description"),
            "description",
            required=False,
        )
        if error:
            raise ValueError(error)

        area_ids.append(area_id)
        names.append(name)
        descriptions.append(description)

    existing_area_ids = mcp_repo.get_existing_area_ids(area_ids)
    missing_area_ids = sorted(set(area_ids) - existing_area_ids)

    if missing_area_ids:
        missing_ids = ", ".join(str(area_id) for area_id in missing_area_ids)
        raise ValueError(f"Aree non trovate: {missing_ids}.")

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
        raise ValueError("Inserire almeno una task.")

    if len(tasks) > MAX_BULK_TASKS:
        raise ValueError(
            f"Puoi creare al massimo {MAX_BULK_TASKS} task."
        )

    project_ids = []
    titles = []
    descriptions = []
    parent_ids = []

    for task in tasks:
        project_id, error = validate_int(task.get("project_id"), "project_id")
        if error:
            raise ValueError(error)

        title, error = validate_text(task.get("title"), "title")
        if error:
            raise ValueError(error)

        description, error = validate_text(
            task.get("description"),
            "description",
            required=False,
        )
        if error:
            raise ValueError(error)

        parent_id = task.get("parent_id")
        if parent_id is not None:
            parent_id, error = validate_int(parent_id, "parent_id")
            if error:
                raise ValueError(error)

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
        raise ValueError(f"Progetti non trovati: {missing_ids}.")

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
        raise ValueError(f"Task padre non trovate: {missing_ids}.")

    for project_id, parent_id in zip(project_ids, parent_ids, strict=True):
        if parent_id is None:
            continue

        parent_task = parent_tasks_by_id[parent_id]

        if parent_task["project_id"] != project_id:
            raise ValueError(
                f"La task padre {parent_id} appartiene a un altro progetto."
            )

        if parent_task["parent_id"] is not None:
            raise ValueError(
                f"La task {parent_id} indicata come padre risulta una sotto-task."
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
        raise ValueError("Inserire almeno un progetto.")

    if len(projects) > MAX_BULK_PROJECTS:
        raise ValueError(
            f"Puoi aggiornare al massimo {MAX_BULK_PROJECTS} progetti."
        )

    project_ids = []
    names = []
    descriptions = []

    for project in projects:
        project_id, error = validate_int(project.get("id"), "id")
        if error:
            raise ValueError(error)

        name, error = validate_text(project.get("name"), "name")
        if error:
            raise ValueError(error)

        description, error = validate_text(
            project.get("description"),
            "description",
            required=False,
        )
        if error:
            raise ValueError(error)

        project_ids.append(project_id)
        names.append(name)
        descriptions.append(description)

    if len(project_ids) != len(set(project_ids)):
        raise ValueError("La richiesta contiene ID progetto duplicati.")

    existing_project_ids = mcp_repo.get_existing_project_ids(project_ids)
    missing_project_ids = sorted(set(project_ids) - existing_project_ids)

    if missing_project_ids:
        missing_ids = ", ".join(
            str(project_id) for project_id in missing_project_ids
        )
        raise ValueError(f"Progetti non trovati: {missing_ids}.")

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
        raise ValueError("Inserire almeno una task.")

    if len(tasks) > MAX_BULK_TASKS:
        raise ValueError(
            f"Puoi aggiornare al massimo {MAX_BULK_TASKS} task."
        )

    task_ids = []
    titles = []
    descriptions = []

    for task in tasks:
        task_id, error = validate_int(task.get("id"), "id")
        if error:
            raise ValueError(error)

        title, error = validate_text(task.get("title"), "title")
        if error:
            raise ValueError(error)

        description, error = validate_text(
            task.get("description"),
            "description",
            required=False,
        )
        if error:
            raise ValueError(error)

        task_ids.append(task_id)
        titles.append(title)
        descriptions.append(description)

    if len(task_ids) != len(set(task_ids)):
        raise ValueError("La richiesta contiene ID task duplicati.")

    existing_task_ids = mcp_repo.get_existing_task_ids(task_ids)
    missing_task_ids = sorted(set(task_ids) - existing_task_ids)

    if missing_task_ids:
        missing_ids = ", ".join(str(task_id) for task_id in missing_task_ids)
        raise ValueError(f"Task non trovate: {missing_ids}.")

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
        raise ValueError("Inserire almeno una task.")

    if len(tasks) > MAX_BULK_TASKS:
        raise ValueError(
            f"Puoi aggiornare al massimo {MAX_BULK_TASKS} task."
        )

    task_ids = []
    completeds = []

    for task in tasks:
        task_id, error = validate_int(task.get("id"), "id")
        if error:
            raise ValueError(error)

        completed = task.get("completed")
        if not isinstance(completed, bool):
            raise ValueError("Il campo completed deve essere booleano.")

        task_ids.append(task_id)
        completeds.append(completed)

    if len(task_ids) != len(set(task_ids)):
        raise ValueError("La richiesta contiene ID task duplicati.")

    existing_task_ids = mcp_repo.get_existing_task_ids(task_ids)
    missing_task_ids = sorted(set(task_ids) - existing_task_ids)

    if missing_task_ids:
        missing_ids = ", ".join(str(task_id) for task_id in missing_task_ids)
        raise ValueError(f"Task non trovate: {missing_ids}.")

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
