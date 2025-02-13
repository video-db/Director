import logging
import os
import requests
import uuid
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, MsgStatus, TextContent, VideoContent, VideoData
from director.tools.elevenlabs import ElevenLabsTool
from director.tools.videodb_tool import VideoDBTool
from director.constants import DOWNLOADS_PATH
from videodb.asset import VideoAsset, AudioAsset
from videodb.timeline import Timeline
logger = logging.getLogger(__name__)

VOICE_REPLACEMENT_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "sample_audios": {
            "type": "array",
            "description": "List of audio file URLs provided by the user to clone",
            "items": {
                "type": "string",
                "description": "The URL of the audio file"
            }
        },
        "name_of_voice" : {
            "type": "string",
            "description": "The name to give to the voice. This can be the user's name",
        },
        "description" : {
            "type": "string",
            "description": "Description about how the voice sounds like. For example: This is a sounds of an old person, the voice is child like and cute etc."
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
        },
        "video_id": {
            "type": "string",
            "description": "The ID of the video on which the cloned voice will be added"
        }
    },
    "required": ["sample_audios", "is_authorized_to_clone_voice", "collection_id", "video_id", "name_of_voice"],
}

class VoiceReplacementAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "voice_replacement"
        self.description = "This agent is used to clone the voice of the given by the user and overlay it on top of the video given. The user must be authorised to clone the voice"
        self.parameters = VOICE_REPLACEMENT_AGENT_PARAMETERS
        self.timeline: Timeline | None = None
        super().__init__(session=session, **kwargs)
        

    def _download_audio_files(self, audio_urls: list[str]) -> list[str]:

        os.makedirs(DOWNLOADS_PATH, exist_ok=True)
        downloaded_files = []

        for audio_url in audio_urls:
            try:
                response = requests.get(audio_url, stream=True)
                response.raise_for_status()

                if not response.headers.get('Content-Type', '').startswith('audio'):
                    raise ValueError(f"The URL does not point to an MP3 file: {audio_url}")

                download_file_name = f"audio_clone_voice_download_{str(uuid.uuid4())}.mp3"
                local_path = os.path.join(DOWNLOADS_PATH, download_file_name)

                with open(local_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)

                downloaded_files.append(local_path)
            except Exception as e:
                print(f"Failed to download {audio_url}: {e}")

        return downloaded_files
    
    def _get_transcript(self, video_id):
        self.output_message.actions.append("Retrieving video transcript..")
        self.output_message.push_update()
        try:
            return self.videodb_tool.get_transcript(video_id)
        except Exception:
            self.output_message.actions.append(
                "Transcript unavailable. Indexing spoken content."
            )
            self.output_message.push_update()
            self.videodb_tool.index_spoken_words(video_id)
            return self.videodb_tool.get_transcript(video_id)

    def _generate_overlay(self, video_id, audio_id):

        if self.timeline is None:
            return None

        self.timeline.add_inline(VideoAsset(video_id))
        self.timeline.add_overlay(start=0, asset=AudioAsset(audio_id))

        stream = self.timeline.generate_stream()
        return stream

    def run(
            self,
            sample_audios: list[str],
            video_id: str,
            name_of_voice: str,
            is_authorized_to_clone_voice: bool,
            collection_id: str,
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

            ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
            if not ELEVENLABS_API_KEY:
                    raise Exception("Elevenlabs API key not present in .env")
            
            audio_gen_tool = ElevenLabsTool(api_key=ELEVENLABS_API_KEY)
            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            sample_files = self._download_audio_files(sample_audios)

            if not sample_files:
                return AgentResponse(status=AgentStatus.ERROR, message="Could'nt process the sample audios")

            if cloned_voice_id:
                self.output_message.actions.append("Using previously generated cloned voice")
                self.output_message.push_update()
                voice = audio_gen_tool.get_voice(voice_id=cloned_voice_id)
            else:
                self.output_message.actions.append("Cloning the voice")
                self.output_message.push_update()
                voice = audio_gen_tool.clone_audio(audio_files=sample_files, name_of_voice=name_of_voice, description=description)

            if not voice:
                return AgentResponse(status=AgentStatus.ERROR, message="Failed to generate the voice clone")

            text_to_synthesis = self._get_transcript(video_id=video_id)

            self.output_message.actions.append("Synthesising the transcript in cloned voice")
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


            audio = self.videodb_tool.upload(
                output_path, source_type="file_path", media_type="audio"
            )

            video_content = VideoContent(
                status=MsgStatus.progress,
                status_message="Adding cloned voice to the video",
                agent_name=self.agent_name
            )

            self.output_message.content.append(video_content)
            self.output_message.push_update()


            self.timeline = self.videodb_tool.get_and_set_timeline()

            stream_url = self._generate_overlay(video_id, audio_id=audio['id'])

            video_content.video = VideoData(stream_url=stream_url)
            video_content.status = MsgStatus.success
            video_content.status_message = "Here is your video with the cloned voice"

            self.output_message.push_update()
            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message=f"Agent {self.name} completed successfully.",
                data={
                    "cloned_voice_id": voice.voice_id,
                    "audio_id": audio["id"]
                }
            )
        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            text_content = TextContent(
                agent_name=self.agent_name,
                status=MsgStatus.error,
                status_message="Failed to generate the final video",
            )
            self.output_message.content.append(text_content)
            self.output_message.push_update()
            self.output_message.publish()
            error_message = f"Agent failed with error {e}"
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)
