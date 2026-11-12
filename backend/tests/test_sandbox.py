import os

import pytest

from director.agents.base import AgentStatus
from director.agents.bash_executor import BashExecutorAgent
from director.agents.code_executor import CodeExecutorAgent
from director.agents.sandbox_agent import truncate
from director.core.sandbox import (
    LocalSandboxExecutor,
    get_default_sandbox,
)
from director.core.sandbox.local import TIMEOUT_EXIT_CODE
from director.core.session import Session
from director.core.sink import CollectingSink


@pytest.fixture
def local():
    return LocalSandboxExecutor(timeout=30)


@pytest.fixture(autouse=True)
def fresh_factory():
    get_default_sandbox.cache_clear()
    yield
    get_default_sandbox.cache_clear()


def test_run_code_uses_the_server_python(local):
    result = local.run_code("import sys, videodb; print(sys.executable)")
    assert result.ok
    assert result.stdout.strip() == local._python


def test_run_bash_captures_output_and_exit_code(local):
    result = local.run_bash("echo out; echo err >&2; exit 3")
    assert result.stdout == "out\n"
    assert result.stderr == "err\n"
    assert result.exit_code == 3 and not result.ok


def test_each_call_gets_a_fresh_directory_that_is_removed(local):
    first = local.run_bash("pwd; touch marker").stdout.strip()
    second = local.run_bash("pwd; ls").stdout.split()
    assert first != second[0]
    assert "marker" not in second
    assert not os.path.exists(first)


def test_only_secrets_and_basic_env_reach_the_process(local, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-leak")
    result = local.run_bash(
        'echo "${OPENAI_API_KEY:-unset} $VIDEO_DB_API_KEY"',
        secrets={"VIDEO_DB_API_KEY": "vdb-key"},
    )
    assert result.stdout.strip() == "unset vdb-key"


def test_timeout_returns_a_result_instead_of_raising(local):
    result = local.run_bash("echo started; sleep 5", timeout=1)
    assert result.exit_code == TIMEOUT_EXIT_CODE
    assert "Timed out after 1s" in result.stderr


def test_factory_defaults_to_local(monkeypatch):
    monkeypatch.delenv("SANDBOX_PROVIDER", raising=False)
    assert isinstance(get_default_sandbox(), LocalSandboxExecutor)


@pytest.mark.parametrize("provider", ["none", "nonsense"])
def test_factory_returns_none_when_disabled_or_unknown(provider):
    assert get_default_sandbox(provider) is None


def test_factory_returns_none_when_modal_has_no_credentials(monkeypatch, tmp_path):
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert get_default_sandbox("modal") is None


def make_session(db, sandbox):
    session = Session(db=db, sink=CollectingSink(), session_id="s-1", conv_id="c-1")
    session.sandbox = sandbox
    return session


def test_code_executor_returns_stdout_and_shows_the_code(db, local, monkeypatch):
    monkeypatch.delenv("VIDEO_DB_API_KEY", raising=False)
    session = make_session(db, local)
    agent = CodeExecutorAgent(session=session)

    response = agent.run(
        code="print(conn is None, json.dumps({'a': 1}))",
        progress_message="Testing",
    )

    assert response.status == AgentStatus.SUCCESS
    assert response.data["stdout"] == 'True {"a": 1}\n'
    shown = session.output_message.content[-1]
    assert shown.text.startswith("```python\nprint(conn is None")
    assert shown.status_message == "Testing"


def test_code_executor_reports_errors(db, local):
    agent = CodeExecutorAgent(session=make_session(db, local))
    response = agent.run(code="raise ValueError('nope')", progress_message="Failing")

    assert response.status == AgentStatus.ERROR
    assert "ValueError: nope" in response.data["stderr"]


def test_bash_executor_passes_videodb_key(db, local, monkeypatch):
    monkeypatch.setenv("VIDEO_DB_API_KEY", "vdb-key")
    agent = BashExecutorAgent(session=make_session(db, local))

    response = agent.run(command="echo $VIDEO_DB_API_KEY", progress_message="Key")

    assert response.data["stdout"] == "vdb-key\n"


def test_agent_without_sandbox_returns_error(db):
    agent = BashExecutorAgent(session=make_session(db, None))
    response = agent.run(command="echo hi", progress_message="Nope")
    assert response.status == AgentStatus.ERROR


def test_agent_schemas_are_valid_tools(db):
    for agent_cls in (CodeExecutorAgent, BashExecutorAgent):
        tool = agent_cls(session=make_session(db, None)).to_llm_format()
        assert tool["parameters"]["required"][0] in tool["parameters"]["properties"]


def test_truncate_keeps_head_and_tail():
    text = "a" * 6000 + "b" * 6000
    out = truncate(text)
    assert out.startswith("a" * 4000) and out.endswith("b" * 4000)
    assert "[4000 chars truncated]" in out


def test_chat_handler_tools_follow_the_sandbox(db, monkeypatch):
    from director.agents.stream_content import StreamContentAgent
    from director.handler import ChatHandler

    monkeypatch.setenv("SANDBOX_PROVIDER", "none")
    assert ChatHandler(db=db).agents == [StreamContentAgent]

    get_default_sandbox.cache_clear()
    monkeypatch.setenv("SANDBOX_PROVIDER", "local")
    assert ChatHandler(db=db).agents == [
        StreamContentAgent,
        CodeExecutorAgent,
        BashExecutorAgent,
    ]


def test_local_without_bash_offers_only_code(db, monkeypatch):
    from director.agents.stream_content import StreamContentAgent
    from director.handler import ChatHandler

    monkeypatch.setattr("director.core.sandbox.local.shutil.which", lambda name: None)
    monkeypatch.setenv("SANDBOX_PROVIDER", "local")
    assert not LocalSandboxExecutor().supports_bash
    assert ChatHandler(db=db).agents == [StreamContentAgent, CodeExecutorAgent]


def test_engine_runs_code_executor_end_to_end(db, local):
    from types import SimpleNamespace

    from director.core.reasoning import ReasoningEngine
    from director.core.session import InputMessage
    from director.llm.base import LLMResponse, LLMResponseStatus

    class ScriptedLLM:
        def __init__(self):
            self.calls = []

        def chat_completions(self, messages, tools=None, **kwargs):
            self.calls.append(messages)
            if len(self.calls) == 1:
                return LLMResponse(
                    tool_calls=[
                        {
                            "id": "call_1",
                            "type": "function",
                            "tool": {
                                "name": "code_executor",
                                "arguments": {
                                    "code": "print(sum(range(10)))",
                                    "progress_message": "Adding numbers",
                                },
                            },
                        }
                    ],
                    status=LLMResponseStatus.SUCCESS,
                )
            return LLMResponse(
                content="The sum is 45.", status=LLMResponseStatus.SUCCESS
            )

    session = make_session(db, local)
    session.state["collection"] = SimpleNamespace(
        name="default", id="c-1", description=""
    )
    llm = ScriptedLLM()
    ReasoningEngine(
        session=session, llm=llm, agents=[CodeExecutorAgent(session=session)]
    ).run(
        InputMessage(
            db=db,
            session_id="s-1",
            conv_id="c-1",
            content=[{"type": "text", "text": "sum 0..9"}],
        )
    )

    tool_result = llm.calls[1][-1]["content"]
    assert "'stdout': '45\\n'" in tool_result
    assert session.output_message.content[-1].text == "The sum is 45."
