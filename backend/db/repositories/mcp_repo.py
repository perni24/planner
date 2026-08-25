from db.db import get_db_connection

def get_all_projects():
    with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT *
                FROM v_projects_status
                WHERE area_id = ?
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [dict(row) for row in cursor]

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
                INSERT INTO projects (area_id, name, description) VALUES (?, ?, ?)
                """,
                (area_id, name, description)
            )
            inserted_ids.append(cursor.lastrowid)
        return inserted_ids