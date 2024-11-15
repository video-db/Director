import requests
import time


class KlingAITool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_route = "https://api.klingai.com"
        self.video_endpoint = f"{self.api_route}/v1/videos/text2video"

    def text_to_video(self, prompt: str, save_at: str, duration: float, config: dict):
        """
        Generate a video from a text prompt using KlingAI's API.
        :param str prompt: The text prompt to generate the video
        :param str save_at: File path to save the generated video
        :param float duration: Duration of the video in seconds
        :param dict config: Additional configuration options
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "model": config.get("model", "default_model"),
            "duration": duration,
            **config,  # Include any additional configuration parameters
        }

        response = requests.post(self.video_endpoint, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Error generating video: {response.text}")

        # Assuming the API returns a job ID for asynchronous processing
        job_id = response.json().get("job_id")
        if not job_id:
            raise Exception("No job ID returned from the API.")

        # Polling for the video generation completion
        result_endpoint = f"{self.api_route}/v1/videos/result/{job_id}"

        while True:
            result_response = requests.get(
                result_endpoint, headers={"Authorization": f"Bearer {self.api_key}"}
            )

            if result_response.status_code == 200:
                # Video generation is complete
                with open(save_at, "wb") as f:
                    f.write(result_response.content)
                break
            elif result_response.status_code == 202:
                # Still processing
                time.sleep(5)
                continue
            else:
                raise Exception(f"Error fetching video: {result_response.text}")
