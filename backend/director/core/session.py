import json

from enum import Enum
from datetime import datetime
from typing import Optional, List, Union

from flask_socketio import emit
from pydantic import BaseModel, Field, ConfigDict

from director.db.base import BaseDB


class RoleTypes(str, Enum):
    """Role types for the context message."""

    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class MsgStatus(str, Enum):
    """Message status for the message, for loading state."""

    progress = "progress"
    success = "success"
    error = "error"
    not_generated = "not_generated"
    overlimit = "overlimit"
    sessionlimit = "sessionlimit"


class MsgType(str, Enum):
    """Message type for the message. input is for the user input and output is for the director output."""

    input = "input"
    output = "output"


class ContentType(str, Enum):
    """Content type for the content in the input/output message."""

    text = "text"
    video = "video"
    videos = "videos"
    image = "image"
    search_results = "search_results"


class EventType(str, Enum):
    """Event types for WebSocket event emission."""

    update_data = "update_data"


class BaseEvent(BaseModel):
    """Base event class for the WebSocket event."""

    event_type: EventType


class CollectionsUpdateEvent(BaseEvent):
    """Collections update event class for the WebSocket event."""

    event_type: EventType = EventType.update_data
    update: str = "collections"


class VideosUpdateEvent(BaseEvent):
    """Videos update event class for the WebSocket event."""

    event_type: EventType = EventType.update_data
    update: str = "videos"
    collection_id: str


class BaseContent(BaseModel):
    """Base content class for the content in the message."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        validate_default=True,
    )

    type: ContentType
    status: MsgStatus = MsgStatus.progress
    status_message: Optional[str] = None
    agent_name: Optional[str] = None


class TextContent(BaseContent):
    """Text content model class for text content."""

    text: str = ""
    type: ContentType = ContentType.text


class VideoData(BaseModel):
    """Video data model class for video content."""

    stream_url: Optional[str] = None
    external_url: Optional[str] = None
    player_url: Optional[str] = None
    id: Optional[str] = None
    collection_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    length: Optional[Union[int, float]] = None
    error: Optional[str] = None


class VideoContent(BaseContent):
    """Video content model class for video content."""

    video: Optional[VideoData] = None
    type: ContentType = ContentType.video


class VideosContentUIConfig(BaseModel):
    columns: Optional[int] = 4


class VideosContent(BaseContent):
    """Videos content model class for videos content."""

    videos: Optional[List[VideoData]] = None
    ui_config: VideosContentUIConfig = VideosContentUIConfig()
    type: ContentType = ContentType.videos


class ImageData(BaseModel):
    """Image data model class for image content."""

    url: str
    name: Optional[str] = None
    description: Optional[str] = None
    id: Optional[str] = None
    collection_id: Optional[str] = None


class ImageContent(BaseContent):
    """Image content model class for image content."""

    image: Optional[ImageData] = None
    type: ContentType = ContentType.image


class ShotData(BaseModel):
    """Shot data model class for search results content."""

    search_score: Union[int, float]
    start: Union[int, float]
    end: Union[int, float]
    text: str


class SearchData(BaseModel):
    """Search data model class for search results content."""

    video_id: str
    video_title: Optional[str] = None
    stream_url: str
    duration: Union[int, float]
    shots: List[ShotData]


class SearchResultsContent(BaseContent):
    search_results: Optional[List[SearchData]] = None
    type: ContentType = ContentType.search_results


class BaseMessage(BaseModel):
    """Base message class for the input/output message. All the input/output messages will be inherited from this class."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        validate_default=True,
    )

    session_id: str
    conv_id: str
    msg_type: MsgType
    actions: List[str] = []
    agents: List[str] = []
    content: List[
        Union[
            dict,
            TextContent,
            ImageContent,
            VideoContent,
            VideosContent,
            SearchResultsContent,
        ]
    ] = []
    status: MsgStatus = MsgStatus.success
    msg_id: str = Field(
        default_factory=lambda: str(datetime.now().timestamp() * 100000)
    )


class InputMessage(BaseMessage):
    """Input message from the user. This class is used to create the input message from the user."""

    db: BaseDB
    msg_type: MsgType = MsgType.input

    def publish(self):
        """Store the message in the database. for conversation history."""
        self.db.add_or_update_msg_to_conv(**self.model_dump(exclude={"db"}))


