import logging
import os
import requests
from dotenv import load_dotenv

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    VideosContent,
    VideoData,
    MsgStatus,
)
from director.tools.serp import SerpAPI

load_dotenv()
logger = logging.getLogger(__name__)

SEARCH_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "engine": {
            "type": "string",
            "description": "Engine to use for the search. Currently supports 'serp'.",
            "enum": ["serp"],
            "default": "serp",
        },
        "job_type": {
            "type": "string",
            "description": "Type of search to perform.",
            "enum": ["search_videos"],
            "default": "search_videos",
        },
        "common_config": {
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
            },
            "required": ["query"],
        },
        "job_config": {
            "type": "object",
            "description": "Job-specific configurations.",
            "properties": {
                "duration": {
                    "type": "string",
                    "description": "Filter videos by duration (short, medium, long).",
                    "enum": ["short", "medium", "long"],
                },
                "collection_id": {
                    "type": "string",
                    "description": "Collection ID for uploading selected results.",
                },
            },
        },
    },
    "required": ["engine", "job_type", "common_config"],
}

SUPPORTED_ENGINES = ["serp"]

class WebSearchAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "web_search"
        self.description = (
            "Performs web searches to find and retrieve relevant videos using various engines."
        )
        self.parameters = SEARCH_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        engine: str,
        job_type: str,
        common_config: dict,
        job_config: dict = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Perform a search using the specified engine and handle different output types.

        :param engine: Search engine to use (e.g., 'serp').
        :param job_type: Type of job to execute (e.g., 'search_videos').
        :param common_config: Common search parameters (e.g., query, count).
        :param job_config: Job-specific parameters (e.g., duration, collection_id).
        :return: A structured response containing search results.
        """
        if engine not in SUPPORTED_ENGINES:
            logger.error(f"Unsupported engine: {engine}")
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"Engine '{engine}' is not supported.",
            )

        logger.info(
            f"WebSearchAgent run started with engine: {engine}, job_type: {job_type}, "
            f"common_config: {common_config}, job_config: {job_config}"
        )

        search_engine_tool = None
        if engine == "serp":
            self.api_key = os.getenv("SERP_API_KEY")
            if not self.api_key:
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="SERP_API_KEY environment variable is not set.",
                )
            search_engine_tool = SerpAPI(api_key=self.api_key)

        query = common_config.get("query")
        count = common_config.get("count", 5)

        if job_type == "search_videos":
            duration = job_config.get("duration") if job_config else None
            collection_id = job_config.get("collection_id") if job_config else None
            return self._handle_video_search(query, count, duration, collection_id, search_engine_tool)
        else:
            logger.error(f"Unsupported job type: {job_type}")
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"Unsupported job type: {job_type}.",
            )

    def _handle_video_search(self, query: str, count: int, duration: str, collection_id: str, search_engine_tool) -> AgentResponse:
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

        try:
            results = search_engine_tool.search_videos(query=query, count=count, duration=duration)
            uploaded_videos = []
            for idx, video in enumerate(results):
                if idx < len(videos_content.videos):
                    external_url = video.get("video_link") or video.get("link")

                    # Verify if the link is a valid video link
                    from urllib.parse import urlparse
                    parsed_url = urlparse(external_url)
                    if "youtube.com" in parsed_url.netloc and any(
                        parsed_url.path.startswith(prefix) for prefix in ["/channel/", "/user/", "/c/"]
                    ):
                        logger.warning(f"Skipping non-video YouTube link: {external_url}")
                        continue

                    # Prepare video data
                    video_data = VideoData(
                        external_url=external_url,
                        name=video.get("title", "Untitled Video"),
                        thumbnail_url=video.get("thumbnail"),
                        collection_id=collection_id,  # Assign collection ID
                    )
                    videos_content.videos[idx] = video_data

                    # Add to uploaded videos
                    uploaded_videos.append(video_data)

            if not uploaded_videos:
                logger.error("No valid videos found for upload.")
                videos_content.status = MsgStatus.error
                videos_content.status_message = "No valid videos found for upload."
                self.output_message.push_update()
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="No valid videos were found for upload.",
                )

            # Update success status
            videos_content.status = MsgStatus.success
            videos_content.status_message = f"Uploaded {len(uploaded_videos)} videos successfully."
            self.output_message.push_update()

            logger.info(f"Successfully uploaded {len(uploaded_videos)} videos.")
            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Video search and upload completed successfully.",
                data={"videos": [video.dict() for video in uploaded_videos]},
            )
        except requests.exceptions.RequestException as e:
            error_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            logger.exception(f"API request failed: Status code: {error_code}")
            error_message = "An error occurred during the video search."
            if isinstance(e, requests.exceptions.Timeout):
                error_message = "The search is taking longer than expected. Please try again."
            elif isinstance(e, requests.exceptions.HTTPError) and error_code == 429:
                error_message = "Rate limit exceeded. Please try again in a few minutes."
            videos_content.status = MsgStatus.error
            videos_content.status_message = error_message
            self.output_message.push_update()
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=error_message,
            )
