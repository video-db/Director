import logging
import os
import uuid

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, VideoContent, VideoData, MsgStatus
from director.tools.videodb_tool import VideoDBTool
from director.tools.stabilityai import StabilityAITool
from director.tools.kling import KlingAITool

from director.constants import DOWNLOADS_PATH

logger = logging.getLogger(__name__)

SUPPORTED_ENGINES = ["stabilityai", "kling"]

VIDEO_GENERATION_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "The unique identifier of the collection to store the video",
        },
        "engine": {
            "type": "string",
            "description": "The video generation engine to use",
            "enum": ["stabilityai", "kling"],
        },
        "job_type": {
            "type": "string",
            "enum": ["text_to_video"],
            "description": "The type of video generation to perform",
        },
        "text_to_video": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The text prompt to generate the video",
                },
                "duration": {
                    "type": "number",
                    "description": "The duration of the video in seconds",
                    "default": 5,
                },
                "config": {
                    "type": "object",
                    "description": "Additional configuration options for video generation",
                    "default": {},
                },
            },
            "required": ["prompt"],
        },
    },
    "required": ["job_type", "collection_id", "engine"],
}


class VideoGenerationAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "video_generation"
        self.description = "An agent designed to generate videos from text prompts"
        self.parameters = VIDEO_GENERATION_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        job_type: str,
        engine: str,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Generates video using Stability AI's API based on input text prompt.
        :param str collection_id: The collection ID to store the generated video
        :param str job_type: The type of video generation job to perform
        :param str engine: The engine to use for video generation
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: Response containing the generated video ID
        :rtype: AgentResponse
        """
        try:
            self.videodb_tool = VideoDBTool(collection_id=collection_id)
            print("using engine", engine)

            if engine not in SUPPORTED_ENGINES:
                raise Exception(f"{engine} not supported")

            if engine == "stabilityai":
                STABILITYAI_API_KEY = os.getenv("STABILITYAI_API_KEY")
                if not STABILITYAI_API_KEY:
                    raise Exception(
                        "Stability AI API key not present in environment variables"
                    )
                video_gen_tool = StabilityAITool(api_key=STABILITYAI_API_KEY)
            elif engine == "kling":
                KING_AI_API_KEY = os.getenv("KING_AI_API_KEY")
                if not KING_AI_API_KEY:
                    raise Exception(
                        "Kling AI API key not present in environment variables"
                    )
                video_gen_tool = KlingAITool(api_key=KING_AI_API_KEY)

            os.makedirs(DOWNLOADS_PATH, exist_ok=True)
            output_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp4"

            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Processing...",
            )
            self.output_message.content.append(video_content)

            if job_type == "text_to_video":
                self.output_message.actions.append("Generating video from text prompt")
                self.output_message.push_update()
                args = kwargs.get("text_to_video", {})
                video_gen_tool.text_to_video(
                    prompt=args.get("prompt"),
                    save_at=output_path,
                    duration=args.get("duration", 5),
                    config=args.get("config", {}),
                )

            self.output_message.actions.append(
                f"Uploading generated video {output_path}"
            )
            self.output_message.push_update()
            media = self.videodb_tool.upload(
                output_path, source_type="file_path", media_type="video"
            )
            self.output_message.actions.append(
                f"Uploaded generated video with Video ID: {media['id']}"
            )

            stream_url = media["stream_url"]
            video_content.video = VideoData(stream_url=stream_url)
            video_content.status = MsgStatus.success
            video_content.status_message = (
                "Video editing completed successfully. Here is your stream."
            )
            self.output_message.push_update()
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Video generated successfully. Generated Media video ID: {media['id']} and Stream Url: {stream_url}",
            data={"video_id": media["id"], "video_stream_url": stream_url},
        )
