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
    def get_message(self, msg_id: str) -> dict:
        """Get one conversation message by msg_id, or None."""
        pass

    @abstractmethod
    def get_awaiting_output(self, session_id: str) -> dict:
        """The session's output message that is waiting for approvals, or None."""
        pass

    @abstractmethod
    def claim_resume(self, msg_id: str) -> bool:
        """Move a message from awaiting_approval to progress. True only for the one caller that did it."""
        pass

    @abstractmethod
    def update_session_metadata(self, session_id: str, patch: dict) -> None:
        """Merge top-level keys into the session's metadata."""
        pass

    @abstractmethod
    def create_approval(self, **approval) -> None:
        """Save a pending approval for a tool call."""
        pass

    @abstractmethod
    def resolve_approval(
        self, approval_id: str, session_id: str, status: str, decision: str, note: str = None
    ) -> dict:
        """Answer a pending approval. Returns the row only to the first caller; None if it wasn't pending."""
        pass

    @abstractmethod
    def set_approval_result(self, approval_id: str, result: str, status: str) -> None:
        """Store the tool output, or the denial, that goes back to the model."""
        pass

    @abstractmethod
    def skip_pending(self, msg_id: str, skipped_result: str, interrupted_result: str) -> None:
        """Close a message's open approvals: pending ones become skipped, unfinished running ones interrupted."""
        pass

    @abstractmethod
    def get_approvals(self, msg_id: str, statuses: tuple = None) -> list:
        """A message's approvals in creation order, optionally filtered by status."""
        pass

    @abstractmethod
    def add_permission_rule(self, **rule) -> None:
        """Save an "Always allow" rule: rule_id, agent, pattern, action, approval_id, created_at. A duplicate is ignored."""
        pass

    @abstractmethod
    def get_permission_rules(self, action: str = None) -> list:
        """All rules, oldest first, optionally only one action."""
        pass

    @abstractmethod
    def delete_permission_rule(self, rule_id: str) -> bool:
        """Remove a rule. True if it existed."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the database is healthy."""
        pass
