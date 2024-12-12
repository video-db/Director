import logging
import os
import uuid

from typing import Optional

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, VideoContent, VideoData, MsgStatus
from director.tools.videodb_tool import VideoDBTool
from director.tools.stabilityai import (
    StabilityAITool,
    PARAMS_CONFIG as STABILITYAI_PARAMS_CONFIG,
)
from director.tools.kling import KlingAITool, PARAMS_CONFIG as KLING_PARAMS_CONFIG
from director.tools.fal_video import (
    FalVideoGenerationTool,
    PARAMS_CONFIG as FAL_VIDEO_GEN_PARAMS_CONFIG,
)
from director.constants import DOWNLOADS_PATH

logger = logging.getLogger(__name__)

SUPPORTED_ENGINES = ["stabilityai", "kling", "fal"]

VIDEO_GENERATION_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "Collection ID to store the video",
        },
        "engine": {
            "type": "string",
            "description": "The video generation engine to use",
            "default": "fal",
            "enum": ["stabilityai", "kling", "fal"],
        },
        "job_type": {
            "type": "string",
            "enum": ["text_to_video"],
            "description": """
            The type of video generation to perform
            Possible values:
                - text_to_video: generates a video from a text prompt
            """,
        },
        "text_to_video": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The text prompt to generate the video",
                },
                "name": {
                    "type": "string",
                    "description": "The name of the video, Keep the name short and descriptive, it should convey the neccessary information about the config",
                },
                "duration": {
                    "type": "number",
                    "description": "The duration of the video in seconds",
                    "default": 5,
                },
                "stabilityai_config": {
                    "type": "object",
                    "properties": STABILITYAI_PARAMS_CONFIG["text_to_video"],
                    "description": "Config to use when stabilityai engine is used",
                },
                "kling_config": {
                    "type": "object",
                    "properties": KLING_PARAMS_CONFIG["text_to_video"],
                    "description": "Config to use when kling engine is used",
                },
                "fal_config": {
                    "type": "object",
                    "properties": FAL_VIDEO_GEN_PARAMS_CONFIG["text_to_video"],
                    "description": "Config to use when fal engine is used",
                },
            },
            "required": ["prompt", "name"],
        },
    },
    "required": ["job_type", "collection_id", "engine"],
}


class VideoGenerationAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "video_generation"
        self.description = "Agent designed to generate videos from text prompts"
        self.parameters = VIDEO_GENERATION_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        job_type: str,
        engine: str,
        text_to_video: Optional[dict] = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Generates video using Stability AI's API based on input text prompt.
        :param collection_id: The collection ID to store the generated video
        :param job_type: The type of video generation job to perform
        :param engine: The engine to use for video generation
        :param text_to_video: The text to convert to video
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: Response containing the generated video ID
        """
        try:
            self.videodb_tool = VideoDBTool(collection_id=collection_id)
            stealth_mode = kwargs.get("stealth_mode", False)

            if engine not in SUPPORTED_ENGINES:
                raise Exception(f"{engine} not supported")

            if engine == "stabilityai":
                STABILITYAI_API_KEY = os.getenv("STABILITYAI_API_KEY")
                if not STABILITYAI_API_KEY:
                    raise Exception("Stability AI API key not found")
                video_gen_tool = StabilityAITool(api_key=STABILITYAI_API_KEY)
                config_key = "stabilityai_config"
            elif engine == "kling":
                KLING_AI_ACCESS_API_KEY = os.getenv("KLING_AI_ACCESS_API_KEY")
                KLING_AI_SECRET_API_KEY = os.getenv("KLING_AI_SECRET_API_KEY")
                if not KLING_AI_ACCESS_API_KEY or not KLING_AI_SECRET_API_KEY:
                    raise Exception("Kling AI API key not found")
                video_gen_tool = KlingAITool(
                    access_key=KLING_AI_ACCESS_API_KEY,
                    secret_key=KLING_AI_SECRET_API_KEY,
                )
                config_key = "kling_config"
            elif engine == "fal":
                FAL_KEY = os.getenv("FAL_KEY")
                if not FAL_KEY:
                    raise Exception("FAL API key not found")
                video_gen_tool = FalVideoGenerationTool(api_key=FAL_KEY)
                config_key = "fal_config"
            else:
                raise Exception(f"{engine} not supported")

            os.makedirs(DOWNLOADS_PATH, exist_ok=True)
            output_file_name = f"video_{job_type}_{str(uuid.uuid4())}.mp4"
            output_path = f"{DOWNLOADS_PATH}/{output_file_name}"

            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Processing...",
            )
            if not stealth_mode:
                self.output_message.content.append(video_content)

            if job_type == "text_to_video":
                prompt = text_to_video.get("prompt")
                video_name = text_to_video.get("name")
                duration = text_to_video.get("duration", 5)
                config = text_to_video.get(config_key, {})
                if prompt is None:
                    raise Exception("Prompt is required for video generation")
                self.output_message.actions.append(
                    f"Generating video using <b>{engine}</b> for prompt <i>{prompt}</i>"
                )
                self.output_message.push_update()
                video_gen_tool.text_to_video(
                    prompt=prompt,
                    save_at=output_path,
                    duration=duration,
                    config=config,
                )
            else:
                raise Exception(f"{job_type} not supported")

            self.output_message.actions.append(
                f"Generated video saved at <i>{output_path}</i>"
            )
            self.output_message.push_update()

            # Upload to VideoDB
            media = self.videodb_tool.upload(
                output_path,
                source_type="file_path",
                media_type="video",
                name=video_name,
            )
            self.output_message.actions.append(
                f"Uploaded generated video to VideoDB with Video ID {media['id']}"
            )
            stream_url = media["stream_url"]
            video_content.video = VideoData(stream_url=stream_url)
            video_content.status = MsgStatus.success
            video_content.status_message = "Here is your generated video"
            self.output_message.push_update()
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            video_content.status = MsgStatus.error
            video_content.status_message = "Failed to generate video"
            self.output_message.push_update()
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Generated video ID {media['id']}",
            data={"video_id": media["id"], "video_stream_url": stream_url},
        )
