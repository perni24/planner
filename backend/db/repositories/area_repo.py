from db.db import get_db_connection

def format_data(row):
    return dict(row) if row else None

def get_all_areas(): 
    with get_db_connection() as conn:
        cursor = conn.execute(
                """
                SELECT * FROM areas
                """
            ).fetchall()
        return [format_data(row) for row in cursor]

def insert_area(name):
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO areas (name) VALUES (?)
            """,
            (name,)
        )
        conn.commit()
        return cursor.lastrowid

def unpdate_area(id, name):
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE areas SET name = ? WHERE id = ?
            """,
            (name, id)
        )
        conn.commit()