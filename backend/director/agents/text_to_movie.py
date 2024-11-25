import logging
import os
import json
import uuid
from typing import List, Optional, Dict
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

TEXT_TO_MOVIE_AGENT_PARAMETERS = {
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
                "sound_effects_description": {
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
            "required": ["storyline"],
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


@dataclass
class EngineConfig:
    name: str
    max_duration: int
    preferred_style: str
    prompt_format: str


@dataclass
class VisualStyle:
    camera_setup: str
    color_grading: str
    lighting_style: str
    movement_style: str
    film_mood: str
    director_reference: str
    character_constants: Dict
    setting_constants: Dict


class TextToMovieAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        """Initialize agent with basic parameters"""
        self.agent_name = "text_to_movie"
        self.description = (
            "Agent for generating movies from storylines using Gen AI models"
        )
        self.parameters = TEXT_TO_MOVIE_AGENT_PARAMETERS
        self.llm = OpenAI(OpenaiConfig(timeout=120))

        self.engine_configs = {
            "kling": EngineConfig(
                name="kling",
                max_duration=10,
                preferred_style="cinematic",
                prompt_format="detailed",
            ),
            "stabilityai": EngineConfig(
                name="stabilityai",
                max_duration=4,
                preferred_style="photorealistic",
                prompt_format="concise",
            ),
        }

        # Initialize video generation tools
        self.stability_tool = None
        self.kling_tool = None

        STABILITY_API_KEY = os.getenv("STABILITYAI_API_KEY")
        if STABILITY_API_KEY:
            self.stability_tool = StabilityAITool(api_key=STABILITY_API_KEY)

        KLING_API_ACCESS_KEY = os.getenv("KLING_AI_ACCESS_API_KEY")
        KLING_API_SECRET_KEY = os.getenv("KLING_AI_SECRET_API_KEY")
        if KLING_API_ACCESS_KEY and KLING_API_SECRET_KEY:
            self.kling_tool = KlingAITool(
                access_key=KLING_API_ACCESS_KEY, secret_key=KLING_API_SECRET_KEY
            )

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

            if engine not in self.engine_configs:
                raise ValueError(f"Unsupported engine: {engine}")

            if engine == "kling" and not self.kling_tool:
                raise ValueError("Kling engine selected but not initialized")
            elif engine == "stabilityai" and not self.stability_tool:
                raise ValueError("Stability engine selected but not initialized")

            # Initialize tools
            self.audio_tool = ElevenLabsTool(api_key=os.getenv("ELEVENLABS_API_KEY"))

            # Initialize steps
            config = kwargs.get("text_to_video", {})
            raw_storyline = config.get("storyline", [])

            # Generate visual style
            visual_style = self.generate_visual_style(raw_storyline)
            print("these are the visual styles", visual_style)

            # Generate scenes
            scenes = self.generate_scene_sequence(raw_storyline, visual_style, engine)
            print("these are the scenes", scenes)

            # Generate videos sequentially
            video_results = self.generate_videos_sequentially(
                scenes, visual_style, engine
            )
            print("these are the video results", video_results)

            # Process videos and track duration
            total_duration = 0
            for result in video_results:
                if result.success:
                    media = self.videodb_tool.upload(
                        result.video_path, source_type="file_path", media_type="video"
                    )
                    total_duration += float(media.get("length", 0))
                    scenes[result.step_index]["video"] = media

                    # Cleanup temporary files
                    if os.path.exists(result.video_path):
                        os.remove(result.video_path)
                else:
                    raise Exception(
                        f"Failed to generate video {result.step_index}: {result.error}"
                    )

            # Generate audio prompt
            sound_effects_description = self.generate_audio_prompt(raw_storyline)

            # Generate and add sound effects
            os.makedirs(DOWNLOADS_PATH, exist_ok=True)
            sound_effects_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp3"

            # Configure sound effects generation
            sound_effects_config = {}

            self.audio_tool.generate_sound_effect(
                prompt=sound_effects_description,
                save_at=sound_effects_path,
                duration=total_duration,
                config=sound_effects_config,
            )

            sound_effects_media = self.videodb_tool.upload(
                sound_effects_path, source_type="file_path", media_type="audio"
            )

            if os.path.exists(sound_effects_path):
                os.remove(sound_effects_path)

            # Combine everything into final video
            final_video = self.combine_assets(scenes, sound_effects_media)

            video_content.video = VideoData(stream_url=final_video)
            video_content.status = MsgStatus.success
            video_content.status_message = "Movie generation complete"
            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Movie generated successfully",
                data={"video_url": final_video},
            )

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            video_content.status = MsgStatus.error
            video_content.status_message = "Error generating movie"
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.ERROR, message=f"Agent failed with error: {str(e)}"
            )

    def generate_visual_style(self, storyline: str) -> VisualStyle:
        """Generate consistent visual style for entire film."""
        style_prompt = f"""
        As a cinematographer, define a consistent visual style for this short film:
        Storyline: {storyline}
        
        Return a JSON response with visual style parameters:
        {{
            "camera_setup": "Camera and lens combination",
            "color_grading": "Color grading style and palette",
            "lighting_style": "Core lighting approach",
            "movement_style": "Camera movement philosophy",
            "film_mood": "Overall atmospheric mood",
            "director_reference": "Key director's style to reference",
            "character_constants": {{
                "physical_description": "Consistent character details",
                "costume_details": "Consistent costume elements"
            }},
            "setting_constants": {{
                "time_period": "When this takes place",
                "environment": "Core setting elements that stay consistent"
            }}
        }}
        """

        style_message = ContextMessage(content=style_prompt, role=RoleTypes.user)
        llm_response = self.llm.chat_completions(
            [style_message.to_llm_msg()], response_format={"type": "json_object"}
        )
        return VisualStyle(**json.loads(llm_response.content))

    def generate_scene_sequence(
        self, storyline: str, style: VisualStyle, engine: str
    ) -> List[dict]:
        """Generate 3-5 scenes with visual and narrative consistency."""
        engine_config = self.engine_configs[engine]

        sequence_prompt = f"""
        Break this storyline into 3 distinct scenes maintaining visual consistency.
        Generate scene descriptions optimized for {engine} {engine_config.preferred_style} style.
        
        Visual Style:
        - Camera/Lens: {style.camera_setup}
        - Color Grade: {style.color_grading}
        - Lighting: {style.lighting_style}
        - Movement: {style.movement_style}
        - Mood: {style.film_mood}
        - Director Style: {style.director_reference}
        
        Character Constants:
        {json.dumps(style.character_constants, indent=2)}
        
        Setting Constants:
        {json.dumps(style.setting_constants, indent=2)}
        
        Maximum duration per scene: {engine_config.max_duration} seconds
        
        Storyline: {storyline}

        Return a JSON array of scenes with:
        {{
            "story_beat": "What happens in this scene",
            "scene_description": "Visual description optimized for {engine}",
            "suggested_duration": "Duration as integer in seconds (max {engine_config.max_duration})"
        }}
        Make sure suggested_duration is a number, not a string.
        """

        sequence_message = ContextMessage(content=sequence_prompt, role=RoleTypes.user)
        llm_response = self.llm.chat_completions(
            [sequence_message.to_llm_msg()], response_format={"type": "json_object"}
        )
        scenes_data = json.loads(llm_response.content)["scenes"]

        # Ensure durations are integers
        for scene in scenes_data:
            try:
                scene["suggested_duration"] = int(scene.get("suggested_duration", 5))
            except (ValueError, TypeError):
                scene["suggested_duration"] = 5

        return scenes_data

    def generate_engine_prompt(
        self, scene: dict, style: VisualStyle, engine: str
    ) -> str:
        """Generate engine-specific prompt"""
        engine_config = self.engine_configs[engine]

        if engine == "stabilityai":
            return f"""
            {style.director_reference} style.
            {scene['scene_description']}.
            {style.character_constants['physical_description']}.
            {style.lighting_style}, {style.color_grading}.
            Photorealistic, detailed, high quality, masterful composition.
            """
        else:  # Kling
            initial_prompt = f"""
            {style.director_reference} style shot. 
            Filmed on {style.camera_setup}.
            
            {scene['scene_description']}
            
            Character Details:
            {json.dumps(style.character_constants, indent=2)}
            
            Setting Elements:
            {json.dumps(style.setting_constants, indent=2)}
            
            {style.lighting_style} lighting.
            {style.color_grading} color palette.
            {style.movement_style} camera movement.
            
            Mood: {style.film_mood}
            """

            # Run through LLM to compress while maintaining structure
            compression_prompt = f"""
            Compress the following prompt to under 2450 characters while maintaining its structure and key information:

            {initial_prompt}
            """
            
            compression_message = ContextMessage(content=compression_prompt, role=RoleTypes.user)
            llm_response = self.llm.chat_completions(
                [compression_message.to_llm_msg()], response_format={"type": "text"}
            )
            return llm_response.content

    def generate_videos_sequentially(
        self, scenes: List[dict], style: VisualStyle, engine: str
    ) -> List[VideoGenResult]:
        """Generate videos maintaining visual consistency."""
        video_results = []
        engine_config = self.engine_configs[engine]

        for index, scene in enumerate(scenes):
            # Duration is already guaranteed to be int from generate_scene_sequence
            suggested_duration = min(
                scene.get("suggested_duration", 5), engine_config.max_duration
            )

            # Generate engine-specific prompt
            prompt = self.generate_engine_prompt(scene, style, engine)

            # Add engine-specific parameters
            engine_params = {"prompt": prompt, "duration": suggested_duration}

            print("these are the engine params", engine_params)

            if engine == "stabilityai":
                engine_params.update(
                    {
                        "cfg_scale": 7.5,
                        "motion_bucket_id": 127,
                    }
                )

            result = self.generate_single_video(index, engine_params, engine)
            video_results.append(result)

        return video_results

    def generate_audio_prompt(self, storyline: str) -> str:
        """Generate minimal, music-focused prompt for ElevenLabs."""
        audio_prompt = f"""
        As a composer, create a simple musical description focusing ONLY on:
        - Main instrument/sound
        - One key mood change
        - Basic progression
        
        Keep it under 100 characters. No visual references or scene descriptions.
        Focus on the music.
        
        Story context: {storyline}
        """

        prompt_message = ContextMessage(content=audio_prompt, role=RoleTypes.user)
        llm_response = self.llm.chat_completions(
            [prompt_message.to_llm_msg()], response_format={"type": "text"}
        )
        return llm_response.content[:100]

    def generate_single_video(
        self, index: int, params: dict, engine: str
    ) -> VideoGenResult:
        """Generate a single video clip using the specified engine."""
        try:
            video_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp4"
            os.makedirs(DOWNLOADS_PATH, exist_ok=True)

            if engine == "stabilityai":
                if not self.stability_tool:
                    raise Exception("StabilityAI tool not initialized")

                # Configure Stability-specific parameters
                stability_config = {
                    "cfg_scale": params.get("cfg_scale", 7.5),
                    "motion_bucket_id": params.get("motion_bucket_id", 127),
                }

                self.stability_tool.text_to_video(
                    prompt=params["prompt"],
                    save_at=video_path,
                    duration=params["duration"],
                    config=stability_config,
                )
            else:  # kling
                if not self.kling_tool:
                    raise Exception("Kling tool not initialized")

                # Configure Kling-specific parameters
                kling_config = {"model": "kling-v1"}

                self.kling_tool.text_to_video(
                    prompt=params["prompt"],
                    save_at=video_path,
                    duration=params["duration"],
                    config=kling_config,
                )

            if not os.path.exists(video_path):
                raise Exception("Failed to generate video file")

            return VideoGenResult(step_index=index, video_path=video_path, success=True)

        except Exception as e:
            logger.error(f"Error generating video for step {index}: {str(e)}")
            return VideoGenResult(
                step_index=index, video_path=None, success=False, error=str(e)
            )

    def combine_assets(self, scenes: List[dict], audio_media: Optional[dict]) -> str:
        timeline = self.videodb_tool.get_and_set_timeline()

        # Add videos sequentially
        for scene in scenes:
            video_asset = VideoAsset(asset_id=scene["video"]["id"])
            timeline.add_inline(video_asset)

        # Add background score if available
        if audio_media:
            audio_asset = AudioAsset(
                asset_id=audio_media["id"], start=0, disable_other_tracks=True
            )
            timeline.add_overlay(0, audio_asset)

        return timeline.generate_stream()
