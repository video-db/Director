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
        "sample_video": {
            "type": "object",
            "properties": {
                "video_id": {
                    "type": "string",
                    "description": "The video id from which the 1 and a half minute sample audio has to be taken",
                }, 
                "start_time": {
                    "type": "number",
                    "description": "The start time from where the 1 and a half minute. start time is given in seconds that is 1 minute 37 seconds is 97",
                    "default": 0
                },
                "end_time": {
                    "type": "number",
                    "description": "The end time is where the extracted audio sample must end. Make sure that the end time is farther than start time and should only be 1 to 2 minutes farther than start_time. end time is given in seconds. for example 1 minute 37 seconds is 97",
                    "default": 90
                }

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
        "video_ids": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "A list of IDs of videos which needs to be overlayed"
        }
    },
    "required": ["sample_video", "is_authorized_to_clone_voice", "collection_id", "video_ids", "name_of_voice"],
}

class VoiceReplacementAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "voice_replacement"
        self.description = "This agent is used to clone the voice of the given by the user and overlay it on top of all the videos given. The user must be authorised to clone the voice. This agent can handle multiple agents at once"
        self.parameters = VOICE_REPLACEMENT_AGENT_PARAMETERS
        self.timeline: Timeline | None = None
        super().__init__(session=session, **kwargs)
        

    def _download_video_file(self, video_url: str) -> str:

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
        
    def _download_audio_file(self, audio_url: str) -> str:

        os.makedirs(DOWNLOADS_PATH, exist_ok=True)

        try:

            response = requests.get(audio_url, stream=True)
            response.raise_for_status()


            download_file_name = f"audio_url_{str(uuid.uuid4())}.mp3"
            local_path = os.path.join(DOWNLOADS_PATH, download_file_name)

            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=65536):
                    file.write(chunk)

            return local_path

        except Exception as e:
            logger.error(f"Failed to download {audio_url}: {e}")
            return None

    def _extract_audio_from_video(self, video_path: str):
        try:
            audio_uploaded = self.videodb_tool.upload(video_path, source_type="file_path", media_type="audio")
            audio = self.videodb_tool.get_audio(audio_id=audio_uploaded["id"])
            audio_path = self._download_audio_file(audio["url"])
            return audio_path
        
        except Exception as e:
            logger.error(f"Failed to download audio: {e}")
            return None

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
            sample_video,
            video_ids: list[str],
            name_of_voice: str,
            is_authorized_to_clone_voice: bool,
            collection_id: str,
            description="",
            cloned_voice_id=None,
            *args, 
            **kwargs) -> AgentResponse:
        """
        Clone the given audio file and synthesis the given text

        :param sample_video: An boject containing video_id and strt_time for taking sample
        :param str text_to_synthesis: The given text which needs to be synthesised in the cloned voice
        :param bool is_authorized_to_clone_voice: The flag which tells whether the user is authorised to clone the audio or not
        :param str name_of_voice: The name to be given to the cloned voice
        :param str descrption: The description about how the voice sounds like
        :param str collection_id: The collection id to store generated voice
        :param list[str] video_ids: The IDs of the videos from which we retrieve the transcript.
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


            self.output_message.actions.append("Getting the sample video's stream")
            self.output_message.push_update()
            stream_url = self.videodb_tool.generate_video_stream(sample_video["video_id"], [(sample_video.get("start_time", 0),sample_video.get("end_time", 90))]) 

            self.output_message.actions.append("Getting the sample video's download URL")
            self.output_message.push_update()
            download_response = self.videodb_tool.download(stream_url, name="audio_sample_video")
            if download_response.get("status") == "done":
                download_url = download_response.get("download_url")
            else:
                raise Exception("Couldn't find the video download url")
            
            self.output_message.actions.append("Downloading the sample video")
            self.output_message.push_update()
            video_path = self._download_video_file(download_url)

            if not video_path:
                raise Exception("Couldn't fetch the video for sampling")
            
            sample_audio = self._extract_audio_from_video(video_path=video_path)

            if not sample_audio:
                return AgentResponse(status=AgentStatus.ERROR, message="Could'nt process the sample audios")

            if cloned_voice_id:
                self.output_message.actions.append("Using previously generated cloned voice")
                self.output_message.push_update()
                voice = audio_gen_tool.get_voice(voice_id=cloned_voice_id)
            else:
                self.output_message.actions.append("Cloning the voice")
                self.output_message.push_update()
                voice = audio_gen_tool.clone_audio(audio_files=[sample_audio], name_of_voice=name_of_voice, description=description)

            if not voice:
                return AgentResponse(status=AgentStatus.ERROR, message="Failed to generate the voice clone")

            for video_id in video_ids:
                video = self.videodb_tool.get_video(video_id=video_id)
                text_to_synthesis = self._get_transcript(video_id=video_id)
                self.output_message.actions.append(f"Synthesising {video['name']}'s transcript in cloned voice")
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

                if not audio:
                    error_content = TextContent(
                        status=MsgStatus.progress,
                        status_message=f"Adding cloned voice to {video['name']} failed",
                        agent_name=self.agent_name
                    )
                    self.output_message.content.append(error_content)
                    self.output_message.push_update()
                    continue

                video_content = VideoContent(
                    status=MsgStatus.progress,
                    status_message=f"Adding cloned voice to {video['name']}",
                    agent_name=self.agent_name
                )

                self.output_message.content.append(video_content)
                self.output_message.push_update()


                self.timeline = self.videodb_tool.get_and_set_timeline()

                stream_url = self._generate_overlay(video_id, audio_id=audio['id'])

                video_content.video = VideoData(stream_url=stream_url)
                video_content.status = MsgStatus.success
                video_content.status_message = f"Here is your video {video['name']} with the cloned voice"

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
