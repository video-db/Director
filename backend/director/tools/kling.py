import requests
import time
import jwt

PARAMS_CONFIG = {
    "text_to_video": {
        "model": {
            "type": "string",
            "description": "Model to use for video generation",
            "enum": ["kling-v1"],
            "default": "kling-v1",
        },
        "negative_prompt": {
            "type": "string",
            "description": "Negative text prompt",
            "maxLength": 5200,
        },
        "cfg_scale": {
            "type": "number",
            "description": "Flexibility in video generation. The higher the value, "
            "the lower the model's degree of flexibility and the "
            "stronger the relevance to the user's prompt",
            "minimum": 0,
            "maximum": 1,
            "default": 0.5,
        },
        "mode": {
            "type": "string",
            "description": "Video generation mode",
            "enum": ["std", "pro"],
            "default": "std",
        },
        "camera_control": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Type of camera movement. Options are:\n"
                    "- simple: Basic camera movement, configurable via config\n"
                    "- none: No camera movement\n"
                    "- down_back: Camera descends and moves backward with pan down and\n"
                    "  zoom out effect\n"
                    "- forward_up: Camera moves forward and tilts up with zoom in\n"
                    "  and pan up effect\n"
                    "- right_turn_forward: Camera rotates right while moving forward\n"
                    "- left_turn_forward: Camera rotates left while moving forward",
                    "enum": [
                        "simple",
                        "none",
                        "down_back",
                        "forward_up",
                        "right_turn_forward",
                        "left_turn_forward",
                    ],
                    "default": "none",
                },
                "config": {
                    "type": "object",
                    "description": "Contains 8 fields to specify the camera's movement or change in different directions, This should only be passed if type is simple",
                    "properties": {
                        "horizontal": {
                            "type": "number",
                            "description": "Controls the camera's movement along the horizontal axis (translation along the x-axis). Value range: [-10, 10], negative value indicates translation to the left, positive value indicates translation to the right",
                            "minimum": -10,
                            "maximum": 10,
                            "default": 0,
                        },
                        "vertical": {
                            "type": "number",
                            "description": "Controls the camera's movement along the vertical axis (translation along the y-axis). Value range: [-10, 10], negative value indicates a downward translation, positive value indicates an upward translation",
                            "minimum": -10,
                            "maximum": 10,
                            "default": 0,
                        },
                        "pan": {
                            "type": "number",
                            "description": "Controls the camera's rotation in the horizontal plane (rotation around the y-axis). Value range: [-10, 10], negative value indicates rotation to the left, positive value indicates rotation to the right",
                            "minimum": -10,
                            "maximum": 10,
                            "default": 0,
                        },
                        "tilt": {
                            "type": "number",
                            "description": "Controls the camera's rotation in the vertical plane (rotation around the x-axis). Value range: [-10, 10], negative value indicates downward rotation, positive value indicates upward rotation",
                            "minimum": -10,
                            "maximum": 10,
                            "default": 0,
                        },
                        "roll": {
                            "type": "number",
                            "description": "Controls the camera's rolling amount (rotation around the z-axis). Value range: [-10, 10], negative value indicates counterclockwise rotation, positive value indicates clockwise rotation",
                            "minimum": -10,
                            "maximum": 10,
                            "default": 0,
                        },
                        "zoom": {
                            "type": "number",
                            "description": "Controls the change in the camera's focal length, affecting the proximity of the field of view. Value range: [-10, 10], negative value indicates increase in focal length (narrower field of view), positive value indicates decrease in focal length (wider field of view)",
                            "minimum": -10,
                            "maximum": 10,
                            "default": 0,
                        },
                    },
                },
            },
        },
    }
}


class KlingAITool:
    def __init__(self, access_key: str, secret_key: str):
        self.api_route = "https://api.klingai.com"
        self.video_endpoint = f"{self.api_route}/v1/videos/text2video"
        self.access_key = access_key
        self.secret_key = secret_key
        self.polling_interval = 30  # seconds

    def get_authorization_token(self):
        headers = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "iss": self.access_key,
            "exp": int(time.time()) + 1800,  # Valid for 30 minutes
            "nbf": int(time.time()) - 5,  # Start 5 seconds ago
        }
        token = jwt.encode(payload, self.secret_key, headers=headers)
        return token

    def text_to_video(
        self, prompt: str, save_at: str, duration: float, config: dict
    ):
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

            print("Kling Response", response)

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