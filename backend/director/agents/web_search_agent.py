import logging
import requests
import os
from dotenv import load_dotenv

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    TextContent,
    MsgStatus,
)

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
        base_url = "https://serpapi.com/search.json"
        params = {
            "q": query,
            "tbm": "vid",
            "num": count,
            "hl": "en",
            "gl": "us",
            "api_key": self.api_key,
        }

        # Map duration values to API's expected format
        duration_mapping = {
            "short": "short",
            "medium": "medium",
            "long": "long"
        }
        if duration:
            if duration not in duration_mapping:
                raise ValueError(f"Invalid duration value: {duration}")
            params["video_duration"] = duration_mapping[duration]

        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)

        text_content = TextContent(
            agent_name=self.agent_name,
            status=MsgStatus.progress,
            status_message=f"Searching for videos: {query}...",
        )
        self.output_message.content.append(text_content)
        self.output_message.push_update()

        try:
            response = session.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            raw_response = response.json()

            results = raw_response.get("video_results", [])
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
                    "source": r.get("link") or "",
                    "source_type": "url",
                    "media_type": "video",
                    "name": r.get("title") or f"Untitled Video {idx + 1}",
                    "collection_id": collection_id,
                    "thumbnail": r.get("thumbnail") or None,
                    "duration": r.get("duration") or "unknown",
                }
                for idx, r in enumerate(results)
                if r.get("link")
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

        except requests.exceptions.RequestException as e:
            error_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            logger.exception(f"API request failed in {self.agent_name}: {e}, Status code: {error_code}")

            # Generic user-facing messages
            error_message = "API request failed. Please try again later."
            if isinstance(e, requests.exceptions.Timeout):
                error_message = "The search is taking longer than expected. Please try again."
            elif isinstance(e, requests.exceptions.TooManyRedirects):
                error_message = "Unable to complete the search. Please try again."
            elif isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code == 429:
                    error_message = "Rate limit exceeded. Please try again in a few minutes."
                elif e.response.status_code == 401:
                    error_message = "API authentication failed. Please check your API key."
                elif e.response.status_code >= 500:
                    error_message = "Search service is temporarily unavailable. Please try again later."

            text_content.status = MsgStatus.error
            text_content.status_message = error_message
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=error_message,
            )
