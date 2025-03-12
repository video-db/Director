import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    video_id TEXT,
    collection_id TEXT,
    created_at BIGINT,
    updated_at BIGINT,
    metadata JSONB
);
"""

CREATE_CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    session_id TEXT,
    conv_id TEXT,
    msg_id TEXT PRIMARY KEY,
    msg_type TEXT,
    agents JSONB,
    actions JSONB,
    content JSONB,
    status TEXT,
    created_at BIGINT,
    updated_at BIGINT,
    metadata JSONB,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
"""

CREATE_CONTEXT_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS context_messages (
    session_id TEXT PRIMARY KEY,
    context_data JSONB,
    created_at BIGINT,
    updated_at BIGINT,
    metadata JSONB,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
"""


def initialize_postgres():
    """Initialize the PostgreSQL database by creating the necessary tables."""

    try:
        import psycopg2

    except ImportError:
        raise ImportError("Please install psycopg2 library to use PostgreSQL.")

    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
    )
    cursor = conn.cursor()

    try:
        cursor.execute(CREATE_SESSIONS_TABLE)
        cursor.execute(CREATE_CONVERSATIONS_TABLE)
        cursor.execute(CREATE_CONTEXT_MESSAGES_TABLE)
        conn.commit()
        logger.info("PostgreSQL tables created successfully")
    except Exception as e:
        logger.exception(f"Error creating PostgreSQL tables: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    initialize_postgres()
