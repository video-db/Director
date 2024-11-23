import logging
import json
import os
from typing import List
import uuid
import requests
from PIL import Image
import io

from videodb.asset import VideoAsset, ImageAsset, AudioAsset, TextAsset, TextStyle
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    MsgStatus,
    VideoContent,
    VideoData,
    ContextMessage,
    RoleTypes,
)
from director.tools.elevenlabs import ElevenLabsTool
from director.tools.videodb_tool import VideoDBTool
from director.llm.openai import OpenAI, OpenaiConfig
from director.tools.replicate import flux_dev

from director.constants import DOWNLOADS_PATH

logger = logging.getLogger(__name__)


class StoryboardingAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "storyboarding"
        self.description = "Agent for generating storyboards using Gen AI models on given app description and steps."
        self.llm = OpenAI(config=OpenaiConfig(timeout=120))
        self.parameters = self.get_parameters()
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        app_description: str,
        raw_steps: List[str],
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Process the app_description and steps to generate a storyboard video.

        :param str collection_id: The collection ID to store the generated audio
        :param str app_description: Description of the app.
        :param List[str] raw_steps: List of steps in the user journey.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about generated storyboard.
        :rtype: AgentResponse
        """
        try:
            self.output_message.actions.append("Processing input...")
            video_content = VideoContent(
                agent_name=self.agent_name, status=MsgStatus.progress
            )
            video_content.status_message = "Generating storyboard video..."
            self.output_message.content.append(video_content)
            self.output_message.push_update()

            # Tools
            ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
            if not ELEVENLABS_API_KEY:
                raise Exception("Elevenlabs API key not present in .env")
            self.audio_gen_tool = ElevenLabsTool(api_key=ELEVENLABS_API_KEY)
            self.videodb_tool = VideoDBTool(collection_id=collection_id)

            # Initialize step data
            steps = [{"step": step} for step in raw_steps]

            # Step 1: Generate voiceover scripts and step descriptions using OpenAI
            self.output_message.actions.append(
                "Generating step descriptions and voiceover scripts..."
            )
            self.output_message.push_update()

            step_scripts = self.generate_voiceover_scripts(steps, app_description)
            if not step_scripts:
                video_content.status = MsgStatus.error
                video_content.status_message = "Error in generating voiceover scripts."
                self.output_message.publish()
                error_message = (
                    "Agent failed with error in generating voiceover scripts."
                )
                return AgentResponse(status=AgentStatus.ERROR, message=error_message)

            for index, step in enumerate(step_scripts):
                steps[index]["step_description"] = step["step_description"]
                steps[index]["voiceover_script"] = step["voiceover_script"]

            print(steps)

            # Step 2: Generate images using DALL-E
            self.output_message.actions.append("Generating images...")
            self.output_message.push_update()

            for index, step in enumerate(steps):
                # image_url = self.generate_image_dalle(step, app_description)
                image_url = self.generate_image_flux(step, app_description)
                print("####this is image url ", image_url)
                if not image_url:
                    video_content.status = MsgStatus.error
                    video_content.status_message = (
                        f"Error in generating image for step {index+1}."
                    )
                    self.output_message.publish()
                    error_message = f"Agent failed with error in generating image for step {index+1}."
                    return AgentResponse(
                        status=AgentStatus.ERROR, message=error_message
                    )

                # Download webp image and convert to PNG
                response = requests.get(image_url)
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content))
                    os.makedirs(DOWNLOADS_PATH, exist_ok=True)
                    png_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.png"
                    image.save(png_path, "PNG")
                    media = self.videodb_tool.upload(
                        png_path, source_type="file_path", media_type="image"
                    )
                    steps[index]["image_id"] = media["id"]
                else:
                    logger.error("Failed to download image")
                    return None

            print(steps)

            # Step 3: Generate voiceover audio using ElevenLabs
            self.output_message.actions.append("Generating voiceover audio...")
            self.output_message.push_update()

            for index, step in enumerate(steps):
                try:
                    os.makedirs(DOWNLOADS_PATH, exist_ok=True)
                    voiceover_path = f"{DOWNLOADS_PATH}/{str(uuid.uuid4())}.mp3"
                    self.audio_gen_tool.text_to_speech(
                        text=step["voiceover_script"],
                        save_at=voiceover_path,
                        config={
                            "voice_id": "IsEXLHzSvLH9UMB6SLHj",
                        },
                    )
                except Exception as e:
                    video_content.status = MsgStatus.error
                    video_content.status_message = (
                        f"Error in generating audio for step {step['step']}."
                    )
                    self.output_message.publish()
                    error_message = f"Agent failed with error in generating audio for step {index+1}."
                    return AgentResponse(
                        status=AgentStatus.ERROR, message=error_message
                    )
                media = self.videodb_tool.upload(
                    voiceover_path, source_type="file_path", media_type="audio"
                )
                steps[index]["audio_id"] = media["id"]

            print(steps)

            # # Step 4: Combine assets using VideoDB
            self.output_message.actions.append(
                "Combining assets into storyboard video..."
            )
            self.output_message.push_update()

            video_url = self.combine_assets(steps)
            if not video_url:
                video_content.status = MsgStatus.error
                video_content.status_message = "Error in combining assets into video."
                self.output_message.publish()
                error_message = (
                    "Agent failed with error in combining assets into video."
                )
                return AgentResponse(status=AgentStatus.ERROR, message=error_message)

            video_content.video = VideoData(stream_url=video_url)
            video_content.status = MsgStatus.success
            video_content.status_message = "Here is your generated storyboard video."
            self.output_message.publish()
        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            video_content.status = MsgStatus.error
            video_content.status_message = "Error in generating storyboard."
            self.output_message.publish()
            error_message = f"Agent failed with error {e}"
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Agent {self.agent_name} completed successfully.",
            data={"video_url": video_url},
        )

    def generate_voiceover_scripts(self, steps, app_description):
        """
        Generates step descriptions and voiceover scripts using OpenAI.
        :param steps: List of steps.
        :param app_description: Description of the app.
        :return: List of dicts with 'step_description' and 'voiceover_script'.
        """
        try:
            # Build the prompt
            prompt = self.prompt_voiceover_scripts(steps, app_description)
            # Call OpenAI API
            message = ContextMessage(
                content=prompt,
                role=RoleTypes.user,
            )
            llm_response = self.llm.chat_completions(
                [message.to_llm_msg()],
                response_format={"type": "json_object"},
            )
            # Parse the response
            step_data = json.loads(llm_response.content)["steps"]
            return step_data
        except Exception as e:
            logger.exception("Error in generating voiceover scripts.")
            return None

    def prompt_voiceover_scripts(self, steps, app_description):
        """
        Generates the prompt to get step descriptions and voiceover scripts.
        """
        prompt = f"Generate a structured response for an app that {app_description}. Here are the steps involved in the user journey:"
        for step in steps:
            prompt += f"""\n-
