import os
import fal_client
import requests
import asyncio

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
}


class FalVideoGenerationTool:
    def __init__(self, api_key: str):
        if not api_key:
            raise Exception("FAL API key not found")
        # os.environ["FAL_KEY"] = api_key
        self.api_key = api_key
        self.queue_endpoint = "https://queue.fal.run"
        self.polling_interval = 10  # seconds

    async def text_to_video_async(
        self, prompt: str, save_at: str, duration: float, config: dict
    ):
        try:
            model_name = config.get(
                "model_name", "fal-ai/fast-animatediff/text-to-video"
            )

            headers = {"authorization": f"Key {self.api_key}"}
            fal_queue_payload = ({"prompt": prompt, "duration": duration},)
            fal_queue_endpoint = f"{self.queue_endpoint}/{model_name}"

            fal_response = requests.post(
                fal_queue_endpoint, headers=headers, json=fal_queue_payload
            )

            status_url = fal_response.json()["status_url"]
            response_url = fal_response.json()["response_url"]

            while True:
                response = requests.get(status_url, headers=headers)
                res = response.json()

                if res["status"] == "IN_QUEUE" or res["status"] == "IN_PROGRESS":
                    await asyncio.sleep(self.polling_interval)
                    continue
                elif res["status"] == "COMPLETED":
                    response = requests.get(response_url, headers=headers)
                    res = response.json()
                    print("res", res)
                    video_url = res["video"]["url"]
                    with open(save_at, "wb") as f:
                        f.write(requests.get(video_url).content)
                    break
                else:
                    raise ValueError(f"Unkown status for FAL request {res}")

        except Exception as e:
            raise Exception(f"Error generating video: {str(e)}")
        return {"status": "success", "video_path": save_at}

    def text_to_video(self, *args, **kwargs):
        return asyncio.run(self.text_to_video_async(*args, **kwargs))
