import json
from typing import List

from director.core.prompts import REASONING_SYSTEM_PROMPT
from director.core.session import ContextMessage, InputMessage, RoleTypes, Session
from director.core.skills import format_skills_for_prompt, get_skills_dir, load_skills


class ContextBuilder:
    """Prepares the reasoning context for a turn.

    The system message is rebuilt every turn, so skills added or updated in the
    skills folder show up on the next message.
    """

    def __init__(self, system_prompt: str = REASONING_SYSTEM_PROMPT):
        self.system_prompt = system_prompt

    def build(
        self, session: Session, input_message: InputMessage
    ) -> List[ContextMessage]:
        system = ContextMessage(
            content=self._system_prompt(session), role=RoleTypes.system
        )
        ctx = session.reasoning_context
        if ctx and ctx[0].role == RoleTypes.system:
            ctx[0] = system
        else:
            ctx.insert(0, system)
        ctx.append(ContextMessage(content=input_message.content, role=RoleTypes.user))
        return ctx

    def _system_prompt(self, session: Session) -> str:
        return (
            self.system_prompt
            + self._scope(session)
            + self._skills(getattr(session, "sandbox", None))
        )

    def _scope(self, session: Session) -> str:
        """Which collection, and video if any, this chat is about. The media itself is queried with code."""
        collection = session.state["collection"]
        scope = f"\n\nThis chat is in the collection titled {collection.name} (collection_id: {collection.id}). Collection description: {collection.description}"
        if session.video_id:
            video = session.state["video"]
            scope += f"\nThe user opened this video: title: {video.name}, video_id: {video.id}, description: {video.description}, length: {video.length}"
        return scope

    def _skills(self, sandbox) -> str:
        # Skills are read and run through the executors, so without a sandbox there is nothing to offer.
        if sandbox is None:
            return ""
        skills_dir = get_skills_dir()
        return format_skills_for_prompt(load_skills(skills_dir), skills_dir, sandbox)


class ContextPolicy:
    """Trims what is sent to the LLM. The saved context stays complete."""

    def __init__(self, max_chars: int = 200_000):
        self.max_chars = max_chars

    def apply(self, ctx: List[ContextMessage]) -> List[dict]:
        messages = [message.to_llm_msg() for message in ctx]
        head = messages[:1] if messages and messages[0]["role"] == "system" else []

        # Turns start at user messages, so tool_call/tool pairs never split.
        turns = []
        for message in messages[len(head) :]:
            if message["role"] == RoleTypes.user or not turns:
                turns.append([])
            turns[-1].append(message)

        size = sum(_size(message) for message in messages)
        while len(turns) > 1 and size > self.max_chars:
            size -= sum(_size(message) for message in turns.pop(0))

        return head + [message for turn in turns for message in turn]


def _size(message: dict) -> int:
    return len(json.dumps(message, default=str))
