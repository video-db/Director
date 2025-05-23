import logging
import os
import uuid
import base64
from typing import Optional

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, TextContent, MsgStatus
from director.tools.videodb_tool import VDBAudioGenerationTool, VideoDBTool
from director.tools.elevenlabs import (
    ElevenLabsTool,
    PARAMS_CONFIG as ELEVENLABS_PARAMS_CONFIG
)
from director.tools.beatoven import BeatovenTool

from director.constants import DOWNLOADS_PATH

logger = logging.getLogger(__name__)

SUPPORTED_ENGINES = ["elevenlabs", "beatoven", "videodb"]

AUDIO_GENERATION_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "The unique identifier of the collection to store audio",
        },
        "engine": {
            "type": "string",
            "description": """The engine to use for audio generation. Default is 'videodb'.`:
                - videodb: supports text_to_speech, sound_effect and create_music
                - elevenlabs: supports text_to_speech and sound_effect
                - beatoven: supports create_music""",
            "default": "videodb",
            "enum": SUPPORTED_ENGINES,
        },
        "job_type": {
            "type": "string",
            "enum": ["text_to_speech", "sound_effect", "create_music"],
            "description": """The type of audio generation to perform:
                - text_to_speech: converts text to speech (elevenlabs and videodb engine only)
                - sound_effect: creates sound effects (elevenlabs and videodb engine only)
                - create_music: creates background music (beatoven and videodb engine only)""",
        },
        "sound_effect": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt to generate the sound effect",
                },
                "duration": {
                    "type": "number",
                    "description": "Duration of the sound effect in seconds",
                    "default": 2,
                },
                "audio_config": {
                    "type": "object",
                    "properties": ELEVENLABS_PARAMS_CONFIG["sound_effect"],
                    "description": "Config for elevenlabs engine",
                },
            },
            "required": ["prompt"],
        },
        "create_music": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt to generate the music",
                },
                "duration": {
                    "type": "number",
                    "description": "Duration of the music in seconds",
                    "default": 30,
                },
            },
            "required": ["prompt"],
        },
        "text_to_speech": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to convert to speech",
                },
                "audio_config": {
                    "type": "object",
                    "properties": ELEVENLABS_PARAMS_CONFIG["text_to_speech"],
                },
            },
            "required": ["text"],
        },
    },
    "required": ["job_type", "collection_id", "engine"],
}


class AudioGenerationAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "audio_generation"
        self.description = (
            "Agent to generate speech, sound effects, and background music"
        )
        self.parameters = AUDIO_GENERATION_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        job_type: str,
        engine: str,
        sound_effect: Optional[dict] = None,
        text_to_speech: Optional[dict] = None,
        create_music: Optional[dict] = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Generates audio using various engines based on input.
        :param collection_id: The collection ID to store the generated audio
        :param job_type: The type of audio to generate
        :param engine: The engine to use for generation
        :param sound_effect: The sound effect parameters
        :param text_to_speech: The text to speech parameters
        :param create_music: The music generation parameters
        :return: Response containing the generated audio URL
        """
        try:
            media = None
            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            if engine not in SUPPORTED_ENGINES:
                raise Exception(f"{engine} not supported")

            config_key = "audio_config"
            if engine == "elevenlabs":
                ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
                if not ELEVENLABS_API_KEY:
                    raise Exception("Elevenlabs API key not present in .env")
                audio_gen_tool = ElevenLabsTool(api_key=ELEVENLABS_API_KEY)
            elif engine == "beatoven":
                BEATOVEN_API_KEY = os.getenv("BEATOVEN_API_KEY")
                if not BEATOVEN_API_KEY:
                    raise Exception("Beatoven API key not present in .env")
                audio_gen_tool = BeatovenTool(api_key=BEATOVEN_API_KEY)
            elif engine == "videodb":
                audio_gen_tool = VDBAudioGenerationTool()    

            os.makedirs(DOWNLOADS_PATH, exist_ok=True)
            output_file_name = f"audio_{job_type}_{str(uuid.uuid4())}.mp3"
            output_path = f"{DOWNLOADS_PATH}/{output_file_name}"

            if job_type == "sound_effect":
                if engine == "beatoven":
                    raise Exception("Sound effects only supported with elevenlabs or videodb")
                prompt = sound_effect.get("prompt")
                duration = sound_effect.get("duration", 5)
                config = sound_effect.get(config_key, {})
                if prompt is None:
                    raise Exception("Prompt is required for sound effect")
                msg = f"Generating sound effect using <b>{engine}</b>"
                self.output_message.actions.append(
                    f"{msg} for prompt <i>{prompt}</i>"
                )
                self.output_message.push_update()
                media = audio_gen_tool.generate_sound_effect(
                    prompt=prompt,
                    save_at=output_path,
                    duration=duration,
                    config=config,
                )
            elif job_type == "create_music":
                if engine not in ["beatoven", "videodb"]:
                    raise Exception("Music creation only supported with beatoven")
                prompt = create_music.get("prompt")
                duration = create_music.get("duration", 30)
                if prompt is None:
                    raise Exception("Prompt is required for music generation")
                msg = f"Generating music using <b>{engine}</b>"
                self.output_message.actions.append(
                    f"{msg} for prompt <i>{prompt}</i>"
                )
                self.output_message.push_update()
                media = audio_gen_tool.generate_music(
                    prompt=prompt,
                    save_at=output_path,
                    duration=duration
                )
            elif job_type == "text_to_speech":
                if engine not in ["elevenlabs", "videodb"]:
                    raise Exception("Text to speech only supported with elevenlabs and videodb")
                text = text_to_speech.get("text")
                config = text_to_speech.get(config_key, {})
                msg = f"Using <b>{engine}</b> to convert text"
                self.output_message.actions.append(
                    f"{msg} <i>{text}</i> to speech"
                )
                self.output_message.push_update()
                media = audio_gen_tool.text_to_speech(
                    text=text,
                    save_at=output_path,
                    config=config,
                )

            self.output_message.push_update()

            if media is None:
                self.output_message.actions.append(
                    f"Generated audio saved at <i>{output_path}</i>"
                )
                media = self.videodb_tool.upload(
                    output_path,
                    source_type="file_path",
                    media_type="audio"
                )
                msg = "Uploaded generated audio to VideoDB"
            else:
                msg = "Generated audio stored in collection"
            self.output_message.actions.append(
                f"{msg} with Audio ID {media['id']}"
            )
            with open(os.path.abspath(output_path), "rb") as file:
                b64_data = base64.b64encode(file.read()).decode('utf-8')
                data_url = f"data:audio/mpeg;base64,{b64_data}"
                dl_link = (
                    f"<a href='{data_url}' "
                    f"download='{output_file_name}' "
                    f"target='_blank'>here</a>"
                )
                text_content = TextContent(
                    agent_name=self.agent_name,
                    status=MsgStatus.success,
                    status_message="Here is your generated audio",
                    text=f"Click {dl_link} to download the audio",
                )
            self.output_message.content.append(text_content)
            self.output_message.push_update()
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            text_content = TextContent(
                agent_name=self.agent_name,
                status=MsgStatus.error,
                status_message="Failed to generate audio",
            )
            self.output_message.content.append(text_content)
            self.output_message.push_update()
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        finally:
            if output_path and os.path.exists(output_path):
                os.remove(output_path)
        msg = "Audio generated successfully"
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"{msg}, Generated Media audio id: {media['id']}",
            data={"audio_id": media["id"]},
        )
