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

MOVIENARRATOR_AGENT_PARAMETERS = {
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
            "enum": ["movie_narrator"],
            "description": "The type of video generation to perform",
        },
        "movie_narrator": {
            "type": "object",
            "properties": {
                "storyline": {
                    "type": "string",
                    "description": "The storyline to generate the video",
                },
                "voiceover_description": {
                    "type": "string",
                    "description": "Optional description for voiceover script generation",
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
                    "properties": ELEVENLABS_PARAMS_CONFIG["text_to_speech"],
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


class MovieNarratorAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        """Initialize agent with basic parameters"""
        self.agent_name = "movie_narrator"
        self.description = "Agent for generating movies with narrations and voiceovers from storylines using Gen AI models"
        self.parameters = MOVIENARRATOR_AGENT_PARAMETERS
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
        job_type: str = "movie_narrator",
        movie_narrator: Optional[dict] = None,
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
            if job_type == "movie_narrator":
                raw_storyline = movie_narrator.get("storyline", [])
                video_gen_config = movie_narrator.get(self.video_gen_config_key, {})
                audio_gen_config = movie_narrator.get(self.audio_gen_config_key, {})

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

                # Generate audio prompt
                voiceover_description = self.generate_audio_prompt(raw_storyline)
                print("Generated voiceover script:", voiceover_description)

                self.output_message.actions.append("Generating voiceover...")
                self.output_message.push_update()

                # Generate and add voiceover
                os.makedirs(DOWNLOADS_PATH, exist_ok=True)
                voiceover_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp3"
                self.audio_gen_tool.text_to_speech(
                    text=voiceover_description,
                    save_at=voiceover_path,
                    config=audio_gen_config,
                )

                self.output_message.actions.append("Uploading voiceover to VideoDB...")
                self.output_message.push_update()

                voiceover_media = self.videodb_tool.upload(
                    voiceover_path, source_type="file_path", media_type="audio"
                )

                if os.path.exists(voiceover_path):
                    os.remove(voiceover_path)

                self.output_message.actions.append(
                    "Combining assets into final video..."
                )
                self.output_message.push_update()

                # Combine everything into final video
                final_video = self.combine_assets(scenes, voiceover_media)

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
        """Generate 5 scenes with visual and narrative consistency."""
        engine_config = self.engine_configs[engine]

        sequence_prompt = f"""
        Break this storyline into 5 distinct scenes maintaining visual consistency.
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
            IMPORTANT: Compress the following prompt to under 2450 characters while maintaining its structure and key information:

            {initial_prompt}
            """

            compression_message = ContextMessage(
                content=compression_prompt, role=RoleTypes.user
            )
            llm_response = self.llm.chat_completions(
                [compression_message.to_llm_msg()], response_format={"type": "text"}
            )
            return llm_response.content

    def generate_audio_prompt(self, storyline: str) -> str:
        """Generate voiceover script for ElevenLabs."""
        audio_prompt = f"""
        Write the exact words for a movie trailer voiceover about this story:
        "{storyline}"

        EXAMPLE FORMAT:
        For storyline "A chef discovers he can taste memories":
        "One man's gift will change everything. In a world of ordinary flavors, he tastes what no one else can - the very essence of memories themselves."

        For storyline "A cat learns to drive":
        "They said four legs couldn't reach the pedals. They were wrong. This summer, witness the tail of the most extraordinary driver in history."
        
        YOUR TURN - Write a dramatic movie trailer voiceover for: "{storyline}"
        Remember:
        - Write ONLY the actual words to be spoken
        - Use dramatic movie trailer style
        - Keep it between 6-8 complete, but short sentences. IMPORTANT: keep it less than 850 characters.
        - No descriptions, just pure narration
        - Include ... (ellipses) for a longer pause and , (comma) for a shorter pause. Use these to manage the tone and pace.
        - Ensure all sentences are complete
        - Match the tempo and duration of a 60-second video, with 4-second scenes.
        """

        prompt_message = ContextMessage(content=audio_prompt, role=RoleTypes.user)
        llm_response = self.llm.chat_completions(
            [prompt_message.to_llm_msg()], response_format={"type": "text"}
        )
        return llm_response.content.strip()  # Remove the [:100] truncation

    def combine_assets(
        self, scenes: List[dict], voiceover_media: Optional[dict]
    ) -> str:
        timeline = self.videodb_tool.get_and_set_timeline()

        # Add videos sequentially
        for scene in scenes:
            video_asset = VideoAsset(asset_id=scene["video"]["id"])
            timeline.add_inline(video_asset)

        # Add voiceover if available
        if voiceover_media:
            voiceover_asset = AudioAsset(
                asset_id=voiceover_media["id"], start=0, disable_other_tracks=True
            )
            timeline.add_overlay(0, voiceover_asset)

        return timeline.generate_stream()