import requests
import time
from PIL import Image
import io


class StabilityAITool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.image_endpoint = (
            "https://api.stability.ai/v2beta/stable-image/generate/sd3"
        )
        self.video_endpoint = "https://api.stability.ai/v2beta/image-to-video"
        self.result_endpoint = "https://api.stability.ai/v2beta/image-to-video/result"

    def text_to_video(self, prompt: str, save_at: str, duration: float, config: dict):
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
            "output_format": "png",
            "aspect_ratio": "16:9",
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
            result_response = requests.request(
                "GET", f"{self.result_endpoint}/{generation_id}", headers=result_headers
            )

            if result_response.status_code == 202:
                # Still processing
                time.sleep(10)
                continue
            elif result_response.status_code == 200:
                # Generation complete, save video
                with open(save_at, "wb") as f:
                    f.write(result_response.content)
                break
            else:
                raise Exception(str(result_response.json()))
