import os
import logging
import threading

from director.agents.frame import FrameAgent
from director.agents.summarize_video import SummarizeVideoAgent
from director.agents.download import DownloadAgent
from director.agents.pricing import PricingAgent
from director.agents.upload import UploadAgent
from director.agents.search import SearchAgent
from director.agents.prompt_clip import PromptClipAgent
from director.agents.index import IndexAgent
from director.agents.censor import CensorAgent
from director.agents.image_generation import ImageGenerationAgent
from director.agents.audio_generation import AudioGenerationAgent
from director.agents.video_generation import VideoGenerationAgent
from director.agents.stream_video import StreamVideoAgent
from director.agents.subtitle import SubtitleAgent
from director.agents.slack_agent import SlackAgent
from director.agents.editing import EditingAgent
from director.agents.dubbing import DubbingAgent
from director.agents.text_to_movie import TextToMovieAgent
from director.agents.composio import ComposioAgent
from director.agents.transcription import TranscriptionAgent
from director.agents.comparison import ComparisonAgent
from director.agents.code_assistant import CodeAssistantAgent
from director.agents.web_search_agent import WebSearchAgent
from director.agents.clone_voice import CloneVoiceAgent
from director.agents.voice_replacement import VoiceReplacementAgent


from director.core.session import Session, InputMessage, MsgStatus
from director.core.reasoning import ReasoningEngine
from director.db.base import BaseDB
from director.db import load_db
from director.tools.videodb_tool import VideoDBTool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Registry of currently running ReasoningEngine instances keyed by session_id.
# Used by on_stop_generation to cancel an in-progress generation.
_active_engines: dict = {}
_active_engines_lock = threading.Lock()


class ChatHandler:
    def __init__(self, db, **kwargs):
        self.db = db

        # Register the agents here
        self.agents = [
            SummarizeVideoAgent,
            UploadAgent,
            IndexAgent,
            SearchAgent,
            PromptClipAgent,
            FrameAgent,
            DownloadAgent,
            CloneVoiceAgent,
            CensorAgent,
            ImageGenerationAgent,
            AudioGenerationAgent,
            VideoGenerationAgent,
            StreamVideoAgent,
            SubtitleAgent,
            SlackAgent,
            EditingAgent,
            DubbingAgent,
            TranscriptionAgent,
            TextToMovieAgent,
            ComposioAgent,
            ComparisonAgent,
            CodeAssistantAgent,
            WebSearchAgent,
            VoiceReplacementAgent,
            PricingAgent,
        ]

    def add_videodb_state(self, session):
        """Populate session.state with a VideoDB connection, collection, and optionally a video."""
        from videodb import connect

        session.state["conn"] = connect(
            base_url=os.getenv("VIDEO_DB_BASE_URL", "https://api.videodb.io")
        )
        session.state["collection"] = session.state["conn"].get_collection(
            session.collection_id
        )
        if session.video_id:
            session.state["video"] = session.state["collection"].get_video(
                session.video_id
            )

    def agents_list(self):
        """Return a list of agent name/description dicts for all registered agents."""
        return [
            {
                "name": agent_instance.name,
                "description": agent_instance.agent_description,
            }
            for agent in self.agents
            for agent_instance in [agent(Session(db=self.db))]
        ]

    def chat(self, message):
        """Process an incoming chat message, run the reasoning engine, and stream the response."""
        logger.info(f"ChatHandler input message: {message}")

        session = Session(db=self.db, **message)

        # Reject duplicates before any DB writes or progress events.
        with _active_engines_lock:
            if session.session_id in _active_engines:
                logger.warning(
                    f"Generation already running for session {session.session_id}, ignoring duplicate"
                )
                return

        session.create()
        input_message = InputMessage(db=self.db, **message)
        input_message.publish()

        try:
            self.add_videodb_state(session)
            agents = [agent(session=session) for agent in self.agents]
            agents_mapping = {agent.name: agent for agent in agents}

            res_eng = ReasoningEngine(input_message=input_message, session=session)
            if input_message.agents:
                for agent_name in input_message.agents:
                    res_eng.register_agents([agents_mapping[agent_name]])
            else:
                res_eng.register_agents(agents)

            # Second check-and-claim to cover the window between the early check and engine creation.
            with _active_engines_lock:
                if session.session_id in _active_engines:
                    logger.warning(
                        f"Generation already running for session {session.session_id}, ignoring duplicate (late check)"
                    )
                    session.output_message.update_status(MsgStatus.error)
                    return
                _active_engines[session.session_id] = res_eng
            try:
                res_eng.run()
            finally:
                with _active_engines_lock:
                    if _active_engines.get(session.session_id) is res_eng:
                        _active_engines.pop(session.session_id, None)
                if res_eng.stop_flag:
                    session.output_message.update_status(MsgStatus.error)

        except Exception as e:
            session.output_message.update_status(MsgStatus.error)
            logger.exception(f"Error in chat handler: {e}")


