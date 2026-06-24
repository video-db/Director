import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Default models. Pegasus powers video understanding/analysis, Marengo powers
# multimodal embeddings. These can be overridden through the agent config.
PEGASUS_MODEL = "pegasus1.5"
MARENGO_MODEL = "marengo3.0"

PARAMS_CONFIG = {
    "analyze": {
        "model_name": {
            "type": "string",
            "description": "TwelveLabs Pegasus model to use for video analysis",
            "default": PEGASUS_MODEL,
            "enum": ["pegasus1.5", "pegasus1.2"],
        },
        "temperature": {
            "type": "number",
            "description": "Sampling temperature for the generated text",
            "minimum": 0,
            "maximum": 1,
        },
        "max_tokens": {
            "type": "integer",
            "description": "Maximum number of tokens to generate",
            "default": 2048,
        },
    },
    "embed": {
        "model_name": {
            "type": "string",
            "description": "TwelveLabs Marengo model to use for embeddings",
            "default": MARENGO_MODEL,
            "enum": ["marengo3.0"],
        },
    },
}


class TwelveLabsTool:
    """Thin wrapper around the official ``twelvelabs`` SDK.

    Exposes the two TwelveLabs foundation models used by Director:
    Pegasus for video understanding/analysis and Marengo for multimodal
    embeddings.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise Exception("TwelveLabs API key not found")
        # Imported lazily so the dependency is only required when the
        # TwelveLabs engine is actually selected.
        from twelvelabs import TwelveLabs

        self.client = TwelveLabs(api_key=api_key)

    def analyze_video(
        self,
        video_url: str,
        prompt: str,
        config: Optional[dict] = None,
    ) -> str:
        """Analyze a video from a public URL using Pegasus.

        TwelveLabs fetches the video server-side from ``video_url``.

        :param str video_url: Publicly accessible URL of the video to analyze.
        :param str prompt: The instruction guiding the analysis.
        :param dict config: Optional overrides (``model_name``, ``temperature``,
            ``max_tokens``).
        :return: The generated text analysis.
        :rtype: str
        """
        from twelvelabs import VideoContext_Url

        config = config or {}
        try:
            response = self.client.analyze(
                model_name=config.get("model_name", PEGASUS_MODEL),
                video=VideoContext_Url(url=video_url),
                prompt=prompt,
                temperature=config.get("temperature"),
                max_tokens=config.get("max_tokens", 2048),
            )
        except Exception as e:
            raise Exception(
                f"Error analyzing video with TwelveLabs: {type(e).__name__}: {e}"
            ) from e
        return response.data

    def get_text_embedding(self, text: str, config: Optional[dict] = None) -> list:
        """Create a multimodal embedding for a text query using Marengo.

        The returned vector lives in the same embedding space as
        TwelveLabs video embeddings, so it can be used for text-to-video
        retrieval.

        :param str text: The text to embed.
        :param dict config: Optional overrides (``model_name``).
        :return: A list of floats (512-dimensional vector).
        :rtype: list
        """
        config = config or {}
        try:
            response = self.client.embed.create(
                model_name=config.get("model_name", MARENGO_MODEL),
                text=text,
            )
        except Exception as e:
            raise Exception(
                f"Error creating embedding with TwelveLabs: {type(e).__name__}: {e}"
            ) from e
        return response.text_embedding.segments[0].float_
