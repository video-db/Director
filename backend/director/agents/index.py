import logging

from director.agents.base import BaseAgent, AgentResponse, AgentStatus

from director.core.session import Session
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)

EXTRACTION_CONFIGS_DEFAULTS = {
    "shot": {
        "threshold": 20,
        "min_scene_len": 15,
        "frame_count": 4,
    },
    "time": {
        "time": 10,
        "select_frames": ["first", "middle", "last"],
    },
}

SCENE_INDEX_CONFIG_DEFAULTS = {
    "type": "shot",
    "shot_based_config": EXTRACTION_CONFIGS_DEFAULTS["shot"],
    "time_based_config": EXTRACTION_CONFIGS_DEFAULTS["time"],
}

INDEX_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "video_id": {
            "type": "string",
            "description": "The ID of the video to process.",
        },
        "index_type": {
            "type": "string",
            "enum": ["spoken_words", "scene"],
            "default": "spoken_words",
        },
        "scene_index_prompt": {
            "type": "string",
            "description": "The prompt to use for scene indexing. Optional parameter only for scene based indexing ",
        },
        "scene_index_config": {
            "type": "object",
            "description": "Configuration for scene indexing behavior, Don't ask user to provide this parameter, provide if user explicitly mentions itt ",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["shot", "time"],
                    "default": "shot",
                    "description": "Method to use for scene detection and frame extraction",
                },
                "shot_based_config": {
                    "type": "object",
                    "description": "Configuration for shot-based scene detection and frame extraction, This is a required parameter for shot_based indexing",
                    "properties": {
                        "threshold": {
                            "type": "number",
                            "default": SCENE_INDEX_CONFIG_DEFAULTS["shot_based_config"][
                                "threshold"
                            ],
                            "description": "Threshold value for scene change detection",
                        },
                        "min_scene_len": {
                            "type": "number",
                            "default": SCENE_INDEX_CONFIG_DEFAULTS["shot_based_config"][
                                "min_scene_len"
                            ],
                            "description": "Minimum length of a scene in frames",
                        },
                        "frame_count": {
                            "type": "number",
                            "default": SCENE_INDEX_CONFIG_DEFAULTS["shot_based_config"][
                                "frame_count"
                            ],
                            "description": "Number of frames to extract per scene",
                        },
                    },
                    "required": ["threshold", "min_scene_len", "frame_count"],
                },
                "time_based_config": {
                    "type": "object",
                    "description": "Configuration for time-based scene detection and frame extraction, This is a required parameter for time_based indexing",
                    "properties": {
                        "time": {
                            "type": "number",
                            "default": SCENE_INDEX_CONFIG_DEFAULTS["time_based_config"][
                                "time"
                            ],
                            "description": "Time interval in seconds between frame extractions",
                        },
                        "select_frames": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": SCENE_INDEX_CONFIG_DEFAULTS["time_based_config"][
                                "select_frames"
                            ],
                            "description": "Which frames to select from each time interval, In this array first, middle and last are the only allowed values",
                        },
                    },
                    "required": ["time", "select_frames"],
                },
            },
        },
        "collection_id": {
            "type": "string",
            "description": "The ID of the collection to process.",
        },
    },
    "required": ["video_id", "index_type", "collection_id"],
}

