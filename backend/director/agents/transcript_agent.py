import logging
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import TextContent, MsgStatus
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)

class VideoTranscriptionAgent(BaseAgent):
    def __init__(self, session=None, **kwargs):
        self.agent_name = "video_transcription"
        self.description = (
            "This is an agent to get transcripts of videos"
        )
        super().__init__(session=session, **kwargs)

    def run(self, collection_id: str, video_id: str, timestamp_mode: bool = False, time_range: int = 2) -> AgentResponse:
        """
        Transcribe a video and optionally format it with timestamps.

        :param str collection_id: The collection_id where given video_id is available.
        :param str video_id: The id of the video for which the transcription is required.
        :param bool timestamp_mode: Whether to include timestamps in the transcript.
        :param int time_range: Time range for grouping transcripts in minutes (default: 2 minutes).
        :return: AgentResponse with the transcription result.
        :rtype: AgentResponse
        """
        self.output_message.actions.append("Starting video transcription...")
        output_text_content = TextContent(
            agent_name=self.agent_name,
            status_message="Processing the transcription...",
        )
        self.output_message.content.append(output_text_content)
        self.output_message.push_update()

        videodb_tool = VideoDBTool(collection_id=collection_id)

        try:
            transcript_text = videodb_tool.get_transcript(video_id)
        except Exception:
            logger.error("Transcript not found. Indexing spoken words...")
            self.output_message.actions.append("Indexing spoken words...")
            self.output_message.push_update()
            videodb_tool.index_spoken_words(video_id)
            transcript_text = videodb_tool.get_transcript(video_id)

        if timestamp_mode:
            self.output_message.actions.append("Formatting transcript with timestamps...")
            grouped_transcript = self._group_transcript_with_timestamps(
                transcript_text, time_range
            )
            output_text = grouped_transcript
        else:
            output_text = transcript_text

        output_text_content.text = output_text
        output_text_content.status = MsgStatus.success
        output_text_content.status_message = "Transcription completed successfully."
        self.output_message.publish()

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Transcription successful.",
            data={"video_id": video_id, "transcript": output_text},
        )
    
    def _group_transcript_with_timestamps(self, transcript_text: str, time_range: int) -> str:
        """
        Group transcript into specified time ranges with timestamps.

        :param str transcript_text: The raw transcript text.
        :param int time_range: Time range for grouping in minutes.
        :return: Grouped transcript with timestamps.
        :rtype: str
        """
        lines = transcript_text.split("\n")
        grouped_transcript = []
        current_time = 0

        for i, line in enumerate(lines):
            if i % time_range == 0 and line.strip():
                timestamp = f"[{current_time:02d}:00 - {current_time + time_range:02d}:00]"
                grouped_transcript.append(f"{timestamp} {line.strip()}")
                current_time += time_range

        return "\n".join(grouped_transcript)
