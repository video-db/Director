import logging
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    VideoContent,
    VideoData,
    MsgStatus,
)
from director.tools.videodb_tool import VideoDBTool

from videodb.asset import VideoAsset, AudioAsset

logger = logging.getLogger(__name__)

EDITING_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "The ID of the collection to process.",
        },
        "videos": {
            "type": "array",
            "description": "List of videos to edit",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The unique identifier of the video",
                    },
                    "start": {
                        "type": "number",
                        "description": "Start time in seconds, pass non-zero if the video needs to be trimmed",
                        "default": 0,
                    },
                    "end": {
                        "type": ["number", "null"],
                        "description": "End time in seconds, pass non-null if the video needs to be trimmed",
                        "default": None,
                    },
                },
                "required": ["id"],
            },
        },
        "audios": {
            "type": "array",
            "description": "List of audio files to add",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The unique identifier of the audio",
                    },
                    "start": {
                        "type": "number",
                        "description": "Start time (the start time in the original audio file) in seconds, pass non-zero if the audio needs to be trimmed",
                        "default": 0,
                    },
                    "end": {
                        "type": ["number", "null"],
                        "description": "End time (the end time in the original audio file) in seconds, pass non-null if the audio needs to be trimmed",
                        "default": None,
                    },
                },
                "required": ["id"],
            },
        },
    },
    "required": ["videos"],
}


class EditingAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "editing"
        self.description = "An agent designed to edit and combine videos and audio files within VideoDB."
        self.parameters = EDITING_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def add_media_to_timeline(self, timeline, media_list, media_type):
        """Helper method to add media assets to timeline"""
        seeker = 0
        for media in media_list:
            start = media.get("start", 0)
            end = media.get("end", None)

            if media_type == "video":
                asset = VideoAsset(asset_id=media["id"], start=start, end=end)
                timeline.add_inline(asset)

            elif media_type == "audio":
                audio = self.videodb_tool.get_audio(media["id"])
                asset = AudioAsset(
                    asset_id=media["id"],
                    start=start,
                    end=end,
                )
                timeline.add_overlay(seeker, asset)
                seeker += float(audio["length"])
            else:
                raise ValueError(f"Invalid media type: {media_type}")

    def run(
        self,
        collection_id: str,
        videos: list,
        audios: list = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Edits and combines the specified videos and audio files.

        :param list videos: List of video objects with id, start and end times
        :param list audios: Optional list of audio objects with id, start and end times
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: The response indicating the success or failure of the editing operation
        :rtype: AgentResponse
        """
        try:
            # Initialize first video's collection
            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            self.output_message.actions.append("Starting video editing process")
            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Processing...",
            )
            self.output_message.content.append(video_content)
            self.output_message.push_update()

            timeline = self.videodb_tool.get_and_set_timeline()

            # Add videos to timeline
            self.add_media_to_timeline(timeline, videos, "video")

            # Add audio files if provided
            if audios:
                self.add_media_to_timeline(timeline, audios, "audio")

            self.output_message.actions.append("Generating final video stream")
            self.output_message.push_update()

            stream_url = timeline.generate_stream()

            video_content.video = VideoData(stream_url=stream_url)
            video_content.status = MsgStatus.success
            video_content.status_message = (
                "Here is your stream."
            )
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            video_content.status = MsgStatus.error
            video_content.status_message = "An error occurred while editing the video."
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Video editing completed successfully",
            data={"stream_url": stream_url},
        )
