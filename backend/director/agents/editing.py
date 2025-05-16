import logging
from videodb import TextStyle
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.llm.base import LLMResponse
from director.core.session import (
    Session,
    VideoContent,
    VideoData,
    MsgStatus,
    ContextMessage,
    RoleTypes,
)
from director.tools.videodb_tool import VideoDBTool
from director.llm import get_default_llm

from videodb.asset import VideoAsset, AudioAsset, ImageAsset, TextAsset

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

# TODO: round all timeline values to 2 decimal to avoid floating point issues.

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
       - These parameters are Asset's configuration, pass them under asset_config
       - Required fields:
            asset_id: (string) the ID of the source video
            start: (number) start time in the source video (seconds)
            end:   (number) end time in the source video (seconds)
        - The timeline length grows based on these inline video segments.

   (B) Overlay assets (audio_asset, image_asset, text_asset)
       - Overlays do not extend timeline length; they appear at certain times.
       - These parameters are Asset's configuration, pass them under asset_config
       - Two audio overlays cannot overlap each other

       1) audio_asset
          - Required fields:
               asset_id: (string)
               start: (number) start time in the source audio (seconds)
               end:   (number) end time in the source audio (seconds)
          - Optional fields:
               disable_other_tracks: (boolean) mutes other audio while this overlay plays
               fade_in_duration: (number)
               fade_out_duration: (number)

       2) image_asset
          - Required fields:
               asset_id: (string)
            - Optional
               duration: (number) how long the image stays visible (seconds)
               width: (number)
               height: (number)
               x: (number) horizontal position in pixels
               y: (number) vertical position in pixels

       3) text_asset
          - Required fields:
               asset_id: (number) the timeline time at which to appear
               text : (string) the text to display
          - Optional:
               duration: (number) how long the text stays visible (seconds)
               style: (object) e.g. { "fontsize": 18, "fontcolor": "white", "alpha": 0.7, "boxcolor": "black", "x": 50, "y": 50 } // "x" and "y" are the position of the text on the screen
        - These parameter as Asset's configuration 

3. Final Editing 

When you have finished planning all edits, use do_editing tool 

4. Key Constraints and Rules
   - Inline (video) segments must not overlap; they are appended in sequence.
   - Overlays do not affect total timeline length but must have valid times within or at the edges of the existing timeline.
   - Do not overlay two videos at once (no picture-in-picture).
   - Avoid scheduling two identical overlay types at the exact same time unless specifically requested.
   - All media references (media_id) must come from VideoDB and use get_media tool to first fetch and verify relevant info for all selected media ids
   - If the user only provides a name or description, retrieve all media of that type and see if media is available (see Tools below).
   - Timestamps (start, end) for any media segment must be within that media duration.(also this should be verified once you have media info using get_media)
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
         "inline_assets": [{asset_type: "", asset_config: {}}],
         "overlay_assets": [{asset_type: "", overlay_at: 0, asset_config: {}}]
       })

====================
 WORKFLOW TO FOLLOW
====================

1. Check the user request and prior context. Determine which media and timestamps are needed.
2. call get_media(...) to verify if media is present in users db and fetch relevant info. 
3. Build a complete list of inline video segments and overlay assets, following all constraints and correct parameter naming (snake case).
4. Output the final JSON to do_editing(...) in the format described above.
5. If information is missing or the request is ambiguous, ask the user for clarification before finalizing.

=======================================
Your goal is to produce a correct JSON plan for timeline editing with VideoDB.
If the user request is unclear or impossible, seek clarification or provide an alternative.

====================
Rules
====================

""".strip()


class EditingAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "editing"
        self.description = "An agent designed to edit and combine videos and audio files uploaded on VideoDB."
        self.parameters = EDITING_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)
        self.timeline = None
        self.editing_response = None

        # TODO: benchmark different llm
        self.llm = get_default_llm()

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
        self.output_message.actions.append(
            f"Fetching {media_type}(<i>{media_id}</i>) info"
        )
        self.output_message.push_update()
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
        timeline = self.videodb_tool.get_and_set_timeline()
        for inline_asset in inline_assets:
            self.output_message.actions.append(
                f"Adding inline asset with config {inline_asset}"
            )
            self.output_message.push_update()
            video_asset = VideoAsset(**inline_asset.get("asset_config", {}))
            timeline.add_inline(video_asset)
        for overlay_asset in overlay_assets:
            self.output_message.actions.append(
                f"Adding overlay asset with config {overlay_asset}"
            )
            self.output_message.push_update()
            if overlay_asset.get("asset_type") == "audio_asset":
                audio_asset = AudioAsset(**overlay_asset.get("asset_config", {}))
                overlay_at = overlay_asset.get("overlay_at", 0)
                timeline.add_overlay(overlay_at, audio_asset)
            if overlay_asset.get("asset_type") == "image_asset":
                image_asset = ImageAsset(**overlay_asset.get("asset_config", {}))
                overlay_at = overlay_asset.get("overlay_at", 0)
                timeline.add_overlay(overlay_at, image_asset)
            if overlay_asset.get("asset_type") == "text_asset":
                asset_config = overlay_asset.get("asset_config", {}).copy()
                if asset_config.get("style"):
                    style_dict = asset_config.get("style", {}).copy() 
                    style = TextStyle(**style_dict)
                    asset_config["style"] = style

                if not asset_config.get("duration"):
                    asset_config["duration"] = 5
                text_asset = TextAsset(**asset_config)
                overlay_at = overlay_asset.get("overlay_at", 0)
                timeline.add_overlay(overlay_at, text_asset)
        stream_url = timeline.generate_stream()
        data = {
            "inline_assets": inline_assets,
            "overlay_assets": overlay_assets,
            "edited_stream_url": stream_url,
        }
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

        llm_response: LLMResponse = self.llm.chat_completions(
            messages=[message.to_llm_msg() for message in self.editing_context],
            tools=[tool for tool in self.tools],
        )

        print("Editing Agent LLM Response", llm_response)

        if llm_response.tool_calls:
            self.editing_context.append(
                ContextMessage(
                    content=llm_response.content,
                    tool_calls=llm_response.tool_calls,
                    role=RoleTypes.assistant,
                )
            )
            for tool_call in llm_response.tool_calls:
                if tool_call["tool"]["name"] == "do_editing":
                    editing_response = self.do_editing(**tool_call["tool"]["arguments"])
                    if editing_response.status == AgentStatus.ERROR:
                        print("Error in Editing Agent", editing_response)
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
                        print("Error in Get Media Agent", media_response)
                    self.editing_context.append(
                        ContextMessage(
                            content=media_response.__str__(),
                            tool_call_id=tool_call["id"],
                            role=RoleTypes.tool,
                        )
                    )

        if (
            llm_response.finish_reason == "stop"
            or llm_response.finish_reason == "end_turn"
            or self.iterations == 0
        ):
            self.editing_context.append(
                ContextMessage(
                    content=llm_response.content,
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

            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Processing...",
            )
            self.output_message.content.append(video_content)
            self.output_message.push_update()

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

            stream_url = self.editing_response.data.get("edited_stream_url")
            if stream_url:
                video_content.video = VideoData(stream_url=stream_url)
                video_content.status = MsgStatus.success
                video_content.status_message = "Here is your stream."
            else:
                video_content.status = MsgStatus.error
                video_content.status_message = (
                    "An error occurred while editing the video."
                )
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            video_content.status = MsgStatus.error
            video_content.status_message = "An error occurred while editing the video."
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Video editing completed successfully, and editing instruction for this run are attached in data ",
            data={"stream_url": "", "editing_instruction": self.editing_response},
        )
