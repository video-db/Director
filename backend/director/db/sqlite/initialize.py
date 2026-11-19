import sqlite3
import os

# SQL to create the sessions table
CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    video_id TEXT,
    collection_id TEXT,
    created_at INTEGER,
    updated_at INTEGER,
    metadata JSON
)
"""

# SQL to create the conversations table
CREATE_CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    session_id TEXT,
    conv_id TEXT,
    msg_id TEXT PRIMARY KEY,
    msg_type TEXT,
    agents JSON,
    actions JSON,
    content JSON,
    status TEXT,
    created_at INTEGER,
    updated_at INTEGER,
    metadata JSON,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
"""

# SQL to create the context_messages table
CREATE_CONTEXT_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS context_messages (
    session_id TEXT PRIMARY KEY,
    context_data JSON,
    created_at INTEGER,
    updated_at INTEGER,
    metadata JSON,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
"""


# Tool calls waiting for, or answered by, the user.
CREATE_APPROVALS_TABLE = """
CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    conv_id TEXT NOT NULL,
    msg_id TEXT NOT NULL,
    agent TEXT NOT NULL,
    arguments JSON NOT NULL,
    reason TEXT,
    status TEXT NOT NULL,
    decision TEXT,
    note TEXT,
    result TEXT,
    created_at INTEGER,
    resolved_at INTEGER
)
"""

CREATE_APPROVALS_INDEX = """
CREATE INDEX IF NOT EXISTS approvals_msg ON approvals (msg_id, status)
"""

# "Always allow" rules, shared by every chat. pattern is the call's normalized key.
CREATE_PERMISSION_RULES_TABLE = """
CREATE TABLE IF NOT EXISTS permission_rules (
    rule_id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    pattern TEXT NOT NULL,
    action TEXT NOT NULL,
    approval_id TEXT,
    created_at INTEGER,
    UNIQUE (agent, pattern, action)
)
"""


def initialize_sqlite(db_name="director.db"):
    """Initialize the SQLite database by creating the necessary tables."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute(CREATE_SESSIONS_TABLE)
    cursor.execute(CREATE_CONVERSATIONS_TABLE)
    cursor.execute(CREATE_CONTEXT_MESSAGES_TABLE)
    cursor.execute(CREATE_APPROVALS_TABLE)
    cursor.execute(CREATE_APPROVALS_INDEX)
    cursor.execute(CREATE_PERMISSION_RULES_TABLE)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    db_path = os.getenv("SQLITE_DB_PATH", "director.db")
    initialize_sqlite(db_path)
