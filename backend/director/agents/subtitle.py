import logging
import textwrap

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    VideoContent,
    VideoData,
    MsgStatus,
)
from director.tools.videodb_tool import VideoDBTool

from videodb.asset import VideoAsset, TextAsset, TextStyle
from videodb.exceptions import InvalidRequestError

logger = logging.getLogger(__name__)

SUBTITLE_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "video_id": {
            "type": "string",
            "description": "The unique identifier of the video to which subtitles will be added.",
        },
        "collection_id": {
            "type": "string",
            "description": "The unique identifier of the collection containing the video.",
        },
        "language": {
            "type": "string",
            "description": 'The language the user wants the subtitles in. Use the full English name of the language (e.g., "English", "Spanish", "French", etc.)',
        },
        "notes": {
            "type": "string",
            "description": "if user has additional requirements for the style of language",
        },
    },
    "required": ["video_id", "collection_id"],
}


class SubtitleAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "subtitle"
        self.description = "An agent designed to add different languages subtitles to a specified video within VideoDB."
        self.parameters = SUBTITLE_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def wrap_text(self, text, video_width, max_width_percent=0.60, avg_char_width=20):
        max_width_pixels = video_width * max_width_percent
        max_chars_per_line = int(max_width_pixels / avg_char_width)

        # Wrap the text based on the calculated max characters per line
        wrapped_text = "\n".join(textwrap.wrap(text, max_chars_per_line))
        wrapped_text = wrapped_text.replace("'", "")
        return wrapped_text

    def add_subtitles_using_timeline(self, subtitles):
        video_width = 1920
        timeline = self.videodb_tool.get_and_set_timeline()
        video_asset = VideoAsset(asset_id=self.video_id)
        timeline.add_inline(video_asset)
        for subtitle_chunk in subtitles:
            start = round(subtitle_chunk["start"], 2)
            end = round(subtitle_chunk["end"], 2)
            duration = end - start

            wrapped_text = self.wrap_text(subtitle_chunk["text"], video_width)
            style = TextStyle(
                fontsize=20,
                fontcolor="white",
                box=True,
                boxcolor="black@0.6",
                boxborderw="5",
                y="main_h-text_h-50",
            )
            text_asset = TextAsset(
                text=wrapped_text,
                duration=duration,
                style=style,
            )
            timeline.add_overlay(start=start, asset=text_asset)
        stream_url = timeline.generate_stream()
        return stream_url

    def run(
        self,
        video_id: str,
        collection_id: str,
        language: str = "english",
        notes: str = "",
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Adds subtitles to the specified video using the provided style configuration.

        :param str video_id: The unique identifier of the video to process.
        :param str collection_id: The unique identifier of the collection containing the video.
        :param str language: A string specifying the language for the subtitles.
        :param str notes: A String specifying the style of the language used in subtitles
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response indicating the success or failure of the subtitle addition operation.
        :rtype: AgentResponse
        """
        try:
            self.video_id = video_id
            self.videodb_tool = VideoDBTool(collection_id=collection_id)
            target_language = language.lower()

            self.output_message.actions.append(
                "Retrieving the subtitles in the video's original language"
            )
            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Processing...",
            )
            self.output_message.push_update()

            try:
                self.videodb_tool.get_transcript(video_id, text=False)
            except InvalidRequestError:
                logger.info(
                    f"Transcript not available for video {video_id}. Indexing spoken words.."
                )
                self.output_message.actions.append("Indexing video spoken words..")
                self.output_message.push_update()

                self.videodb_tool.index_spoken_words(video_id)

            self.output_message.content.append(video_content)
            self.output_message.actions.append(
                "Translating the subtitles into the target language.."
            )
            self.output_message.push_update()

            try:
                subtitles = self.videodb_tool.translate_transcript(
                    video_id=video_id,
                    language=target_language,
                    additional_notes=notes,
                )

            except Exception as e:
                logger.error(f"Translation failed: {e}")
                video_content.status = MsgStatus.error
                video_content.status_message = "Translation failed. Please try again."
                self.output_message.publish()
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message=f"Translation failed: {str(e)}",
                )

            if notes:
                self.output_message.actions.append(
                    f"Refining the language with additional notes: {notes}"
                )

            self.output_message.actions.append(
                "Overlaying the subtitles onto the video"
            )
            self.output_message.push_update()

            stream_url = self.add_subtitles_using_timeline(subtitles)
            video_content.video = VideoData(stream_url=stream_url)
            video_content.status = MsgStatus.success
            video_content.status_message = f"Subtitles in {language} have been successfully added to your video. Here is your stream."
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            video_content.status = MsgStatus.error
            video_content.status_message = (
                "An error occurred while adding subtitles to the video."
            )
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Subtitles added successfully",
            data={"stream_url": stream_url},
        )