class OutputMessage(BaseMessage):
    """Output message from the director. This class is used to create the output message from the director."""

    db: BaseDB = Field(exclude=True)
    msg_type: MsgType = MsgType.output
    status: MsgStatus = MsgStatus.progress

    def update_status(self, status: MsgStatus):
        """Update the status of the message and publish the message to the socket. for loading state."""
        self.status = status
        self._publish()

    def push_update(self):
        """Publish the message to the socket."""
        try:
            self._publish()
        except Exception as e:
            print(f"Error in emitting message: {str(e)}")

    def publish(self):
        """Store the message in the database. for conversation history and publish the message to the socket."""
        self._publish()

    def _publish(self):
        try:
            emit("chat", self.model_dump(), namespace="/chat")
        except Exception as e:
            print(f"Error in emitting message: {str(e)}")
        self.db.add_or_update_msg_to_conv(**self.model_dump())


def format_user_message(message: dict) -> dict:
    message_content = message.get("content")
    if isinstance(message_content, str):
        return message
    else:
        content_parts = message["content"]
        sanitized_content_parts = []

        for content_part in content_parts:
            sanitized_part = content_part
            if content_part["type"] == "image":
                sanitized_part = {
                    "type": "text",
                    "text": f"User has upload image with following details : {json.dumps(content_part)}",
                }
            sanitized_content_parts.append(sanitized_part)

        message["content"] = sanitized_content_parts
        return message


class ContextMessage(BaseModel):
    """Context message class. This class is used to create the context message for the reasoning context."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=True,
        use_enum_values=True,
    )

    content: Optional[Union[List[dict], str]] = None
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None
    role: RoleTypes = RoleTypes.system

    def to_llm_msg(self):
        """Convert the context message to the llm message."""
        msg = {
            "role": self.role,
            "content": self.content,
        }
        if self.role == RoleTypes.system:
            return msg

        if self.role == RoleTypes.user:
            return format_user_message(msg)

        if self.role == RoleTypes.assistant:
            if self.tool_calls:
                msg["tool_calls"] = self.tool_calls
            if not self.content:
                msg["content"] = []
            return msg

        if self.role == RoleTypes.tool:
            msg["tool_call_id"] = self.tool_call_id
            return msg

    @classmethod
    def from_json(cls, json_data):
        """Create the context message from the json data."""
        return cls(**json_data)


class Session:
    """A class to manage and interact with a session in the database. The session is used to store the conversation and reasoning context messages."""

    def __init__(
        self,
        db: BaseDB,
        session_id: str = "",
        conv_id: str = "",
        collection_id: str = None,
        video_id: str = None,
        **kwargs,
    ):
        self.db = db
        self.session_id = session_id
        self.conv_id = conv_id
        self.conversations = []
        self.video_id = video_id
        self.collection_id = collection_id
        self.reasoning_context = []
        self.state = {}
        self.output_message = OutputMessage(
            db=self.db, session_id=self.session_id, conv_id=self.conv_id
        )

        self.get_context_messages()

    def save_context_messages(self):
        """Save the reasoning context messages to the database."""
        context = {
            "reasoning": [message.to_llm_msg() for message in self.reasoning_context],
        }
        self.db.add_or_update_context_msg(self.session_id, context)

    def get_context_messages(self):
        """Get the reasoning context messages from the database."""
        if not self.reasoning_context:
            context = self.db.get_context_messages(self.session_id)
            self.reasoning_context = [
                ContextMessage.from_json(message)
                for message in context.get("reasoning", [])
            ]

        return self.reasoning_context

    def create(self):
        """Create a new session in the database."""
        self.db.create_session(**self.__dict__)

    def new_message(
        self, msg_type: MsgType = MsgType.output, **kwargs
    ) -> Union[InputMessage, OutputMessage]:
        """Returns a new input/output message object.

        :param MsgType msg_type: The type of the message, input or output.
        :param dict kwargs: The message attributes.
        :return: The input/output message object.
        """
        if msg_type == MsgType.input:
            return InputMessage(
                db=self.db,
                session_id=self.session_id,
                conv_id=self.conv_id,
                **kwargs,
            )
        return OutputMessage(
            db=self.db,
            session_id=self.session_id,
            conv_id=self.conv_id,
            **kwargs,
        )

    def get(self):
        """Get the session from the database."""
        session = self.db.get_session(self.session_id)
        conversation = self.db.get_conversations(self.session_id)
        session["conversation"] = conversation
        return session

    def get_all(self):
        """Get all the sessions from the database."""
        return self.db.get_sessions()

    def delete(self):
        """Delete the session from the database."""
        return self.db.delete_session(self.session_id)

    def emit_event(self, event: BaseEvent, namespace="/chat"):
        """Emits a structured WebSocket event to notify all clients about updates."""

        event_payload = event.model_dump()

        try:
            emit("event", event_payload, namespace=namespace)
        except Exception:
            pass
