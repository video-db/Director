from abc import ABC, abstractmethod


class BaseSink(ABC):
    """Interface for where the engine and agents publish UI updates."""

    @abstractmethod
    def send(self, channel: str, payload: dict) -> None:
        """Send a payload on a channel ("chat" or "event")."""
        pass


class NullSink(BaseSink):
    """Drops every update. Default when no client is listening."""

    def send(self, channel: str, payload: dict) -> None:
        pass


class CollectingSink(BaseSink):
    """Keeps updates in memory, for tests and CLI runs."""

    def __init__(self):
        self.events = []

    def send(self, channel: str, payload: dict) -> None:
        self.events.append((channel, payload))
