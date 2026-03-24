"""Integration tests for MiniMax LLM provider.

These tests call the real MiniMax API and require MINIMAX_API_KEY to be set.
Skip with: pytest -m "not integration"
"""

import json
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("MINIMAX_API_KEY"),
    reason="MINIMAX_API_KEY not set",
)


@pytest.fixture
def minimax_llm():
    """Create a MiniMax LLM instance with real API credentials."""
    from director.llm.minimax import MiniMax, MiniMaxConfig

    config = MiniMaxConfig()
    return MiniMax(config=config)


class TestMiniMaxIntegration:
    """Integration tests for MiniMax LLM provider against real API."""

    def test_simple_chat(self, minimax_llm):
        """Test a simple chat completion."""
        from director.llm.base import LLMResponseStatus

        result = minimax_llm.chat_completions(
            [{"role": "user", "content": "Reply with exactly: Hello Director"}]
        )
        assert result.status == LLMResponseStatus.SUCCESS
        assert len(result.content) > 0
        assert result.total_tokens > 0

    def test_json_response_format(self, minimax_llm):
        """Test chat completion with JSON response format."""
        from director.llm.base import LLMResponseStatus

        result = minimax_llm.chat_completions(
            [
                {
                    "role": "user",
                    "content": 'Return a JSON object with key "status" and value "ok". No other text.',
                }
            ],
            response_format={"type": "json_object"},
        )
        assert result.status == LLMResponseStatus.SUCCESS
        parsed = json.loads(result.content)
        assert "status" in parsed

    def test_tool_calling(self, minimax_llm):
        """Test function/tool calling capabilities."""
        from director.llm.base import LLMResponseStatus

        tools = [
            {
                "name": "search_video",
                "description": "Search for a video by query string",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query",
                        }
                    },
                    "required": ["query"],
                },
            }
        ]

        result = minimax_llm.chat_completions(
            [{"role": "user", "content": "Search for cat videos"}],
            tools=tools,
        )
        assert result.status == LLMResponseStatus.SUCCESS
        assert len(result.tool_calls) > 0
        assert result.tool_calls[0]["tool"]["name"] == "search_video"
