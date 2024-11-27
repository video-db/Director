import logging
import os
import uuid
import base64
from typing import Optional

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, TextContent, MsgStatus
from director.tools.videodb_tool import VideoDBTool
from director.tools.elevenlabs import (
    ElevenLabsTool,
    PARAMS_CONFIG as ELEVENLABS_PARAMS_CONFIG,
)

from director.constants import DOWNLOADS_PATH

logger = logging.getLogger(__name__)

SUPPORTED_ENGINES = ["elevenlabs"]

AUDIO_GENERATION_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "The unique identifier of the collection to store the audio",
        },
        "engine": {
            "type": "string",
            "description": "The engine to use",
            "default": "elevenlabs",
            "enum": ["elevenlabs"],
        },
        "job_type": {
            "type": "string",
            "enum": ["text_to_speech", "sound_effect"],
            "description": """
                The type of audio generation to perform
                Possible values:
                    - text_to_speech: converts text to speech
                    - sound_effect: creates a sound effect from a text prompt
            """,
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
                    "description": "The duration of the sound effect in seconds",
                    "default": 2,
                },
                "elevenlabs_config": {
                    "type": "object",
                    "properties": ELEVENLABS_PARAMS_CONFIG["sound_effect"],
                    "description": "Config to use when elevenlabs engine is used",
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
                "elevenlabs_config": {
                    "type": "object",
                    "properties": ELEVENLABS_PARAMS_CONFIG["text_to_speech"],
                    "description": "Config to use when elevenlabs engine is used",
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
        self.description = "An agent designed to generate speech from text and sound effects from prompt"
        self.parameters = AUDIO_GENERATION_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        job_type: str,
        engine: str,
        sound_effect: Optional[dict] = None,
        text_to_speech: Optional[dict] = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Generates audio using ElevenLabs API based on input text.
        :param str collection_id: The collection ID to store the generated audio
        :param job_type: The audio generation engine to use
        :param sound_effect: The sound effect to generate
        :param text_to_speech: The text to convert to speech
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: Response containing the generated audio URL
        :rtype: AgentResponse
        """
        try:
            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            if engine not in SUPPORTED_ENGINES:
                raise Exception(f"{engine} not supported")

            if engine == "elevenlabs":
                ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
                if not ELEVENLABS_API_KEY:
                    raise Exception("Elevenlabs API key not present in .env")
                audio_gen_tool = ElevenLabsTool(api_key=ELEVENLABS_API_KEY)
                config_key = "elevenlabs_config"

            os.makedirs(DOWNLOADS_PATH, exist_ok=True)
            output_file_name = f"audio_{job_type}_{str(uuid.uuid4())}.mp3"
            output_path = f"{DOWNLOADS_PATH}/{output_file_name}"

            if job_type == "sound_effect":
                prompt = sound_effect.get("prompt")
                duration = sound_effect.get("duration", 5)
                config = sound_effect.get(config_key, {})
                if prompt is None:
                    raise Exception("Prompt is required for sound effect generation")
                self.output_message.actions.append(
                    f"Generating sound effect using <b>{engine}</b> for prompt <i>{prompt}</i>"
                )
                self.output_message.push_update()
                audio_gen_tool.generate_sound_effect(
                    prompt=prompt,
                    save_at=output_path,
                    duration=duration,
                    config=config,
                )
            elif job_type == "text_to_speech":
                text = text_to_speech.get("text")
                config = text_to_speech.get(config_key, {})
                self.output_message.actions.append(
                    f"Using <b> {engine} </b> to convert text <i>{text}</i> to speech"
                )
                self.output_message.push_update()
                audio_gen_tool.text_to_speech(
                    text=text,
                    save_at=output_path,
                    config=config,
                )

            self.output_message.actions.append(
                f"Generated audio saved at <i>{output_path}</i>"
            )
            self.output_message.push_update()

            # Upload to VideoDB
            media = self.videodb_tool.upload(
                output_path, source_type="file_path", media_type="audio"
            )
            self.output_message.actions.append(
                f"Uploaded generated audio to VideoDB with Audio ID {media['id']}"
            )
            with open(os.path.abspath(output_path), "rb") as file:
                data_url = f"data:audio/mpeg;base64,{base64.b64encode(file.read()).decode('utf-8')}"
                text_content = TextContent(
                    agent_name=self.agent_name,
                    status=MsgStatus.success,
                    status_message="Here is your generated audio",
                    text=f"""Click <a href='{data_url}' download='{output_file_name}' target='_blank'>here</a> to download the audio
                    """,
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

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Audio generated successfully, Generated Media audio id : {media['id']}",
            data={"audio_id": media["id"]},
        )
