import logging
import os
import json
import uuid
from typing import List, Optional
from dataclasses import dataclass

from videodb.asset import VideoAsset, AudioAsset
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    ContextMessage,
    MsgStatus,
    VideoContent,
    RoleTypes,
    VideoData,
)
from director.llm.openai import OpenAI, OpenaiConfig
from director.tools.kling import KlingAITool
from director.tools.stabilityai import StabilityAITool
from director.tools.elevenlabs import ElevenLabsTool
from director.tools.videodb_tool import VideoDBTool
from director.constants import DOWNLOADS_PATH


logger = logging.getLogger(__name__)

SUPPORTED_ENGINES = ["stabilityai", "kling"]

SCREENPLAY_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "Collection ID to store the video",
        },
        "engine": {
            "type": "string",
            "description": "The video generation engine to use",
            "enum": ["stabilityai", "kling"],
            "default": "stabilityai",
        },
        "job_type": {
            "type": "string",
            "enum": ["text_to_video"],
            "description": "The type of video generation to perform",
        },
        "text_to_video": {
            "type": "object",
            "properties": {
                "storyline": {
                    "type": "string",
                    "description": "The storyline to generate the video",
                },
                "user_music_description": {
                    "type": "string",
                    "description": "Optional description for background music generation",
                    "default": None,
                },
                "config": {
                    "type": "object",
                    "description": "Additional configuration options",
                    "properties": {
                        "aspect_ratio": {
                            "type": "string",
                            "enum": ["16:9", "9:16", "1:1"],
                            "description": "Aspect ratio of the output video",
                        },
                        "strength": {
                            "type": "number",
                            "description": "Image influence on output",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "output_format": {
                            "type": "string",
                            "description": "Format of the output video",
                            "enum": ["mp4", "webm"],
                        },
                    },
                    "default": {},
                },
            },
            "required": ["prompt"],
        },
    },
    "required": ["job_type", "collection_id", "engine"],
}


@dataclass
class VideoGenResult:
    """Track results of video generation"""

    step_index: int
    video_path: Optional[str]
    success: bool
    error: Optional[str] = None
    video: Optional[dict] = None


class TextToMovieAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        """Initialize agent with basic parameters"""
        self.agent_name = "text-to-movie"
        self.description = (
            "Agent for generating movies from storylines using Gen AI models"
        )
        self.parameters = SCREENPLAY_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        engine: str = "stabilityai",
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Process the storyline to generate a movie.

        :param collection_id: The collection ID to store generated assets
        :param engine: Video generation engine to use
        :return: AgentResponse containing information about generated movie
        """
        try:
            self.videodb_tool = VideoDBTool(collection_id=collection_id)
            self.output_message.actions.append("Processing input...")
            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Generating movie...",
            )
            self.output_message.content.append(video_content)
            self.output_message.push_update()
            self.llm = OpenAI(OpenaiConfig(timeout=120))

            # Tools initialization
            if engine not in SUPPORTED_ENGINES:
                raise Exception(f"{engine} not supported")

            if engine == "kling":
                KLING_AI_ACCESS_API_KEY = os.getenv("KLING_AI_ACCESS_API_KEY")
                KLING_AI_SECRET_API_KEY = os.getenv("KLING_AI_SECRET_API_KEY")
                if not KLING_AI_ACCESS_API_KEY or not KLING_AI_SECRET_API_KEY:
                    raise Exception("Kling AI API keys not found")
                self.video_tool = KlingAITool(
                    access_key=KLING_AI_ACCESS_API_KEY,
                    secret_key=KLING_AI_SECRET_API_KEY,
                )
            elif engine == "stabilityai":
                STABILITYAI_API_KEY = os.getenv("STABILITYAI_API_KEY")
                if not STABILITYAI_API_KEY:
                    raise Exception("StabilityAI API key not found")
                self.video_tool = StabilityAITool(api_key=STABILITYAI_API_KEY)

            ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
            if not ELEVENLABS_API_KEY:
                raise Exception("Elevenlabs API key not found")
            self.audio_tool = ElevenLabsTool(api_key=ELEVENLABS_API_KEY)

            # Initialize steps
            config = kwargs.get("text_to_video", {})
            raw_storyline = config.get("storyline", [])

            translation_llm_prompt = f"""
You are a professional movie director. Break down this storyline into individual shots that can be generated by an AI video generation model.

Storyline: {raw_storyline}

Guidelines:
1. Break the storyline into 4-6 distinct shots/scenes
2. Each shot should be a clear, detailed visual description
3. Each shot should make sense on its own
4. Avoid abstract concepts - focus on concrete visuals
5. Keep each shot description under 75 words
6. Ensure chronological flow between shots

