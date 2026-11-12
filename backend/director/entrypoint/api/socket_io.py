import os

from flask import current_app as app
from flask_socketio import Namespace

from director.db import load_db
from director.entrypoint.api.sink import SocketIOSink
from director.handler import ChatHandler


class ChatNamespace(Namespace):
    """Chat namespace for socket.io"""

    def on_chat(self, message):
        """Handle chat messages"""
        chat_handler = ChatHandler(
            db=load_db(os.getenv("SERVER_DB_TYPE", app.config["DB_TYPE"])),
            sink=SocketIOSink(),
        )
        chat_handler.chat(message)
