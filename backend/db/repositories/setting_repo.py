from db.db import get_db_connection

def format_data(row):
    return dict(row) if row else None

def get_all_settings():
    with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT * FROM settings
                """
            ).fetchall()
        return [format_data(row) for row in cursor]
    