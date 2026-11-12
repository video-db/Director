import logging

from pydantic import ValidationError

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    ImageContent,
    ImageData,
    MsgStatus,
    SearchData,
    SearchResultsContent,
    ShotData,
    TextContent,
    VideoContent,
    VideoData,
    VideosContent,
)

logger = logging.getLogger(__name__)

OUTPUT_SHAPES = """Each item needs a "type" and that type's field. "status_message" is a short title shown above it.

- text:           {"type": "text", "status_message": "...", "text": "Markdown text"}
- video:          {"type": "video", "status_message": "...", "video": {"stream_url": "...", "id": "m-xxx", "name": "...", "length": 120.0, "thumbnail_url": "...", "collection_id": "c-xxx"}}
- videos:         {"type": "videos", "status_message": "...", "videos": [{"stream_url": "...", "id": "m-xxx", "name": "...", "length": 120.0, "thumbnail_url": "..."}]}
- image:          {"type": "image", "status_message": "...", "image": {"url": "...", "id": "img-xxx", "name": "...", "collection_id": "c-xxx"}}
- search_results: {"type": "search_results", "status_message": "...", "search_results": [{"video_id": "m-xxx", "video_title": "...", "stream_url": "...", "duration": 120.0, "shots": [{"start": 1.0, "end": 4.5, "text": "...", "search_score": 0.8}]}]}

Only `stream_url` (video), `url` (image) and the search_results fields other than `video_title` are required. Use `image.generate_url()` for image URLs."""

STREAM_CONTENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "output": {
            "type": "array",
            "description": OUTPUT_SHAPES,
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["text", "video", "videos", "image", "search_results"],
                    },
                    "status_message": {"type": "string"},
                    "text": {"type": "string"},
                    "video": {"type": "object"},
                    "videos": {"type": "array", "items": {"type": "object"}},
                    "image": {"type": "object"},
                    "search_results": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["type"],
            },
        },
    },
    "required": ["output"],
}


class StreamContentAgent(BaseAgent):
    """Shows videos, images, search results and text in the chat."""

    def __init__(self, session=None, **kwargs):
        self.agent_name = "stream_content"
        self.description = (
            "Shows videos, images, search results and formatted text to the user in the chat. "
            "code_executor and bash_executor only return text to you, so use this whenever "
            "the user should see or play a result."
        )
        self.parameters = STREAM_CONTENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(self, output: list, *args, **kwargs) -> AgentResponse:
        try:
            contents = [self._to_content(item) for item in output]
        except (ValidationError, KeyError, TypeError, ValueError) as e:
            # Nothing is shown; the model gets the error and can fix the payload.
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"Invalid output item: {e}",
            )

        self.output_message.content.extend(contents)
        self.output_message.push_update()
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Showed {len(contents)} item(s) to the user.",
        )

    def _to_content(self, item: dict):
        common = dict(
            status=MsgStatus.success,
            status_message=item.get("status_message"),
            agent_name=self.agent_name,
        )
        content_type = item.get("type")
        if content_type == "text":
            return TextContent(text=item.get("text", ""), **common)
        if content_type == "video":
            return VideoContent(video=_video(item["video"]), **common)
        if content_type == "videos":
            return VideosContent(videos=[_video(v) for v in item["videos"]], **common)
        if content_type == "image":
            return ImageContent(image=ImageData(**item["image"]), **common)
        if content_type == "search_results":
            return SearchResultsContent(
                search_results=[
                    SearchData(
                        **{**result, "shots": [ShotData(**s) for s in result["shots"]]}
                    )
                    for result in item["search_results"]
                ],
                **common,
            )
        raise ValueError(f"unknown type {content_type!r}")


def _video(raw: dict) -> VideoData:
    # VideoData allows a missing stream_url, but the player can't show one.
    if not raw.get("stream_url"):
        raise ValueError("every video needs a stream_url")
    return VideoData(**raw)
