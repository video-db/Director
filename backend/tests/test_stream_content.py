from director.agents.base import AgentStatus
from director.agents.stream_content import StreamContentAgent
from director.core.session import Session
from director.core.sink import CollectingSink


def make_agent(db):
    session = Session(db=db, sink=CollectingSink(), session_id="s-1", conv_id="c-1")
    return StreamContentAgent(session=session), session


def test_shows_each_item_as_chat_content(db):
    agent, session = make_agent(db)

    response = agent.run(
        output=[
            {
                "type": "video",
                "status_message": "Your clip",
                "video": {
                    "stream_url": "https://x/v.m3u8",
                    "id": "m-1",
                    "extra": "ignored",
                },
            },
            {
                "type": "search_results",
                "status_message": "Matches",
                "search_results": [
                    {
                        "video_id": "m-1",
                        "stream_url": "https://x/s.m3u8",
                        "duration": 10,
                        "shots": [
                            {"start": 1, "end": 2, "text": "hi", "search_score": 0.9}
                        ],
                    }
                ],
            },
            {"type": "text", "text": "**Done**"},
        ]
    )

    assert response.status == AgentStatus.SUCCESS
    shown = [c.model_dump() for c in session.output_message.content]
    assert [c["type"] for c in shown] == ["video", "search_results", "text"]
    assert shown[0]["video"]["stream_url"] == "https://x/v.m3u8"
    assert shown[0]["status_message"] == "Your clip"
    assert shown[1]["search_results"][0]["shots"][0]["text"] == "hi"
    assert session.sink.events[-1][0] == "chat"


def test_invalid_item_shows_nothing_and_reports_the_error(db):
    agent, session = make_agent(db)

    response = agent.run(
        output=[
            {"type": "text", "text": "fine"},
            {"type": "video", "video": {"name": "no stream url"}},
        ]
    )

    assert response.status == AgentStatus.ERROR
    assert "Invalid output item" in response.message
    assert session.output_message.content == []


def test_unknown_type_is_an_error(db):
    agent, _ = make_agent(db)
    response = agent.run(output=[{"type": "audio"}])
    assert response.status == AgentStatus.ERROR
