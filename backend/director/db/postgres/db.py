import json
import time
import logging
import os
from typing import List

from director.constants import DBType
from director.db.base import BaseDB
from director.db.postgres.initialize import initialize_postgres

logger = logging.getLogger(__name__)


class PostgresDB(BaseDB):
    def __init__(self):
        """Initialize PostgreSQL connection using environment variables."""

        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

        except ImportError:
            raise ImportError("Please install psycopg2 library to use PostgreSQL.")

        self.db_type = DBType.POSTGRES
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        initialize_postgres()
    def create_session(
        self,
        session_id: str,
        video_id: str,
        collection_id: str,
        name: str = None,
        created_at: int = None,
        updated_at: int = None,
        metadata: dict = {},
        **kwargs,
    ) -> None:
        created_at = created_at or int(time.time())
        updated_at = updated_at or int(time.time())

        self.cursor.execute(
            """
            INSERT INTO sessions (session_id, video_id, collection_id, name, created_at, updated_at, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO NOTHING
            """,
            (
                session_id,
                video_id,
                collection_id,
                name,
                created_at,
                updated_at,
                json.dumps(metadata),
            ),
        )
        self.conn.commit()

    def get_session(self, session_id: str) -> dict:
        self.cursor.execute(
            "SELECT * FROM sessions WHERE session_id = %s", (session_id,)
        )
        row = self.cursor.fetchone()
        if row is not None:
            session = dict(row)
            return session
        return {}

    def get_sessions(self) -> list:
        self.cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

    def add_or_update_msg_to_conv(
        self,
        session_id: str,
        conv_id: str,
        msg_id: str,
        msg_type: str,
        agents: List[str],
        actions: List[str],
        content: List[dict],
        status: str = None,
        created_at: int = None,
        updated_at: int = None,
        metadata: dict = {},
        **kwargs,
    ) -> None:
        created_at = created_at or int(time.time())
        updated_at = updated_at or int(time.time())

        self.cursor.execute(
            """
            INSERT INTO conversations (
                session_id, conv_id, msg_id, msg_type, agents, actions,
                content, status, created_at, updated_at, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (msg_id) DO UPDATE SET
                session_id = EXCLUDED.session_id,
                conv_id = EXCLUDED.conv_id,
                msg_type = EXCLUDED.msg_type,
                agents = EXCLUDED.agents,
                actions = EXCLUDED.actions,
                content = EXCLUDED.content,
                status = EXCLUDED.status,
                updated_at = EXCLUDED.updated_at,
                metadata = EXCLUDED.metadata
            """,
            (
                session_id,
                conv_id,
                msg_id,
                msg_type,
                json.dumps(agents),
                json.dumps(actions),
                json.dumps(content),
                status,
                created_at,
                updated_at,
                json.dumps(metadata),
            ),
        )
        self.conn.commit()

    def get_conversations(self, session_id: str) -> list:
        self.cursor.execute(
            "SELECT * FROM conversations WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,),
        )
        rows = self.cursor.fetchall()
        conversations = []
        for row in rows:
            if row is not None:
                conv_dict = dict(row)
                conversations.append(conv_dict)
        return conversations

    def get_context_messages(self, session_id: str) -> list:
        self.cursor.execute(
            "SELECT context_data FROM context_messages WHERE session_id = %s",
            (session_id,),
        )
        result = self.cursor.fetchone()
        return result["context_data"] if result else {}

    def add_or_update_context_msg(
        self,
        session_id: str,
        context_messages: list,
        created_at: int = None,
        updated_at: int = None,
        metadata: dict = {},
        **kwargs,
    ) -> None:
        created_at = created_at or int(time.time())
        updated_at = updated_at or int(time.time())

        self.cursor.execute(
            """
            INSERT INTO context_messages (context_data, session_id, created_at, updated_at, metadata)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                context_data = EXCLUDED.context_data,
                updated_at = EXCLUDED.updated_at,
                metadata = EXCLUDED.metadata
            """,
            (
                json.dumps(context_messages),
                session_id,
                created_at,
                updated_at,
                json.dumps(metadata),
            ),
        )
        self.conn.commit()

    def delete_conversation(self, session_id: str) -> bool:
        self.cursor.execute(
            "DELETE FROM conversations WHERE session_id = %s", (session_id,)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_context(self, session_id: str) -> bool:
        self.cursor.execute(
            "DELETE FROM context_messages WHERE session_id = %s", (session_id,)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_session(self, session_id: str) -> tuple[bool, list]:
        failed_components = []
        if not self.delete_conversation(session_id):
            failed_components.append("conversation")
        if not self.delete_context(session_id):
            failed_components.append("context")

        self.cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        self.conn.commit()
        if not self.cursor.rowcount > 0:
            failed_components.append("session")

        success = len(failed_components) < 3
        return success, failed_components

    def update_session(self, session_id: str, **kwargs) -> bool:
        """Update a session in the database."""
        try:
            if not kwargs:
                return False

            allowed_fields = {"name", "video_id", "collection_id", "metadata"}
            update_fields = []
            update_values = []

            for key, value in kwargs.items():
                if key not in allowed_fields:
                    continue
                if key == "metadata" and not isinstance(value, str):
                    value = json.dumps(value)
                update_fields.append(f"{key} = %s")
                update_values.append(value)

            if not update_fields:
                return False

            update_fields.append("updated_at = %s")
            update_values.append(int(time.time()))

            update_values.extend([session_id])

            query = f"""
                UPDATE sessions
                SET {', '.join(update_fields)}
                WHERE session_id = %s
            """

            self.cursor.execute(query, update_values)
            self.conn.commit()
            return self.cursor.rowcount > 0

        except Exception:
            logger.exception(f"Error updating session {session_id}")
            return False

    def make_session_public(self, session_id: str, is_public: bool) -> bool:
        """Make a session public or private."""
        try:
            query = """
                UPDATE sessions 
                SET is_public = %s, updated_at = %s
                WHERE session_id = %s
            """
            current_time = int(time.time())
            self.cursor.execute(query, (is_public, current_time, session_id))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Error making session public/private: {e}")
            return False

    def get_public_session(self, session_id: str) -> dict:
        """Get a public session by session_id."""
        try:
            query = """
                SELECT session_id, video_id, collection_id, name, created_at, updated_at, metadata, is_public
                FROM sessions 
                WHERE session_id = %s AND is_public = TRUE
            """
            self.cursor.execute(query, (session_id,))
            row = self.cursor.fetchone()
            if row:
                session = {
                    "session_id": row["session_id"],
                    "video_id": row["video_id"],
                    "collection_id": row["collection_id"],
                    "name": row["name"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": row["metadata"] if row["metadata"] else {},
                    "is_public": row["is_public"]
                }
                return session
            return {}
        except Exception as e:
            logger.exception(f"Error getting public session: {e}")
            return {}

    def health_check(self) -> bool:
        try:
            query = """
                SELECT COUNT(table_name)
                FROM information_schema.tables
                WHERE table_name IN ('sessions', 'conversations', 'context_messages')
                AND table_schema = 'public';
            """
            self.cursor.execute(query)
            table_count = self.cursor.fetchone()["count"]

            if table_count < 3:
                logger.info("Tables not found. Initializing PostgreSQL DB...")
                initialize_postgres()
            return True

        except Exception as e:
            logger.exception(f"PostgreSQL health check failed: {e}")
            return False

    def __del__(self):
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
