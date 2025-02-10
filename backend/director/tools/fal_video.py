import os
import fal_client
import requests
from typing import Optional


PARAMS_CONFIG = {
    "text_to_video": {
        "model_name": {
            "type": "string",
            "description": "The model name to use for video generation",
            "default": "fal-ai/fast-animatediff/text-to-video",
            "enum": [
                "fal-ai/minimax-video",
                "fal-ai/mochi-v1",
                "fal-ai/hunyuan-video",
                "fal-ai/luma-dream-machine",
                "fal-ai/kling-video/v1/standard/text-to-video",
                "fal-ai/kling-video/v1.5/pro/text-to-video",
                "fal-ai/cogvideox-5b",
                "fal-ai/ltx-video",
                "fal-ai/fast-svd/text-to-video",
                "fal-ai/fast-svd-lcm/text-to-video",
                "fal-ai/t2v-turbo",
                "fal-ai/fast-animatediff/text-to-video",
                "fal-ai/fast-animatediff/turbo/text-to-video",
                # "fal-ai/animatediff-sparsectrl-lcm",
            ],
        },
    },
    "image_to_video": {
        "model_name": {
            "type": "string",
            "description": "The model name to use for image-to-video generation",
            "default": "fal-ai/fast-svd-lcm",
            "enum": [
                "fal-ai/haiper-video/v2/image-to-video",
                "fal-ai/luma-dream-machine/image-to-video",
                # "fal-ai/kling-video/v1/standard/image-to-video",
                # "fal-ai/kling-video/v1/pro/image-to-video",
                # "fal-ai/kling-video/v1.5/pro/image-to-video",
                "fal-ai/cogvideox-5b/image-to-video",
                "fal-ai/ltx-video/image-to-video",
                "fal-ai/stable-video",
                "fal-ai/fast-svd-lcm",
            ],
        },
    },
    "image_to_image": {
        "model_name": {
            "type": "string",
            "description": "The model name to use for image-to-image transformation",
            "default": "fal-ai/flux-lora-canny",
            "enum": [
                "fal-ai/flux-pro/v1.1-ultra/redux",
                "fal-ai/flux-lora-canny",
                "fal-ai/flux-lora-depth",
                "fal-ai/ideogram/v2/turbo/remix",
                "fal-ai/iclight-v2",
            ],
        },
    },
}


class FalVideoGenerationTool:
    def __init__(self, api_key: str):
        if not api_key:
            raise Exception("FAL API key not found")
        self.api_key = api_key
        self.queue_endpoint = "https://queue.fal.run"
        self.polling_interval = 10  # seconds

    def text_to_video(
        self, prompt: str, save_at: str, duration: float, config: dict
    ):
        """
        Generates a video from using text-to-video models.
        """
        try:
            model_name = config.get("model_name", "fal-ai/minimax-video")
            res = fal_client.run(
                model_name,
                arguments={"prompt": prompt, "duration": duration},
            )
            video_url = res["video"]["url"]
            with open(save_at, "wb") as f:
                f.write(requests.get(video_url).content)

        except Exception as e:
            raise Exception(f"Error generating video: {type(e).__name__}: {str(e)}")

        return {"status": "success", "video_path": save_at}

    def image_to_video(
        self,
        image_url: str,
        save_at: str,
        duration: float,
        config: dict,
        prompt: Optional[str] = None,
    ):
        """
        Generate video from an image URL.
        """
        try:
            model_name = config.get("model_name", "fal-ai/fast-svd-lcm")
            arguments = {"image_url": image_url, "duration": duration}

            if model_name == "fal-ai/haiper-video/v2/image-to-video":
                arguments["duration"] = 6

            if prompt:
                arguments["prompt"] = prompt

            res = fal_client.run(
                model_name,
                arguments=arguments,
            )

            video_url = res["video"]["url"]

            with open(save_at, "wb") as f:
                f.write(requests.get(video_url).content)
        except Exception as e:
            raise Exception(f"Error generating video: {type(e).__name__}: {str(e)}")

    def image_to_image(self, image_url: str, prompt: str, config: dict):
        try:
            model_name = config.get("model_name", "fal-ai/flux-lora-canny")
            arguments = {"image_url": image_url, "prompt": prompt}

            res = fal_client.run(
                model_name,
                arguments=arguments,
            )

            print("we got this response", res)
            return res["images"]

        except Exception as e:
            raise Exception(f"Error generating image: {type(e).__name__}: {str(e)}")
