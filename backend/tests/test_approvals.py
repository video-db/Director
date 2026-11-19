from types import SimpleNamespace

import pytest

import director.handler as handler_module
from director.agents.base import AgentResponse, BaseAgent
from director.core.permissions import (
    CallInfo,
    Decision,
    Mode,
    Permissions,
    clamp,
    decide,
)
from director.core.sink import CollectingSink
from director.db.sqlite.db import SQLiteDB
from director.db.sqlite.initialize import initialize_sqlite
from director.handler import INTERRUPTED, SKIPPED, ChatHandler
from director.llm.base import LLMResponse, LLMResponseStatus

RUNS = []


class EchoAgent(BaseAgent):
    def __init__(self, session=None, **kwargs):
        self.agent_name = "echo"
        self.description = "Echoes the given text."
        self.parameters = self.get_parameters()
        super().__init__(session=session, **kwargs)

    def inspect(self, text: str = "", **kwargs) -> CallInfo:
        return CallInfo(
            preview=text,
            destructive="Deletes things." if text == "delete" else None,
            key=f"echo:{text}",
        )

    def run(self, text: str, *args, **kwargs) -> AgentResponse:
        """
        Echo the text.

        :param str text: The text to echo.
        """
        RUNS.append(text)
        return AgentResponse(message=f"echo: {text}")


class FakeLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat_completions(self, messages, tools=None, **kwargs):
        self.calls.append(messages)
        return self.responses.pop(0)


def answer(text):
    return LLMResponse(content=text, status=LLMResponseStatus.SUCCESS)


def calls(*items):
    return LLMResponse(
        tool_calls=[
            {
                "id": call_id,
                "type": "function",
                "tool": {"name": "echo", "arguments": {"text": text}},
            }
            for call_id, text in items
        ],
        status=LLMResponseStatus.SUCCESS,
    )


@pytest.fixture
def setup(tmp_path, monkeypatch):
    RUNS.clear()
    path = str(tmp_path / "director.db")
    initialize_sqlite(path)
    state = SimpleNamespace(llm=None, judge=None, sink=CollectingSink(), path=path)

    monkeypatch.setattr(handler_module, "get_default_llm", lambda: state.llm)
    monkeypatch.setattr(handler_module, "judge_llm", lambda: state.judge)
    monkeypatch.setattr(
        ChatHandler,
        "add_videodb_state",
        lambda self, s: s.state.update(
            collection=SimpleNamespace(name="default", id="c-1", description="")
        ),
    )

    def handler():
        h = ChatHandler(db=SQLiteDB(path), sink=state.sink)
        h.agents = [EchoAgent]
        return h

    state.handler = handler
    state.db = SQLiteDB(path)
    return state


def chat(state, text="hi", mode="ask", conv="1"):
    state.handler().chat(
        {
            "session_id": "s-1",
            "conv_id": conv,
            "msg_id": f"in-{conv}",
            "collection_id": "c-1",
            "content": [{"type": "text", "text": text}],
            "mode": mode,
        }
    )
    return state.db.get_awaiting_output("s-1")


def approve(state, msg, approval_id, decision="once", note=None):
    state.handler().approve(
        {
            "session_id": "s-1",
            "msg_id": msg["msg_id"],
            "approval_id": approval_id,
            "decision": decision,
            "note": note,
        }
    )
    return state.db.get_message(msg["msg_id"])


def card(message, approval_id):
    return next(c for c in message["content"] if c.get("approval_id") == approval_id)


def tool_messages(llm_call):
    return [m for m in llm_call if m["role"] == "tool"]


# ---- decide ----


def test_decide_order():
    perms = Permissions(mode=Mode.ask)
    assert (
        decide(
            "x", CallInfo(preview="", blocked="no"), Permissions(mode=Mode.full)
        ).action
        == "deny"
    )
    assert decide("x", CallInfo(preview="", read_only=True), perms).action == "allow"
    assert decide("x", CallInfo(preview=""), perms).action == "ask"
    assert (
        decide(
            "x", CallInfo(preview="", destructive="d"), Permissions(mode=Mode.full)
        ).action
        == "allow"
    )
    assert (
        decide(
            "x", CallInfo(preview="", destructive="d"), Permissions(mode=Mode.auto)
        ).offer_chat
        is False
    )
    allowed = Permissions(mode=Mode.ask, allowed=["k"])
    assert decide("x", CallInfo(preview="", key="k"), allowed).source == "chat"
    assert (
        decide("x", CallInfo(preview="", key="k", risks=["r"]), allowed).action == "ask"
    )


def test_auto_without_judge_asks_and_paused_judge_asks():
    assert (
        decide("x", CallInfo(preview=""), Permissions(mode=Mode.auto)).action == "ask"
    )
    perms = Permissions(mode=Mode.auto, judge_streak=3)
    verdict = decide(
        "x",
        CallInfo(preview=""),
        perms,
        judge=lambda n, i: Decision("allow", source="judge"),
    )
    assert verdict.action == "ask"


def test_clamp_respects_the_ceiling(monkeypatch):
    assert clamp("full") == Mode.full
    assert clamp("nonsense") == Mode.auto
    monkeypatch.setenv("DIRECTOR_MAX_MODE", "ask")
    assert clamp("full") == Mode.ask


# ---- pause and resume ----


