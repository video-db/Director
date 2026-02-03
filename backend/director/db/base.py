from abc import ABC, abstractmethod


class BaseDB(ABC):
    """Interface for all databases. It provides a common interface for all databases to follow."""

    @abstractmethod
    def create_session(
        self, session_id: str, video_id: str = None, collection_id: str = None
    ) -> None:
        """Create a new session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> dict:
        """Get a session by session_id."""
        pass

    @abstractmethod
    def get_sessions(self) -> list:
        """Get all sessions."""
        pass

    @abstractmethod
    def add_or_update_msg_to_conv() -> None:
        """Add a new message (input or output) to the conversation."""
        pass

    @abstractmethod
    def get_conversations(self, session_id: str) -> list:
        """Get all conversations for a given session."""
        pass

    @abstractmethod
    def get_context_messages(self, session_id: str) -> list:
        """Get context messages for a session."""
        pass

    @abstractmethod
    def add_or_update_context_msg(
        self, session_id: str, context_messages: list
    ) -> None:
        """Update context messages for a session."""
        pass

    @abstractmethod
    def update_session(self, session_id: str, **kwargs) -> bool:
        """Update a session in the database."""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> tuple[bool, list]:
        """Delete a session from the database.
        :return: (success, failed_components)
        """
        pass

    @abstractmethod
    def make_session_public(self, session_id: str, is_public: bool) -> bool:
        """Make a session public or private."""
        pass

    @abstractmethod
    def get_public_session(self, session_id: str) -> dict:
        """Get a public session by session_id."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the database is healthy."""
        pass
