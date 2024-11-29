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
from director.llm import get_default_llm
from director.tools.kling import KlingAITool, PARAMS_CONFIG as KLING_PARAMS_CONFIG
from director.tools.stabilityai import (
    StabilityAITool,
    PARAMS_CONFIG as STABILITYAI_PARAMS_CONFIG,
)
from director.tools.elevenlabs import (
    ElevenLabsTool,
    PARAMS_CONFIG as ELEVENLABS_PARAMS_CONFIG,
)
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
            "enum": SUPPORTED_ENGINES,
            "default": "stabilityai",
        },
        "job_type": {
            "type": "string",
            "enum": ["text_to_movie"],
            "description": "The type of video generation to perform",
        },
        "text_to_movie": {
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
                "video_stabilityai_config": {
                    "type": "object",
                    "description": "Optional configuration for StabilityAI engine",
                    "properties": STABILITYAI_PARAMS_CONFIG["text_to_video"],
                },
                "video_kling_config": {
                    "type": "object",
                    "description": "Optional configuration for Kling engine",
                    "properties": KLING_PARAMS_CONFIG["text_to_video"],
                },
                "audio_elevenlabs_config": {
                    "type": "object",
                    "description": "Optional configuration for ElevenLabs engine",
                    "properties": ELEVENLABS_PARAMS_CONFIG["sound_effect"],
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
class AudioGenResult:
    """Track results of audio generation"""

    step_index: int
    audio_path: Optional[str]
    success: bool
    error: Optional[str] = None
    audio: Optional[dict] = None


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


def truncate_to_one_decimal(num):
    return int(num * 10) / 10


class TextToMovieAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        """Initialize agent with basic parameters"""
        self.agent_name = "text_to_movie"
        self.description = (
            "Agent for generating movies from storylines using Gen AI models"
        )
        self.parameters = TEXT_TO_MOVIE_AGENT_PARAMETERS
        self.llm = get_default_llm()

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
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        engine: str = "stabilityai",
        job_type: str = "text_to_movie",
        text_to_movie: Optional[dict] = None,
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

            if engine == "stabilityai":
                STABILITY_API_KEY = os.getenv("STABILITYAI_API_KEY")
                if not STABILITY_API_KEY:
                    raise Exception("Stability AI API key not found")
                self.video_gen_tool = StabilityAITool(api_key=STABILITY_API_KEY)
                self.video_gen_config_key = "video_stabilityai_config"
            elif engine == "kling":
                KLING_API_ACCESS_KEY = os.getenv("KLING_AI_ACCESS_API_KEY")
                KLING_API_SECRET_KEY = os.getenv("KLING_AI_SECRET_API_KEY")
                if not KLING_API_ACCESS_KEY or not KLING_API_SECRET_KEY:
                    raise Exception("Kling AI API key not found")
                self.video_gen_tool = KlingAITool(
                    access_key=KLING_API_ACCESS_KEY, secret_key=KLING_API_SECRET_KEY
                )
                self.video_gen_config_key = "video_kling_config"
            else:
                raise Exception(f"{engine} not supported")

            # Initialize tools
            ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
            if not ELEVENLABS_API_KEY:
                raise Exception("ElevenLabs API key not found")
            self.audio_gen_tool = ElevenLabsTool(api_key=ELEVENLABS_API_KEY)
            self.audio_gen_config_key = "audio_elevenlabs_config"

            # Initialize steps
            if job_type == "text_to_movie":
                raw_storyline = text_to_movie.get("storyline", [])
                video_gen_config = text_to_movie.get(self.video_gen_config_key, {})
                audio_gen_config = text_to_movie.get(self.audio_gen_config_key, {})

                # Generate visual style
                visual_style = self.generate_visual_style(raw_storyline)
                print("These are visual styles", visual_style)

                # Generate scenes
                scenes = self.generate_scene_sequence(
                    raw_storyline, visual_style, engine
                )
                print("These are scenes", scenes)

                self.output_message.actions.append(
                    f"Generating {len(scenes)} videos..."
                )
                self.output_message.push_update()

                engine_config = self.engine_configs[engine]
                generated_videos_results = []
                generated_audio_results = []

                # Generate videos sequentially
                for index, scene in enumerate(scenes):
                    self.output_message.actions.append(
                        f"Generating video for scene {index + 1}..."
                    )
                    self.output_message.push_update()

                    suggested_duration = min(
                        scene.get("suggested_duration", 5), engine_config.max_duration
                    )
                    # Generate engine-specific prompt
                    prompt = self.generate_engine_prompt(scene, visual_style, engine)

                    print(f"Generating video for scene {index + 1}...")
                    print("This is the prompt", prompt)

                    video_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp4"
                    os.makedirs(DOWNLOADS_PATH, exist_ok=True)

                    self.video_gen_tool.text_to_video(
                        prompt=prompt,
                        save_at=video_path,
                        duration=suggested_duration,
                        config=video_gen_config,
                    )
                    generated_videos_results.append(
                        VideoGenResult(
                            step_index=index, video_path=video_path, success=True
                        )
                    )

                self.output_message.actions.append(
                    f"Uploading {len(generated_videos_results)} videos to VideoDB..."
                )
                self.output_message.push_update()

                # Process videos and track duration
                total_duration = 0
                for result in generated_videos_results:
                    if result.success:
                        self.output_message.actions.append(
                            f"Uploading video {result.step_index + 1}..."
                        )
                        self.output_message.push_update()
                        media = self.videodb_tool.upload(
                            result.video_path,
                            source_type="file_path",
                            media_type="video",
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

                self.output_message.actions.append("Generating background music...")
                self.output_message.push_update()

                self.output_message.actions.append(
                    f"Generating {len(scenes)} audio tracks..."
                )
                self.output_message.push_update()

                # Generate and add sound effects for each scene
                for index, scene in enumerate(scenes):
                    self.output_message.actions.append(
                        f"Generating audio for scene {index + 1}..."
                    )
                    self.output_message.push_update()

                    sound_effects_description = self.generate_audio_prompt(scene)
                    scene_duration = float(scene["video"].get("length", 0))

                    os.makedirs(DOWNLOADS_PATH, exist_ok=True)
                    sound_effects_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp3"

                    self.audio_gen_tool.generate_sound_effect(
                        prompt=sound_effects_description,
                        save_at=sound_effects_path,
                        duration=scene_duration,
                        config=audio_gen_config,
                    )

                    generated_audio_results.append(
                        AudioGenResult(
                            step_index=index,
                            audio_path=sound_effects_path,
                            success=True,
                        )
                    )

                self.output_message.actions.append(
                    f"Uploading {len(generated_audio_results)} audio tracks to VideoDB..."
                )
                self.output_message.push_update()

                for result in generated_audio_results:
                    if result.success:
                        self.output_message.actions.append(
                            f"Uploading audio for scene {result.step_index + 1}..."
                        )
                        self.output_message.push_update()

                        sound_effects_media = self.videodb_tool.upload(
                            result.audio_path,
                            source_type="file_path",
                            media_type="audio",
                        )
                        scenes[result.step_index]["audio"] = sound_effects_media

                        if os.path.exists(result.audio_path):
                            os.remove(result.audio_path)
                    else:
                        raise Exception(
                            f"Failed to generate audio for scene {result.step_index}: {result.error}"
                        )

                self.output_message.actions.append(
                    "Combining assets into final video..."
                )
                self.output_message.push_update()

                # Combine everything into final video
                final_video = self.combine_assets(scenes)

                video_content.video = VideoData(stream_url=final_video)
                video_content.status = MsgStatus.success
                video_content.status_message = "Movie generation complete"
                self.output_message.publish()

                return AgentResponse(
                    status=AgentStatus.SUCCESS,
                    message="Movie generated successfully",
                    data={"video_url": final_video},
                )

            else:
                raise ValueError(f"Unsupported job type: {job_type}")

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

            compression_message = ContextMessage(
                content=compression_prompt, role=RoleTypes.user
            )
            llm_response = self.llm.chat_completions(
                [compression_message.to_llm_msg()], response_format={"type": "text"}
            )
            return llm_response.content

    def generate_audio_prompt(self, scene: dict) -> str:
        """Generate scene-specific audio prompt for ElevenLabs."""
        audio_prompt = f"""
        As a composer, create a musical description for this scene:
        Story beat: {scene['story_beat']}
        Scene description: {scene['scene_description']}
        
        Focus on:
        - Main instruments/sounds that match the scene's mood
        - Tempo and rhythm that fits the action
        - Any specific sound effects needed
        
        Keep it under 100 characters. Focus only on audio elements.
        """

        prompt_message = ContextMessage(content=audio_prompt, role=RoleTypes.user)
        llm_response = self.llm.chat_completions(
            [prompt_message.to_llm_msg()], response_format={"type": "text"}
        )
        return llm_response.content[:100]

    def combine_assets(self, scenes: List[dict]) -> str:
        print("Combining assets...", scenes)
        timeline = self.videodb_tool.get_and_set_timeline()

        seeker = 0

        # Add videos and their corresponding audio sequentially
        for scene in scenes:
            video_asset = VideoAsset(asset_id=scene["video"]["id"])
            timeline.add_inline(video_asset)
            video_length = float(scene["video"].get("length", 0))

            if "audio" in scene:
                audio_length = float(scene["audio"].get("length", 0))
                audio_asset = AudioAsset(
                    asset_id=scene["audio"]["id"],
                    start=0,
                    end=truncate_to_one_decimal(min(video_length, audio_length)),
                    disable_other_tracks=True,
                    fade_in_duration=0.5,
                    fade_out_duration=0.5,
                )
                timeline.add_overlay(seeker, audio_asset)
            seeker += video_length

        return timeline.generate_stream()
