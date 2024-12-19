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
        :return: A list of filtered video results.
        """
        params = {
            "q": query,
            "tbm": "vid",
            "num": count,
            "hl": "en",
            "gl": "us",
            "api_key": self.api_key,
        }

        # Map duration values to SerpApi's expected format
        duration_mapping = {
            "short": "dur:s",
            "medium": "dur:m",
            "long": "dur:l",
        }

        if duration:
            if duration not in duration_mapping:
                raise ValueError(f"Invalid duration value: {duration}")
            params["tbs"] = duration_mapping[duration]  # Add duration filter

        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            raw_results = response.json().get("video_results", [])

            # Filter results to include only valid YouTube or downloadable links
            filtered_results = []
            for result in raw_results:
                link = result.get("link", "")
                video_link = result.get("video_link", "")

                # Skip channels or invalid links
                if "channel" in link or "user" in link:
                    continue

                # Prefer YouTube videos or links with valid video_link
                if "youtube.com/watch" in link or video_link:
                    filtered_results.append({
                        "link": link,
                        "video_link": video_link,
                        "title": result.get("title"),
                        "thumbnail": result.get("thumbnail"),
                        "duration": result.get("duration"),
                    })

            return filtered_results

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error during SerpAPI video search: {e}")
