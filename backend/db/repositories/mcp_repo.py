from db.db import get_db_connection

def get_all_projects():
    with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT * FROM projects
                """
            ).fetchall()

        return [dict(row) for row in cursor]