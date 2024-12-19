import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class SerpApi:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Please provide a valid SerpApi key")
        self.api_key = api_key
        self.base_url = 'https://serpapi.com/search'

        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def search(self, query: str, max_results: int = 5, content_type: str = 'text'):
        params = {
            "hl": "en",
            "gl": "us",
            'q': query,
            'num': max_results,
            'api_key': self.api_key,
        }

        # For text/normal google search
        if content_type == 'text':
            params['engine'] = 'google'

        # For videos search
        if content_type == 'videos':
            params['tbm'] = 'vid'
            params['engine'] = 'google_videos'

        # For future implementation of image search
        # if content_type == 'images':
        #     params['ijn'] = "0"
        #     params['tbm'] = 'isch'
        #     params['engine'] = 'google_images'

        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error while making request to SerpApi: {e}")