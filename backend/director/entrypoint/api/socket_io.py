import os
import logging

from flask import current_app as app
from flask_socketio import Namespace

from director.db import load_db
from director.handler import ChatHandler, _active_engines

logger = logging.getLogger(__name__)


class ChatNamespace(Namespace):
    """Chat namespace for socket.io"""

    def on_chat(self, message):
        """Handle chat messages"""
        chat_handler = ChatHandler(
            db=load_db(os.getenv("SERVER_DB_TYPE", app.config["DB_TYPE"]))
        )
        chat_handler.chat(message)

    def on_stop_generation(self, message):
        """Stop an in-progress generation for the given session_id.

        Note: Director is designed for single-user local deployments; there is
        no multi-user authentication layer. Any connected client can request a
        stop for any session_id. If you deploy Director in a shared environment,
        add session-ownership verification here before calling engine.stop().
        """
        session_id = message.get("session_id")
        if not session_id:
            logger.warning("stop_generation received without session_id")
            return
        engine = _active_engines.get(session_id)
        if engine:
            logger.info(f"Stopping generation for session {session_id}")
            engine.stop()
        else:
            logger.info(f"No active generation found for session {session_id}")
