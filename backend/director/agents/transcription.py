import logging
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import TextContent, MsgStatus
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)

class TranscriptionAgent(BaseAgent):
    def __init__(self, session=None, **kwargs):
        self.agent_name = "transcription"
        self.description = (
            "This is an agent to get transcripts of videos"
        )
        self.parameters = self.get_parameters()
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
        self.output_message.actions.append("Trying to get the video transcription..")
        output_text_content = TextContent(
            agent_name=self.agent_name,
            status_message="Processing the transcription..",
        )
        self.output_message.content.append(output_text_content)
        self.output_message.push_update()

        videodb_tool = VideoDBTool(collection_id=collection_id)
        video_info = videodb_tool.get_video(video_id)
        video_length = int(video_info["length"]) 

        try:
            transcript_text = videodb_tool.get_transcript(video_id)
        except Exception:
            logger.error("Transcript not found. Indexing spoken words..")
            self.output_message.actions.append("Indexing spoken words..")
            self.output_message.push_update()
            videodb_tool.index_spoken_words(video_id)
            transcript_text = videodb_tool.get_transcript(video_id)

        if timestamp_mode:
            self.output_message.actions.append("Formatting transcript with timestamps..")
            transcript_data = videodb_tool.get_transcript(video_id, text=False)
            output_text = self._group_transcript_with_timestamps(transcript_data, time_range, video_length)
        else:
            output_text = transcript_text

        output_text_content.text = output_text
        output_text_content.status = MsgStatus.success
        output_text_content.status_message = "Here is your transcription."
        self.output_message.publish()

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Transcription successful.",
            data={"video_id": video_id, "transcript": output_text},
        )
    
    def _group_transcript_with_timestamps(self, transcript_data: list, time_range: int, video_length: int) -> str:
        """
        Group transcript data into specified time ranges with timestamps.

        :param list transcript_data: List of dictionaries containing transcription details.
        :param int time_range: Time range for grouping in minutes (default: 2 minutes).
        :return: Grouped transcript with timestamps.
        :rtype: str
        """
        grouped_transcript = []
        current_start_time = 0
        current_end_time = time_range * 60
        current_text = []

        for entry in transcript_data:
            start_time = int(entry.get("start", 0))
            text = entry.get("text", "").strip()


            if start_time < current_end_time:
                current_text.append(text)
            else:
                actual_end_time = min(current_end_time, video_length)
                timestamp = f"[{current_start_time // 60:02d}:{current_start_time % 60:02d} - {actual_end_time // 60:02d}:{actual_end_time % 60:02d}]"
                grouped_transcript.append(f"{timestamp} {' '.join(current_text).strip()}\n")
                current_start_time = current_end_time
                current_end_time += time_range * 60
                current_text = [text]
                
        if current_text:
            actual_end_time = min(current_end_time, video_length)
            timestamp = f"[{current_start_time // 60:02d}:{current_start_time % 60:02d} - {actual_end_time // 60:02d}:{actual_end_time % 60:02d}]"
            grouped_transcript.append(f"{timestamp} {' '.join(current_text).strip()}\n")

        return "\n".join(grouped_transcript).replace(" - ", " ")
