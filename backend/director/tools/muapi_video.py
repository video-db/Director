import os
import time
import requests
from typing import Optional


PARAMS_CONFIG = {
    "text_to_video": {
        "model_name": {
            "type": "string",
            "description": "The muapi.ai model to use for text-to-video generation",
            "default": "veo3-fast",
            "enum": [
                "veo3",
                "veo3-fast",
                "kling-master",
                "wan2.1",
                "wan2.2",
                "seedance-pro",
                "seedance-pro-fast",
                "runway",
                "pixverse",
                "hunyuan",
                "minimax-hailuo-02-std",
                "minimax-hailuo-02-pro",
            ],
        },
        "duration": {
            "type": "integer",
            "description": "Duration of the video in seconds",
            "default": 5,
            "minimum": 3,
            "maximum": 60,
        },
        "aspect_ratio": {
            "type": "string",
            "description": "Aspect ratio of the generated video",
            "default": "16:9",
            "enum": ["16:9", "9:16", "1:1", "4:3", "3:4"],
        },
    },
    "image_to_video": {
        "model_name": {
            "type": "string",
            "description": "The muapi.ai model to use for image-to-video generation",
            "default": "kling-master",
            "enum": [
                "kling-master",
                "kling-v2.5-pro",
                "wan2.1",
                "wan2.2",
                "seedance-pro",
                "seedance-pro-fast",
                "runway",
                "pixverse",
                "hunyuan",
                "vidu",
            ],
        },
        "duration": {
            "type": "integer",
            "description": "Duration of the video in seconds",
            "default": 5,
            "minimum": 3,
            "maximum": 60,
        },
        "aspect_ratio": {
            "type": "string",
            "description": "Aspect ratio of the generated video",
            "default": "16:9",
            "enum": ["16:9", "9:16", "1:1", "4:3", "3:4"],
        },
    },
}

# Endpoints are the model IDs themselves for muapi
T2V_ENDPOINTS = {
    "veo3": "veo3",
    "veo3-fast": "veo3-fast",
    "kling-master": "kling",
    "wan2.1": "wan2.1",
    "wan2.2": "wan2.2",
    "seedance-pro": "seedance-pro",
    "seedance-pro-fast": "seedance-pro-fast",
    "runway": "runway",
    "pixverse": "pixverse",
    "hunyuan": "hunyuan",
    "minimax-hailuo-02-std": "minimax-hailuo-02-std",
    "minimax-hailuo-02-pro": "minimax-hailuo-02-pro",
}

I2V_ENDPOINTS = {
    "kling-master": "kling-i2v",
    "kling-v2.5-pro": "kling-v2.5-pro-i2v",
    "wan2.1": "wan2.1-i2v",
    "wan2.2": "wan2.2-i2v",
    "seedance-pro": "seedance-pro-i2v",
    "seedance-pro-fast": "seedance-pro-fast-i2v",
    "runway": "runway-i2v",
    "pixverse": "pixverse-i2v",
    "hunyuan": "hunyuan-i2v",
    "vidu": "vidu-i2v",
}


class MuApiVideoGenerationTool:
    """Video generation tool using muapi.ai's 400+ model aggregator API."""

    BASE_URL = "https://api.muapi.ai/api/v1"
    POLL_INTERVAL = 5  # seconds

    def __init__(self, api_key: str):
        if not api_key:
            raise Exception(
                "MUAPI_API_KEY not found. Get one at https://muapi.ai/dashboard/api-keys"
            )
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {"x-api-key": self.api_key, "Content-Type": "application/json"}
        )

    def _submit(self, endpoint: str, payload: dict) -> str:
        """Submit a generation request and return the request_id."""
        resp = self.session.post(f"{self.BASE_URL}/{endpoint}", json=payload, timeout=30)
        resp.raise_for_status()
        try:
            request_id = resp.json()["request_id"]
        except KeyError:
            raise Exception(
                f"MuAPI did not return a request_id. Response: {resp.text}"
            )
        return request_id

    def _poll(self, request_id: str, timeout: int = 600) -> str:
        """Poll until the generation completes and return the output URL."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self.session.get(
                f"{self.BASE_URL}/predictions/{request_id}/result", timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "pending")
            if status == "completed":
                outputs = data.get("outputs", [])
                if not outputs:
                    raise Exception("Completed but no outputs returned")
                return outputs[0]
            if status in ("failed", "cancelled"):
                raise Exception(f"Video generation {status}: {data.get('error', '')}")
            time.sleep(self.POLL_INTERVAL)
        raise Exception(f"Video generation timed out after {timeout}s")

    def text_to_video(
        self, prompt: str, save_at: str, duration: float, config: dict
    ) -> dict:
        """Generate a video from a text prompt using muapi.ai."""
        model_name = config.get("model_name", "veo3-fast")
        endpoint = T2V_ENDPOINTS.get(model_name, model_name)

        payload = {
            "prompt": prompt,
            "duration": int(duration),
            "aspect_ratio": config.get("aspect_ratio", "16:9"),
        }

        try:
            request_id = self._submit(endpoint, payload)
            video_url = self._poll(request_id)
            video_data = requests.get(video_url, timeout=120)
            video_data.raise_for_status()
            with open(save_at, "wb") as f:
                f.write(video_data.content)
        except Exception as e:
            raise Exception(f"Error generating video: {type(e).__name__}: {str(e)}") from e

        return {"status": "success", "video_path": save_at}

    def image_to_video(
        self,
        image_url: str,
        save_at: str,
        duration: float,
        config: dict,
        prompt: Optional[str] = None,
    ) -> dict:
        """Generate a video from an image URL using muapi.ai."""
        model_name = config.get("model_name", "kling-master")
        endpoint = I2V_ENDPOINTS.get(model_name, f"{model_name}-i2v")

        payload: dict = {
            "image_url": image_url,
            "duration": int(duration),
            "aspect_ratio": config.get("aspect_ratio", "16:9"),
        }
        if prompt:
            payload["prompt"] = prompt

        try:
            request_id = self._submit(endpoint, payload)
            video_url = self._poll(request_id)
            video_data = requests.get(video_url, timeout=120)
            video_data.raise_for_status()
            with open(save_at, "wb") as f:
                f.write(video_data.content)
        except Exception as e:
            raise Exception(f"Error generating video: {type(e).__name__}: {str(e)}") from e

        return {"status": "success", "video_path": save_at}
