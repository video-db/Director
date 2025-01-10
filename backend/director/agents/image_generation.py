import logging
import os
from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import Session, MsgStatus, ImageContent, ImageData
from director.tools.fal_video import FalVideoGenerationTool, PARAMS_CONFIG as FAL_VIDEO_GEN_PARAMS_CONFIG
from director.tools.replicate import flux_dev

logger = logging.getLogger(__name__)

SUPPORTED_ENGINES = ["replicate", "fal"]

IMAGE_GENERATION_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "job_type": {
            "type": "string",
            "enum": SUPPORTED_ENGINES,
            "description": "Engine for image generation. Use 'replicate' for text-to-image or 'fal' for image-to-image.",
        },
        "prompt": {
            "type": "string",
            "description": "Prompt for image generation or enhancement.",
        },
        "image_to_image": {
            "type": "object",
            "properties": {
                "image_url": {
                    "type": "string",
                    "description": "URL of the image to enhance.",
                },
                "fal_config": {
                    "type": "object",
                    "properties": FAL_VIDEO_GEN_PARAMS_CONFIG["image_to_image"],
                    "description": "Configuration for FAL enhancement.",
                },
            },
            "required": ["image_url"],
        },
    },
    "required": ["job_type", "prompt"],
}


class ImageGenerationAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "image_generation"
        self.description = (
            "Generates or enhances images using GenAI models. Supports 'replicate' for text-to-image and 'fal' for image-to-image."
        )
        self.parameters = IMAGE_GENERATION_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def initialize_fal_tool(self):
        fal_key = os.getenv("FAL_KEY")
        if not fal_key:
            raise Exception("FAL API key not found. Please set FAL_KEY in the environment variables.")
        return FalVideoGenerationTool(api_key=fal_key)

    async def run_async(self, job_type: str, prompt: str, image_to_image: dict = None, *args, **kwargs) -> AgentResponse:
        try:
            image_content = ImageContent(
                agent_name=self.agent_name, status=MsgStatus.progress, status_message="Processing image..."
            )
            self.output_message.content.append(image_content)
            self.output_message.push_update()

            if job_type not in SUPPORTED_ENGINES:
                raise ValueError(f"Unsupported job_type '{job_type}'.")

            if job_type == "replicate":
                # Replicate (text-to-image)
                logger.info("Generating image using Replicate (text-to-image).")
                flux_output = flux_dev(prompt)
                if not flux_output or not hasattr(flux_output[0], 'url'):
                    raise ValueError("Invalid output from Replicate (flux_dev): Missing 'url' attribute.")
                image_url = flux_output[0].url

            elif job_type == "fal":
                # FAL (image-to-image)
                if not image_to_image:
                    raise ValueError("'image_to_image' parameters are required for this job type.")
                fal_tool = self.initialize_fal_tool()
                image_url = image_to_image.get("image_url")
                fal_config = image_to_image.get("fal_config", {})
                enhanced_image_path = f"/tmp/enhanced_image_{os.getpid()}.png"
                logger.info("Enhancing image using FAL.")
                fal_result = await fal_tool.image_to_image_async(
                    image_url=image_url, save_at=enhanced_image_path, prompt=prompt, config=fal_config
                )
                image_url = fal_result.get("image_url")
                if not image_url:
                    raise ValueError("Error enhancing image using FAL: No image URL returned.")
                if os.path.exists(enhanced_image_path):
                    os.remove(enhanced_image_path)

            # Update content with success status
            image_content.image = ImageData(url=image_url)
            image_content.status = MsgStatus.success
            image_content.status_message = "Image processed successfully."
            self.output_message.push_update()
            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Image processing completed successfully.",
                data={"image_url": image_url},
            )

        except Exception as e:
            logger.exception(f"Error in {self.agent_name}: {e}")
            image_content.status = MsgStatus.error
            image_content.status_message = str(e)
            self.output_message.push_update()
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

    def run(self, *args, **kwargs):
        from director.utils.asyncio import is_event_loop_running
        import asyncio

        if not is_event_loop_running():
            return asyncio.run(self.run_async(*args, **kwargs))
        else:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.run_async(*args, **kwargs))
