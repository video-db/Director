import logging
import textwrap
import json
import concurrent.futures
from typing import List, Dict
from dataclasses import dataclass
from collections import OrderedDict

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
You are provided with a transcript of a video in a compact format called compact_list to optimize context size. The transcript is presented as a single string where each sentence block is formatted as:

sentence|start|end

sentence: The sentence itself.
start: The start time of the sentence in the video.
end: The end time of the sentence in the video.

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

@dataclass
class BatchTranslationResult:
    batch_index: int
    subtitles: List[Dict]
    success: bool
    error: str = ""

class SubtitleAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "subtitle"
        self.description = "An agent designed to add different languages subtitles to a specified video within VideoDB."
        self.llm = get_default_llm()
        self.parameters = SUBTITLE_AGENT_PARAMETERS
        self.batch_size = 40  # Configurable batch size
        self.max_parallel_requests = 5  
        self.max_retries = 3
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

        try:
            detection_response = self.llm.chat_completions(
                [detection_message.to_llm_msg()],
                response_format={"type": "json_object"},
            )

            result = json.loads(detection_response.content)
            detected_language = result.get("detected_language", "").lower()

            if not detected_language:
                raise ValueError("Language detection failed: Empty or invalid response")

            logger.info(f"Detected language: {detected_language}")
            return detected_language

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse language detection response: {e}")
            raise RuntimeError(
                "Language detection failed: Invalid response format"
            ) from e
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise RuntimeError(f"Language detection failed: {str(e)}") from e

    def _translate_batch(self, batch: List[str], batch_index: int, target_language: str, notes: str) -> BatchTranslationResult:
        """
        Translate a single batch of transcript segments with retry mechanism and comprehensive error handling.
        """
        for retry in range(self.max_retries):
            try:
                translation_llm_prompt = f"{translater_prompt} Translate to {target_language}, additional notes : {notes} compact_list: {batch}"
                translation_llm_message = ContextMessage(
                    content=translation_llm_prompt,
                    role=RoleTypes.user,
                )

                llm_response = self.llm.chat_completions(
                    [translation_llm_message.to_llm_msg()],
                    response_format={"type": "json_object"},
                )

                batch_subtitles = json.loads(llm_response.content)

                if "subtitles" not in batch_subtitles:
                    raise ValueError(f"Missing 'subtitles' key in response. Content: {batch_subtitles}")

                if not isinstance(batch_subtitles["subtitles"], list):
                    raise ValueError(f"'subtitles' is not a list. Received type: {type(batch_subtitles['subtitles'])}")

                return BatchTranslationResult(
                    batch_index=batch_index,
                    subtitles=batch_subtitles["subtitles"],
                    success=True
                )

            except (json.JSONDecodeError, ValueError) as e:
                error_msg = f"Error in batch {batch_index} (attempt {retry + 1}/{self.max_retries}): {str(e)}"
                logger.error(error_msg)
                if retry < self.max_retries - 1:
                    logger.info(f"Retrying batch {batch_index}")
                    continue
                return BatchTranslationResult(
                    batch_index=batch_index,
                    subtitles=[],
                    success=False,
                    error=error_msg
                )
            except Exception as e:
                error_msg = f"Unexpected error in batch {batch_index} (attempt {retry + 1}/{self.max_retries}): {str(e)}"
                logger.error(error_msg)
                if retry < self.max_retries - 1:
                    logger.info(f"Retrying batch {batch_index}")
                    continue
                return BatchTranslationResult(
                    batch_index=batch_index,
                    subtitles=[],
                    success=False,
                    error=error_msg
                )

    def translate_transcript_in_parallel(self, compact_transcript: List[str], target_language: str, notes: str = "") -> Dict:
        """
        Translate transcript segments in parallel while preserving order and handling failures.
        """
        total_segments = len(compact_transcript)
        total_batches = (total_segments + self.batch_size - 1) // self.batch_size

        # Initialize progress tracking
        progress_message = "Translation: 0% completed"
        self.output_message.actions.append(progress_message)
        progress_index = len(self.output_message.actions) - 1
        self.output_message.push_update()

        batches = []
        for i in range(0, total_segments, self.batch_size):
            batch = compact_transcript[i:i + self.batch_size]
            batches.append((i // self.batch_size, batch))

        # Store results in an ordered dictionary to maintain sequence
        results_dict = OrderedDict()
        failed_batches = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_requests) as executor:
            # Submit translation tasks for each batch
            future_to_batch = {
                executor.submit(
                    self._translate_batch,
                    batch,
                    batch_index,
                    target_language,
                    notes
                ): (batch_index, batch)
                for batch_index, batch in batches
            }

            completed_batches = 0
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_result = future.result()
                results_dict[batch_result.batch_index] = batch_result

                if not batch_result.success:
                    failed_batches.append((batch_result.batch_index, batch_result.error))

                completed_batches += 1
                completion_percentage = (completed_batches / total_batches) * 100
                self.output_message.actions[progress_index] = (
                    f"Translation progress: {int(completion_percentage)}% completed"
                )
                self.output_message.push_update()

        if failed_batches:
            error_messages = "\n".join([f"Batch {idx}: {error}" for idx, error in failed_batches])
            raise Exception(f"Translation failed for some batches:\n{error_messages}")

        all_subtitles = []
        for batch_index in range(total_batches):
            batch_result = results_dict.get(batch_index)
            if batch_result and batch_result.success:
                all_subtitles.extend(batch_result.subtitles)

        all_subtitles.sort(key=lambda x: float(x["start"]))

        # Validate subtitle sequence
        for i in range(1, len(all_subtitles)):
            current_start = float(all_subtitles[i]["start"])
            prev_end = float(all_subtitles[i-1]["end"])
            if current_start < prev_end:
                all_subtitles[i]["start"] = prev_end
                logger.warning(f"Fixed overlapping subtitles at index {i}")

        return {"subtitles": all_subtitles}

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
                transcript = self.videodb_tool.get_transcript(
                    video_id, text=False, length=5
                )
            except InvalidRequestError:
                logger.info(
                    f"Transcript not available for video {video_id}. Indexing spoken words..."
                )
                self.output_message.actions.append("Indexing video spoken words...")
                self.output_message.push_update()

                self.videodb_tool.index_spoken_words(video_id)
                transcript = self.videodb_tool.get_transcript(
                    video_id, text=False, length=5
                )

            self.output_message.content.append(video_content)
            self.output_message.push_update()

            compact_transcript = self.get_compact_transcript(transcript=transcript)

            self.output_message.actions.append("Detecting source language of the video")
            self.output_message.push_update()
            source_language = self.detect_language(compact_transcript)
            logger.info(f"Detected source language: {source_language}")

            if source_language == target_language:
                logger.info(
                    "Source language matches target language. No translation needed"
                )
                self.output_message.actions.append(
                    f"Source language ({source_language}) matches target language.."
                )
                self.output_message.push_update()

                subtitles = {"subtitles": transcript}
            else:
                logger.info("Translating subtitles...")
                self.output_message.actions.append(
                    f"Translating the subtitles from {source_language} to {target_language}"
                )
                self.output_message.push_update()

                try:
                    subtitles = self.translate_transcript_in_parallel(
                        compact_transcript=compact_transcript,
                        target_language=target_language,
                        notes=notes,
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

            stream_url = self.add_subtitles_using_timeline(subtitles["subtitles"])
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
