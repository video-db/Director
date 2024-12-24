import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SerpAPI:
    BASE_URL = "https://serpapi.com/search.json"
    RETRY_TOTAL = 3
    RETRY_BACKOFF_FACTOR = 1
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

    def __init__(self, api_key: str, base_url: str = None, timeout: int = 10):
        """
        Initialize the SerpAPI client.
        :param api_key: API key for SerpAPI.
        :param base_url: Optional base URL for the API.
        :param timeout: Timeout for API requests in seconds.
        """
        if not api_key:
            raise ValueError("API key is required for SerpAPI.")
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout

        # Configure retries
        retry_strategy = Retry(
            total=self.RETRY_TOTAL,
            backoff_factor=self.RETRY_BACKOFF_FACTOR,
            status_forcelist=self.RETRY_STATUS_CODES,
        )
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)

    def search_videos(self, query: str, count: int, duration: str = None) -> list:
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")
        if not isinstance(count, int) or count < 1:
            raise ValueError("Count must be a positive integer.")
        """
        Perform a video search using SerpAPI.
        :param query: Search query for the video.
        :param count: Number of video results to retrieve.
        :param duration: Filter videos by duration (short, medium, long).
        :return: A list of raw video results from SerpAPI.
        """
        params = {
            "q": query,
            "tbm": "vid",
            "num": count,
            "hl": "en",
            "gl": "us",
            "api_key": self.api_key,
        }

        # Map duration values to SerpAPI's expected format
        duration_mapping = {
            "short": "dur:s",
            "medium": "dur:m",
            "long": "dur:l",
        }

        if duration:
            if duration not in duration_mapping:
                raise ValueError(f"Invalid duration value: {duration}")
            params["tbs"] = duration_mapping[duration]

        try:
            response = self.session.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError as e:
                raise RuntimeError("Invalid JSON response from SerpAPI") from e
            
            results = data.get("video_results")
            if results is None:
                raise RuntimeError("Unexpected response format: 'video_results' not found")
            return results
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error during SerpAPI video search: {e}") from e
