from director.core.session import Session, TextContent, VideosUpdateEvent
from director.core.sink import CollectingSink


def test_output_message_publishes_to_sink_and_db(db):
    sink = CollectingSink()
    session = Session(db=db, sink=sink, session_id="s-1", conv_id="c-1")
    message = session.output_message

    message.content.append(TextContent(text="hello", agent_name="assistant"))
    message.push_update()

    channel, payload = sink.events[-1]
    assert channel == "chat"
    assert payload["content"][0]["text"] == "hello"
    assert "sink" not in payload and "db" not in payload
    assert db.messages[message.msg_id]["content"][0]["text"] == "hello"


def test_new_output_message_shares_the_session_sink(db):
    sink = CollectingSink()
    session = Session(db=db, sink=sink, session_id="s-1", conv_id="c-1")

    session.new_message().publish()

    assert len(sink.events) == 1


def test_emit_event_goes_to_event_channel(db):
    sink = CollectingSink()
    session = Session(db=db, sink=sink, session_id="s-1")

    session.emit_event(VideosUpdateEvent(collection_id="c-1"))

    assert sink.events == [
        (
            "event",
            {"event_type": "update_data", "update": "videos", "collection_id": "c-1"},
        )
    ]


def test_session_without_sink_does_not_fail(db):
    session = Session(db=db, session_id="s-1")
    session.output_message.publish()


def test_default_llm_env_wins_over_keys(monkeypatch):
    from director.llm import get_default_llm
    from director.llm.anthropic import AnthropicAI
    from director.llm.openai import OpenAI

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("DEFAULT_LLM", "anthropic")
    assert isinstance(get_default_llm(), AnthropicAI)

    monkeypatch.delenv("DEFAULT_LLM")
    assert isinstance(get_default_llm(), OpenAI)
