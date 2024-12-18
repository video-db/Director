import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SerpAPI:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required for SerpAPI.")
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search.json"

        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def search_videos(self, query: str, count: int, duration: str = None) -> list:
        """
        Perform a video search using SerpAPI.
        :param query: Search query for the video.
        :param count: Number of video results to retrieve.
        :param duration: Filter videos by duration (short, medium, long).
        :return: A list of video results.
        """
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
            "long": "long",
        }
        if duration:
            if duration not in duration_mapping:
                raise ValueError(f"Invalid duration value: {duration}")
            params["video_duration"] = duration_mapping[duration]

        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get("video_results", [])
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error during SerpAPI video search: {e}")