Create a concise description for the step '{step['step']}' in the user journey. This description should capture the essence of the action performed by the user during this step.
Create a conversational and engaging script for an app where the user is {step['step']}.
Keep it narrative-driven, within two sentences."""
        prompt += """\nReturn a response in JSON format, with key 'steps', and value being a list of dicts, where each dict has two keys 'step_description' and 'voiceover_script', like this:
{
    "steps": [
        {
            "step_description": "A concise description for the step",
            "voiceover_script": "A conversational and engaging script for the step. Keep it narrative-driven, within two sentences."
        },
        ...
    ]
}
"""
        return prompt

    def generate_image_dalle(self, step, app_description):
        """
        Generates an image using DALL-E.
        :param step: Dict containing step information.
        :param app_description: Description of the app.
        :return: URL of the generated image.
        """
        try:
            prompt = self.prompt_image_generation(step, app_description)
            import openai

            openai.api_key = os.environ.get("OPENAI_API_KEY")
            # TODO: add image agent here
            response = self.llm.client.images.generate(
                prompt=prompt, n=1, size="1024x1024"
            )
            print("this is response ", response)
            image_url = response.data[0].url
            return image_url
        except Exception as e:
            logger.exception("Error in generating image.")
            return None

    def generate_image_flux(self, step, app_description):
        """
        Generates an image using Flux.
        :param step: Dict containing step information.
        :param app_description: Description of the app.
        :return: URL of the generated image.
        """
        try:
            prompt = self.prompt_image_generation(step, app_description)
            flux_output = flux_dev(prompt)
            if not flux_output:
                logger.error("Error in generating image with Flux")
                return None
            image_url = flux_output[0].url
            return image_url
        except Exception as e:
            logger.exception("Error in generating image with Flux.")
            return None

    def prompt_image_generation(self, step, app_description):
        """
        Generates the prompt for image generation.
        """
        consistent_part = "Create a stippling black ballpoint pen illustration of a Nigerian woman with a tight afro, living in her minimalist New York apartment. Keep the illustration simple with minimal elements. Generate less than 600 characters"
        variable_part = f"This illustration is a part of a storyboard to explain the user journey of an app built for {app_description}. This image will portray the '{step['step']}' stage in the app. Step description: {step['step_description']}. This illustration is meant for professional storyboarding, so understand the requirements accordingly and create a suitable illustration with the woman as a central character in the frame, but include other supporting props that can indicate that she's in the '{step['step']}' step in the user flow."
        prompt = f"{consistent_part}\n- {variable_part}"
        return prompt

    def combine_assets(self, steps):
        """
        Combines images and audio into a storyboard video using VideoDB.
        :param steps: List of dicts containing image and audio URLs.
        :return: URL of the generated video.
        """
        try:
            # Initialize VideoDB client
            timeline = self.videodb_tool.get_and_set_timeline()
            # Upload base video
            base_video = self.videodb_tool.upload(
                "https://www.youtube.com/watch?v=4dW1ybhA5bM"
            )
            base_video_id = base_video["id"]

            seeker = 0
            for index, step in enumerate(steps):
                # Upload image and audio
                audio = self.videodb_tool.get_audio(step["audio_id"])
                image = self.videodb_tool.get_image(step["image_id"])

                audio_duration = float(audio["length"])

                image_asset = ImageAsset(
                    asset_id=image["id"],
                    duration=audio_duration,
                    x="(main_w-overlay_w)/2",
                    y="(main_h-overlay_h)/2",
                    height="w=iw/3",
                    width="h=ih/3",
                )
                audio_asset = AudioAsset(
                    asset_id=audio["id"], disable_other_tracks=True
                )
                text_asset = TextAsset(
                    step["step"],
                    duration=audio_duration,
                    style=TextStyle(
                        x="(w-text_w)/2",
                        y="(h-text_h*2)",
                        font="League Spartan",
                        fontsize="(h/20)",
                        fontcolor="Snow",
                        boxcolor="OrangeRed",
                        boxborderw=10,
                    ),
                )

                # Add assets to timeline
                timeline.add_overlay(seeker, image_asset)
                timeline.add_overlay(seeker, audio_asset)
                timeline.add_overlay(seeker, text_asset)

                seeker += audio_duration

            # Add base video to timeline
            base_vid_asset = VideoAsset(base_video_id, end=seeker)
            timeline.add_inline(base_vid_asset)

            # Generate the video
            video_url = timeline.generate_stream()
            return video_url
        except Exception as e:
            logger.exception("Error in combining assets into video.")
            return None


# Helper function to upload audio to storage and return URL
def upload_to_storage(content, filename):
    """
    Uploads content to storage and returns the URL.
    """
    # Implement your storage upload logic here
    # For demonstration, we'll return a placeholder URL
    return f"https://storage.example.com/{filename}"
