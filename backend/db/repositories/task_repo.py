from db.db import get_db_connection

def format_data(row):
    return dict(row) if row else None

def get_tasks_by_project(project_id):
    with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT * FROM tasks WHERE project_id = ?
                """, 
                (project_id,)
            ).fetchall()
        return [format_data(row) for row in cursor]
    
def insert_task(project_id, title, description):
    with get_db_connection() as conn:
        cursor  = conn.execute(
            """
            INSERT INTO tasks (project_id, title, description) VALUES (?, ?, ?)
            """,
            (project_id, title, description)
        )
        conn.commit()
        return cursor.lastrowid 
    
def delete_task(id):
    with get_db_connection() as conn:
        cursor  = conn.execute(
            """
            DELETE FROM tasks WHERE id = ?
            """,
            (id)
        )
        conn.commit()
        return cursor.lastrowid