SCENE_INDEX_PROMPT = """
    AI Assistant Task: Video Image Analysis for Classification and Indexing

    For the attached image, please provide a comprehensive analysis covering the following categories:

    Scene Description:
        People: Describe the number of individuals, their appearance, actions, and expressions.
        Objects: Identify notable items and their relevance to the scene.
        Actions: Outline any activities or movements occurring.
        Environment: Specify details of the setting (e.g., indoor/outdoor, location type).
        Visual Elements: Note colors, lighting, and any stylistic features.

    Video Category Identification:
    Select the most likely category for the video from these options:
        Surveillance Video
        Movie Trailer
        Podcast
        Product Review
        Educational Lecture/Tutorial
        Music Video
        News Broadcast
        Sports Event
        Documentary
        Animated Content
        Advertisement/Commercial
        Gaming Video
        Vlog (Video Blog)
        Interview
        Live Stream
        Tutorial/How-To Video
        Corporate Presentation
        Promotional Event
        Cinematic Short Film
        User-Generated Content
        Other (please specify)
        Justification for Classification:
        Provide reasons for the chosen category based on visual cues observed.

    Text Extraction:
    List any text present, including:

    Titles
        Headlines
        Subtitles
        Labels
        Overlaid graphics
        Time and date stamps
        Explain the relevance of extracted text to the scene or video category.
    Notable Personalities and Characters:
        Identify recognizable individuals, characters, or public figures. Include names and relevance if possible.

    Logo and Brand Recognition:
        Describe visible logos, brand names, or trademarks and their relevance to the video content.

    Object and Symbol Detection:
        List key objects, symbols, or visual motifs. Explain their significance in context.

    Emotion and Mood Assessment:
        Assess the emotional tone (e.g., happy, tense, dramatic, instructional) and mention visual elements that contribute to this assessment.

    Genre and Style Identification (if applicable):
        For content like movies, music videos, or short films, identify the genre (e.g., action, comedy, horror) and stylistic elements that indicate genre or style.

    Additional Category-Specific Details:
    Provide relevant details based on the identified category, such as:
        Surveillance Video: Presence of timestamps, camera angles, or suspicious activities.
        Movie Trailer/Cinematic Short Film: Actor names, setting descriptions, special effects, and plot hints.
        Podcast/Interview: Speaker names, topics discussed, and setting details.
        Product Review/Advertisement: Product name, brand, highlighted features, and promotional messaging.
        Educational Lecture/Tutorial: Subject matter, instructional materials, and slide content.
        Music Video: Artist name, performance details, choreography, and symbolic imagery.
        News Broadcast: Anchors, headlines, network logos, and tickers.
        Sports Event: Sport type, teams or players, scores, and stadium details.
        Gaming Video: Game title, genre, in-game interfaces, and player reactions.
        Vlog/User-Generated Content: Content creator identity, activities, and setting.

    Technical Aspects (if noticeable):
    Comment on image quality (e.g., high-definition, low-resolution) and any visual effects, filters, or overlays.

    Cultural and Contextual Indicators:
    Identify any cultural references, language used, or regional indicators.

    Privacy and Ethical Considerations:
    Note if the image contains sensitive content, personal data, or requires discretion in handling.

    Instructions:
        Be Objective: Provide unbiased observations based solely on the visual content.
        Be Detailed: Include as much relevant information as possible to aid in accurate classification and indexing.
        Be Concise: Ensure clarity while providing thorough information.
        Handle Uncertainty: If certain elements are unclear, mention them and offer possible interpretations.
        Output Format: Provide a detailed description in a Paragraph do not use any formatting for easy reference and analysis.
    """.strip()


class IndexAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "index"
        self.description = "This is an agent to index the given video of VideoDB. The indexing can be done for spoken words or scene."
        self.parameters = INDEX_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        video_id: str,
        index_type: str,
        scene_index_prompt=SCENE_INDEX_PROMPT,
        scene_index_config=SCENE_INDEX_CONFIG_DEFAULTS,
        collection_id=None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Process the sample based on the given sample ID.
        :param str video_id: The ID of the video to process.
        :param str index_type: The type of indexing to perform.
        :param str collection_id: The ID of the collection to process.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: The response containing information about the sample processing operation.
        :rtype: AgentResponse
        """
        try:
            scene_data = {}
            if collection_id is None:
                self.videodb_tool = VideoDBTool()
            else:
                self.videodb_tool = VideoDBTool(collection_id=collection_id)
            self.output_message.actions.append(f"Indexing {index_type} of video..")
            self.output_message.push_update()

            if index_type == "spoken_words":
                self.videodb_tool.index_spoken_words(video_id)

            elif index_type == "scene":
                scene_index_type = scene_index_config["type"]
                scene_index_config = scene_index_config[
                    scene_index_type + "_based_config"
                ]
                scene_index_id = self.videodb_tool.index_scene(
                    video_id=video_id,
                    extraction_type=scene_index_type,
                    extraction_config=scene_index_config,
                    prompt=scene_index_prompt,
                )
                self.videodb_tool.get_scene_index(
                    video_id=video_id, scene_id=scene_index_id
                )
                scene_data = {"scene_index_id": scene_index_id}

        except Exception as e:
            logger.exception(f"error in {self.agent_name} agent: {e}")
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"{index_type} indexing successful",
            data=scene_data,
        )
