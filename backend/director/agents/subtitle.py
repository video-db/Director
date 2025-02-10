import logging
import textwrap
import json

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    ContextMessage,
    RoleTypes,
    VideoContent,
    VideoData,
    MsgStatus,
)
from director.tools.videodb_tool import VideoDBTool
from director.llm import get_default_llm

from videodb.asset import VideoAsset, TextAsset, TextStyle

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
            "description": "The language the user wants the subtitles in",
        },
        "notes": {
            "type": "string",
            "description": "if user has additional requirements for the style of language",
        },
    },
    "required": ["video_id", "collection_id"],
}

language_detection_prompt = """
Task Description:
---
You are provided with a sample of transcript text. Your task is to identify the language of this text.

Guidelines:
- Analyze the provided text carefully
- Consider language patterns, common words, and grammatical structures
- Return your response in JSON format with a single field "detected_language"
- Use the full English name of the language (e.g., "English", "Spanish", "French", etc.)

Please return your response in this format:
{"detected_language": "name of detected language"}
"""

translater_prompt = """
Task Description:
---
You are provided with a transcript of a video in a compact format called compact_list to optimize context size. The transcript is presented as a single string where each word block is formatted as:

word|start|end

word: The word itself.
start: The start time of the word in the video.
end: The end time of the word in the video.

Example Input (compact_list):

[ 'hello|0|10',  'world|11|12',  'how are you|13|15']

Your Task:
---
1.Translate the Text into [TARGET LANGUAGE]:
Translate all the words in the transcript from the source language to [TARGET LANGUAGE].

2.Combine Words into Meaningful Phrases or Sentences:
Group the translated words into logical phrases or sentences that make sense together.
Ensure each group is suitable for subtitle usage—neither too long nor too short.
Adjust Timing for Each Phrase/Block.

3.For each grouped phrase or sentence:
Start Time: Use the start time of the first word in the group.
End Time: Use the end time of the last word in the group.

4.Produce the Final Output:
Provide a list of subtitle blocks in the following format:
[    {"start": 0, "end": 30, "text": "Translated block of text here"},    {"start": 31, "end": 55, "text": "Another translated block of text"},    ...]
Ensure the translated text is coherent and appropriately grouped for subtitles.

Guidelines:
---
Coherence: The translated phrases should be grammatically correct and natural in [TARGET LANGUAGE].
Subtitle Length: Each subtitle block should follow standard subtitle length guidelines (e.g., no more than two lines of text, appropriate reading speed).
Timing Accuracy: Maintain accurate synchronization with the video's audio by correctly calculating start and end times.
Don't add any quotes, or %, that makes escaping the characters difficult.

Example Output:
---
If translating to Spanish, your output might look like:

you should return json of this format
{
subtitles: [    {"start": 0, "end": 30, "text": "Bloque traducido de texto aquí"},    {"start": 31, "end": 55, "text": "Otro bloque de texto traducido"},    ...]
}

Notes:
---
Be mindful of linguistic differences that may affect how words are grouped in [TARGET LANGUAGE].
Ensure that cultural nuances and idiomatic expressions are appropriately translated.
"""


class SubtitleAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "subtitle"
        self.description = "An agent designed to add different languages subtitles to a specified video within VideoDB."
        self.llm = get_default_llm()
        self.parameters = SUBTITLE_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def wrap_text(self, text, video_width, max_width_percent=0.60, avg_char_width=20):
        max_width_pixels = video_width * max_width_percent
        max_chars_per_line = int(max_width_pixels / avg_char_width)

        # Wrap the text based on the calculated max characters per line
        wrapped_text = "\n".join(textwrap.wrap(text, max_chars_per_line))
        wrapped_text = wrapped_text.replace("'", "")
        return wrapped_text

    def get_compact_transcript(self, transcript):
        compact_list = []
        for word_block in transcript:
            word = word_block["text"]
            if word == "-":
                continue
            start = word_block["start"]
            end = word_block["end"]
            compact_word = f"{word}|{start}|{end}"
            compact_list.append(compact_word)
        return compact_list

    def detect_language(self, transcript_sample):
        logger.info("Detecting language...")
        sample_text = " ".join([item.split("|")[0] for item in transcript_sample[:10]])

        detection_prompt = (
            f"{language_detection_prompt} Sample text for analysis: {sample_text}"
        )
        detection_message = ContextMessage(
            content=detection_prompt,
            role=RoleTypes.user,
        )

        detection_response = self.llm.chat_completions(
            [detection_message.to_llm_msg()],
            response_format={"type": "json_object"},
        )

        result = json.loads(detection_response.content)
        logger.info(f"Detected language: {result['detected_language'].lower()}")
        return result["detected_language"].lower()

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
            self.output_message.content.append(video_content)
            self.output_message.push_update()

            transcript = self.videodb_tool.get_transcript(video_id, text=False)
            compact_transcript = self.get_compact_transcript(transcript=transcript)

            self.output_message.actions.append("Detecting source language of the video")
            self.output_message.push_update()
            source_language = self.detect_language(compact_transcript)
            logger.info(f"Detected source language: {source_language}")

            # Check if translation is needed
            if source_language == target_language:
                logger.info(
                    "Source language matches target language. No translation needed"
                )
                self.output_message.actions.append(
                    f"Source language ({source_language}) matches target language. No translation needed."
                )
                self.output_message.push_update()

                # Convert transcript directly to subtitle format without translation
                subtitles = []
                current_subtitle = {"start": None, "end": None, "text": []}

                for item in compact_transcript:
                    word, start, end = item.split("|")
                    start, end = float(start), float(end)

                    if current_subtitle["start"] is None:
                        current_subtitle["start"] = start
                        current_subtitle["text"].append(word)
                    elif end - current_subtitle["start"] > 5:
                        current_subtitle["end"] = float(end)
                        current_subtitle["text"] = " ".join(current_subtitle["text"])
                        subtitles.append(current_subtitle)
                        current_subtitle = {"start": start, "end": None, "text": [word]}
                    else:
                        current_subtitle["text"].append(word)

                    current_subtitle["end"] = end

                if current_subtitle["text"]:
                    current_subtitle["text"] = " ".join(current_subtitle["text"])
                    subtitles.append(current_subtitle)

                translated_subtitles = {"subtitles": subtitles}
            else:
                logger.info("Translating subtitles...")
                self.output_message.actions.append(
                    f"Translating the subtitles from {source_language} to {target_language}"
                )
                self.output_message.push_update()

                translation_llm_prompt = f"{translater_prompt} Translate to {target_language}, additional notes : {notes} compact_list: {compact_transcript}"
                translation_llm_message = ContextMessage(
                    content=translation_llm_prompt,
                    role=RoleTypes.user,
                )
                llm_response = self.llm.chat_completions(
                    [translation_llm_message.to_llm_msg()],
                    response_format={"type": "json_object"},
                )
                translated_subtitles = json.loads(llm_response.content)

            if notes:
                self.output_message.actions.append(
                    f"Refining the language with additional notes: {notes}"
                )

            self.output_message.actions.append(
                "Overlaying the subtitles onto the video"
            )
            self.output_message.push_update()

            stream_url = self.add_subtitles_using_timeline(
                translated_subtitles["subtitles"]
            )
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
            data={stream_url: stream_url},
        )
