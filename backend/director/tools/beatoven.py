import time
from typing import Optional
import requests
import logging

logger = logging.getLogger(__name__)

PARAMS_CONFIG = {
    "sound_effect": {"prompt": {"type": "string", "description": "An example"}}
}


class BeatovenTool:
    def __init__(self, api_key: str):
        if not api_key:
            raise Exception("Beatoven API key not found")
        self.api_key = api_key
        self.base_url = "https://public-api.beatoven.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def generate_music(
        self, prompt: str, save_at: str, duration: float
    ):
        """
        Generate a sound effect using Beatoven API
        """
        try:
            create_response = requests.post(
                f"{self.base_url}/api/v1/tracks",
                headers=self.headers,
                json={"prompt": {"text": f"{duration} seconds {prompt}"}},
            )
            create_response.raise_for_status()
            create_data = create_response.json()
            track_id = create_data["tracks"][0]

            compose_response = requests.post(
                f"{self.base_url}/api/v1/tracks/compose/{track_id}",
                headers=self.headers,
                json={"format": "mp3", "looping": False},
            )
            compose_response.raise_for_status()
            compose_data = compose_response.json()
            task_id = compose_data["task_id"]

            while True:
                status_response = requests.get(
                    f"{self.base_url}/api/v1/tasks/{task_id}", headers=self.headers
                )
                status_response.raise_for_status()
                status_data = status_response.json()

                if status_data["status"] == "composed":
                    track_url = status_data["meta"]["track_url"]
                    audio_response = requests.get(track_url)
                    audio_response.raise_for_status()

                    with open(save_at, "wb") as f:
                        f.write(audio_response.content)
                    break
                elif status_data["status"] in ["composing", "running"]:
                    time.sleep(5)
                else:
                    raise Exception(f"Unexpected status: {status_data['status']}")

        except Exception as e:
            raise Exception(f"Error generating sound effect: {str(e)}")
