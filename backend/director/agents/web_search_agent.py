import logging
import os
from dotenv import load_dotenv

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    TextContent,
    MsgStatus,
)
from director.tools.serp import SerpAPI

load_dotenv()
logger = logging.getLogger(__name__)

class WebSearchAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.api_key = os.getenv("SERP_API_KEY")
        if not self.api_key:
            raise ValueError("SERP_API_KEY environment variable is not set")

        self.agent_name = "web_search"
        self.description = "Searches for videos on the web using SerpAPI."
        self.parameters = self.get_parameters()
        super().__init__(session=session, **kwargs)

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for the video",
                    "minLength": 1,
                },
                "count": {
                    "type": "integer",
                    "description": "Number of video results to retrieve",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 50,
                },
                "duration": {
                    "type": "string",
                    "description": "Filter videos by duration",
                    "enum": ["short", "medium", "long"],
                    "default": None,
                },
                "collection_id": {
                    "type": "string",
                    "description": "Collection ID for uploading selected video(s)",
                    "default": None,
                },
            },
            "required": ["query"],
        }

    def run(self, query: str, count: int = 5, collection_id: str = None, duration: str = None, *args, **kwargs) -> AgentResponse:
        """
        Perform a video search using SerpAPI.
        :param query: Search query for the video.
        :param count: Number of video results to retrieve.
        :param collection_id: Collection ID for uploading the selected video(s).
        :param duration: Filter videos by duration (short, medium, long).
        :return: A structured response containing video search results.
        """
        text_content = TextContent(
            agent_name=self.agent_name,
            status=MsgStatus.progress,
            status_message=f"Searching for videos: {query}...",
        )
        self.output_message.content.append(text_content)
        self.output_message.push_update()

        serp_api = SerpAPI(api_key=self.api_key)

        try:
            results = serp_api.search_videos(query=query, count=count, duration=duration)
            if not results:
                text_content.status = MsgStatus.error
                text_content.status_message = "No video results found. Consider refining your query."
                self.output_message.publish()
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="No video results found.",
                    data={"results": []},
                )

            formatted_results = [
                {
                    "source": r.get("video_link") or r.get("link"),  # Use video_link if available, fallback to link
                    "source_type": "url",
                    "media_type": "video",
                    "name": r.get("title") or f"Untitled Video {idx + 1}",
                    "collection_id": collection_id,
                    "thumbnail": r.get("thumbnail") or None,
                    "duration": r.get("duration") or "unknown",
                }
                for idx, r in enumerate(results)
                if r.get("link") or r.get("video_link")
            ]

            suggested = formatted_results[0] if formatted_results else None

            text_content.status = MsgStatus.success
            text_content.status_message = f"Found {len(formatted_results)} video results."
            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Video search completed successfully.",
                data={"results": formatted_results, "suggested": suggested},
            )

        except RuntimeError as e:
            logger.exception(f"Error in SerpAPI call: {e}")
            text_content.status = MsgStatus.error
            text_content.status_message = "An error occurred while searching for videos."
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.ERROR,
                message="An error occurred during the video search. Please try again later.",
            )
