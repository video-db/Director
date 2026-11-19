import os

from flask import current_app as app
from flask_socketio import Namespace

from director.db import load_db
from director.entrypoint.api.sink import SocketIOSink
from director.handler import ChatHandler


class ChatNamespace(Namespace):
    """Chat namespace for socket.io"""

    def _handler(self) -> ChatHandler:
        return ChatHandler(
            db=load_db(os.getenv("SERVER_DB_TYPE", app.config["DB_TYPE"])),
            sink=SocketIOSink(),
        )

    def on_chat(self, message):
        """Handle chat messages"""
        self._handler().chat(message)

    def on_approval(self, payload):
        """The user's answer to an approval card: {session_id, msg_id, approval_id, decision, note?}."""
        self._handler().approve(payload)
