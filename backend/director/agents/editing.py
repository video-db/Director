import logging
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.llm.base import LLMResponse
from director.core.session import (
    Session,
    VideoContent,
    VideoData,
    MsgStatus,
    ContextMessage,
    RoleTypes,
    InputMessage,
    OutputMessage,
    TextContent,
    MsgStatus,
)
from director.tools.videodb_tool import VideoDBTool
from director.llm.openai import OpenAI, OpenaiConfig, OpenAIChatModel

from videodb.asset import VideoAsset, AudioAsset

from openai_function_calling import FunctionInferrer

logger = logging.getLogger(__name__)

EDITING_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "The ID of the collection to process.",
        },
    },
    "required": ["collection_id"],
}

# TODO: Create tools that can create asset and return asset config as json

EDITING_PROMPT = """
You are an AI video editing assistant using the VideoDB framework. 
User will be giving their editing requirement in Natural language, you can parse that create a plan for user edit.
Past Chat Context is also given to you to see what media is user referring to
Your job is to produce valid timeline-based video edits according to user requests and the following rules. 
In your final output, create a JSON object containing two lists: 'inline_assets' and 'overlay_assets'.

=============================
 VIDEO EDITING CAPABILITIES
=============================

1. Video Timeline Model
   - You have a single continuous video timeline.
   - You can add video segments inline (sequentially) and overlay assets at specific timestamps.
   - Only one video track is allowed. No overlapping (parallel) video playback.
   - Multiple overlays can appear, but do not schedule two of the same overlay type at exactly the same moment in time unless specifically needed.

2. Asset Types and Parameters

   (A) Inline video_asset
       - Represents a contiguous video clip used in sequence.
       - Required fields:
            asset_type: "video_asset"
            media_id: (string) the ID of the source video
            start_time: (number) start time in the source video (seconds)
            end_time:   (number) end time in the source video (seconds)
       - In your final JSON, place such objects under the "inline_assets" array.
       - The timeline length grows based on these inline video segments.

   (B) Overlay assets (audio_asset, image_asset, text_asset)
       - Overlays do not extend timeline length; they appear at certain times.
       - Two audio overlays cannot overlap each other

       1) audio_asset
          - Required fields:
               media_id: (string)
               start_time: (number) start time in the source audio (seconds)
               end_time:   (number) end time in the source audio (segconds)
          - Optional fields:
               disable_other_tracks: (boolean) mutes other audio while this overlay plays
               fade_in_duration: (number)
               fade_out_duration: (number)

       2) image_asset
          - Required fields:
               media_id: (string)
               x_coord: (number) horizontal position in pixels
               y_coord: (number) vertical position in pixels
               duration: (number) how long the image stays visible (seconds)

       3) text_asset
          - Required fields:
               timeline_time: (number) the timeline time at which to appear
               text_content: (string) the text to display
          - Optional:
               style: (object) e.g. { "font_size": 24, "text_color": "white", "alpha": 0.8, "x_coord": 100, "y_coord": 50 }

       - In your final JSON, place these objects under the "overlay_assets" array.

3. Final Editing 

When you have finished planning all edits, use do_editing tool 

4. Key Constraints and Rules
   - Inline (video) segments must not overlap; they are appended in sequence.
   - Overlays do not affect total timeline length but must have valid times within or at the edges of the existing timeline.
   - Do not overlay two videos at once (no picture-in-picture).
   - Avoid scheduling two identical overlay types at the exact same time unless specifically requested.
   - All media references (media_id) must come from VideoDB. If the user only provides a name or description, retrieve the actual media_id first (see Tools below).
   - Timestamps (start_time, end_time) for any media segment must be within that media’s duration.
   - If a request is impossible (e.g., "overlay two videos simultaneously"), explain or propose an alternative.

=============================
  TOOLS & USAGE INSTRUCTIONS
=============================

1) get_media(media_id: str, media_type: str (audio, video, image))
   - Use this to look up a media_id in VideoDB by name, description, or duration of audio asset.

2) do_editing(plan: JSON)
   - Once you have your final JSON plan with "inline_assets" and "overlay_assets", call this tool and pass in that JSON.
   - Example usage:
       do_editing({
         "inline_assets": [...],
         "overlay_assets": [...]
       })

3) Wherever you mentioned media_id it is always a ID of a media uploaded to VideoDB.

====================
 WORKFLOW TO FOLLOW
====================

1. Check the user’s request and prior context. Determine which media and timestamps are needed.
2. If needed, call get_media(...) to find or confirm from user.
3. Build a complete list of inline video segments and overlay assets, following all constraints and correct parameter naming (snake case).
4. Output the final JSON to do_editing(...) in the format described above.
5. If information is missing or the request is ambiguous, ask the user for clarification before finalizing.

=======================================
Your goal is to produce a correct JSON plan for timeline editing with VideoDB.
If the user’s request is unclear or impossible, seek clarification or provide an alternative.

====================
Rules
====================

""".strip()


