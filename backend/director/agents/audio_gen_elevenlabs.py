import logging
import json
import os
import uuid

from elevenlabs.client import ElevenLabs

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)

ELEVENLABS_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "The unique identifier of the collection to store the audio",
        },
        "job_type": {
            "type": "string",
            "enum": ["text_to_speech", "sound_effect", "speech_to_speech"],
            "description": """The type of audio generation to perform
            text_to_speech: 
                - converts text to speech
                - input: text, voice_id
                - output: will be a videodb audio
            sound_effect: 
                - creates a sound effect from a text prompt
                - input: prompt, duration
                - output: will be a videodb audio
            speech_to_speech: 
                - can be used to dub audio or video from one voice to another
                - input: can be videodb audio or videodb vide
                - output: will be a videodb audio
            audio_isolation: 
                - removes the bg noise from media
                - input: can be videodb audio or videodb video, 
                - output: will be a videodb audio
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
                "voice_id": {
                    "type": "string",
                    "description": "The ID of the voice to use for speech generation",
                },
            },
            "required": ["text"],
        },
        "speech_to_speech": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "The ID (videodb audio or videodb video) of the media to convert to speech",
                },
                "type": {
                    "type": "string",
                    "enum": ["audio", "video"],
                    "description": "If passed media_id is a video, then type should be video, else audio",
                },
                "voice_id": {
                    "type": "string",
                    "description": "The ID of the voice to use for speech generation (only used if is_sound_effect is false)",
                },
            },
            "required": ["media_id"],
        },
        "audio_isolation": {
            "type": "object",
            "properties": {
                "media_id": {
                    "type": "string",
                    "description": "The ID (videodb audio or videodb video) of the media whose audio needs to be isolated",
                },
                "type": {
                    "type": "string",
                    "enum": ["audio", "video"],
                    "description": "If passed media_id is a video, then type should be video, else audio",
                },
            },
            "required": ["media_id"],
        },
    },
    "required": ["type", "collection_id"],
}


class ElevenLabsAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "audio_gen_elevenlabs"
        self.description = (
            "An agent designed to generate speech and sound effects using ElevenLabs AI"
        )
        self.parameters = ELEVENLABS_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        job_type: str,
        collection_id: str,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Generates audio using ElevenLabs API based on input text.

        :param str text: The text to convert to speech or sound effect
        :param str collection_id: The collection ID to store the generated audio
        :param bool is_sound_effect: Whether to generate sound effect or speech
        :param str voice_id: Voice ID for speech generation (optional)
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: Response containing the generated audio URL
        :rtype: AgentResponse
        """
        try:
            elevenlabs = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            directory_path = os.path.abspath("director/editing_assets")
            os.makedirs(directory_path, exist_ok=True)
            file_name = str(uuid.uuid4()) + ".mp3"
            output_path = os.path.join(directory_path, file_name)
            if job_type == "sound_effect":
                self.output_message.actions.append(
                    "Generating sound effect from text description"
                )
                self.output_message.push_update()
                args = kwargs.get("sound_effect", {})
                result = elevenlabs.text_to_sound_effects.convert(
                    text=args.get("prompt"),
                    duration_seconds=args.get("duration"),
                    prompt_influence=0.3,
                )
            elif job_type == "text_to_speech":
                self.output_message.actions.append("Converting text to speech")
                self.output_message.push_update()
                args = kwargs.get("text_to_speech", {})
                print("we got args", args)
            elif job_type == "speech_to_speech":
                self.output_message.actions.append("Generating speech to speech")
                self.output_message.push_update()
                args = kwargs.get("speech_to_speech", {})
                print("we got args", args)
            elif job_type == "audio_isolation":
                self.output_message.actions.append("🧹 Cleaning up the media ")
                self.output_message.push_update()
                args = kwargs.get("audio_isolation", {})
                media_id = args.get("media_id")
                media_type = args.get("type")
                if media_type == "video":
                    media = self.videodb_tool.get_video(media_id)
                    result = self.videodb_tool.download(media.get("stream_url"))
                    print("this is result ", result)
                else:
                    print("Not supported")
                    # media = self.videodb_tool.get_audio(media_id)
                    # result = self.videodb_tool.download(media.get("stream_url"))
            with open(output_path, "wb") as f:
                for chunk in result:
                    f.write(chunk)
            media = self.videodb_tool.upload(
                output_path, source_type="file_path", media_type="audio"
            )
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Audio generated successfully",
            data={"audio_id": media["id"]},
        )
