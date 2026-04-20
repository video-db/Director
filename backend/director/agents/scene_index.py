import logging
from typing import Optional

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, MsgStatus, TextContent
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)

SCENE_INDEX_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "video_id": {
            "type": "string",
            "description": "The ID of the video whose scene descriptions you want to view.",
        },
        "collection_id": {
            "type": "string",
            "description": "The ID of the collection containing the video.",
        },
        "scene_index_id": {
            "type": "string",
            "description": "Optional. The specific scene index ID to display. If omitted, the most recent scene index is used.",
        },
    },
    "required": ["video_id", "collection_id"],
}


class SceneIndexAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "scene_index"
        self.description = (
            "Retrieve and display the indexed scene descriptions of a video. "
            "Use this when the user wants to view, see, or list the scene descriptions "
            "or scene index of a video that has already been scene-indexed."
        )
        self.parameters = SCENE_INDEX_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self, video_id: str, collection_id: str, scene_index_id: Optional[str] = None
    ) -> AgentResponse:
        """
        Display the indexed scene descriptions for a video as a formatted table.

        :param str video_id: The ID of the video
        :param str collection_id: The ID of the collection containing the video
        :param str scene_index_id: Optional scene index ID; uses the most recent index if not provided
        """
        output_text_content = TextContent(
            agent_name=self.agent_name,
            status_message="Fetching scene index...",
        )
        self.output_message.content.append(output_text_content)
        self.output_message.push_update()

        try:
            videodb_tool = VideoDBTool(collection_id=collection_id)

            if not scene_index_id:
                self.output_message.actions.append("Listing available scene indexes...")
                self.output_message.push_update()
                scene_list = videodb_tool.list_scene_index(video_id)
                if not scene_list:
                    output_text_content.status = MsgStatus.error
                    output_text_content.status_message = (
                        "No scene index found for this video. "
                        "Please index the video scenes first."
                    )
                    self.output_message.publish()
                    return AgentResponse(
                        status=AgentStatus.ERROR,
                        message="No scene index found. Index the video scenes first.",
                    )
                # Use the last entry: REST list APIs typically append, so newest is last.
                scene_index_id = scene_list[-1]["scene_index_id"]

            self.output_message.actions.append("Loading scene descriptions...")
            self.output_message.push_update()
            scenes = videodb_tool.get_scene_index(video_id, scene_index_id)

            if not scenes:
                output_text_content.status = MsgStatus.error
                output_text_content.status_message = "Scene index exists but contains no entries."
                self.output_message.publish()
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="Scene index is empty.",
                )

            rows = [
                "| # | Start | End | Description |",
                "|---|---|---|---|",
            ]
            for i, scene in enumerate(scenes, 1):
                start = f"{float(scene.get('start', 0)):.1f}s"
                end = f"{float(scene.get('end', 0)):.1f}s"
                raw_desc = scene.get("description") or ""
                desc = raw_desc.replace("\r", " ").replace("\n", " ").replace("|", "\\|")
                rows.append(f"| {i} | {start} | {end} | {desc} |")

            output_text_content.text = "\n".join(rows)
            output_text_content.status = MsgStatus.success
            output_text_content.status_message = (
                f"Showing {len(scenes)} scene descriptions."
            )
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message=f"Displayed {len(scenes)} scene descriptions.",
                data={"scene_index_id": scene_index_id, "scene_count": len(scenes)},
            )

        except Exception as e:
            logger.exception(f"SceneIndexAgent failed: {e}")
            output_text_content.status = MsgStatus.error
            output_text_content.status_message = "Failed to retrieve scene descriptions."
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=str(e),
            )
