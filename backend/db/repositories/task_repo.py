from contextlib import closing

from db.db import get_db_connection

def format_data(row):
    return dict(row) if row else None

def get_all_tasks(): 
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.execute(
                """
                SELECT * FROM tasks
                """
            ).fetchall()
        return [format_data(row) for row in cursor]

def get_tasks_by_project(project_id):
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.execute(
                """
                SELECT * FROM tasks WHERE project_id = ?
                """, 
                (project_id,)
            ).fetchall()
        return [format_data(row) for row in cursor]

def get_task(task_id):
    with closing(get_db_connection()) as conn, conn:
        row = conn.execute(
            """
            SELECT id, project_id, parent_id
            FROM tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()
        return format_data(row)

def insert_task(project_id, title, description, parent_id=None):
    with closing(get_db_connection()) as conn, conn:
        cursor  = conn.execute(
            """
            INSERT INTO tasks (project_id, parent_id, title, description) VALUES (?, ?, ?, ?)
            """,
            (project_id, parent_id, title, description)
        )
        conn.commit()
        return cursor.lastrowid 
    
def update_task(id, title, description):
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.execute(
            """
            UPDATE tasks 
            SET title = ? , description = ? , updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, description, id)
        )
        conn.commit()
        return cursor.rowcount

def has_subtasks(id):
    with closing(get_db_connection()) as conn, conn:
        row = conn.execute(
            """
            SELECT 1 FROM tasks WHERE parent_id = ? LIMIT 1
            """,
            (id,)
        ).fetchone()
        return row is not None

def update_status_task(id): 
    with closing(get_db_connection()) as conn, conn:
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
        return cursor.rowcount

def delete_task(id):
    with closing(get_db_connection()) as conn, conn:
        cursor  = conn.execute(
            """
            DELETE FROM tasks WHERE id = ?
            """,
            (id,)
        )
        conn.commit()
        return cursor.rowcount
