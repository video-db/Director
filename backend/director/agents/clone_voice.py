import logging
import os
import requests
import uuid
import base64
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, MsgStatus, TextContent
from director.tools.elevenlabs import ElevenLabsTool
from director.tools.videodb_tool import VideoDBTool
from director.constants import DOWNLOADS_PATH

logger = logging.getLogger(__name__)

CLONE_VOICE_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "audio_source": {
            "type": "object",
            "properties": {
                "audio_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "A direct URL to the audio file to clone the voice from."
                },
                "video_id": {
                    "type": "string",
                    "description": "ID of the video from which the audio should be extracted."
                }, 
                "start_time": {
                    "type": "number",
                    "description": "The start time (in seconds)."
                },
                "end_time": {
                    "type": "number",
                    "description": "The end time (in seconds)."
                },
                "collection_id": {
                    "type": "string",
                    "description": "ID of the collection where the sample video is stored."
                }
            },
            "required": [],
            "description": "Provide either an audio URL or a video ID, but not both. If video_id is provided, collection_id is required."
        },
        "text_to_synthesis": {
            "type": "string",
            "description": "The text which the user wants to convert into audio in the given voice.",
        },
        "name_of_voice": {
            "type": "string",
            "description": "The name to give to the voice.",
        },
        "description": {
            "type": "string",
            "description": "Description of how the voice sounds, e.g., 'old person', 'childlike and cute', etc."
        },
        "is_authorized_to_clone_voice": {
            "type": "boolean",
            "description": "This is a flag to check if the user is authorised to clone the voice or not. If the user has explicitly mentioned that they are authorised to clone the voice, then the flag is TRUE else FALSE. Make sure to confirm that the user is authorised or not. If not specified explicitly or not specified at all, the flag should be FALSE"
        },
        "cloned_voice_id": {
            "type": "string",
            "description": "This is the ID of the voice which is present if the user has already cloned a voice before. The cloned_voice_id can be taken from the previous results of cloning if the audio URL is not changed"
        },
        "collection_id": {
            "type": "string",
            "description": "the ID of the collection to store the output audio file",
        }
    },
    "required": ["audio_source", "text_to_synthesis", "is_authorized_to_clone_voice", "collection_id", "name_of_voice"],
}

class CloneVoiceAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "clone_voice"
        self.description = "This agent is used to clone the voice of the given by the user. The user must be authorised to clone the voice"
        self.parameters = CLONE_VOICE_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)
        

    def _download_audio_file(self, audio_url: str) -> str | None:
        os.makedirs(DOWNLOADS_PATH, exist_ok=True)
        try:
            self.output_message.actions.append("Downloading sample audio URL")
            self.output_message.push_update()
            response = requests.get(audio_url, stream=True)
            response.raise_for_status()

            if not response.headers.get('Content-Type', '').startswith('audio'):
                raise ValueError(f"The URL does not point to an MP3 file: {audio_url}")

            download_file_name = f"audio_clone_voice_download_{str(uuid.uuid4())}.mp3"
            local_path = os.path.join(DOWNLOADS_PATH, download_file_name)

            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return local_path
        except Exception as e:
            logger.error(f"Failed to download {audio_url}: {e}")
            return None
        
    def _download_video_file(self, video_url: str) -> str | None:
        os.makedirs(DOWNLOADS_PATH, exist_ok=True)

        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()

            if not response.headers.get('Content-Type', '').startswith('video'):
                raise ValueError(f"The URL does not point to a video file: {video_url}")

            download_file_name = f"video_download_{str(uuid.uuid4())}.mp4"
            local_path = os.path.join(DOWNLOADS_PATH, download_file_name)

            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=65536):
                    file.write(chunk)

            return local_path

        except Exception as e:
            print(f"Failed to download {video_url}: {e}")
            return None
        
    def _download_audio_from_video(self, audio_source: dict) -> str | None:
        required_keys = {"video_id", "collection_id", "start_time", "end_time"}
        if not isinstance(audio_source, dict) or not required_keys.issubset(audio_source.keys()):
            return None
        video_id = audio_source["video_id"]
        collection_id = audio_source["collection_id"]
        start_time = audio_source.get("start_time", 0)
        end_time =  audio_source.get("end_time", 90)
        try:
            videodb_tool = VideoDBTool(collection_id)
            self.output_message.actions.append("Generating the video stream for the sample")
            self.output_message.push_update()
            video_stream = videodb_tool.generate_video_stream(video_id, [(start_time, end_time)])
            download_response = videodb_tool.download(video_stream)
            download_url = download_response["download_url"]
            video_path = self._download_video_file(download_url)
            if not video_path:
                return None
            self.output_message.actions.append("Extracting the audio from the sample video")
            self.output_message.push_update()
            uploaded_audio = videodb_tool.upload(source=video_path, source_type="file_path", media_type="audio")
            audio = videodb_tool.get_audio(uploaded_audio["id"])
            audio_url = audio["url"]

            response = requests.get(audio_url, stream=True)
            response.raise_for_status()

            download_file_name = f"audio_clone_voice_download_{str(uuid.uuid4())}.mp3"
            local_path = os.path.join(DOWNLOADS_PATH, download_file_name)

            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return local_path
        except Exception as e:
            logger.error(f"Failed to download audio from video: {e}")
            return None

    def validate_audio_source(self, audio_source: dict):
        """Ensure that either 'audio_url' or 'video_id' is provided, but not both."""
        has_audio_url = "audio_url" in audio_source and bool(audio_source["audio_url"])
        has_video_id = "video_id" in audio_source and bool(audio_source["video_id"])

        if has_audio_url and has_video_id:
            raise ValueError("Provide either 'audio_url' or 'video_id', but not both.")

        if not has_audio_url and not has_video_id:
            raise ValueError("Either 'audio_url' or 'video_id' must be provided.")

        if has_video_id:
            audio_source.setdefault("start_time", 0)
            audio_source.setdefault("end_time", 90)
            if "collection_id" not in audio_source:
                raise ValueError("'collection_id' is required when using 'video_id'.")

        return audio_source

    def run(
            self,
            audio_source: dict,
            text_to_synthesis: str,
            name_of_voice: str,
            is_authorized_to_clone_voice: bool,
            collection_id: str = "default",
            description="",
            cloned_voice_id=None,
            *args, 
            **kwargs) -> AgentResponse:
        """
        Clone the given audio file and synthesis the given text

        :param list sample_audios: The urls of the video given to clone
        :param str text_to_synthesis: The given text which needs to be synthesised in the cloned voice
        :param bool is_authorized_to_clone_voice: The flag which tells whether the user is authorised to clone the audio or not
        :param str name_of_voice: The name to be given to the cloned voice
        :param str descrption: The description about how the voice sounds like
        :param str collection_id: The collection id to store generated voice
        :param str cloned_voice_id: The voice ID generated from the previously given voice which can be used for cloning
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about voice cloning.
        :rtype: AgentResponse
        """
        try:
            if not is_authorized_to_clone_voice:
                return AgentResponse(status=AgentStatus.ERROR, message="Not authorised to clone the voice")
            
            audio_source = self.validate_audio_source(audio_source)

            ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
            if not ELEVENLABS_API_KEY:
                    raise Exception("Elevenlabs API key not present in .env")
            
            audio_gen_tool = ElevenLabsTool(api_key=ELEVENLABS_API_KEY)
            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            if "audio_url" in audio_source:
                sample_file = self._download_audio_file(audio_source["audio_url"])
            
            if "video_id" in audio_source:
                sample_file = self._download_audio_from_video(audio_source)

            if not sample_file:
                return AgentResponse(status=AgentStatus.ERROR, message="Could'nt process the sample audios")

            if cloned_voice_id:
                self.output_message.actions.append("Using previously generated cloned voice")
                self.output_message.push_update()
                voice = audio_gen_tool.get_voice(voice_id=cloned_voice_id)
            else:
                self.output_message.actions.append("Cloning the voice")
                self.output_message.push_update()
                voice = audio_gen_tool.clone_audio(audio_files=[sample_file], name_of_voice=name_of_voice, description=description)

            if not voice:
                return AgentResponse(status=AgentStatus.ERROR, message="Failed to generate the voice clone")
            
            self.output_message.actions.append("Synthesising the given text")
            self.output_message.push_update()

            synthesised_audio = audio_gen_tool.synthesis_text(voice=voice, text_to_synthesis=text_to_synthesis)
            
            if not synthesised_audio:
                return AgentResponse(status=AgentStatus.ERROR, message="Failed to generate the voice clone")

            output_file_name = f"audio_clone_voice_output_{str(uuid.uuid4())}.mp3"
            output_path = f"{DOWNLOADS_PATH}/{output_file_name}"

            with open(output_path, "wb") as f:
                for chunk in synthesised_audio:
                    if chunk:
                        f.write(chunk)

            self.output_message.actions.append(
                f"Generated audio saved at <i>{output_path}</i>"
            )
            self.output_message.push_update()

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

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message=f"Agent {self.name} completed successfully.",
                data={
                    "cloned_voice_id": voice.voice_id,
                    "audio_id": media["id"]
                }
            )
        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            text_content = TextContent(
                agent_name=self.agent_name,
                status=MsgStatus.error,
                status_message="Failed to generate audio",
            )
            self.output_message.content.append(text_content)
            self.output_message.push_update()
            self.output_message.publish()
            error_message = f"Agent failed with error {e}"
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)
