from types import SimpleNamespace

from director.agents.base import BaseAgent, AgentResponse
from director.core.context import ContextPolicy
from director.core.reasoning import MAX_ITERATIONS_REPLY, ReasoningEngine
from director.core.session import (
    ContextMessage,
    InputMessage,
    MsgStatus,
    RoleTypes,
    Session,
)
from director.core.sink import CollectingSink
from director.llm.base import LLMResponse, LLMResponseStatus


class FakeLLM:
    """Returns scripted responses in order and records every call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat_completions(self, messages, tools=None, **kwargs):
        self.calls.append({"messages": messages, "tools": tools})
        return self.responses.pop(0)


class EchoAgent(BaseAgent):
    def __init__(self, session=None, **kwargs):
        self.agent_name = "echo"
        self.description = "Echoes the given text."
        self.parameters = self.get_parameters()
        super().__init__(session=session, **kwargs)

    def run(self, text: str, *args, **kwargs) -> AgentResponse:
        """
        Echo the text.

        :param str text: The text to echo.
        """
        if text == "boom":
            raise ValueError("boom")
        return AgentResponse(message=f"echo: {text}")


def answer(text):
    return LLMResponse(
        content=text, finish_reason="stop", status=LLMResponseStatus.SUCCESS
    )


def call_echo(text, call_id="call_1"):
    return LLMResponse(
        tool_calls=[
            {
                "id": call_id,
                "type": "function",
                "tool": {"name": "echo", "arguments": {"text": text}},
            }
        ],
        finish_reason="tool_calls",
        status=LLMResponseStatus.SUCCESS,
    )


def fake_collection(video_names):
    videos = [
        SimpleNamespace(name=name, id=f"m-{i}", description="", length=1, stream_url="")
        for i, name in enumerate(video_names)
    ]
    return SimpleNamespace(
        name="default",
        id="c-1",
        description="",
        get_videos=lambda: videos,
        get_images=lambda: [],
    )


def make_session(db, sink, video_names=("intro",)):
    session = Session(
        db=db, sink=sink, session_id="s-1", conv_id="c-1", collection_id="c-1"
    )
    session.state["collection"] = fake_collection(video_names)
    return session


def run_turn(db, sink, llm, text="hi", max_iterations=10, video_names=("intro",)):
    session = make_session(db, sink, video_names)
    engine = ReasoningEngine(
        session=session,
        llm=llm,
        agents=[EchoAgent(session=session)],
        max_iterations=max_iterations,
    )
    input_message = InputMessage(
        db=db,
        session_id="s-1",
        conv_id="c-1",
        content=[{"type": "text", "text": text}],
    )
    engine.run(input_message)
    return session


def reply(session):
    return session.output_message.content[-1]


def test_direct_answer_is_the_reply(db):
    llm = FakeLLM([answer("Hello!")])
    session = run_turn(db, CollectingSink(), llm)

    assert len(llm.calls) == 1
    assert reply(session).text == "Hello!"
    assert session.output_message.status == MsgStatus.success


def test_tool_call_then_final_answer_needs_no_extra_call(db):
    sink = CollectingSink()
    llm = FakeLLM([call_echo("ping"), answer("Done, echoed ping.")])
    session = run_turn(db, sink, llm)

    assert len(llm.calls) == 2
    assert llm.calls[0]["tools"][0]["name"] == "echo"
    tool_msg = llm.calls[1]["messages"][-1]
    assert tool_msg["role"] == RoleTypes.tool
    assert "echo: ping" in tool_msg["content"]
    assert reply(session).text == "Done, echoed ping."
    assert session.output_message.agents == ["echo"]
    assert sink.events and all(channel == "chat" for channel, _ in sink.events)

    saved = db.context["s-1"]["reasoning"]
    assert saved[-1] == {"role": "assistant", "content": "Done, echoed ping."}


def test_text_alongside_tool_call_is_shown(db):
    first = call_echo("ping")
    first.content = "Let me check that."
    llm = FakeLLM([first, answer("All done.")])
    session = run_turn(db, CollectingSink(), llm)

    texts = [c.text for c in session.output_message.content]
    assert texts == ["Let me check that.", "All done."]


def test_agent_error_goes_back_to_the_llm(db):
    llm = FakeLLM([call_echo("boom"), answer("The echo failed.")])
    session = run_turn(db, CollectingSink(), llm)

    tool_msg = llm.calls[1]["messages"][-1]
    assert "status='error'" in tool_msg["content"] and "boom" in tool_msg["content"]
    assert reply(session).text == "The echo failed."


def test_unknown_agent_is_reported_not_raised(db):
    bad_call = call_echo("x")
    bad_call.tool_calls[0]["tool"]["name"] = "missing"
    llm = FakeLLM([bad_call, answer("done")])
    run_turn(db, CollectingSink(), llm)

    assert "Unknown agent: missing" in llm.calls[1]["messages"][-1]["content"]


def test_stops_at_max_iterations(db):
    llm = FakeLLM([call_echo("a", f"call_{i}") for i in range(3)])
    session = run_turn(db, CollectingSink(), llm, max_iterations=3)

    assert len(llm.calls) == 3
    assert reply(session).text == MAX_ITERATIONS_REPLY


def test_context_is_saved_and_system_prompt_refreshed(db):
    run_turn(db, CollectingSink(), FakeLLM([answer("one")]), video_names=("intro",))
    saved = db.context["s-1"]["reasoning"]
    assert [m["role"] for m in saved] == ["system", "user", "assistant"]

    llm = FakeLLM([answer("two")])
    run_turn(db, CollectingSink(), llm, video_names=("intro", "uploaded later"))
    sent = llm.calls[0]["messages"]
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"]
    assert "uploaded later" in sent[0]["content"]


def test_policy_drops_oldest_whole_turns():
    def turn(i):
        return [
            ContextMessage(content=f"q{i}", role=RoleTypes.user),
            ContextMessage(
                content="",
                tool_calls=[{"id": f"t{i}", "type": "function", "tool": {}}],
                role=RoleTypes.assistant,
            ),
            ContextMessage(
                content="x" * 500, tool_call_id=f"t{i}", role=RoleTypes.tool
            ),
            ContextMessage(content=f"a{i}", role=RoleTypes.assistant),
        ]

    ctx = [ContextMessage(content="system", role=RoleTypes.system)]
    for i in range(5):
        ctx += turn(i)

    sent = ContextPolicy(max_chars=1500).apply(ctx)

    assert sent[0]["content"] == "system"
    assert sent[1]["role"] == RoleTypes.user
    assert sent[-1]["content"] == "a4"
    assert len(sent) < len(ctx)
    for i, message in enumerate(sent):
        if message["role"] == RoleTypes.tool:
            assert sent[i - 1].get("tool_calls")


def test_policy_keeps_latest_turn_even_if_over_limit():
    ctx = [
        ContextMessage(content="system", role=RoleTypes.system),
        ContextMessage(content="x" * 5000, role=RoleTypes.user),
    ]
    assert len(ContextPolicy(max_chars=10).apply(ctx)) == 2
