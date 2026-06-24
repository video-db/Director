import logging
import os
from typing import Optional

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, TextContent, MsgStatus
from director.tools.videodb_tool import VideoDBTool
from director.tools.twelvelabs_tool import (
    TwelveLabsTool,
    PARAMS_CONFIG as TWELVELABS_PARAMS_CONFIG,
)

logger = logging.getLogger(__name__)

VIDEO_UNDERSTANDING_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "The collection_id where the given video_id is available.",
        },
        "video_id": {
            "type": "string",
            "description": "The id of the video to analyze.",
        },
        "prompt": {
            "type": "string",
            "description": "The instruction guiding the analysis, e.g. 'Describe this video', 'List the key moments', 'What products appear?'.",
        },
        "twelvelabs_config": {
            "type": "object",
            "properties": TWELVELABS_PARAMS_CONFIG["analyze"],
            "description": "Optional TwelveLabs Pegasus configuration overrides.",
        },
    },
    "required": ["collection_id", "video_id", "prompt"],
}


class VideoUnderstandingAgent(BaseAgent):
    """Multimodal video understanding using TwelveLabs Pegasus.

    Unlike ``summarize_video``, which reasons over the spoken-word transcript
    only, this agent sends the actual video to TwelveLabs Pegasus so the
    analysis is grounded in the visual content (scenes, objects, on-screen
    actions) as well as the audio. Requires ``TWELVELABS_API_KEY`` to be set;
    if it is not, the agent reports an error and existing behaviour is
    unaffected.
    """

    def __init__(self, session: Session, **kwargs):
        self.agent_name = "video_understanding"
        self.description = (
            "Analyzes a VideoDB video using the TwelveLabs Pegasus model for true "
            "multimodal video understanding (visual + audio), not just the transcript. "
            "Use this when the user asks about what is visually happening in a video, "
            "wants a description grounded in the footage, or asks questions that need "
            "the model to watch the video. Requires the TWELVELABS_API_KEY environment "
            "variable."
        )
        self.parameters = VIDEO_UNDERSTANDING_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        video_id: str,
        prompt: str,
        twelvelabs_config: Optional[dict] = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Analyze the given video with TwelveLabs Pegasus.

        :param str collection_id: The collection_id where the video is available.
        :param str video_id: The id of the video to analyze.
        :param str prompt: The instruction guiding the analysis.
        :param dict twelvelabs_config: Optional Pegasus configuration overrides.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing the generated analysis.
        :rtype: AgentResponse
        """
        text_content = TextContent(
            agent_name=self.agent_name,
            status_message="Analyzing video with TwelveLabs Pegasus..",
        )
        try:
            api_key = os.getenv("TWELVELABS_API_KEY")
            if not api_key:
                raise Exception(
                    "TwelveLabs API key not found. Set the TWELVELABS_API_KEY "
                    "environment variable to use the video_understanding agent."
                )

            self.output_message.actions.append("Started video understanding..")
            self.output_message.content.append(text_content)
            self.output_message.push_update()

            videodb_tool = VideoDBTool(collection_id=collection_id)
            video = videodb_tool.get_video(video_id)

            # Pegasus fetches the video server-side from a public URL, so we
            # resolve a downloadable URL from the VideoDB stream.
            self.output_message.actions.append("Resolving a downloadable video URL..")
            self.output_message.push_update()
            download_response = videodb_tool.download(video["stream_url"])
            video_url = download_response.get("download_url")
            if download_response.get("status") != "done" or not video_url:
                raise Exception(
                    f"Could not resolve a downloadable URL for video {video_id}: "
                    f"{download_response}"
                )

            self.output_message.actions.append(
                "Analyzing video with <b>TwelveLabs Pegasus</b>.."
            )
            self.output_message.push_update()

            twelvelabs_tool = TwelveLabsTool(api_key=api_key)
            analysis = twelvelabs_tool.analyze_video(
                video_url=video_url,
                prompt=prompt,
                config=twelvelabs_config or {},
            )

            text_content.text = analysis
            text_content.status = MsgStatus.success
            text_content.status_message = "Here is the video analysis"
            self.output_message.publish()
        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent: {e}")
            text_content.status = MsgStatus.error
            text_content.status_message = "Failed to analyze the video."
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Video analysis generated and displayed to user.",
            data={"analysis": analysis},
        )
