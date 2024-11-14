import logging
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
from director.llm.openai import OpenAI, OpenaiConfig

from videodb.asset import VideoAsset, AudioAsset, TextAsset, TextStyle

logger = logging.getLogger(__name__)

EDITING_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "The unique identifier of the collection containing the videos.",
        },
        "instructions": {
            "type": "string",
            "description": "A detailed description of the editing operations to perform on the videos. When mentioning media from VideoDB Collection either Videos, Image or Audio also mention their Id and other details",
        },
    },
    "required": ["collection_id", "instructions"],
}

editing_prompt = """
**Task Description:**
---

You are provided with a set of instructions to create a custom video timeline. The timeline can include videos, audio, or images within VideoDB. Your task is to interpret the instructions and generate a set of editing commands that can be applied to create such a timeline.

**Timeline Rules:**

- **Videos:**
  - The timeline can contain multiple videos, but they must be placed sequentially; videos cannot be overlaid on top of each other.
  - Videos are added inline, and the sequence in which they are added determines their order in the final output—the first video added will play first.
  - You may include an entire video or select a specific segment by trimming from the start or end using custom `start` and `end` parameters. 
        Default value of start is 0, and end is None
  - These inline videos form the base layer of the timeline.

- **Audio:**
  - Multiple audio tracks can be added to the timeline and are overlaid onto the video layer.
  - Audio tracks function as a single layer; they cannot overlap with each other. Arrange multiple audio tracks in sequence without any overlap, ensuring that each audio's starting position is after the previous one's end.
  - Specify the starting position of an audio track on the timeline using the `overlay_start` parameter.
  - Like videos, you can include the full audio track or select a specific segment by trimming using `start` and `end` parameters.
  - Audio should not overflow the base timeline

** Image:**
  - Multiple images can be overlaid onto the video layer.
  - Unlike audio and images Multiple images can be overlapped over any duration of time. 
  - You can specify duration for which the image should be there
  - Specify the starting position of an image on the timeline using the `overlay_start` parameter.
---

**Your Task:**

---

1. **Parse the Editing Instructions:**
   - Interpret the natural language instructions provided by the user.
   - Identify all assets involved (videos, audios, images), which may be specified by IDs, names, or positions.

2. **Identify Assets and Parameters:**
   - Determine the specific sections of the assets to include based on `start` and `end` parameters.
   - For videos, decide the order they will appear in the timeline.
   - For audios, ensure they are placed correctly without overlapping, using the `overlay_start` parameter.

3. **Generate Editing Actions:**
   - Convert the instructions into a sequence of editing actions with precise timings, asset references, and parameters.
   - Each editing action should include:
     - The type of action (e.g., `add_video`, `add_audio`, `overlay_text`, `add_transition`).
     - References to the asset(s) involved.
     - The `start` and `end` times (if applicable).
     - Any additional parameters needed (e.g., `overlay_start` for audio, effect type, style).

4. **Produce the Final Output:**
   - Provide the final output as a JSON object with a list of editing actions.
   - Ensure the actions are in the correct sequence to build the desired timeline.

---

**Guidelines:**
---

- Ensure that the editing actions accurately reflect the user's instructions.
- Be precise with timings, asset references, and parameters.
- If any instruction is ambiguous, make a reasonable assumption and proceed.
- Do not include any additional commentary or text outside of the JSON object.
- Ensure that the audio tracks do not overlap and are correctly positioned on the timeline.
- Videos should be added inline, respecting the specified order.

---

**Example Output:**
---

```json
{
  "actions": [
    {
      "action": "add_video",
      "asset_id": "video_1",
      "start": 0,
      "end": 15.0,
      "order": 1
    },
    {
      "action": "add_video",
      "asset_id": "video_2",
      "start": 5.0,
      "end": 20.0,
      "order": 2
    },
    {
      "action": "add_audio",
      "asset_id": "audio_1",
      "start": 0,
      "end": 10.0,
      "overlay_at": 5.0
    },
    {
      "action": "add_audio",
      "asset_id": "audio_2",
      "start": 0,
      "end": 5.0,
      "overlay_at": 15.0
    },
    {
      "action": "overlay_text",
      "text": "Sample Text",
      "duration": 10,
      "overlay_at": 10,
      "style" : "Bold font and italic"
    }
  ]
}


Notes:
---
- Use accurate and appropriate parameters for each action.
- Ensure that the JSON is properly formatted and can be parsed.
"""


class EditingAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "editing"
        self.description = "An agent designed to perform video editing operations, potentially involving multiple videos, audio or images within VideoDB."
        self.llm = OpenAI(config=OpenaiConfig(timeout=120))
        self.parameters = EDITING_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def apply_editing_actions(self, actions):
        timeline = self.videodb_tool.get_and_set_timeline()

        # Now, process the actions
        for action in actions:
            action_type = action.get("action")
            if action_type == "add_video":
                video_id = action.get("asset_id")
                start = action.get("start")
                end = action.get("end")
                video_asset = VideoAsset(asset_id=video_id, start=start, end=end)
                print("#### adding video_asset", video_asset)
                timeline.add_inline(video_asset)
            elif action_type == "add_audio":
                audio_id = action.get("asset_id")
                start = action.get("start")
                end = action.get("end")
                overlay_at = action.get("overlay_at")
                audio_asset = AudioAsset(asset_id=audio_id, start=start, end=end)
                print("#### adding video_asset", video_asset)
                timeline.add_overlay(overlay_at, audio_asset)
            else:
                logger.warning(f"Unknown action type: {action_type}")
                continue

        stream_url = timeline.generate_stream()
        return stream_url

    def run(
        self,
        collection_id: str,
        instructions: str,
        notes: str = "",
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Performs editing operations on videos using the provided instructions.

        :param str collection_id: The unique identifier of the collection containing the videos.
        :param str instructions: A detailed description of the editing operations to perform.
        :param str notes: Additional requirements or notes for the editing process.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response indicating the success or failure of the editing operation.
        :rtype: AgentResponse
        """
        try:
            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            self.output_message.actions.append("Parsing the editing instructions")
            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Processing...",
            )
            self.output_message.content.append(video_content)

            self.output_message.actions.append(f"[DEBUG] Instructions : {instructions}")
            self.output_message.actions.append(f"[DEBUG] Notes: {notes}")
            self.output_message.push_update()

            # Prepare the prompt for the LLM
            editing_llm_prompt = f"{editing_prompt}\nInstructions: {instructions}\nAdditional notes: {notes}"
            editing_llm_message = ContextMessage(
                content=editing_llm_prompt,
                role=RoleTypes.user,
            )
            llm_response = self.llm.chat_completions(
                [editing_llm_message.to_llm_msg()],
                response_format={"type": "json_object"},
            )
            editing_actions = json.loads(llm_response.content)
            print("these are editing actions", editing_actions)

            self.output_message.actions.append(
                "Applying the editing actions to the videos"
            )
            self.output_message.push_update()

            # Apply the editing actions using the videodb_tool
            stream_url = self.apply_editing_actions(editing_actions["actions"])

            video_content.video = VideoData(stream_url=stream_url)
            video_content.status = MsgStatus.success
            video_content.status_message = (
                "Video editing completed successfully. Here is your stream."
            )
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            video_content.status = MsgStatus.error
            video_content.status_message = (
                "An error occurred while editing the video(s)."
            )
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Video(s) edited successfully",
            data={"stream_url": stream_url},
        )
