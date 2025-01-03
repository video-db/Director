import os
import fal_client
import requests

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
                "fal-ai/haiper-video-v2",
                "fal-ai/minimax/video-01-live",
                "fal-ai/ltx-video",
            ],
        },
    },
}


class FalVideoGenerationTool:
    def __init__(self, api_key: str):
        if not api_key:
            raise Exception("FAL API key not found")
        os.environ["FAL_KEY"] = api_key

    def text_to_video(self, prompt: str, save_at: str, duration: float, config: dict):
        try:
            model_name = config.get("model_name", "fal-ai/fast-animatediff/text-to-video")
            res = fal_client.run(
                model_name,
                arguments={"prompt": prompt, "duration": duration},
            )
            video_url = res["video"]["url"]

            with open(save_at, "wb") as f:
                f.write(requests.get(video_url).content)
        except Exception as e:
            raise Exception(f"Error generating video: {str(e)}")
