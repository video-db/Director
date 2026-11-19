import os
import logging

from director.agents.bash_executor import BashExecutorAgent
from director.agents.code_executor import CodeExecutorAgent
from director.agents.stream_content import StreamContentAgent

from director.core.judge import ActionJudge, judge_llm
from director.core.permissions import Decision, clamp
from director.core.session import (
    ApprovalContent,
    ContextMessage,
    InputMessage,
    MsgStatus,
    OutputMessage,
    RoleTypes,
    Session,
)
from director.core.reasoning import ReasoningEngine, denial_text
from director.core.sandbox import get_default_sandbox
from director.core.sink import BaseSink, NullSink
from director.llm import get_default_llm
from director.db.base import BaseDB
from director.db import load_db
from director.tools.videodb_tool import VideoDBTool
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


SKIPPED = "The user sent a new message instead of answering, so this was not run."
INTERRUPTED = "The tool was interrupted before it finished."
DECISIONS = ("once", "chat", "deny")


class ChatHandler:
    def __init__(self, db, sink: BaseSink = None, **kwargs):
        self.db = db
        self.sink = sink or NullSink()

        # The model writes and runs code, guided by skills. stream_content
        # shows results in the chat; the executors need a sandbox.
        self.sandbox = get_default_sandbox()
        self.agents = [StreamContentAgent]
        if self.sandbox:
            self.agents.append(CodeExecutorAgent)
            if self.sandbox.supports_bash:
                self.agents.append(BashExecutorAgent)

    def add_videodb_state(self, session):
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

    def _engine(self, session) -> ReasoningEngine:
        session.sandbox = self.sandbox
        self.add_videodb_state(session)
        isolated = bool(self.sandbox and self.sandbox.isolated)
        return ReasoningEngine(
            session=session,
            llm=get_default_llm(),
            agents=[agent(session=session) for agent in self.agents],
            judge=ActionJudge(judge_llm(), isolated=isolated),
        )

    def chat(self, message):
        logger.info(f"ChatHandler input message: {message}")

        session = Session(db=self.db, sink=self.sink, **message)
        session.create()
        if message.get("mode"):
            session.permissions.mode = clamp(message["mode"])
            session.save_permissions()
        input_message = InputMessage(db=self.db, **message)
        input_message.publish()

        try:
            self._close_paused_turn(session)
            self._engine(session).run(input_message)

        except Exception as e:
            session.output_message.update_status(MsgStatus.error)
            logger.exception(f"Error in chat handler: {e}")

    def approve(self, payload: dict):
        """Apply the user's answer to an approval card and, once nothing is pending, continue the turn."""
        logger.info(f"ChatHandler approval: {payload}")
        session_id = payload.get("session_id")
        msg_id = payload.get("msg_id")
        approval_id = payload.get("approval_id")
        decision = payload.get("decision")
        note = (payload.get("note") or "").strip()[:2000] or None
        if decision not in DECISIONS:
            return

        saved = self.db.get_message(msg_id)
        if (
            not saved
            or saved.get("session_id") != session_id
            or saved.get("status") != MsgStatus.awaiting_approval
        ):
            return  # stale: the turn is already done

        allowed = decision != "deny"
        row = self.db.resolve_approval(
            approval_id,
            session_id,
            status="running" if allowed else "denied",
            decision=decision,
            note=note,
        )
        if row is None:
            return  # already answered, e.g. a double-click or another tab

        session_row = self.db.get_session(session_id) or {}
        output_message = OutputMessage(db=self.db, sink=self.sink, **saved)
        session = Session(
            db=self.db,
            sink=self.sink,
            session_id=session_id,
            conv_id=saved["conv_id"],
            collection_id=session_row.get("collection_id"),
            video_id=session_row.get("video_id"),
            output_message=output_message,
        )

        try:
            engine = self._engine(session)
            tool_call = {
                "id": approval_id,
                "type": "function",
                "tool": {"name": row["agent"], "arguments": row["arguments"]},
            }
            agent = engine.agents.get(row["agent"])
            info = engine.inspect(agent, row["arguments"]) if agent else None

            # A deny rule added since the card was shown still wins.
            blocked = None
            if allowed and (agent is None or info.blocked):
                allowed = False
                blocked = info.blocked if info else "That tool is no longer available."

            if allowed:
                approved_by = (
                    "Approved by you for this chat"
                    if decision == "chat"
                    else "Approved by you"
                )
                set_card(
                    output_message, approval_id, state="running", decided_by=approved_by
                )
                output_message.push_update()
                result = engine.run_tool(tool_call, approved_by).content
                self.db.set_approval_result(approval_id, result, "approved")
                set_card(output_message, approval_id, state="approved")
                if (
                    decision == "chat"
                    and info.key
                    and info.key not in session.permissions.allowed
                ):
                    session.permissions.allowed.append(info.key)
                session.permissions.record(Decision("allow", source="user"))
            elif blocked:
                self.db.set_approval_result(approval_id, denial_text(blocked), "denied")
                set_card(
                    output_message,
                    approval_id,
                    state="denied",
                    decided_by="Blocked by a rule",
                )
            else:
                reason = "The user denied this." + (
                    f" Their note: {note}" if note else ""
                )
                self.db.set_approval_result(approval_id, denial_text(reason), "denied")
                set_card(
                    output_message,
                    approval_id,
                    state="denied",
                    decided_by="Denied by you",
                    note=note,
                )
            output_message.push_update()
            session.save_permissions()

            # Another card is still open, or another handler is running its tool.
            if self.db.get_approvals(msg_id, statuses=("pending", "running")):
                return
            if not self.db.claim_resume(msg_id):
                return  # another handler is continuing this turn

            add_tool_results(session, self.db.get_approvals(msg_id))
            engine.resume()

        except Exception as e:
            output_message.update_status(MsgStatus.error)
            logger.exception(f"Error resuming turn: {e}")

    def _close_paused_turn(self, session):
        """A new message while cards are open: skip them so the history stays valid."""
        saved = self.db.get_awaiting_output(session.session_id)
        if not saved or not self.db.claim_resume(saved["msg_id"]):
            return
        self.db.skip_pending(saved["msg_id"], SKIPPED, INTERRUPTED)
        rows = self.db.get_approvals(saved["msg_id"])
        add_tool_results(session, rows)
        session.save_context_messages()

        old = OutputMessage(db=self.db, sink=self.sink, **saved)
        for row in rows:
            if row["status"] in ("skipped", "interrupted"):
                set_card(old, row["approval_id"], state=row["status"])
        old.actions.append("Skipped: you sent a new message")
        old.status = MsgStatus.success
        old.publish()


def set_card(output_message, approval_id: str, **changes):
    """Update an approval card in place; cards loaded from the DB are plain dicts."""
    for item in output_message.content:
        if isinstance(item, ApprovalContent) and item.approval_id == approval_id:
            for key, value in changes.items():
                setattr(item, key, value)
        elif isinstance(item, dict) and item.get("approval_id") == approval_id:
            item.update(changes)


def add_tool_results(session, rows):
    """Append each resolved approval's result to the context, once."""
    ctx = session.reasoning_context
    present = {m.tool_call_id for m in ctx if m.role == RoleTypes.tool}
    for row in rows:
        if row["approval_id"] in present or row["status"] in ("pending", "running"):
            continue
        ctx.append(
            ContextMessage(
                content=row.get("result") or INTERRUPTED,
                tool_call_id=row["approval_id"],
                role=RoleTypes.tool,
            )
        )


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
        videodb_configured = True if os.getenv("VIDEO_DB_API_KEY") else False

        db = load_db(os.getenv("SERVER_DB_TYPE", os.getenv("DB_TYPE", "sqlite")))
        db_configured = db.health_check()
        return {
            "videodb_configured": videodb_configured,
            "llm_configured": True,
            "db_configured": db_configured,
        }
