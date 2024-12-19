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

SEARCH_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query for the output.",
            "minLength": 1,
        },
        "count": {
            "type": "integer",
            "description": "Number of results to retrieve.",
            "default": 5,
            "minimum": 1,
            "maximum": 50,
        },
        "output_type": {
            "type": "string",
            "description": "Type of output to search for (videos, text, images).",
            "enum": ["videos", "text", "images"],
            "default": "videos",
        },
        "duration": {
            "type": "string",
            "description": "Filter videos by duration.",
            "enum": ["short", "medium", "long"],
            "default": None,
        },
        "collection_id": {
            "type": "string",
            "description": "Collection ID for uploading selected results.",
            "default": None,
        },
    },
    "required": ["query"],
}


class WebSearchAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.api_key = os.getenv("SERP_API_KEY")
        if not self.api_key:
            raise ValueError("SERP_API_KEY environment variable is not set")

        self.agent_name = "web_search"
        self.description = "Performs searches on the web for videos, text, or images using SerpAPI."
        self.parameters = SEARCH_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(self, query: str, count: int = 5, output_type: str = "videos", duration: str = None, collection_id: str = None, *args, **kwargs) -> AgentResponse:
        """
        Perform a search using SerpAPI and handle different output types.

        :param query: Search query.
        :param count: Number of results to retrieve.
        :param output_type: Type of output (videos, text, images).
        :param duration: Filter videos by duration (short, medium, long).
        :param collection_id: Collection ID for uploading selected results.
        :return: A structured response containing search results.
        """
        logger.info(f"WebSearchAgent run started with query: {query}, count: {count}, output_type: {output_type}, duration: {duration}")

        if output_type == "videos":
            return self._handle_video_search(query, count, duration, collection_id)
        elif output_type == "text":
            return self._handle_text_search(query, count)
        elif output_type == "images":
            return self._handle_image_search(query, count)
        else:
            logger.error(f"Unsupported output type: {output_type}")
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"Unsupported output type: {output_type}",
            )

    def _handle_video_search(self, query: str, count: int, duration: str, collection_id: str) -> AgentResponse:
        """Handles video searches."""
        videos_content = VideosContent(
            agent_name=self.agent_name,
            status=MsgStatus.progress,
            status_message="Searching for videos...",
            videos=[],
        )

        for _ in range(count):
            video_data = VideoData(
                external_url="",
                name="Loading...",
                thumbnail_url=None,
            )
            videos_content.videos.append(video_data)

        self.output_message.content.append(videos_content)
        self.output_message.push_update()

        serp_api = SerpAPI(api_key=self.api_key)

        try:
            serp_api = SerpAPI(api_key=self.api_key)
            results = serp_api.search_videos(query=query, count=count, duration=duration)
            for idx, video in enumerate(results):
                if idx < len(videos_content.videos):
                    videos_content.videos[idx].external_url = video.get("video_link") or video.get("link")
                    videos_content.videos[idx].name = video.get("title", "Untitled Video")
                    videos_content.videos[idx].thumbnail_url = video.get("thumbnail")

            videos_content.status = MsgStatus.success
            videos_content.status_message = f"Found {len(results)} videos."
            self.output_message.push_update()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Video search completed successfully.",
                data={"videos": videos_content.dict()},
            )
        except Exception as e:
            logger.exception(f"Error in video search: {e}")
            videos_content.status = MsgStatus.error
            videos_content.status_message = "An error occurred during the video search."
            self.output_message.push_update()
            return AgentResponse(
                status=AgentStatus.ERROR,
                message="An error occurred during the video search. Please try again later.",
            )

    def _handle_text_search(self, query: str, count: int) -> AgentResponse:
        """Handles text searches."""
        try:
            serp_api = SerpAPI(api_key=self.api_key)
            results = serp_api.search_text(query=query, count=count)
            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Text search completed successfully.",
                data={"results": results},
            )
        except Exception as e:
            logger.exception(f"Error in text search: {e}")
            return AgentResponse(
                status=AgentStatus.ERROR,
                message="An error occurred during the text search. Please try again later.",
            )

    def _handle_image_search(self, query: str, count: int) -> AgentResponse:
        """Handles image searches."""
        try:
            serp_api = SerpAPI(api_key=self.api_key)
            results = serp_api.search_images(query=query, count=count)
            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Image search completed successfully.",
                data={"results": results},
            )
        except Exception as e:
            logger.exception(f"Error in image search: {e}")
            return AgentResponse(
                status=AgentStatus.ERROR,
                message="An error occurred during the image search. Please try again later.",
            )
