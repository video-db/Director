import logging
from typing import Optional

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    MsgStatus,
    TextContent,
    VideoContent,
    VideoData,
)
from director.tools.videodb_tool import VideoDBTool
from director.constants import (
    BRANDKIT_DEMO_INTRO_VIDEO_ID,
    BRANDKIT_DEMO_OUTRO_VIDEO_ID,
    BRANDKIT_DEMO_BRAND_IMAGE_ID,
)

logger = logging.getLogger(__name__)

BRAND_KIT_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "video_id": {
            "type": "string",
            "description": "The ID of the video to apply the brand kit to.",
        },
        "collection_id": {
            "type": "string",
            "description": "The ID of the collection containing the video.",
        },
        "intro_video_id": {
            # ["string", "null"] so OpenAI strict mode can emit explicit null
            "type": ["string", "null"],
            "description": (
                "Optional. The ID of the intro video to prepend. "
                "If not provided, a VideoDB demo intro is used."
            ),
        },
        "outro_video_id": {
            "type": ["string", "null"],
            "description": (
                "Optional. The ID of the outro video to append. "
                "If not provided, a VideoDB demo outro is used."
            ),
        },
        "brand_image_id": {
            "type": ["string", "null"],
            "description": (
                "Optional. The ID of the brand logo image to overlay. "
                "If not provided, a VideoDB demo logo is used."
            ),
        },
    },
    # OpenAI strict mode requires every property to be listed in required.
    # Optional slots use ["string", "null"] so the model can emit null for unset fields.
    "required": [
        "video_id",
        "collection_id",
        "intro_video_id",
        "outro_video_id",
        "brand_image_id",
    ],
    "additionalProperties": False,
}


class BrandKitAgent(BaseAgent):
    """Agent that applies brand kit elements (intro, outro, logo overlay) to a video.

    Resolves each asset slot from user-supplied IDs first, falling back to
    configured public demo assets so users can preview the effect before
    uploading their own brand assets.
    """

    def __init__(self, session: Session, **kwargs):
        """Initialise BrandKitAgent and register it with the reasoning engine.

        :param Session session: The active Director session.
        """
        self.agent_name = "brand_kit"
        self.description = (
            "Apply brand kit elements (intro video, outro video, and brand logo overlay) "
            "to a video. If the user has their own intro, outro, or logo assets, use those IDs. "
            "If they don't have brand assets yet, demo assets are applied automatically so they "
            "can preview the effect and replace them later by uploading their own."
        )
        self.parameters = BRAND_KIT_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        video_id: str,
        collection_id: str,
        intro_video_id: Optional[str] = None,
        outro_video_id: Optional[str] = None,
        brand_image_id: Optional[str] = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Apply a brand kit (intro, outro, logo overlay) to the given video.

        :param str video_id: The ID of the video to brand
        :param str collection_id: The ID of the collection containing the video
        :param str intro_video_id: Optional intro video ID to prepend
        :param str outro_video_id: Optional outro video ID to append
        :param str brand_image_id: Optional brand logo image ID to overlay
        """
        video_content = None
        try:
            videodb_tool = VideoDBTool(collection_id=collection_id)

            # Resolve per-slot: user-supplied ID wins, then demo fallback
            resolved_intro = intro_video_id or BRANDKIT_DEMO_INTRO_VIDEO_ID
            resolved_outro = outro_video_id or BRANDKIT_DEMO_OUTRO_VIDEO_ID
            resolved_image = brand_image_id or BRANDKIT_DEMO_BRAND_IMAGE_ID

            # Track which slots are filled by demo assets (not the user)
            demo_slots = [
                label
                for label, user_id, resolved in (
                    ("intro", intro_video_id, resolved_intro),
                    ("outro", outro_video_id, resolved_outro),
                    ("logo overlay", brand_image_id, resolved_image),
                )
                if resolved and not user_id
            ]
            all_demo = not any([intro_video_id, outro_video_id, brand_image_id])
            nothing_resolved = not any([resolved_intro, resolved_outro, resolved_image])

            if all_demo and nothing_resolved:
                # No user assets and no demo assets configured — guide the user
                self.output_message.content.append(
                    TextContent(
                        agent_name=self.agent_name,
                        status=MsgStatus.error,
                        status_message="No brand kit assets available.",
                        text=(
                            "No brand kit assets were found. To create your brand kit, "
                            "please upload your assets first:\n\n"
                            "- **Intro video**: upload a short intro clip and share its video ID\n"
                            "- **Outro video**: upload a short outro clip and share its video ID\n"
                            "- **Brand logo**: upload a PNG/JPG logo image and share its image ID\n\n"
                            "Once uploaded, ask me to apply the brand kit again with those IDs."
                        ),
                    )
                )
                self.output_message.publish()
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="No brand kit assets configured. Prompted user to upload their own.",
                )

            video_content = VideoContent(
                agent_name=self.agent_name,
                status=MsgStatus.progress,
                status_message="Applying brand kit...",
            )
            self.output_message.content.append(video_content)
            self.output_message.actions.append("Building brand kit timeline...")
            self.output_message.push_update()

            stream_url = videodb_tool.add_brandkit(
                video_id=video_id,
                intro_video_id=resolved_intro,
                outro_video_id=resolved_outro,
                brand_image_id=resolved_image,
            )

            applied = []
            if resolved_intro:
                applied.append("intro")
            if resolved_outro:
                applied.append("outro")
            if resolved_image:
                applied.append("logo overlay")

            # Slots that were requested but couldn't be filled (no user ID, no demo constant)
            unfilled_slots = [
                label
                for label, resolved in (
                    ("intro", resolved_intro),
                    ("outro", resolved_outro),
                    ("logo overlay", resolved_image),
                )
                if not resolved
            ]

            if all_demo:
                status_message = (
                    "Here is your video with the demo brand kit applied. "
                    "Upload your own intro video, outro video, and logo image "
                    "to replace the demo assets with your brand."
                )
            elif demo_slots:
                status_message = (
                    f"Brand kit applied ({', '.join(applied)}). "
                    f"Demo assets used for: {', '.join(demo_slots)}. "
                    "Upload your own to replace them."
                )
            else:
                status_message = f"Brand kit applied ({', '.join(applied)})."

            if unfilled_slots:
                status_message += (
                    f" Note: {', '.join(unfilled_slots)} slot(s) were not available — "
                    "upload assets or configure demo assets to include them."
                )

            video_content.video = VideoData(stream_url=stream_url)
            video_content.status = MsgStatus.success
            video_content.status_message = status_message
            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Brand kit applied successfully.",
                data={
                    "stream_url": stream_url,
                    "intro_video_id": resolved_intro,
                    "outro_video_id": resolved_outro,
                    "brand_image_id": resolved_image,
                    "used_demo_assets": bool(demo_slots),
                    "demo_asset_slots": demo_slots,
                },
            )

        except Exception:
            logger.exception("BrandKitAgent failed")
            if video_content is not None:
                video_content.status = MsgStatus.error
                video_content.status_message = "Failed to apply brand kit."
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=(
                    "Failed to apply brand kit. Please verify the video and "
                    "brand asset IDs, then try again."
                ),
            )
