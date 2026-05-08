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
     

def update_language(language):
    with get_db_connection() as conn:
        conn.execute(
            """
            UPDATE settings SET language = ?
            """,
            (language,)
        )
        conn.commit()


def update_theme(theme, custom_colors):
    with get_db_connection() as conn:
        conn.execute(
            """
            UPDATE settings
            SET theme = ?,
                custom_background = ?,
                custom_foreground = ?,
                custom_card = ?,
                custom_border = ?,
                custom_hover = ?,
                custom_hover_text = ?
            WHERE id = (
                SELECT id
                FROM settings
                LIMIT 1
            )
            """,
            (
                theme,
                custom_colors["background"],
                custom_colors["foreground"],
                custom_colors["card"],
                custom_colors["border"],
                custom_colors["hover"],
                custom_colors["hoverText"],
            ),
        )
        conn.commit()

