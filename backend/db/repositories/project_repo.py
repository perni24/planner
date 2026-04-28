from db.db import get_db_connection

def format_data(row):
    return dict(row) if row else None

def get_all_projects():
    with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT * FROM projects
                """
            ).fetchall()
        return [format_data(row) for row in cursor]
    
def get_projects_by_area(area_id):
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM v_projects_status
            WHERE area_id = ?
            ORDER BY created_at DESC
            """,
            (area_id,),
        ).fetchall()

        return [format_data(row) for row in rows]

def insert_project(area_id, name,description):
    with get_db_connection() as conn:
        cursor  = conn.execute(
            """
            INSERT INTO projects (area_id, name, description) VALUES (?, ?)
            """,
            (area_id, name, description)
        )
        conn.commit()
        return cursor.lastrowid

def delete_project(id):
    with get_db_connection() as conn:
        cursor  = conn.execute(
            """
            DELETE FROM projects WHERE id = ?
            """,
            (id)
        )
        conn.commit()
        return cursor.lastrowid