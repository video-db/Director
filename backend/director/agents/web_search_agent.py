import logging
import os
import requests

from typing import Optional

from dotenv import load_dotenv

from director.tools.videodb_tool import VideoDBTool
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    VideosContent,
    VideoData,
    MsgStatus,
)
from director.tools.serp import SerpAPI
from urllib.parse import urlparse, parse_qs

load_dotenv()
logger = logging.getLogger(__name__)


SUPPORTED_ENGINES = ["serp", "videodb"]
SEARCH_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "engine": {
            "type": "string",
            "description": "Engine to use for the search. Currently supports 'videodb' and 'serp'. Default is 'videodb'",
            "enum": SUPPORTED_ENGINES,
            "default": "videodb",
        },
        "job_type": {
            "type": "string",
            "enum": ["search_videos"],
            "description": "The type of search to perform. Possible value: search_videos.",
        },
        "search_videos": {
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
                "duration": {
                    "type": "string",
                    "description": "Filter videos by duration (short, medium, long).",
                    "enum": ["short", "medium", "long"],
                },
                "serp_config": {
                    "type": "object",
                    "description": "Config to use when SerpAPI engine is used",
                    "properties": {
                        "base_url": {
                            "type": "string",
                            "description": "Base URL for the SerpAPI service",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds for API requests",
                            "default": 10,
                        },
                    },
                },
            },
            "required": ["query"],
        },
    },
    "required": ["job_type", "engine"],
}

class VideoDBSearchTool:
    def __init__(self):
        self.videodb_tool = VideoDBTool()
    def search_videos(
        self, query: str, count: int = 5, duration="medium"
    ) -> list:
        return self.videodb_tool.youtube_search(query=query, count=count, duration=duration)
        

class WebSearchAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "web_search"
        self.description = "Performs web searches to find and retrieve relevant videos using various engines."
        self.parameters = SEARCH_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        engine: str,
        job_type: str,
        search_videos: Optional[str] = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Perform a search using the specified engine and handle different job types.

        :param engine: Search engine to use (e.g., 'serp').
        :param job_type: Type of job to execute (e.g., 'search_videos').
        :param search_videos: Parameters specific to the 'search_videos' job type.
        :return: A structured response containing search results.
        """
        if engine not in SUPPORTED_ENGINES:
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"Engine '{engine}' is not supported.",
            )

        self.api_key = os.getenv("SERP_API_KEY")
        if self.api_key and engine == "serp":
            serp_config = search_videos.get("serp_config", {})
            search_engine_tool = SerpAPI(
                api_key=self.api_key,
                base_url=serp_config.get("base_url"),
                timeout=serp_config.get("timeout", 10),
            )
        else:
            search_engine_tool = VideoDBSearchTool()

        if job_type == "search_videos":
            if not isinstance(search_videos, dict):
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="'search_videos' must be a dictionary.",
                )
            if not search_videos:
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="Parameters for 'search_videos' are required.",
                )
            return self._handle_video_search(search_videos, search_engine_tool)
        else:
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"Unsupported job type: {job_type}.",
            )

    def _handle_video_search(
        self, search_videos: dict, search_engine_tool
    ) -> AgentResponse:
        """Handles video searches."""
        query = search_videos.get("query")
        count = search_videos.get("count", 5)
        duration = search_videos.get("duration")
        if not isinstance(count, int) or count < 1 or count > 50:
            return AgentResponse(
                status=AgentStatus.ERROR,
                message="Count must be between 1 and 50",
            )
        if duration and duration not in ["short", "medium", "long"]:
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"Invalid duration value: {duration}",
            )

        if not query or not isinstance(query, str) or not query.strip():
            return AgentResponse(
                status=AgentStatus.ERROR,
                message="Search query is required and cannot be empty.",
            )

        try:
            results = search_engine_tool.search_videos(
                query=query, count=count, duration=duration
            )
            valid_videos = []

            for video in results:
                external_url = video.get("link") or video.get("video_link")

                # Skip non-video YouTube links
                parsed_url = urlparse(external_url)
                if parsed_url.netloc in ["youtube.com", "www.youtube.com"]:
                    if any(
                        parsed_url.path.startswith(prefix)
                        for prefix in ["/channel/", "/@", "/c/", "/playlist"]
                    ):
                        continue
                    if not parsed_url.path.startswith("/watch") or not parse_qs(
                        parsed_url.query
                    ).get("v"):
                        continue

                # Prepare video data
                video_data = VideoData(
                    external_url=external_url,
                    name=video.get("title", "Untitled Video"),
                    thumbnail_url=video.get("thumbnail"),
                )
                valid_videos.append(video_data)

            if not valid_videos:
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="No valid videos were found.",
                )

            videos_content = VideosContent(
                agent_name=self.agent_name,
                status=MsgStatus.success,
                status_message=f"Found {len(valid_videos)} videos.",
                videos=valid_videos,
            )
            self.output_message.content.append(videos_content)
            self.output_message.push_update()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Video search completed successfully.",
                data={"videos": [video.dict() for video in valid_videos]},
            )
        except requests.exceptions.RequestException as e:
            error_message = "An error occurred during the video search."
            if isinstance(e, requests.exceptions.Timeout):
                error_message = "The search request timed out. Please try again."
            elif isinstance(e, requests.exceptions.HTTPError):
                if getattr(e.response, "status_code", None) == 429:
                    error_message = (
                        "Rate limit exceeded. Please try again in a few minutes."
                    )
                elif getattr(e.response, "status_code", None) == 401:
                    error_message = (
                        "API authentication failed. Please check your API key."
                    )
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=error_message,
            )
