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

def insert_project(name,description):
    with get_db_connection() as conn:
        cursor  = conn.execute(
            """
            INSERT INTO projects (name, description) VALUES (?, ?)
            """,
            (name, description)
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