def get_parameters(func):
    function_inferrer = FunctionInferrer.infer_from_function_reference(func)
    function_json = function_inferrer.to_json_schema()
    parameters = function_json.get("parameters")
    if not parameters:
        raise Exception(
            "Failed to infere parameters, please define JSON instead of using this automated util."
        )
    return parameters


class EditingAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "editing"
        self.description = "An agent designed to edit and combine videos and audio files uploaded on VideoDB."
        self.parameters = EDITING_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)
        self.timeline = None
        self.editing_response = None

        # TODO: benchmark different llm
        self.llm = OpenAI()
        self.o3mini = OpenAI(OpenaiConfig(chat_model=OpenAIChatModel.o3_MINI))

        # TODO: find a way to get the tool description from function/tool and not hardcode here
        self.tools = [
            {
                "name": "get_media",
                "description": "Used to get media details of a given media",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "media_id": {
                            "type": "string",
                            "description": "id of media you need details for",
                        },
                        "media_type": {
                            "type": "string",
                            "description": "Type of media",
                            "enum": ["audio", "video", "image"],
                        },
                    },
                },
            },
            {
                "name": "do_editing",
                "description": "Executes video editing operations based on a structured timeline configuration.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "inline_assets": {
                            "type": "array",
                            "description": "A list of video assets to be placed inline in the timeline, sequentially.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "asset_type": {
                                        "type": "string",
                                        "enum": ["video_asset"],
                                        "description": "The type of asset (always 'video_asset' for inline assets).",
                                    },
                                    "asset_config": {
                                        "type": "object",
                                        "description": "A object having parameter details for the asset.",
                                    },
                                },
                                "required": ["asset_type", "asset_config"],
                            },
                        },
                        "overlay_assets": {
                            "type": "array",
                            "description": "A list of overlay assets (audio, image, text) that will be placed at specific timestamps.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "asset_type": {
                                        "type": "string",
                                        "enum": [
                                            "audio_asset",
                                            "image_asset",
                                            "text_asset",
                                        ],
                                        "description": "The type of overlay asset.",
                                    },
                                    "overlay_at": {
                                        "type": "number",
                                        "description": "The timeline position (in seconds) where the overlay should be applied.",
                                    },
                                    "asset_config": {
                                        "type": "object",
                                        "description": "A object having parameter details for the asset.",
                                    },
                                },
                                "required": [
                                    "asset_type",
                                    "overlay_at",
                                    "asset_config",
                                ],
                            },
                        },
                    },
                    "required": ["inline_assets", "overlay_assets"],
                },
            },
        ]

    def get_media(self, media_id, media_type):
        media_data = None
        if media_type == "video":
            media_data = self.videodb_tool.get_video(media_id)
        if media_type == "audio":
            media_data = self.videodb_tool.get_audio(media_id)
        if media_type == "image":
            media_data = self.videodb_tool.get_image(media_id)

        return AgentResponse(
            data=media_data,
            message="Attached is media details",
            status=AgentStatus.SUCCESS,
        )

    def do_editing(self, inline_assets, overlay_assets):
        self.output_message.actions.append("Composing Timeline")
        self.output_message.push_update()
        for inline_asset in inline_assets:
            self.output_message.actions.append(
                f"Adding inline asset with config {inline_asset}"
            )
            self.output_message.push_update()
        for overlay_asset in overlay_assets:
            self.output_message.actions.append(
                f"Adding overlay asset with config {overlay_asset}"
            )
            self.output_message.push_update()
        data = {"inline_assets": inline_assets, "overlay_assets": overlay_assets}
        return AgentResponse(
            data=data,
            message="Attached is editing timeline response",
            status=AgentStatus.SUCCESS,
        )

    def run_llm(self):
        print(
            "###### Editing context ####",
            [message.to_llm_msg() for message in self.editing_context],
            "\n\n",
        )

        llm_response_1: LLMResponse = self.llm.chat_completions(
            messages=[message.to_llm_msg() for message in self.editing_context],
            tools=[tool for tool in self.tools],
        )
        # llm_response_2: LLMResponse = self.o3mini.chat_completions(
        #     messages=[message.to_llm_msg() for message in self.editing_context],
        #     tools=[tool for tool in self.tools],
        # )

        print("this is llm response ", llm_response_1)
        # print("this is tool response 2", llm_response_2)

        if llm_response_1.tool_calls:
            self.editing_context.append(
                ContextMessage(
                    content=llm_response_1.content,
                    tool_calls=llm_response_1.tool_calls,
                    role=RoleTypes.assistant,
                )
            )
            for tool_call in llm_response_1.tool_calls:
                print("###### TOOL CALL #####: ", tool_call)
                if tool_call["tool"]["name"] == "do_editing":
                    editing_response = self.do_editing(**tool_call["tool"]["arguments"])
                    if editing_response.status == AgentStatus.ERROR:
                        print("Some error in editing agent", editing_response)
                        # self.failed_agents.append(tool_call["tool"]["name"])
                    self.editing_response = editing_response
                    self.editing_context.append(
                        ContextMessage(
                            content=editing_response.__str__(),
                            tool_call_id=tool_call["id"],
                            role=RoleTypes.tool,
                        )
                    )
                elif tool_call["tool"]["name"] == "get_media":
                    media_response = self.get_media(**tool_call["tool"]["arguments"])
                    if media_response.status == AgentStatus.ERROR:
                        print("Some error in media response", media_response)
                        # self.failed_agents.append(tool_call["tool"]["name"])
                    self.editing_context.append(
                        ContextMessage(
                            content=media_response.__str__(),
                            tool_call_id=tool_call["id"],
                            role=RoleTypes.tool,
                        )
                    )

        if (
            llm_response_1.finish_reason == "stop"
            or llm_response_1.finish_reason == "end_turn"
            or self.iterations == 0
        ):
            self.editing_context.append(
                ContextMessage(
                    content=llm_response_1.content,
                    role=RoleTypes.assistant,
                )
            )
            self.stop_flag = True

    def run(
        self,
        collection_id: str,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Edits and combines the specified videos and audio files.

        :param list videos: List of video objects with id, start and end times
        :param list audios: Optional list of audio objects with id, start and end times
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: The response indicating the success or failure of the editing operation
        :rtype: AgentResponse
        """
        try:
            # Initialize first video's collection
            self.videodb_tool = VideoDBTool(collection_id=collection_id)
            self.iterations = 10
            self.stop_flag = False

            input_context = ContextMessage(
                content=f"{EDITING_PROMPT}", role=RoleTypes.user
            )

            # TODO: find a better way to do remove last of tool call from this.
            self.editing_context = self.session.reasoning_context[:-1]
            self.editing_context.append(input_context)

            it = 0
            while self.iterations > 0:
                self.iterations -= 1
                print("-" * 40, "Editing LLM iteration ", it, "-" * 40)
                if self.stop_flag:
                    break

                self.run_llm()
                it += 1

            print("-" * 40, "Ended Run", "-" * 40)
            print(
                "Editing context",
                [message.to_llm_msg() for message in self.editing_context],
                "\n\n",
            )

        #     self.output_message.actions.append("Starting video editing process")
        #     video_content = VideoContent(
        #         agent_name=self.agent_name,
        #         status=MsgStatus.progress,
        #         status_message="Processing...",
        #     )
        #     self.output_message.content.append(video_content)
        #     self.output_message.push_update()

        #     self.timeline = self.videodb_tool.get_and_set_timeline()

        #     # Add videos to timeline
        #     self.add_media_to_timeline(videos, "video")

        #     # Add audio files if provided
        #     if audios:
        #         self.add_media_to_timeline(audios, "audio")

        #     self.output_message.actions.append("Generating final video stream")
        #     self.output_message.push_update()

        #     stream_url = self.timeline.generate_stream()

        #     video_content.video = VideoData(stream_url=stream_url)
        #     video_content.status = MsgStatus.success
        #     video_content.status_message = "Here is your stream."
        #     self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            # video_content.status = MsgStatus.error
            # video_content.status_message = "An error occurred while editing the video."
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Video editing completed successfully, and editing instruction for this run are attached in data ",
            data={"stream_url": "", "editing_instruction": self.editing_response},
        )
