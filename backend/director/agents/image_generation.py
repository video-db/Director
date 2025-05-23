import logging
import os

from typing import Optional

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, MsgStatus, ImageContent, ImageData
from director.tools.replicate import flux_dev
from director.tools.videodb_tool import VideoDBTool
from director.tools.fal_video import (
    FalVideoGenerationTool,
    PARAMS_CONFIG as FAL_VIDEO_GEN_PARAMS_CONFIG,
)

logger = logging.getLogger(__name__)

IMAGE_GENERATION_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "The collection ID being used",
        },
        "job_type": {
            "type": "string",
            "enum": ["image_to_image", "text_to_image"],
            "description": """
            The type of image generation to perform
            Possible values:
                - image_to_image: generates an image from an image input 
                - text_to_image: generates an image from a given text prompt.
            """,
        },
        "prompt": {
            "type": "string",
            "description": "Prompt for image generation or enhancement.",
        },
        "image_to_image": {
            "type": "object",
            "properties": {
                "image_id": {
                    "type": "string",
                    "description": "The ID of the image in VideoDB to use for image generation",
                },
                "fal_config": {
                    "type": "object",
                    "properties": FAL_VIDEO_GEN_PARAMS_CONFIG["image_to_image"],
                    "description": "Configuration for FAL enhancement.",
                },
            },
            "required": ["image_id"],
        },
        "text_to_image": {
            "type": "object",
            "properties": {
                "engine": {
                    "type": "string",
                    "description": "The engine to use for image generation. Possible values: 'videodb' and 'flux'. Must be present if job_type is 'text_to_image'.",
                    "default": "videodb",
                    "enum": ["videodb", "flux"],
                },
            },
        },
    },
    "required": ["collection_id", "job_type", "prompt"],
    "if": {"properties": {"job_type": {"const": "image_to_image"}}},
    "then": {"required": ["image_to_image"]},
}

class ImageGenerationAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "image_generation"
        self.description = "Generates or enhances images using GenAI models. Supports 'replicate' for text-to-image and 'fal' for image-to-image."
        self.parameters = IMAGE_GENERATION_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        collection_id: str,
        job_type: str,
        prompt: str,
        image_to_image: Optional[dict] = None,
        text_to_image: Optional[dict] = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Process the prompt to generate the image.

        :param str prompt: prompt for image generation.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about generated image.
        :rtype: AgentResponse
        """
        try:
            self.videodb_tool = VideoDBTool(collection_id=collection_id)
            self.output_message.actions.append("Processing prompt..")
            image_content = ImageContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Generating image...",
            )
            self.output_message.content.append(image_content)
            self.output_message.push_update()

            output_image_url = ""
            if job_type == "text_to_image":
                engine = text_to_image.get("engine", "videodb") if text_to_image else "videodb"
                if engine == "flux":
                    flux_output = flux_dev(prompt)
                    if not flux_output:
                        image_content.status = MsgStatus.error
                        image_content.status_message = "Error in generating image."
                        self.output_message.publish()
                        error_message = "Agent failed with error in replicate."
                        return AgentResponse(
                            status=AgentStatus.ERROR, message=error_message
                        )
                    output_image_url = flux_output[0].url
                    image_content.image = ImageData(url=output_image_url)
                    image_content.status = MsgStatus.success
                    image_content.status_message = "Here is your generated image"
                else:
                    generated_image = self.videodb_tool.generate_image(prompt)
                    image_content.image = ImageData(**generated_image)
                    image_content.status = MsgStatus.success
                    image_content.status_message = "Here is your generated image"
            elif job_type == "image_to_image":
                FAL_KEY = os.getenv("FAL_KEY")
                image_id = image_to_image.get("image_id")

                if not image_id:
                    raise ValueError(
                        "Missing required parameter: 'image_id' for image-to-video generation"
                    )

                image_data = self.videodb_tool.get_image(image_id)
                if not image_data:
                    raise ValueError(
                        f"Image with ID '{image_id}' not found in collection "
                        f"'{collection_id}'. Please verify the image ID."
                    )

                image_url = None
                if isinstance(image_data.get("url"), str) and image_data.get("url"):
                    image_url = image_data["url"]
                else:
                    image_url = self.videodb_tool.generate_image_url(image_id)

                fal_tool = FalVideoGenerationTool(api_key=FAL_KEY)
                config = image_to_image.get("fal_config", {})
                fal_output = fal_tool.image_to_image(
                    image_url=image_url,
                    prompt=prompt,
                    config=config,
                )
                output_image_url = fal_output[0]["url"]
            else:
                raise Exception(f"{job_type} not supported")
            
            self.output_message.publish()
        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            image_content.status = MsgStatus.error
            image_content.status_message = "Error in generating image."
            self.output_message.publish()
            error_message = f"Agent failed with error {e}"
            return AgentResponse(status=AgentStatus.ERROR, message=error_message)
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Agent {self.name} completed successfully.",
            data={"image_content": image_content},
        )
