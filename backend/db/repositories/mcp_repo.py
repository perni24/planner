from db.db import get_db_connection

def get_all_areas():
    with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT *
                FROM areas
                """
            ).fetchall()
        return [dict(row) for row in cursor]

def get_all_projects():
    with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT *
                FROM v_projects_status
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [dict(row) for row in cursor]

def get_project_tasks(project_id):
    with get_db_connection() as conn:
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

    with get_db_connection() as conn:
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

    with get_db_connection() as conn:
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

    with get_db_connection() as conn:
        rows = conn.execute(
            f"SELECT id FROM tasks WHERE id IN ({placeholders})",
            unique_task_ids,
        ).fetchall()

    return {row["id"] for row in rows}

def get_parent_tasks(parent_ids):
    unique_parent_ids = tuple(set(parent_ids))

    if not unique_parent_ids:
        return []

    placeholders = ", ".join("?" for _ in unique_parent_ids)

    with get_db_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT id, project_id, parent_id
            FROM tasks
            WHERE id IN ({placeholders})
            """,
            unique_parent_ids,
        ).fetchall()

    return [dict(row) for row in rows]

def bulk_insert_area(names):

    inserted_ids = []

    with get_db_connection() as conn:
        for name in names:
            cursor = conn.execute(
                """
                INSERT INTO areas (name) VALUES (?)
                """,
                (name,)
            )
            inserted_ids.append(cursor.lastrowid)
        return inserted_ids

def bulk_insert_project(area_ids, names, descriptions):

    inserted_ids = []

    with get_db_connection() as conn:
        for area_id, name, description in zip(
            area_ids,
            names,
            descriptions,
            strict=True,
        ):
            cursor = conn.execute(
                """
                INSERT INTO projects (area_id, name, description)
                VALUES (?, ?, ?)
                """,
                (area_id, name, description)
            )
            inserted_ids.append(cursor.lastrowid)
        return inserted_ids

def bulk_insert_task(project_ids, titles, descriptions, parent_ids):

    inserted_ids = []

    with get_db_connection() as conn:
        for project_id, title, description, parent_id in zip(
            project_ids,
            titles,
            descriptions,
            parent_ids,
            strict=True,
        ):
            cursor = conn.execute(
                """
                INSERT INTO tasks (project_id, parent_id, title, description)
                VALUES (?, ?, ?, ?)
                """,
                (project_id, parent_id, title, description)
            )
            inserted_ids.append(cursor.lastrowid)
        return inserted_ids

def bulk_update_project(project_ids, names, descriptions):
    updated_ids = []

    with get_db_connection() as conn:
        for project_id, name, description in zip(
            project_ids,
            names,
            descriptions,
            strict=True,
        ):
            cursor = conn.execute(
                """
                UPDATE projects
                SET name = ?,
                    description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, description, project_id)
            )

            if cursor.rowcount == 1:
                updated_ids.append(project_id)

    return updated_ids

def bulk_update_task(ids, titles, descriptions):
    updated_ids = []

    with get_db_connection() as conn:
        for task_id, title, description in zip(
            ids,
            titles,
            descriptions,
            strict=True,
        ):
            cursor = conn.execute(
                """
                UPDATE tasks
                SET title = ?,
                    description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, description, task_id)
            )

            if cursor.rowcount == 1:
                updated_ids.append(task_id)

    return updated_ids

def bulk_set_task_completed(ids, completeds):
    updated_ids = []

    with get_db_connection() as conn:
        for task_id, completed in zip(
            ids,
            completeds,
            strict=True,
        ):
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

    return updated_ids
