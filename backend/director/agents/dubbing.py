import logging
import os

from director.constants import DOWNLOADS_PATH

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, VideoContent, MsgStatus, VideoData
from director.tools.videodb_tool import VideoDBTool
from director.tools.elevenlabs import ElevenLabsTool

logger = logging.getLogger(__name__)

SUPPORTED_ENGINES = ["elevenlabs", "videodb"]
DUBBING_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "video_id": {
            "type": "string",
            "description": "The unique identifier of the video that needs to be dubbed. This ID is used to retrieve the video from the VideoDB collection.",
        },
        "target_language": {
            "type": "string",
            "description": "The target language for dubbing (e.g. 'Spanish', 'French', 'German'). The video's audio will be translated and dubbed into this language.",
        },
        "target_language_code": {
            "type": "string",
            "description": "The target language code for dubbing (e.g. 'es' for Spanish, 'fr' for French, 'de' for German').",
        },
        "collection_id": {
            "type": "string",
            "description": "The unique identifier of the VideoDB collection containing the video. Required to locate and access the correct video library.",
        },
        "engine": {
            "type": "string",
            "description": "The dubbing engine to use. Default is 'videodb'. Possible values include 'videodb' and 'elevenlabs'.",
            "default": "videodb",
            "enum": SUPPORTED_ENGINES,
        },
    },
    "required": [
        "video_id",
        "target_language",
        "target_language_code",
        "collection_id",
        "engine",
    ],
}


class DubbingAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "dubbing"
        self.description = (
            "This is an agent to dub the given video into a target language"
        )
        self.parameters = DUBBING_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        video_id: str,
        target_language: str,
        target_language_code: str,
        collection_id: str,
        engine: str,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Process the video dubbing based on the given video ID.
        :param str video_id: The ID of the video to process.
        :param str target_language: The target language name for dubbing (e.g. Spanish).
        :param str target_language_code: The target language code for dubbing (e.g. es).
        :param str collection_id: The ID of the collection to process.
        :param str engine: The dubbing engine to use. Default is 'elevenlabs'.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about the dubbing operation.
        :rtype: AgentResponse
        """
        try:
            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            # Get video audio file
            video = self.videodb_tool.get_video(video_id)
            if not video:
                raise Exception(f"Video {video_id} not found")

            if engine not in SUPPORTED_ENGINES:
                raise Exception(f"{engine} not supported")

            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Processing...",
            )
            self.output_message.content.append(video_content)
            self.output_message.push_update()

            if engine == "elevenlabs":
                self.output_message.actions.append("Downloading video")
                self.output_message.push_update()

                download_response = self.videodb_tool.download(video["stream_url"])

                os.makedirs(DOWNLOADS_PATH, exist_ok=True)
                dubbed_file_path = f"{DOWNLOADS_PATH}/{video_id}_dubbed.mp4"
                ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
                if not ELEVENLABS_API_KEY:
                    raise Exception("Elevenlabs API key not present in .env")
                elevenlabs_tool = ElevenLabsTool(api_key=ELEVENLABS_API_KEY)
                job_id = elevenlabs_tool.create_dub_job(
                    source_url=download_response["download_url"],
                    target_language=target_language_code,
                )
                self.output_message.actions.append(
                    f"Dubbing job initiated with Job ID: {job_id}"
                )
                self.output_message.push_update()

                self.output_message.actions.append(
                    "Waiting for dubbing process to complete.."
                )
                self.output_message.push_update()
                elevenlabs_tool.wait_for_dub_job(job_id)

                self.output_message.actions.append("Downloading dubbed video")
                self.output_message.push_update()
                elevenlabs_tool.download_dub_file(
                    job_id,
                    target_language_code,
                    dubbed_file_path,
                )

                self.output_message.actions.append(
                    f"Uploading dubbed video to VideoDB as '[Dubbed in {target_language}] {video['name']}'"
                )
                self.output_message.push_update()

                dubbed_video = self.videodb_tool.upload(
                    dubbed_file_path,
                    source_type="file_path",
                    media_type="video",
                    name=f"[Dubbed in {target_language}] {video['name']}",
                )
                if os.path.exists(dubbed_file_path):
                    os.remove(dubbed_file_path)
            else:
                self.output_message.actions.append("Dubbing job initiated")
                self.output_message.actions.append(
                    "Waiting for the dubbing process. It may take a few minutes to complete.."
                )
                self.output_message.push_update()

                dubbed_video = self.videodb_tool.dub_video(
                    video_id=video_id, language_code=target_language_code
                )

            video_content.video = VideoData(stream_url=dubbed_video["stream_url"])
            video_content.status = MsgStatus.success
            video_content.status_message = f"Dubbed video in {target_language} has been successfully added to your video. Here is your stream."
            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message=f"Successfully dubbed video '{video['name']}' to {target_language}",
                data={
                    "stream_url": dubbed_video["stream_url"],
                    "video_id": dubbed_video["id"],
                },
            )

        except Exception as e:
            video_content.status = MsgStatus.error
            video_content.status_message = "An error occurred while dubbing the video."
            self.output_message.publish()
            logger.exception(f"Error in {self.agent_name} agent: {str(e)}")
            return AgentResponse(
                status=AgentStatus.ERROR, message=f"Failed to dub video: {str(e)}"
            )
