import json
import sqlite3
import time
import logging
import os

from typing import List

from director.constants import DBType
from director.db.base import BaseDB
from director.db.sqlite.initialize import initialize_sqlite

logger = logging.getLogger(__name__)


class SQLiteDB(BaseDB):
    def __init__(self, db_path: str = None):
        """
        :param db_path: Path to the SQLite database file.
        """
        self.db_type = DBType.SQLITE
        if db_path is None:
            self.db_path = os.getenv("SQLITE_DB_PATH", "director.db")
        else:
            self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=True)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        logger.info("Connected to SQLite DB...")

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
        """Create a new session.

        :param session_id: Unique session ID.
        :param video_id: ID of the video associated with the session.
        :param collection_id: ID of the collection associated with the session.
        :param created_at: Timestamp when the session was created.
        :param updated_at: Timestamp when the session was last updated.
        :param metadata: Additional metadata for the session.
        """
        created_at = created_at or int(time.time())
        updated_at = updated_at or int(time.time())

        self.cursor.execute(
            """
        INSERT OR IGNORE INTO sessions (session_id, video_id, collection_id, created_at, updated_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
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
        """Get a session by session_id.

        :param session_id: Unique session ID.
        :return: Session data as a dictionary.
        :rtype: dict
        """
        self.cursor.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        )
        row = self.cursor.fetchone()
        if row is not None:
            session = dict(row)  # Convert sqlite3.Row to dictionary
            session["metadata"] = json.loads(session["metadata"])
            return session

        else:
            return {}  # Return an empty dictionary if no data found

    def get_sessions(self) -> list:
        """Get all sessions.

        :return: List of all sessions.
        :rtype: list
        """
        self.cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
        row = self.cursor.fetchall()
        sessions = [dict(r) for r in row]
        for s in sessions:
            s["metadata"] = json.loads(s["metadata"])
        return sessions

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
        """Add a new message (input or output) to the conversation.

        :param str session_id: Unique session ID.
        :param str conv_id: Unique conversation ID.
        :param str msg_id: Unique message ID.
        :param str msg_type: Type of message (input or output).
        :param list agents: List of agents involved in the conversation.
        :param list actions: List of actions taken by the agents.
        :param list content: List of message content.
        :param str status: Status of the message.
        :param int created_at: Timestamp when the message was created.
        :param int updated_at: Timestamp when the message was last updated.
        :param dict metadata: Additional metadata for the message.
        """
        created_at = created_at or int(time.time())
        updated_at = updated_at or int(time.time())

        self.cursor.execute(
            """
        INSERT OR REPLACE INTO conversations (session_id, conv_id, msg_id, msg_type, agents, actions, content, status, created_at, updated_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            "SELECT * FROM conversations WHERE session_id = ?", (session_id,)
        )
        rows = self.cursor.fetchall()
        conversations = []
        for row in rows:
            if row is not None:
                conv_dict = dict(row)
                conv_dict["agents"] = json.loads(conv_dict["agents"])
                conv_dict["actions"] = json.loads(conv_dict["actions"])
                conv_dict["content"] = json.loads(conv_dict["content"])
                conv_dict["metadata"] = json.loads(conv_dict["metadata"])
                conversations.append(conv_dict)
        return conversations

    def get_context_messages(self, session_id: str) -> list:
        """Get context messages for a session.

        :param str session_id: Unique session ID.
        :return: List of context messages.
        :rtype: list
        """
        self.cursor.execute(
            "SELECT context_data FROM context_messages WHERE session_id = ?",
            (session_id,),
        )
        result = self.cursor.fetchone()
        return json.loads(result[0]) if result else {}

    def add_or_update_context_msg(
        self,
        session_id: str,
        context_messages: list,
        created_at: int = None,
        updated_at: int = None,
        metadata: dict = {},
        **kwargs,
    ) -> None:
        """Update context messages for a session.

        :param str session_id: Unique session ID.
        :param List context_messages: List of context messages.
        :param int created_at: Timestamp when the context messages were created.
        :param int updated_at: Timestamp when the context messages were last updated.
        :param dict metadata: Additional metadata for the context messages.
        """
        created_at = created_at or int(time.time())
        updated_at = updated_at or int(time.time())

        self.cursor.execute(
            """
        INSERT OR REPLACE INTO context_messages (context_data, session_id, created_at, updated_at, metadata)
        VALUES (?, ?, ?, ?, ?)
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
        """Delete all conversations for a given session.

        :param str session_id: Unique session ID.
        :return: True if conversations were deleted, False otherwise.
        """
        self.cursor.execute(
            "DELETE FROM conversations WHERE session_id = ?", (session_id,)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_context(self, session_id: str) -> bool:
        """Delete context messages for a given session.

        :param str session_id: Unique session ID.
        :return: True if context messages were deleted, False otherwise.
        """
        self.cursor.execute(
            "DELETE FROM context_messages WHERE session_id = ?", (session_id,)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its associated data.

        :param str session_id: Unique session ID.
        :return: True if the session was deleted, False otherwise.
        """
        failed_components = []
        if not self.delete_conversation(session_id):
            failed_components.append("conversation")
        if not self.delete_context(session_id):
            failed_components.append("context")
        self.cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        self.conn.commit()
        if not self.cursor.rowcount > 0:
            failed_components.append("session")
        success = len(failed_components) < 3
        return success, failed_components

    def health_check(self) -> bool:
        """Check if the SQLite database is healthy and the necessary tables exist. If not, create them."""
        try:
            query = """
                SELECT COUNT(name)
                FROM sqlite_master
                WHERE type='table'
                AND name IN ('sessions', 'conversations', 'context_messages');
            """
            self.cursor.execute(query)
            table_count = self.cursor.fetchone()[0]
            if table_count < 3:
                logger.info("Tables not found. Initializing SQLite DB...")
                initialize_sqlite(self.db_path)
            return True

        except Exception as e:
            logger.exception(f"SQLite health check failed: {e}")
            return False

    def __del__(self):
        self.conn.close()
