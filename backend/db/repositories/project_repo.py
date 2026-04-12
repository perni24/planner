from init_db import get_db_connection

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
            """
        ).fetchall()
        conn.commit()
        return cursor.lastrowid

def update_project(id, name, description):
    with get_db_connection() as conn:
        cursor  = conn.execute(
            """
            UPDATE projects SET name = ?, description = ? WHERE id = ?
            """
        ).fetchall()
        conn.commit()
        return cursor.lastrowid

def delete_project(id):
    with get_db_connection() as conn:
        cursor  = conn.execute(
            """
            DELETE FROM projects WHERE id = ?
            """
        ).fetchall()
        conn.commit()
        return cursor.lastrowid