import logging
import os
from director.agents.base import BaseAgent, AgentResponse, AgentStatus

from director.core.session import Session, MsgStatus, ImageContent, ImageData
from director.tools.videodb_tool import VideoDBTool

from director.tools.fal_video import (
    FalVideoGenerationTool,
    PARAMS_CONFIG as FAL_VIDEO_GEN_PARAMS_CONFIG,
)

logger = logging.getLogger(__name__)

THUMBNAIL_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "collection_id": {
            "type": "string",
            "description": "Collection Id to of the video",
        },
        "video_id": {
            "type": "string",
            "description": "Video Id to generate thumbnail",
        },
        "timestamp": {
            "type": "integer",
            "description": "Timestamp in seconds of the video to generate thumbnail, Optional parameter don't ask from user",
        },
        "job_type": {
            "type": "string",
            "enum": ["default", "image_to_image"],
            "description": "The type of thumbnail generation to perform. Use 'default' for standard thumbnails and 'image_to_image' to enhance thumbnails using a model.",
        },
        "image_to_image": {
            "type": "object",
            "properties": {
                "image_id": {
                    "type": "string",
                    "description": "The ID of the image in VideoDB to enhance with FAL models.",
                },
                "prompt": {
                    "type": "string",
                    "description": "Optional text prompt to guide the image enhancement.",
                },
                "fal_config": {
                    "type": "object",
                    "properties": FAL_VIDEO_GEN_PARAMS_CONFIG["image_to_image"],
                    "description": "Config to use when FAL engine is used for image-to-image transformations.",
                },
            },
            "required": ["image_id"],
        },
    },
    "required": ["collection_id", "video_id", "job_type"],
}

# Default prompt for thumbnails
DEFAULT_THUMBNAIL_PROMPT = (
    "Enhance the image with vibrant, eye-catching colors, and add bold, glowing text overlay featuring the main title in a cinematic font. "
    "Create a visually striking thumbnail with a large, bold title and a subtle vignette effect around the edges. "
    "Create a minimalist thumbnail with a soft background blur, clean typography, and a central focus on the main subject. "
    "Create a thumbnail with a modern, sleek design featuring a bold, sans-serif font and a subtle gradient overlay. "
    "Include a bright call-to-action text in bold, glowing letters. Add an arrow pointing to the focus area of the thumbnail for maximum impact."
)

class ThumbnailAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "thumbnail"
        self.description = "Generates a thumbnail image from a video file. This Agent takes a video id and a optionl timestamp as input. Use this tool when a user requests a preview, snapshot, generate or visual representation of a specific moment in a video file. The output is a static image file suitable for quick previews or thumbnails. It will not provide any other processing or editing options beyond generating the thumbnail."
        self.parameters = THUMBNAIL_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def initialize_fal_tool(self):
        fal_key = os.getenv("FAL_KEY")
        if not fal_key:
            raise Exception("FAL API key not found. Please set FAL_KEY in the environment variables.")
        return FalVideoGenerationTool(api_key=fal_key)

    def run(
        self,
        collection_id: str,
        video_id: str,
        job_type: str,
        timestamp: int = 5,
        image_to_image: dict = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Get the thumbnail for the video at the given timestamp
        """
        try:
            self.output_message.actions.append("Generating thumbnail..")
            image_content = ImageContent(agent_name=self.agent_name)
            image_content.status_message = "Generating thumbnail.."
            self.output_message.content.append(image_content)
            self.output_message.push_update()

            videodb_tool = VideoDBTool(collection_id=collection_id)

            # Generate the default thumbnail
            logger.info(f"Generating default thumbnail for video ID: {video_id} at timestamp: {timestamp}")
            try:
                thumbnail_data = videodb_tool.generate_thumbnail(video_id=video_id, timestamp=timestamp)
            except Exception as e:
                logger.error(f"Failed to generate default thumbnail: {e}")
                raise Exception(f"Failed to generate default thumbnail: {e}") from e

            if job_type == "image_to_image":
                if not image_to_image:
                    raise ValueError("Missing 'image_to_image' parameters for enhancement.")

                fal_tool = self.initialize_fal_tool()
                image_id = image_to_image.get("image_id")
                prompt = image_to_image.get("prompt", DEFAULT_THUMBNAIL_PROMPT)  # Apply default prompt
                fal_config = image_to_image.get("fal_config", {})

                model_name = fal_config.get("model_name")
                if not model_name:
                    model_name = "fal-ai/flux-lora-canny"
                    logger.warning(f"Model name not provided in FAL config. Using default model '{model_name}'.")

                logger.info(f"Enhancing thumbnail using FAL engine with the '{model_name}' model for video ID: {video_id}")
                self.output_message.actions.append(f"Enhancing thumbnail using FAL engine with the '{model_name}' model...")
                image_content.status_message = f"Enhancing thumbnail using FAL engine with the '{model_name}' model..."
                self.output_message.push_update()

                # Fetch the image using image_id
                image_data = videodb_tool.get_image(image_id=image_id)
                logger.info(image_data)
                if not image_data or "url" not in image_data:
                    raise ValueError(f"Invalid image data received for image_id: {image_id}")

                image_url = image_data["url"]
            
                safe_video_id = "".join(c for c in video_id if c.isalnum() or c in ('-', '_'))
                enhanced_image_path = f"/tmp/enhanced_thumbnail_{safe_video_id}.png"
                try:
                    fal_result = fal_tool.image_to_image(
                        image_url=image_url,
                        save_at=enhanced_image_path,
                        prompt=prompt,
                        config=fal_config,
                    )
                    thumbnail_data = {"url": fal_result["image_url"]}
                finally:
                    if os.path.exists(enhanced_image_path):
                        os.remove(enhanced_image_path)
                
            else:
                # Use the generated thumbnail URL
                image_url = thumbnail_data["url"]

            image_content.image = ImageData(**thumbnail_data)
            image_content.status = MsgStatus.success
            image_content.status_message = "Here is your thumbnail."
            self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name} agent.")
            image_content.status = MsgStatus.error
            image_content.status_message = "Error in generating thumbnail."
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message="Thumbnail generated and displayed to user.",
            data=thumbnail_data,
        )