class SessionHandler:
    def __init__(self, db: BaseDB, **kwargs):
        self.db = db

    def get_sessions(self):
        session = Session(db=self.db)
        return session.get_all()

    def get_session(self, session_id):
        session = Session(db=self.db, session_id=session_id)
        return session.get()

    def delete_session(self, session_id):
        session = Session(db=self.db, session_id=session_id)
        return session.delete()


class VideoDBHandler:
    def __init__(self, collection_id="default"):
        self.videodb_tool = VideoDBTool(collection_id=collection_id)

    def upload(self, source, source_type="url", media_type="video", name=None):
        return self.videodb_tool.upload(source, source_type, media_type, name)

    def get_collection(self):
        """Get a collection by ID."""
        return self.videodb_tool.get_collection()

    def get_collections(self):
        """Get all collections."""
        return self.videodb_tool.get_collections()

    def create_collection(self, name, description=""):
        return self.videodb_tool.create_collection(name, description)

    def delete_collection(self):
        return self.videodb_tool.delete_collection()

    def get_video(self, video_id):
        """Get a video by ID."""
        return self.videodb_tool.get_video(video_id)

    def delete_video(self, video_id):
        """Delete a specific video by its ID."""
        return self.videodb_tool.delete_video(video_id)

    def delete_image(self, image_id):
        """Delete a specific image by its ID."""
        return self.videodb_tool.delete_image(image_id)

    def delete_audio(self, video_id):
        """Delete a specific audio by its ID."""
        return self.videodb_tool.delete_audio(video_id)

    def get_videos(self):
        """Get all videos in a collection."""
        return self.videodb_tool.get_videos()

    def get_audio(self, audio_id):
        """Get a audio by ID."""
        return self.videodb_tool.get_audio(audio_id)

    def get_audios(self):
        """Get all audios in a collection."""
        return self.videodb_tool.get_audios()

    def generate_audio_url(self, audio_id):
        return self.videodb_tool.generate_audio_url(audio_id=audio_id)

    def delete_audio(self, audio_id):
        return self.videodb_tool.delete_audio(audio_id)

    def get_image(self, image_id):
        """Get a image by ID."""
        return self.videodb_tool.get_image(image_id)

    def get_images(self):
        """Get all images in a collection."""
        return self.videodb_tool.get_images()

    def generate_image_url(self, image_id):
        return self.videodb_tool.generate_image_url(image_id=image_id)


class ConfigHandler:
    def check(self):
        """Check the configuration of the server."""
        videodb_configured = bool(os.getenv("VIDEO_DB_API_KEY"))

        try:
            db = load_db(os.getenv("SERVER_DB_TYPE", os.getenv("DB_TYPE", "sqlite")))
            db_configured = db.health_check()
        except Exception:
            logger.exception("Failed to check database configuration")
            db_configured = False

        return {
            "videodb_configured": videodb_configured,
            "llm_configured": True,
            "db_configured": db_configured,
        }
