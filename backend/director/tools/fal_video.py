import os
import fal_client
import requests
import asyncio
import aiohttp
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
                "fal-ai/animatediff-sparsectrl-lcm",
            ],
        },
    },
    "image_to_video": {
        "model_name": {
            "type": "string",
            "description": "The model name to use for image-to-video generation",
            "default": "fal-ai/fast-svd-lcm",
            "enum": [
                "fal-ai/haiper-video-v2/image-to-video",
                "fal-ai/luma-dream-machine/image-to-video",
                "fal-ai/kling-video/v1/standard/image-to-video",
                "fal-ai/kling-video/v1/pro/image-to-video",
                "fal-ai/kling-video/v1.5/pro/image-to-video",
                "fal-ai/cogvideox-5b/image-to-video",
                "fal-ai/ltx-video/image-to-video",
                "fal-ai/stable-video",
                "fal-ai/fast-svd-lcm",
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

    async def text_to_video_async(
        self, prompt: str, save_at: str, duration: float, config: dict
    ):
        """
        Generates a video asynchronously by calling the Fal text-to-video API using aiohttp.
        """
        try:
            model_name = config.get(
                "model_name", "fal-ai/fast-animatediff/text-to-video"
            )

            headers = {"authorization": f"Key {self.api_key}"}
            fal_queue_payload = {"prompt": prompt, "duration": duration}
            fal_queue_endpoint = f"{self.queue_endpoint}/{model_name}"

            async with aiohttp.ClientSession() as session:
                # Submit job to Fal queue
                fal_response = await session.post(
                    fal_queue_endpoint, headers=headers, json=fal_queue_payload
                )
                fal_response_json = await fal_response.json()

                if (
                    "status_url" not in fal_response_json
                    or "response_url" not in fal_response_json
                ):
                    raise ValueError(
                        f"Invalid response from FAL queue: Missing 'status_url' or 'response_url'. Response: {fal_response_json}"
                    )

                status_url = fal_response_json["status_url"]
                response_url = fal_response_json["response_url"]

                # Poll for status
                while True:
                    status_response = await session.get(status_url, headers=headers)
                    status_json = await status_response.json()

                    if "status" not in status_json: 
                        raise ValueError(
                            f"Invalid response from FAL queue: Missing 'status'. Response: {status_json}"
                        )

                    if status_json["status"] in ["IN_QUEUE", "IN_PROGRESS"]:
                        await asyncio.sleep(self.polling_interval)
                        continue
                    elif status_json["status"] == "COMPLETED":
                        # Fetch results
                        response = await session.get(response_url, headers=headers)
                        res = await response.json()

                        video_url = res["video"]["url"]

                        # Download the video
                        async with session.get(video_url) as video_response:
                            with open(save_at, "wb") as f:
                                f.write(await video_response.read())
                        break
                    else:
                        raise ValueError(
                            f"Unknown status for FAL request: {status_json}"
                        )

        except Exception as e:
            raise Exception(f"Error generating video: {type(e).__name__}: {str(e)}")

        return {"status": "success", "video_path": save_at}

    def text_to_video(self, *args, **kwargs):
        """
        Blocking call to generate video (synchronous wrapper around the async method).
        """
        return asyncio.run(self.text_to_video_async(*args, **kwargs))

    def image_to_video(
        self, image_url: str, save_at: str, duration: float, config: dict, prompt: Optional[str] = None
    ):
        """
        Generate video from an image URL.
        """
        try:
            model_name = config.get("model_name", "fal-ai/fast-svd-lcm")
            arguments = {"image_url": image_url, "duration": duration}

            if model_name == "fal-ai/haiper-video-v2/image-to-video":
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
