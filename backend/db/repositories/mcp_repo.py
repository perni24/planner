from contextlib import closing

from db.db import get_db_connection
from config import DATABASE_OPERATION_TIMEOUT_SECONDS
from services.operation_control import check_operation, operation_scope

def get_all_areas():
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.execute(
                """
                SELECT *
                FROM areas
                """
            ).fetchall()
        return [dict(row) for row in cursor]

def get_all_projects():
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.execute(
                """
                SELECT *
                FROM v_projects_status
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [dict(row) for row in cursor]

def get_project_tasks(project_id):
    with closing(get_db_connection()) as conn, conn:
        rows = conn.execute(
            """
            SELECT *
            FROM tasks
            WHERE project_id = ?
            ORDER BY parent_id IS NOT NULL, parent_id, created_at
            """,
            (project_id,)
        ).fetchall()

    return [dict(row) for row in rows]

def get_existing_area_ids(area_ids):
    unique_area_ids = tuple(set(area_ids))

    if not unique_area_ids:
        return set()

    placeholders = ", ".join("?" for _ in unique_area_ids)

    with closing(get_db_connection()) as conn, conn:
        rows = conn.execute(
            f"SELECT id FROM areas WHERE id IN ({placeholders})",
            unique_area_ids,
        ).fetchall()

    return {row["id"] for row in rows}

def get_existing_project_ids(project_ids):
    unique_project_ids = tuple(set(project_ids))

    if not unique_project_ids:
        return set()

    placeholders = ", ".join("?" for _ in unique_project_ids)

    with closing(get_db_connection()) as conn, conn:
        rows = conn.execute(
            f"SELECT id FROM projects WHERE id IN ({placeholders})",
            unique_project_ids,
        ).fetchall()

    return {row["id"] for row in rows}


def get_existing_task_ids(task_ids):
    unique_task_ids = tuple(set(task_ids))

    if not unique_task_ids:
        return set()

    placeholders = ", ".join("?" for _ in unique_task_ids)

    with closing(get_db_connection()) as conn, conn:
        rows = conn.execute(
            f"SELECT id FROM tasks WHERE id IN ({placeholders})",
            unique_task_ids,
        ).fetchall()

    return {row["id"] for row in rows}

def get_task_ids_with_subtasks(task_ids):
    unique_task_ids = tuple(set(task_ids))

    if not unique_task_ids:
        return set()

    placeholders = ", ".join("?" for _ in unique_task_ids)

    with closing(get_db_connection()) as conn, conn:
        rows = conn.execute(
            f"SELECT DISTINCT parent_id FROM tasks WHERE parent_id IN ({placeholders})",
            unique_task_ids,
        ).fetchall()

    return {row["parent_id"] for row in rows}

def _get_tasks_by_ids(conn, task_ids):
    unique_ids = tuple(set(task_ids))
    if not unique_ids:
        return []
    placeholders = ", ".join("?" for _ in unique_ids)
    rows = conn.execute(
        f"SELECT id, project_id, parent_id FROM tasks WHERE id IN ({placeholders})",
        unique_ids,
    ).fetchall()
    return [dict(row) for row in rows]


def get_tasks_by_ids(task_ids):
    task_ids = tuple(task_ids)
    if not task_ids:
        return []
    with closing(get_db_connection()) as conn, conn:
        return _get_tasks_by_ids(conn, task_ids)


def get_parent_tasks(parent_ids):
    return get_tasks_by_ids(parent_ids)

def bulk_insert_area(names):

    inserted_ids = []

    with operation_scope(DATABASE_OPERATION_TIMEOUT_SECONDS), closing(get_db_connection()) as conn, conn:
        for name in names:
            check_operation()
            cursor = conn.execute(
                """
                INSERT INTO areas (name) VALUES (?)
                """,
                (name,)
            )
            inserted_ids.append(cursor.lastrowid)
        check_operation()
        return inserted_ids

def bulk_insert_project(area_ids, names, descriptions):

    inserted_ids = []

    with operation_scope(DATABASE_OPERATION_TIMEOUT_SECONDS), closing(get_db_connection()) as conn, conn:
        for area_id, name, description in zip(
            area_ids,
            names,
            descriptions,
            strict=True,
        ):
            check_operation()
            cursor = conn.execute(
                """
                INSERT INTO projects (area_id, name, description)
                VALUES (?, ?, ?)
                """,
                (area_id, name, description)
            )
            inserted_ids.append(cursor.lastrowid)
        check_operation()
        return inserted_ids

def bulk_insert_task(project_ids, titles, descriptions, parent_ids):

    inserted_ids = []

    with operation_scope(DATABASE_OPERATION_TIMEOUT_SECONDS), closing(get_db_connection()) as conn, conn:
        for project_id, title, description, parent_id in zip(
            project_ids,
            titles,
            descriptions,
            parent_ids,
            strict=True,
        ):
            check_operation()
            cursor = conn.execute(
                """
                INSERT INTO tasks (project_id, parent_id, title, description)
                VALUES (?, ?, ?, ?)
                """,
                (project_id, parent_id, title, description)
            )
            inserted_ids.append(cursor.lastrowid)
        check_operation()
        return inserted_ids

def bulk_update_project(project_ids, names, descriptions):
    updated_ids = []

    with operation_scope(DATABASE_OPERATION_TIMEOUT_SECONDS), closing(get_db_connection()) as conn, conn:
        for project_id, name, description in zip(
            project_ids,
            names,
            descriptions,
            strict=True,
        ):
            check_operation()
            cursor = conn.execute(
                """
                UPDATE projects
                SET name = ?,
                    description = COALESCE(?, description),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, description, project_id)
            )

            if cursor.rowcount == 1:
                updated_ids.append(project_id)
        check_operation()

    return updated_ids

