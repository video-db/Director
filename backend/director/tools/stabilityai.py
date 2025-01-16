import requests
import time
import asyncio
from PIL import Image
import io

from director.utils.asyncio import is_event_loop_running

PARAMS_CONFIG = {
    "text_to_video": {
        "strength": {
            "type": "number",
            "description": "Image influence on output",
            "minimum": 0,
            "maximum": 1,
        },
        "negative_prompt": {
            "type": "string",
            "description": "Keywords to exclude from output",
        },
        "seed": {
            "type": "integer",
            "description": "Randomness seed for generation",
        },
        "cfg_scale": {
            "type": "number",
            "description": "How strongly video sticks to original image",
            "minimum": 0,
            "maximum": 10,
            "default": 1.8,
        },
        "motion_bucket_id": {
            "type": "integer",
            "description": "Controls motion amount in output video",
            "minimum": 1,
            "maximum": 255,
            "default": 127,
        },
    },
    "image_to_video": {
        "seed": {
            "type": "integer",
            "description": "Randomness seed for generation",
        },
        "cfg_scale": {
            "type": "number",
            "description": "Control how strongly the output adheres to the input image",
            "minimum": 0,
            "maximum": 10,
            "default": 1.8,
        },
        "motion_bucket_id": {
            "type": "integer",
            "description": "Controls motion amount in the output video",
            "minimum": 1,
            "maximum": 255,
            "default": 127,
        },
    },
}


class StabilityAITool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.image_endpoint = (
            "https://api.stability.ai/v2beta/stable-image/generate/ultra"
        )
        self.video_endpoint = "https://api.stability.ai/v2beta/image-to-video"
        self.result_endpoint = "https://api.stability.ai/v2beta/image-to-video/result"
        self.polling_interval = 10  # seconds

    async def text_to_video_async(
        self, prompt: str, save_at: str, duration: float, config: dict
    ):
        """
        Generate a video from a text prompt using Stability AI's API.
        First generates an image from text, then converts it to video.
        :param str prompt: The text prompt to generate the video
        :param str save_at: File path to save the generated video
        :param float duration: Duration of the video in seconds
        :param dict config: Additional configuration options
        """
        # First generate image from text
        headers = {"authorization": f"Bearer {self.api_key}", "accept": "image/*"}

        image_payload = {
            "prompt": prompt,
            "output_format": config.get("format", "png"),
            "aspect_ratio": config.get("aspect_ratio", "16:9"),
            "negative_prompt": config.get("negative_prompt", ""),
        }

        image_response = requests.post(
            self.image_endpoint, headers=headers, files={"none": ""}, data=image_payload
        )

        if image_response.status_code != 200:
            raise Exception(f"Error generating image: {image_response.text}")

        image = Image.open(io.BytesIO(image_response.content))

        # Set the new dimensions
        new_width = 1024
        new_height = int(new_width * (576 / 1024))  # Maintain the 16:9 aspect ratio

        # Resize the image
        scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        temp_image_path = f"{save_at}.temp.png"

        # Save temporary image
        scaled_image.save(temp_image_path)

        # Generate video from the image
        video_headers = {"authorization": f"Bearer {self.api_key}"}

        video_payload = {
            "seed": config.get("seed", 0),
            "cfg_scale": config.get("cfg_scale", 1.8),
            "motion_bucket_id": config.get("motion_bucket_id", 127),
        }

        with open(temp_image_path, "rb") as img_file:
            video_response = requests.post(
                self.video_endpoint,
                headers=video_headers,
                files={"image": img_file},
                data=video_payload,
            )

        if video_response.status_code != 200:
            raise Exception(f"Error generating video: {video_response.text}")

        # Get generation ID and wait for completion
        generation_id = video_response.json().get("id")
        if not generation_id:
            raise Exception("No generation ID in response")

        # Poll for completion
        result_headers = {
            "accept": "video/*",
            "authorization": f"Bearer {self.api_key}",
        }

        while True:
            result_response = requests.get(
                f"{self.result_endpoint}/{generation_id}", headers=result_headers
            )

            if result_response.status_code == 202:
                # Still processing
                await asyncio.sleep(self.polling_interval)
                continue
            elif result_response.status_code == 200:
                with open(save_at, "wb") as f:
                    f.write(result_response.content)
                break
            else:
                raise Exception(f"Error fetching video: {result_response.text}")

    def text_to_video(self, *args, **kwargs):
        """
        Synchronous wrapper for text-to-video generation.
        """
        return asyncio.run(self.text_to_video_async(*args, **kwargs))

    def image_to_video(
        self, image_url: str, save_at: str, duration: float, config: dict
    ):
        """
        Generate a video from an image using Stability AI's API.
        """
        headers = {"authorization": f"Bearer {self.api_key}"}

        image_response = requests.get(image_url)
        if image_response.status_code != 200:
            raise Exception(f"Failed to fetch image from URL: {image_response.text}")

        image = Image.open(io.BytesIO(image_response.content))
        target_dimensions = (1024, 576)
        if image.width < image.height:
            target_dimensions = (576, 1024)
        elif image.width == image.height:
            target_dimensions = (768, 768)

        resized_image = image.resize(target_dimensions, Image.Resampling.LANCZOS)
        temp_image_path = f"{save_at}.temp.png"
        resized_image.save(temp_image_path, format="PNG")

        video_payload = {
            "duration": (None, str(duration)),
            "seed": (None, str(config.get("seed", 0))),
            "cfg_scale": (None, str(config.get("cfg_scale", 1.8))),
            "motion_bucket_id": (None, str(config.get("motion_bucket_id", 127))),
        }

        with open(temp_image_path, "rb") as img_file:
            files = {"image": ("image.png", img_file, "image/png")}
            video_response = requests.post(
                self.video_endpoint,
                headers=headers,
                files={**video_payload, **files},
            )

        if video_response.status_code != 200:
            raise Exception(f"Error initiating video generation: {video_response.text}")
        # Get generation ID and wait for completion
        generation_id = video_response.json().get("id")
        if not generation_id:
            raise Exception("No generation ID in response")
        # Poll for completion
        result_headers = {
            "accept": "video/*",
            "authorization": f"Bearer {self.api_key}",
        }

        while True:
            result_response = requests.get(
                f"{self.result_endpoint}/{generation_id}", headers=result_headers
            )

            if result_response.status_code == 202:
                time.sleep(self.polling_interval)
                continue
            elif result_response.status_code == 200:
                # Generation complete, save video
                with open(save_at, "wb") as f:
                    f.write(result_response.content)
                break
            else:
                raise Exception(f"Error fetching video: {result_response.text}")

