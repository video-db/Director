import json
import time
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List

from director.constants import DBType
from director.db.base import BaseDB
from director.db.postgres.initialize import initialize_postgres

logger = logging.getLogger(__name__)

class PostgresDB(BaseDB):
    def __init__(self):
        """Initialize PostgreSQL connection using environment variables."""
        self.db_type = DBType.POSTGRES
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)


    def create_session(
        self,
        session_id: str,
        video_id: str,
        collection_id: str,
        created_at: int = None,
        updated_at: int = None,
        metadata: dict = {},
        **kwargs,
    ) -> None:
        created_at = created_at or int(time.time())
        updated_at = updated_at or int(time.time())

        self.cursor.execute(
            """
            INSERT INTO sessions (session_id, video_id, collection_id, created_at, updated_at, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO NOTHING
            """,
            (
                session_id,
                video_id,
                collection_id,
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
            "SELECT * FROM conversations WHERE session_id = %s", (session_id,)
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

    def delete_session(self, session_id: str) -> bool:
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
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