def bulk_update_task(ids, titles, descriptions):
    updated_ids = []

    with operation_scope(DATABASE_OPERATION_TIMEOUT_SECONDS), closing(get_db_connection()) as conn, conn:
        for task_id, title, description in zip(
            ids,
            titles,
            descriptions,
            strict=True,
        ):
            check_operation()
            cursor = conn.execute(
                """
                UPDATE tasks
                SET title = ?,
                    description = COALESCE(?, description),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, description, task_id)
            )

            if cursor.rowcount == 1:
                updated_ids.append(task_id)
        check_operation()

    return updated_ids

def bulk_set_task_completed(ids, completeds):
    updated_ids = []

    with operation_scope(DATABASE_OPERATION_TIMEOUT_SECONDS), closing(get_db_connection()) as conn, conn:
        for task_id, completed in zip(
            ids,
            completeds,
            strict=True,
        ):
            check_operation()
            cursor = conn.execute(
                """
                UPDATE tasks
                SET completed = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (int(completed), task_id),
            )

            if cursor.rowcount == 1:
                updated_ids.append(task_id)
        check_operation()

    return updated_ids


def bulk_delete_task(ids, include_subtasks=False):
    if not ids:
        return {"deleted_ids": [], "parent_ids": []}

    with operation_scope(DATABASE_OPERATION_TIMEOUT_SECONDS), closing(get_db_connection()) as conn, conn:
        # I controlli sotto lock impediscono che una nuova subtask aggiri il consenso.
        conn.execute("BEGIN IMMEDIATE")
        requested = _get_tasks_by_ids(conn, ids)
        if {row["id"] for row in requested} != set(ids):
            raise ValueError("Some requested tasks no longer exist. Reload tasks and retry.")

        placeholders = ", ".join("?" for _ in ids)
        if not include_subtasks:
            parents = conn.execute(
                f"SELECT DISTINCT parent_id FROM tasks WHERE parent_id IN ({placeholders})",
                tuple(ids),
            ).fetchall()
            if parents:
                raise ValueError("Tasks with subtasks require include_subtasks=true. Reload tasks and retry.")

        deleted_rows = conn.execute(
            f"""
            WITH RECURSIVE removed(id, parent_id) AS (
                SELECT id, parent_id FROM tasks WHERE id IN ({placeholders})
                UNION
                SELECT child.id, child.parent_id
                FROM tasks AS child JOIN removed ON child.parent_id = removed.id
            )
            SELECT id, parent_id FROM removed
            """,
            tuple(ids),
        ).fetchall()
        deleted_ids = {row["id"] for row in deleted_rows}
        parent_ids = {
            row["parent_id"] for row in deleted_rows
            if row["parent_id"] is not None and row["parent_id"] not in deleted_ids
        }
        for task_id in ids:
            check_operation()
            # Un ID richiesto puo essere gia stato eliminato dalla cascata del parent.
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        check_operation()

    return {"deleted_ids": sorted(deleted_ids), "parent_ids": sorted(parent_ids)}


def bulk_move_subtask(ids, parent_ids):
    moved_ids = []
    unchanged_ids = []
    affected_parents = set()

    with operation_scope(DATABASE_OPERATION_TIMEOUT_SECONDS), closing(get_db_connection()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        for task_id, parent_id in zip(ids, parent_ids, strict=True):
            check_operation()
            source = conn.execute(
                """
                SELECT source.parent_id
                FROM tasks AS source JOIN tasks AS target ON target.id = ?
                WHERE source.id = ? AND source.parent_id IS NOT NULL
                  AND source.id != target.id AND target.parent_id IS NULL
                  AND source.project_id = target.project_id
                  AND NOT EXISTS (SELECT 1 FROM tasks WHERE parent_id = source.id)
                """,
                (parent_id, task_id),
            ).fetchone()
            if source is None:
                raise ValueError("Subtask or destination is no longer valid. Reload tasks and retry.")
            old_parent_id = source["parent_id"]
            if old_parent_id == parent_id:
                unchanged_ids.append(task_id)
                continue
            cursor = conn.execute(
                "UPDATE tasks SET parent_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (parent_id, task_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Subtask could not be moved. Reload tasks and retry.")
            moved_ids.append(task_id)
            affected_parents.update((old_parent_id, parent_id))
        check_operation()

    return {
        "moved_ids": moved_ids, "unchanged_ids": unchanged_ids,
        "parent_ids": sorted(affected_parents),
    }
