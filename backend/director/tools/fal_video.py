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
        os.environ["FAL_KEY"] = api_key
        self.polling_interval = 10  # seconds

    async def text_to_video_async(
        self, prompt: str, save_at: str, duration: float, config: dict
    ):
        try:
            model_name = config.get(
                "model_name", "fal-ai/fast-animatediff/text-to-video"
            )
            handler = await fal_client.submit_async(
                model_name,
                arguments={"prompt": prompt, "duration": duration},
            )

            request_id = handler.request_id

            while True:
                result_response = await fal_client.status_async(model_name, request_id)

                if isinstance(
                    result_response, (fal_client.InProgress, fal_client.Queued)
                ):
                    await asyncio.sleep(self.polling_interval)
                    continue
                elif isinstance(result_response, fal_client.Completed):
                    result_response = await fal_client.result_async(
                        model_name, request_id
                    )
                    video_url = result_response["video"]["url"]
                    with open(save_at, "wb") as f:
                        f.write(requests.get(video_url).content)
                    break
                else:
                    raise ValueError(f"Unkown status for FAL request {result_response}")

        except Exception as e:
            raise Exception(f"Error generating video: {str(e)}")

        return {"status": "success", "video_path": save_at}

    def text_to_video(self, *args, **kwargs):
        return asyncio.run(self.text_to_video_async(*args, **kwargs))
