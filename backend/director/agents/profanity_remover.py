import json
import logging
import os

from videodb.asset import VideoAsset, AudioAsset

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    MsgStatus,
    VideoContent,
    VideoData,
    ContextMessage,
    RoleTypes,
)
from director.llm import get_default_llm
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)

BEEP_AUDIO_ID = os.getenv("BEEP_AUDIO_ID")
PROFANITY_FINDER_PROMPT = """
Given the following transcript give the list of timestamps where profanity is there for censoring.
Expected output format is json like {"timestamps": [(start, end), (start, end)]} where start and end are integer in seconds
"""


class ProfanityRemoverAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "profanity_remover"
        self.description = (
            "This agent beep the profanities in the given video and return the updated video stream."
            "if user has not given those optional param of beep_audio_id  send it as `None` so defaults are picked from env"
        )
        self.parameters = self.get_parameters()
        self.llm = get_default_llm()
        super().__init__(session=session, **kwargs)

    def add_beep(self, videodb_tool, video_id, beep_audio_id, timestamps):
        timeline = videodb_tool.get_and_set_timeline()
        video_asset = VideoAsset(asset_id=video_id)
        timeline.add_inline(video_asset)
        for start, _ in timestamps:
            beep = AudioAsset(asset_id=beep_audio_id)
            timeline.add_overlay(start=start, asset=beep)
        stream_url = timeline.generate_stream()
        return stream_url

    def run(
        self,
        collection_id: str,
        video_id: str,
        beep_audio_id: str = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Process the video to remove the profanities by overlaying beep.

        :param str collection_id: collection id in which the source video is present.
        :param str video_id: video_id on which profanity remover needs to run.
        :param str beep_audio_id: audio id of beep asset in videodb, defaults to BEEP_AUDIO_ID
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about the sample processing operation.
        :rtype: AgentResponse
        """
        try:
            beep_audio_id = beep_audio_id or BEEP_AUDIO_ID
            if not beep_audio_id:
                error_message = (
                    "Please provide the beep_audio_id, or set up BEEP_AUDIO_ID in the .env file located in the backend directory."
                    "Notify user this verbatum in summary as well since it isn't displayed to them: If you don’t have a beep sound ready, you can use the audio from https://www.youtube.com/watch?v=GvXbEO5Kbgc YouTube link. Upload it as audio, obtain the audio ID, and set it as BEEP_AUDIO_ID in your .env file.'"
                    "Remember to add above line in summary."
                )
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message=error_message,
                )
            self.output_message.actions.append("Started process to remove profanity..")
            video_content = VideoContent(
                agent_name=self.agent_name, status=MsgStatus.progress
            )
            video_content.status_message = "Generating clean stream.."
            self.output_message.push_update()
            videodb_tool = VideoDBTool(collection_id=collection_id)
            try:
                transcript = videodb_tool.get_transcript(video_id, text=False)
            except Exception:
                logger.error("Failed to get transcript, indexing")
                self.output_message.actions.append("Indexing the video..")
                self.output_message.push_update()
                videodb_tool.index_spoken_words(video_id)
                transcript = videodb_tool.get_transcript(video_id, text=False)
            profanity_prompt = f"{PROFANITY_FINDER_PROMPT}\n\ntranscript: {transcript}"
            profanity_llm_message = ContextMessage(
                content=profanity_prompt,
                role=RoleTypes.user,
            )
            llm_response = self.llm.chat_completions(
                [profanity_llm_message.to_llm_msg()],
                response_format={"type": "json_object"},
            )
            profanity_timeline_response = json.loads(llm_response.content)
            profanity_timeline = profanity_timeline_response.get("timestamps")
            clean_stream = self.add_beep(
                videodb_tool, video_id, beep_audio_id, profanity_timeline
            )
            video_content.video = VideoData(stream_url=clean_stream)
            video_content.status = MsgStatus.success
            video_content.status_message = "Here is the clean stream"
            self.output_message.content.append(video_content)
            self.output_message.publish()
        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            video_content.status = MsgStatus.error
            video_content.status_message = "Failed to generate clean stream"
            self.output_message.publish()
            error_message = f"Error in generating the clean stream due to {e}."
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Agent {self.name} completed successfully.",
            data={"stream_url": clean_stream},
        )