Return a JSON response in this format:
{{
    "shots": [
        "Shot 1 description here",
        "Shot 2 description here",
        etc.
    ]
}}
"""
            translation_llm_message = ContextMessage(
                content=translation_llm_prompt,
                role=RoleTypes.user,
            )
            llm_response = self.llm.chat_completions(
                [translation_llm_message.to_llm_msg()],
                response_format={"type": "json_object"},
            )
            translated_shots = json.loads(llm_response.content)
            print("These are translted shots", translated_shots)

            steps = [{"step": step} for step in translated_shots["shots"]]

            # Step 1: Generate videos sequentially
            self.output_message.actions.append("Generating videos...")
            self.output_message.push_update()

            total_videos = len(steps)
            video_results = self.generate_videos_sequentially(steps, engine)

            self.output_message.actions.append(
                "Uploading generated videos to VideoDB..."
            )
            self.output_message.push_update()

            # Step 2: Upload videos to VideoDB
            for index, result in enumerate(video_results):
                if result.success:
                    self.output_message.actions.append(
                        f"Uploading {index + 1}/{total_videos} video to VideoDB"
                    )
                    self.output_message.push_update()

                    # Upload to VideoDB and get duration
                    media = self.videodb_tool.upload(
                        result.video_path, source_type="file_path", media_type="video"
                    )
                    steps[index]["video"] = media

                    # Cleanup
                    if os.path.exists(result.video_path):
                        os.remove(result.video_path)
                else:
                    error_msg = f"Failed to generate video {index + 1}: {result.error}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

            # Step 3: Generate background music [Optional]
            if config.get("user_music_description"):
                total_videos_duration = sum(
                    float(step["video"]["length"]) for step in steps
                )

                self.output_message.actions.append("Generating background music...")
                self.output_message.push_update()

                music_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp3"
                os.makedirs(DOWNLOADS_PATH, exist_ok=True)
                self.audio_tool.generate_sound_effect(
                    prompt=config.get("user_music_description"),
                    save_at=music_path,
                    duration=total_videos_duration,
                    config={},
                )

                self.output_message.actions.append(
                    "Uploading background music to VideoDB..."
                )
                self.output_message.push_update()

                media = self.videodb_tool.upload(
                    music_path, source_type="file_path", media_type="audio"
                )
                background_music = media

                if os.path.exists(music_path):
                    os.remove(music_path)

            # Step 3: Combine assets
            self.output_message.actions.append("Creating final movie...")
            self.output_message.push_update()

            video_url = self.combine_assets(
                steps,
                background_music if config.get("user_music_description") else None,
            )
            if not video_url:
                raise Exception("Failed to combine assets into final video")

            video_content.video = VideoData(stream_url=video_url)
            video_content.status = MsgStatus.success
            video_content.status_message = "Here is your generated movie"
            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message=f"Agent {self.agent_name} completed successfully",
                data={"video_url": video_url},
            )

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            video_content.status = MsgStatus.error
            video_content.status_message = "Error generating movie"
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.ERROR, message=f"Agent failed with error: {str(e)}"
            )

    def generate_videos_sequentially(
        self, steps: List[dict], engine: str
    ) -> List[VideoGenResult]:
        """Generate videos sequentially with progress tracking"""
        logger.info(
            f"Starting sequential video generation for {len(steps)} steps using {engine}"
        )
        video_results = []
        for index, step in enumerate(steps):
            self.output_message.actions.append(
                f"Generating video {index + 1}/{len(steps)}"
            )
            self.output_message.push_update()
            result = self.generate_single_video(index, step, engine)
            video_results.append(result)
            if result.success:
                logger.info(f"Successfully generated video {index + 1}/{len(steps)}")
            else:
                logger.error(f"Failed to generate video {index + 1}: {result.error}")
        return video_results

    def generate_single_video(
        self, index: int, step: dict, engine: str
    ) -> VideoGenResult:
        """Generate a single video with selected engine"""
        try:
            video_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp4"
            os.makedirs(DOWNLOADS_PATH, exist_ok=True)

            if engine == "kling":
                logger.info(f"Using Kling engine for video {index}")
                self.video_tool.text_to_video(
                    prompt=step["step"],
                    save_at=video_path,
                    duration=5,
                    config={},
                )
            elif engine == "stabilityai":
                logger.info(f"Using StabilityAI engine for video {index}")
                self.video_tool.text_to_video(
                    prompt=step["step"],
                    save_at=video_path,
                    duration=5,
                    config={},
                )

            if not os.path.exists(video_path):
                logger.error(f"Video file not found at path: {video_path}")
                raise Exception("Failed to generate video")

            return VideoGenResult(step_index=index, video_path=video_path, success=True)

        except Exception as e:
            logger.error(f"Error generating video for step {index}: {str(e)}")
            return VideoGenResult(
                step_index=index, video_path=None, success=False, error=str(e)
            )

    def combine_assets(self, steps: List[dict], background_music: str = None) -> str:
        """Combine videos and overlay background music"""
        try:
            timeline = self.videodb_tool.get_and_set_timeline()

            # Add videos using actual durations from VideoDB
            seeker = 0
            for step in steps:
                video = step["video"]
                video_asset = VideoAsset(asset_id=video["id"])
                timeline.add_inline(video_asset)
                seeker += float(video["length"])

            print("audio is ", background_music)
            print("seeker is ", seeker)
            # Add single background music track
            if background_music:
                audio_asset = AudioAsset(
                    asset_id=background_music["id"],
                    start=0,
                    end=min(seeker, float(background_music["length"])),
                )
                timeline.add_overlay(0, audio_asset)

            return timeline.generate_stream()

        except Exception as e:
            logger.exception(f"Error combining assets: {e}")
            raise Exception(f"Error combining assets: {e}")
