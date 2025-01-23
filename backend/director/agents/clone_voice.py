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
        "audio_url": {
            "type": "string",
            "description": "URL of the audio file which consists of the user's voice or the voice which the user is authorised to clone",
        },
        "text_to_synthesis": {
            "type": "string",
            "description": "The text which the user wants to convert into audio in the voice given in the audio_url",
            "enum": ["url", "local_file"],
        },
        "is_authorized_to_clone_voice": {
            "type": "boolean",
            "description": "This is a flag to check if the user is authorised to clone the voice or not. If the user has explicitly mentioned that they are authorised to clone the voice, then the flag is TRUE else FALSE. Make sure to confirm that the user is authorised or not. If not specified explicitly or not specified at all, the flag should be FALSE"
        },
        "collection_id": {
            "type": "string",
            "description": "the ID of the collection to store the output audio file",
        }
    },
    "required": ["audio_url", "text_to_synthesis", "is_authorized_to_clone_voice", "collection_id"],
}

class CloneVoiceAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "clone_voice"
        self.description = "This agent is used to clone the voice of the given by the user. The user must be authorised to clone the voice"
        self.parameters = CLONE_VOICE_AGENT_PARAMETERS
        self.elevenlabs_tool = ElevenLabsTool(api_key=os.getenv("ELEVENLABS_API_KEY"))
        super().__init__(session=session, **kwargs)


    def _download_audio_file(self, audio_url:str, local_path:str):
        try:
            
            response = requests.get(audio_url, stream=True)
            response.raise_for_status()

            if 'audio/mpeg' not in response.headers.get('Content-Type', ''):
                raise ValueError("The URL does not point to an MP3 file.")

            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            return local_path

        except Exception as e:
            raise f"An error occurred while downloading the voice sample: {e}"
    def run(
            self, 
            audio_url: str, 
            text_to_synthesis: str,
            is_authorized_to_clone_voice: str,
            collection_id: str,
            *args, 
            **kwargs) -> AgentResponse:
        """
        Clone the given audio file and synthesis the given text

        :param str audio_url: The url of the video given to clone
        :param str text_to_synthesis: The given text which needs to be synthesised in the cloned voice
        :param bool is_authorized_to_clone_voice: The flag which tells whether the user is authorised to clone the audio or not
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about voice cloning.
        :rtype: AgentResponse
        """
        try:
            if not is_authorized_to_clone_voice:
                return AgentResponse(status=AgentStatus.ERROR, message="Not authorised to clone the voice")

            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            self.output_message.actions.append(
                    f"Cloning the voice"
                )
            self.output_message.push_update()

            os.makedirs(DOWNLOADS_PATH, exist_ok=True)
            download_file_name = f"audio_clone_voice_download_{str(uuid.uuid4())}.mp3"
            download_path = f"{DOWNLOADS_PATH}/{download_file_name}"

            self._download_audio_file(audio_url, local_path=download_path)

            voice = self.elevenlabs_tool.clone_audio(audio_url=download_path)

            if not voice:
                return AgentResponse(status=AgentStatus.ERROR, message="Failed to generate the voice clone")
            
            self.output_message.actions.append(
                    f"Synthesising the given text"
                )
            self.output_message.push_update()

            synthesised_audio = self.elevenlabs_tool.synthesis_text(voice=voice, text_to_synthesis=text_to_synthesis)
            
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
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Agent {self.name} completed successfully.",
            data={},
        )
