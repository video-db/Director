import logging

from director.agents.base import BaseAgent, AgentResponse, AgentStatus

from director.core.session import Session, MsgStatus, ImageContent, ImageData
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)

FRAME_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "Collection Id to of the video",
        },
        "video_id": {
            "type": "string",
            "description": "Video Id to extract frame",
        },
        "timestamp": {
            "type": "integer",
            "description": "Timestamp in seconds of the video to extract the frame, optional parameter, don't ask from user",
        },
    },
    "required": ["collection_id", "video_id"],
}


class FrameAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "frame"
        self.description = "Generates a image frame from a video file. This Agent takes a video id and an optionl timestamp as input. Use this tool when a user requests a screenshot, frame, snapshot, generate or visual representation of a specific moment in a video file. The output is a static image file suitable for quick previews. It will not provide any other processing or editing options beyond generating the frame."
        self.parameters = FRAME_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self, collection_id: str, video_id: str, timestamp = None, *args, **kwargs
    ) -> AgentResponse:
        """
        Get the image frame for the video at a given timestamp.
        """
        if timestamp is None:
            timestamp = 5

        try:
            self.output_message.actions.append("Generating frame..")
            image_content = ImageContent(agent_name=self.agent_name)
            image_content.status_message = "Extracting frame.."
            self.output_message.content.append(image_content)
            self.output_message.push_update()

            videodb_tool = VideoDBTool(collection_id=collection_id)
            frame_data = videodb_tool.extract_frame(
                video_id=video_id, timestamp=timestamp
            )
            image_content.image = ImageData(**frame_data)
            image_content.status = MsgStatus.success
            image_content.status_message = "Here is your frame."
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent.")
            image_content.status = MsgStatus.error
            image_content.status_message = "Error in extracting frame."
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Frame extracted and displayed to user.",
            data=frame_data,
        )
