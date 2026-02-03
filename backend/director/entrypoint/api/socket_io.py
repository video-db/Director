import os

from flask import current_app as app
from flask_socketio import Namespace, join_room, emit
from director.db import load_db
from director.handler import ChatHandler

class ChatNamespace(Namespace):
    """Chat namespace for socket.io with session-based rooms"""
    
    def on_connect(self):
        """Handle client connection"""
        print(f"Client connected to chat namespace")
    
    def on_chat(self, message):
        """Handle chat messages and auto-join session room"""
        session_id = message.get('session_id')
        if not session_id:
            emit('error', {'message': 'session_id is required'})
            return
            
        join_room(session_id)
        print(f"Client joined session room {session_id}")
        
        chat_handler = ChatHandler(
            db=load_db(os.getenv("SERVER_DB_TYPE", app.config["DB_TYPE"]))
        )
        chat_handler.chat(message)
    
    def on_join_session(self, data):
        """Explicitly join a session room (for reconnection)"""
        session_id = data.get('session_id')
        if session_id:
            join_room(session_id)
            emit('session_joined', {'session_id': session_id})
            print(f"Client explicitly joined session room {session_id}")
    
    def on_disconnect(self):
        """Handle client disconnection"""
        print(f"Client disconnected from chat namespace")
