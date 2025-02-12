# database_utils.py
from datetime import datetime

from evaluation_utils.evaluate import format_duration
from utils.config import create_db_connection
from utils.learning_themes import LEARNING_THEMES


def log_conversation_to_db(
    username, prompt, response, start_time, end_time, interaction_count, language, theme
):
    if start_time is None or end_time is None:
        print(
            f"Start time or end time is None for user: {username}. Cannot log conversation."
        )
        return

    duration = end_time - start_time
    conn = create_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO conversations (
                    username, prompt, response, created_at, start_time, end_time,
                    interaction_count, duration, language, theme
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    username,
                    prompt,
                    response,
                    datetime.now(),
                    start_time,
                    end_time,
                    interaction_count,
                    duration,
                    language.lower(),
                    theme,
                ),
            )
            conn.commit()
    except Exception as e:
        print(f"Error logging conversation: {e}")
    finally:
        if conn:
            conn.close()


def fetch_progress_data(
    username, sort_order="desc", language_filter="all", theme_filter="all"
):
    conn = None
    try:
        conn = create_db_connection()
        with conn.cursor() as cursor:
            query = """
                SELECT created_at, language, theme, duration, interaction_count, evaluation
                FROM conversations
                WHERE username = %s
                AND evaluation IS NOT NULL
                AND theme IS NOT NULL
                AND language IS NOT NULL
            """
            params = [username]
            if language_filter != "all":
                query += " AND LOWER(language) = LOWER(%s)"
                params.append(language_filter)

            if theme_filter != "all":
                query += " AND theme = %s"
                params.append(theme_filter)

            order_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
            query += f" ORDER BY created_at {order_direction}"

            cursor.execute(query, params)
            progress = cursor.fetchall()
            result = []
            if progress:
                for row in progress:
                    (
                        created_at,
                        language,
                        theme,
                        duration,
                        interaction_count,
                        evaluation,
                    ) = row
                    result.append(
                        {
                            "date": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                            "language": language.capitalize(),
                            "theme": theme,
                            "duration": format_duration(duration),
                            "interaction_count": interaction_count,
                            "evaluation": evaluation,
                        }
                    )
            return result
    except Exception as e:
        return None
    finally:
        if conn:
            conn.close()


def fetch_all_users():
    conn = None
    try:
        conn = create_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT username FROM conversations")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        return []
    finally:
        if conn:
            conn.close()
