import logging

from flask_socketio import emit

from director.core.sink import BaseSink

logger = logging.getLogger(__name__)


class SocketIOSink(BaseSink):
    """Publishes updates to the Socket.IO client of the current request."""

    def __init__(self, namespace: str = "/chat"):
        self.namespace = namespace

    def send(self, channel: str, payload: dict) -> None:
        try:
            emit(channel, payload, namespace=self.namespace)
        except Exception:
            logger.exception(f"Failed to emit {channel}")
