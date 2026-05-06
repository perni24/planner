from db.db import get_db_connection

def format_data(row):
    return dict(row) if row else None

def get_all_settings():
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM settings
            LIMIT 1
            """
        ).fetchone()

        return format_data(cursor)

    
def get_current_language(): 
     with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT language FROM settings
                """
            ).fetchone()
        
        return cursor["language"] if cursor else "it"