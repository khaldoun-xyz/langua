# create_db.py
from utils.config import create_db_connection

CREATE_TABLES_QUERY = """
CREATE TABLE conversations_sessions (
    conversation_id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    language VARCHAR(50),
    theme VARCHAR(50),
    start_time TIMESTAMPTZ NOT NULL
);

CREATE TABLE conversations_messages (
    message_id SERIAL PRIMARY KEY,
    conversation_id INT NOT NULL REFERENCES conversations_sessions(conversation_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_prompt TEXT NOT NULL,
    bot_message TEXT NOT NULL
);

CREATE TABLE conversations_evaluations (
    evaluation_id SERIAL PRIMARY KEY,
    conversation_id INT NOT NULL REFERENCES conversations_sessions(conversation_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMPTZ NOT NULL,
    evaluation TEXT,
    interaction_count INTEGER NOT NULL,
    duration INTERVAL NOT NULL,
    UNIQUE (conversation_id)
);
"""


def create_tables():
    conn = create_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute(CREATE_TABLES_QUERY)
            conn.commit()
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
