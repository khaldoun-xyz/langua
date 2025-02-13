# database_utils.py
from datetime import datetime
from typing import Dict, List, Optional

from evaluation_utils.evaluate import format_duration
from utils.config import create_db_connection


def log_conversation_to_db(username: str, language: str, theme: str) -> int:
    with create_db_connection() as conn:
        if conn is None:
            return -1

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO conversations_sessions (username, language, theme, start_time)
                    VALUES (%s, %s, %s, %s)
                    RETURNING conversation_id
                    """,
                    (username, language, theme, datetime.now()),
                )
                conversation_id = cursor.fetchone()[0]
                conn.commit()
                return conversation_id
        except Exception as e:
            print(f"Error logging conversation session: {e}")
            return -1


def log_evaluation_to_db(
    conversation_id: int,
    evaluation: str,
    end_time: datetime,
    duration: datetime,
    interaction_count: int,
) -> bool:
    with create_db_connection() as conn:
        if conn is None:
            return False

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO conversations_evaluations
                    (conversation_id, evaluation, end_time, duration, interaction_count)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        conversation_id,
                        evaluation,
                        end_time,
                        duration,
                        interaction_count,
                    ),
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Error logging evaluation: {e}")
            conn.rollback()
            return False


def log_message_to_db(conversation_id: int, user_prompt: str, bot_message: str) -> None:
    with create_db_connection() as conn:
        if conn is None:
            return

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO conversations_messages (conversation_id, user_prompt, bot_message)
                    VALUES (%s, %s, %s)
                    """,
                    (conversation_id, user_prompt, bot_message),
                )
                conn.commit()
        except Exception as e:
            print(f"Error logging message: {e}")


def fetch_progress_data(
    username: str,
    sort_order: str = "desc",
    language_filter: str = "all",
    theme_filter: str = "all",
) -> Optional[List[Dict]]:
    with create_db_connection() as conn:
        if conn is None:
            return None

        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT cs.created_at, cs.language, cs.theme, ce.duration, ce.interaction_count, ce.evaluation
                    FROM conversations_sessions cs
                    LEFT JOIN conversations_evaluations ce ON cs.conversation_id = ce.conversation_id
                    WHERE cs.username = %s
                """
                params = [username]
                if language_filter != "all":
                    query += " AND LOWER(cs.language) = LOWER(%s)"
                    params.append(language_filter)

                if theme_filter != "all":
                    query += " AND cs.theme = %s"
                    params.append(theme_filter)

                order_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
                query += f" ORDER BY cs.created_at {order_direction}"

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
                                "evaluation": (
                                    evaluation
                                    if evaluation
                                    else "No evaluation available"
                                ),
                            }
                        )
                return result
        except Exception as e:
            print(f"Error fetching progress data: {e}")
            return None


def fetch_all_users() -> List[str]:
    with create_db_connection() as conn:
        if conn is None:
            return []

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT DISTINCT username FROM conversations_sessions")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []
