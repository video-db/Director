import logging
import json
import os
import uuid


from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session
from director.tools.videodb_tool import VideoDBTool
from director.tools.elevenlabs import ElevenLabsTool


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
                "config": {
                    "type": "object",
                    "description": "Elevenlabs Config for the text to convert to speech, Pass default value as empty object if not provided",
                    "default": {},
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
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Generates audio using ElevenLabs API based on input text.
        :param str collection_id: The collection ID to store the generated audio
        :param job_type:
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

            os.makedirs(DOWNLOADS_PATH, exist_ok=True)
            output_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp3"

            if job_type == "sound_effect":
                self.output_message.actions.append(
                    "Generating sound effect from text description"
                )
                self.output_message.push_update()
                args = kwargs.get("sound_effect", {})
                audio_gen_tool.generate_sound_effect(
                    prompt=args.get("prompt"),
                    save_at=output_path,
                    duration=args.get("duration"),
                    config={
                        "prompt_influence": 0.8,
                    },
                )
            elif job_type == "text_to_speech":
                self.output_message.actions.append("Converting text to speech")
                self.output_message.push_update()
                args = kwargs.get("text_to_speech", {})
                audio_gen_tool.text_to_speech(
                    text=args.get("text"),
                    save_at=output_path,
                    config=args.get("config", {}),
                )

            self.output_message.actions.append(
                f"Uploading generated audio {output_path}"
            )
            self.output_message.push_update()
            media = self.videodb_tool.upload(
                output_path, source_type="file_path", media_type="audio"
            )
            self.output_message.actions.append(
                f"Uploaded generated audio with Audio ID : {media['id']}"
            )
            self.output_message.push_update()
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Audio generated successfully, Generated Media audio id : {media['id']}",
            data={"audio_id": media["id"]},
        )
