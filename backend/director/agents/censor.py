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
DEFAULT_CENSOR_PROMPT = """
Given the following transcript give the list of timestamps where profanity is there for censoring.
"""
OUTPUT_PROMPT = """
Expected output format is json like {"timestamps": [(start, end), (start, end)]} where start and end are float in seconds
"""


class CensorAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "censor"
        # TODO: When audios are added in context rework in description will be needed to make sure that the existing beep id is being passed
        self.description = (
            "This agent beeps the profanities in the given video and returns the updated video stream. "
            "Take the `beep_audio_id` from the context, if no beep audio found send it as `None` so defaults are picked from the environment."
        )
        self.parameters = self.get_parameters()
        self.llm = get_default_llm()
        super().__init__(session=session, **kwargs)

    def add_beep(
        self, videodb_tool, video_id, beep_audio_id, beep_audio_length, timestamps
    ):
        beep_audio_length = float(beep_audio_length)
        timeline = videodb_tool.get_and_set_timeline()
        video_asset = VideoAsset(asset_id=video_id)
        timeline.add_inline(video_asset)
        for start, end in timestamps:
            # NOTES: when words are very small (sub seconds) we need to add some padding
            # Taking min with audio will make sure that we don't overflow
            buffered_start = start - 0.4
            buffered_end = end + 0.4
            length = min(beep_audio_length, (buffered_end - buffered_start))
            beep = AudioAsset(asset_id=beep_audio_id, end=length)
            # Slight adjustment to land on the word
            # TODO: Check if it can be handled in a better / dynamic way
            adjusted_start = start - 0.4
            timeline.add_overlay(start=adjusted_start, asset=beep)
        stream_url = timeline.generate_stream()
        return stream_url

    def run(
        self,
        collection_id: str,
        video_id: str,
        beep_audio_id: str = None,
        censor_prompt: str = "",
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Process the video to remove the profanities by overlaying beep.

        :param str collection_id: collection id in which the source video is present.
        :param str video_id: video_id on which adding censor needs to run.
        :param str beep_audio_id: audio id of beep asset in videodb, defaults to BEEP_AUDIO_ID
        :param str censor_prompt: direction by users on what to censor
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about the sample processing operation.
        :rtype: AgentResponse
        """
        try:
            video_content = VideoContent(
                agent_name=self.agent_name, status=MsgStatus.progress
            )
            video_content.status_message = "Generating clean stream.."
            self.output_message.actions.append("Started process to censor..")
            self.output_message.push_update()
            videodb_tool = VideoDBTool(collection_id=collection_id)
            beep_audio_id = beep_audio_id or BEEP_AUDIO_ID
            if not beep_audio_id:
                self.output_message.actions.append(
                    "Beep audio ID not passed, finding in the collection.."
                )
                self.output_message.push_update()
                # Find beep in the users context
                # TODO: This can be better by passing the context to LLM to find the auido ID
                audios = videodb_tool.get_audios()
                for audio in audios:
                    if "beep" in audio.get("name", "").lower():
                        beep_audio_id = audio.get("id")
                        beep_audio_length = audio.get("length")
                        self.output_message.actions.append(
                            "Found existing beep in the collection."
                        )
                        self.output_message.push_update()
                        break
                else:
                    # Upload if not found
                    self.output_message.actions.append(
                        "Couldn't find beep in the collection, uploading.."
                    )
                    self.output_message.push_update()
                    beep_audio = videodb_tool.upload(
                        "https://www.youtube.com/watch?v=GvXbEO5Kbgc",
                        media_type="audio",
                        name="beep",
                    )
                    beep_audio_id = beep_audio.get("id")
                    beep_audio_length = beep_audio.get("length")
            else:
                beep_audio = videodb_tool.get_audio(beep_audio_id)
                beep_audio_id = beep_audio.get("id")
                beep_audio_length = beep_audio.get("length")
            try:
                transcript = videodb_tool.get_transcript(video_id, text=False)
            except Exception:
                logger.error("Failed to get transcript, indexing")
                self.output_message.actions.append("Indexing the video..")
                self.output_message.push_update()
                videodb_tool.index_spoken_words(video_id)
                transcript = videodb_tool.get_transcript(video_id, text=False)
            if not censor_prompt:
                censor_prompt = DEFAULT_CENSOR_PROMPT
            self.output_message.actions.append(
                f"Censoring the video with prompt: '{censor_prompt[:1000]}..'"
            )
            self.output_message.push_update()
            final_censor_prompt = (
                f"{censor_prompt}{OUTPUT_PROMPT}\n\ntranscript: {transcript}"
            )
            censor_llm_message = ContextMessage(
                content=final_censor_prompt,
                role=RoleTypes.user,
            )
            llm_response = self.llm.chat_completions(
                [censor_llm_message.to_llm_msg()],
                response_format={"type": "json_object"},
            )
            censor_timeline_response = json.loads(llm_response.content)
            censor_timeline = censor_timeline_response.get("timestamps")
            clean_stream = self.add_beep(
                videodb_tool,
                video_id,
                beep_audio_id,
                beep_audio_length,
                censor_timeline,
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