def test_ask_pauses_and_approve_continues_the_same_message(setup):
    setup.llm = FakeLLM([calls(("call_1", "ping")), answer("Done.")])
    paused = chat(setup)

    assert paused["status"] == "awaiting_approval"
    assert card(paused, "call_1")["state"] == "pending"
    assert RUNS == []
    saved = setup.db.get_context_messages("s-1")["reasoning"]
    assert saved[-1]["tool_calls"][0]["id"] == "call_1"  # waiting for its result

    done = approve(setup, paused, "call_1")
    assert RUNS == ["ping"]
    assert done["status"] == "success"
    assert card(done, "call_1")["state"] == "approved"
    assert card(done, "call_1")["decided_by"] == "Approved by you"
    assert done["content"][-1]["text"] == "Done."
    assert "echo: ping" in tool_messages(setup.llm.calls[1])[0]["content"]


def test_double_approve_runs_the_tool_once(setup):
    setup.llm = FakeLLM([calls(("call_1", "ping")), answer("Done.")])
    paused = chat(setup)
    approve(setup, paused, "call_1")
    approve(setup, paused, "call_1")
    assert RUNS == ["ping"]
    assert len(setup.llm.calls) == 2


def test_deny_sends_the_note_to_the_model(setup):
    setup.llm = FakeLLM([calls(("call_1", "ping")), answer("OK, I won't.")])
    paused = chat(setup)
    done = approve(
        setup, paused, "call_1", decision="deny", note="use the other collection"
    )

    assert RUNS == []
    assert card(done, "call_1")["state"] == "denied"
    result = tool_messages(setup.llm.calls[1])[0]["content"]
    assert "use the other collection" in result


def test_two_cards_resume_once_both_are_answered(setup):
    setup.llm = FakeLLM([calls(("a", "one"), ("b", "two")), answer("Both done.")])
    paused = chat(setup)

    approve(setup, paused, "a")
    assert len(setup.llm.calls) == 1  # still waiting on b
    done = approve(setup, paused, "b", decision="deny")

    assert done["status"] == "success"
    assert len(tool_messages(setup.llm.calls[1])) == 2


def test_new_message_skips_open_cards(setup):
    setup.llm = FakeLLM([calls(("call_1", "ping")), answer("Hello.")])
    paused = chat(setup, conv="1")
    chat(setup, text="never mind", conv="2")

    old = setup.db.get_message(paused["msg_id"])
    assert old["status"] == "success"
    assert card(old, "call_1")["state"] == "skipped"
    sent = setup.llm.calls[1]
    roles = [m["role"] for m in sent]
    assert roles[-2:] == [
        "tool",
        "user",
    ]  # the skipped result comes before the new message
    assert SKIPPED in sent[-2]["content"]
    assert RUNS == []


def test_stale_approval_is_ignored(setup):
    setup.llm = FakeLLM([calls(("call_1", "ping")), answer("Hello.")])
    paused = chat(setup, conv="1")
    chat(setup, text="never mind", conv="2")
    approve(setup, paused, "call_1")
    assert RUNS == []


def test_allow_for_this_chat_skips_the_next_card(setup):
    setup.llm = FakeLLM(
        [
            calls(("call_1", "ping")),
            answer("one"),
            calls(("call_2", "ping")),
            answer("two"),
        ]
    )
    paused = chat(setup, conv="1")
    approve(setup, paused, "call_1", decision="chat")

    assert chat(setup, conv="2") is None  # ran without a card
    assert RUNS == ["ping", "ping"]


def test_deletes_never_offer_allow_for_this_chat(setup):
    setup.llm = FakeLLM([calls(("call_1", "delete"))])
    paused = chat(setup, mode="auto")
    assert card(paused, "call_1")["options"] == ["once", "deny"]


def test_auto_mode_follows_the_judge(setup):
    setup.judge = FakeLLM([answer('{"decision": "allow", "reason": "As asked."}')])
    setup.llm = FakeLLM([calls(("call_1", "ping")), answer("Done.")])
    assert chat(setup, mode="auto") is None
    assert RUNS == ["ping"]


def test_judge_deny_goes_back_to_the_model(setup):
    setup.judge = FakeLLM(
        [answer('{"decision": "deny", "reason": "Reads credentials."}')]
    )
    setup.llm = FakeLLM([calls(("call_1", "ping")), answer("I can't do that.")])
    chat(setup, mode="auto")
    assert RUNS == []
    assert "Reads credentials." in tool_messages(setup.llm.calls[1])[0]["content"]


def test_unreadable_judge_answer_asks(setup):
    setup.judge = FakeLLM([answer("sure thing")])
    setup.llm = FakeLLM([calls(("call_1", "ping"))])
    paused = chat(setup, mode="auto")
    assert paused and card(paused, "call_1")["state"] == "pending"


def test_judge_sees_only_the_users_words(setup):
    setup.judge = FakeLLM([answer('{"decision": "allow", "reason": "ok"}')])
    setup.llm = FakeLLM([calls(("call_1", "ping")), answer("Done.")])
    chat(setup, text="please echo ping", mode="auto")
    judged = setup.judge.calls[0][1]["content"]
    assert "please echo ping" in judged and "echo: " not in judged


def test_interrupted_tool_is_reported_on_the_next_message(setup):
    setup.llm = FakeLLM([calls(("call_1", "ping")), answer("Hello.")])
    chat(setup, conv="1")
    setup.db.resolve_approval(
        "call_1", "s-1", status="running", decision="once"
    )  # crashed mid-run
    chat(setup, text="hello?", conv="2")
    assert INTERRUPTED in setup.llm.calls[1][-2]["content"]


def test_sqlite_keeps_created_at_when_a_message_is_updated(setup):
    row = dict(
        session_id="s-1",
        conv_id="1",
        msg_id="m",
        msg_type="output",
        agents=[],
        actions=[],
        content=[],
    )
    setup.db.add_or_update_msg_to_conv(**row, created_at=100)
    setup.db.add_or_update_msg_to_conv(**row, status="success")
    assert setup.db.get_message("m")["created_at"] == 100
