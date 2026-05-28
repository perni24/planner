from db.db import get_db_connection

def format_data(row):
    return dict(row) if row else None

def get_all_tasks(): 
    with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT * FROM tasks
                """
            ).fetchall()
        return [format_data(row) for row in cursor]

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
    
def update_task(id, title, description):
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE tasks 
            SET title = ? , description = ? , updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, description, id)
        )
        conn.commit()
        return cursor.lastrowid

def update_status_task(id): 
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET completed = 1 - completed,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (id,)
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