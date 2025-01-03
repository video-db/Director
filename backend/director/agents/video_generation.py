import logging
import os
import uuid
import asyncio

from typing import Optional

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, VideoContent, VideoData, MsgStatus
from director.tools.videodb_tool import VideoDBTool
from director.tools.stabilityai import (
    StabilityAITool,
    PARAMS_CONFIG as STABILITYAI_PARAMS_CONFIG,
)
from director.tools.fal_video import (
    FalVideoGenerationTool,
    PARAMS_CONFIG as FAL_VIDEO_GEN_PARAMS_CONFIG,
)
from director.constants import DOWNLOADS_PATH

logger = logging.getLogger(__name__)

SUPPORTED_ENGINES = ["stabilityai", "fal"]

VIDEO_GENERATION_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "Collection ID to store the video",
        },
        "engine": {
            "type": "string",
            "description": "The video generation engine to use. Use Fal by default. If the query includes any of the following: 'minimax-video, mochi-v1, hunyuan-video, luma-dream-machine, cogvideox-5b, ltx-video, fast-svd, fast-svd-lcm, t2v-turbo, kling video v 1.0, kling video v1.5 pro, fast-animatediff, fast-animatediff turbo, and animatediff-sparsectrl-lcm'- always use Fal. In case user specifies any other engine, use the supported engines like Stability.",
            "default": "fal",
            "enum": ["fal", "stabilityai"],
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
                    "description": "Description of the video generation run in two lines. Keep the engine name and parameter configuration of the engine in separate lines. Keep it short, but show the prompt in full. Here's an example: [Tokyo Sunset - Luma - Prompt: 'An aerial shot of a quiet sunset at Tokyo', Duration: 5s, Luma Dream Machine]",
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
        self.description = "Creates videos using ONE specific model/engine. Only use this agent when the request mentions exactly ONE model/engine, without any comparison words like 'compare', 'test', 'versus', 'vs' and no connecting words (and/&/,) between model names. If the request mentions wanting to compare models or try multiple engines, do not use this agent - use the comparison agent instead."
        self.parameters = VIDEO_GENERATION_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    async def run_async(
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

            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Processing...",
            )
            if not stealth_mode:
                self.output_message.content.append(video_content)

            if engine == "stabilityai":
                STABILITYAI_API_KEY = os.getenv("STABILITYAI_API_KEY")
                if not STABILITYAI_API_KEY:
                    raise Exception("Stability AI API key not found")
                video_gen_tool = StabilityAITool(api_key=STABILITYAI_API_KEY)
                config_key = "stabilityai_config"
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
                await video_gen_tool.text_to_video_async(
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
            id = media["id"]
            collection_id = media["collection_id"]
            name = media["name"]
            video_content.video = VideoData(
                stream_url=stream_url,
                id=id,
                collection_id=collection_id,
                name=name,
            )
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
            data={
                "video_id": media["id"],
                "video_stream_url": stream_url,
                "video_content": video_content,
            },
        )

    def run(self, *args, **kwargs):
        return asyncio.run(self.run_async(*args, **kwargs))
