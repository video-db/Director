import json
from typing import List

from director.core.prompts import REASONING_SYSTEM_PROMPT
from director.core.session import ContextMessage, InputMessage, RoleTypes, Session


class ContextBuilder:
    """Prepares the reasoning context for a turn. The system message is rebuilt every turn so the collection listing stays current."""

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
        collection = session.state["collection"]
        if session.video_id:
            video = session.state["video"]
            return (
                self.system_prompt
                + f"""\nThis is a video in the collection titled {collection.name} collection_id is {collection.id} \nHere is the video refer to this for search, summary and editing \n- title: {video.name}, video_id: {video.id}, media_description: {video.description}, length: {video.length}"""
            )

        video_titles = "\n".join(
            f"\n- title: {video.name}, video_id: {video.id}, media_description: {video.description}, length: {video.length}, video_stream: {video.stream_url}"
            for video in collection.get_videos()
        )
        image_titles = "\n".join(
            f"\n- title: {image.name}, image_id: {image.id}, url: {image.url}"
            for image in collection.get_images()
        )
        return (
            self.system_prompt
            + f"""\nThis is a collection of videos and the collection description is {collection.description} and collection_id is {collection.id} \n\nHere are the videos in this collection user may refer to them for search, summary and editing {video_titles}\n\nHere are the images in this collection {image_titles}"""
        )


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
