import pytest

from director.db.base import BaseDB


class MemoryDB(BaseDB):
    def __init__(self):
        self.messages = {}
        self.context = {}

    def create_session(self, session_id, video_id=None, collection_id=None, **kwargs):
        pass

    def get_session(self, session_id):
        return {}

    def get_sessions(self):
        return []

    def add_or_update_msg_to_conv(self, **kwargs):
        self.messages[kwargs["msg_id"]] = kwargs

    def get_conversations(self, session_id):
        return list(self.messages.values())

    def get_context_messages(self, session_id):
        return self.context.get(session_id, {})

    def add_or_update_context_msg(self, session_id, context):
        self.context[session_id] = context

    def health_check(self):
        return True


@pytest.fixture
def db():
    return MemoryDB()


@pytest.fixture(autouse=True)
def isolated_skills_dir(tmp_path, monkeypatch):
    """Point SKILLS_DIR at an empty temp folder so tests never read ~/.agents/skills."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    monkeypatch.setenv("SKILLS_DIR", str(skills_dir))
    return skills_dir
