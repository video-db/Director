import requests
import time
import jwt


class KlingAITool:
    def __init__(self, access_key: str, secret_key: str):
        self.api_route = "https://api.klingai.com"
        self.video_endpoint = f"{self.api_route}/v1/videos/text2video"
        self.access_key = access_key
        self.secret_key = secret_key
        self.polling_interval = 5

    def get_authorization_token(self):
        headers = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "iss": self.access_key,
            "exp": int(time.time()) + 1800,  # Valid for 30 minutes
            "nbf": int(time.time()) - 5,  # Start 5 seconds ago
        }
        token = jwt.encode(payload, self.secret_key, headers=headers)
        return token

    def text_to_video(self, prompt: str, save_at: str, duration: float, config: dict):
        """
        Generate a video from a text prompt using KlingAI's API.
        :param str prompt: The text prompt to generate the video
        :param str save_at: File path to save the generated video
        :param float duration: Duration of the video in seconds
        :param dict config: Additional configuration options
        """
        api_key = self.get_authorization_token()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "model": config.get("model", "kling-v1"),
            "duration": duration,
            **config,  # Include any additional configuration parameters
        }

        response = requests.post(self.video_endpoint, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"Error generating video: {response.text}")

        # Assuming the API returns a job ID for asynchronous processing
        job_id = response.json()["data"].get("task_id")
        if not job_id:
            raise Exception("No task ID returned from the API.")

        # Polling for the video generation completion
        result_endpoint = f"{self.api_route}/v1/videos/text2video/{job_id}"

        while True:
            response = requests.get(
                result_endpoint, headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()

            status = response.json()["data"]["task_status"]

            if status == "succeed":
                # Video generation is complete
                video_url = response.json()["data"]["task_result"]["videos"][0]["url"]
                # Download and save the video
                video_response = requests.get(video_url)
                video_response.raise_for_status()
                with open(save_at, "wb") as f:
                    f.write(video_response.content)
                break
            else:
                # Still processing
                time.sleep(self.polling_interval)
                continue
