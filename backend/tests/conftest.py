import pytest

from director.db.base import BaseDB


class MemoryDB(BaseDB):
    def __init__(self):
        self.messages = {}
        self.context = {}
        self.sessions = {}
        self.approvals = {}
        self.rules = {}

    def create_session(self, session_id, video_id=None, collection_id=None, **kwargs):
        self.sessions.setdefault(
            session_id,
            {"session_id": session_id, "video_id": video_id, "collection_id": collection_id, "metadata": {}},
        )

    def get_session(self, session_id):
        return self.sessions.get(session_id, {})

    def get_message(self, msg_id):
        return self.messages.get(msg_id)

    def get_awaiting_output(self, session_id):
        for message in self.messages.values():
            if message["session_id"] == session_id and message["status"] == "awaiting_approval":
                return message
        return None

    def claim_resume(self, msg_id):
        message = self.messages.get(msg_id)
        if message and message["status"] == "awaiting_approval":
            message["status"] = "progress"
            return True
        return False

    def update_session_metadata(self, session_id, patch):
        self.sessions.setdefault(session_id, {"session_id": session_id, "metadata": {}})
        self.sessions[session_id]["metadata"].update(patch)

    def create_approval(self, **approval):
        self.approvals[approval["approval_id"]] = {**approval, "status": "pending", "result": None}

    def resolve_approval(self, approval_id, session_id, status, decision, note=None):
        row = self.approvals.get(approval_id)
        if not row or row["session_id"] != session_id or row["status"] != "pending":
            return None
        row.update(status=status, decision=decision, note=note)
        return dict(row)

    def set_approval_result(self, approval_id, result, status):
        self.approvals[approval_id].update(result=result, status=status)

    def skip_pending(self, msg_id, skipped_result, interrupted_result):
        for row in self.approvals.values():
            if row["msg_id"] != msg_id:
                continue
            if row["status"] == "pending":
                row.update(status="skipped", result=skipped_result)
            elif row["status"] == "running" and row["result"] is None:
                row.update(status="interrupted", result=interrupted_result)

    def get_approvals(self, msg_id, statuses=None):
        return [
            dict(r)
            for r in self.approvals.values()
            if r["msg_id"] == msg_id and (not statuses or r["status"] in statuses)
        ]

    def add_permission_rule(self, **rule):
        key = (rule["agent"], rule["pattern"], rule["action"])
        if all((r["agent"], r["pattern"], r["action"]) != key for r in self.rules.values()):
            self.rules[rule["rule_id"]] = dict(rule)

    def get_permission_rules(self, action=None):
        return [dict(r) for r in self.rules.values() if not action or r["action"] == action]

    def delete_permission_rule(self, rule_id):
        return self.rules.pop(rule_id, None) is not None

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
