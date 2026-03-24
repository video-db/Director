"""Unit tests for MiniMax LLM provider."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from director.constants import LLMType, EnvPrefix
from director.llm.minimax import MiniMax, MiniMaxConfig, MiniMaxChatModel
from director.llm.base import LLMResponseStatus


class TestMiniMaxChatModel:
    """Tests for MiniMaxChatModel enum."""

    def test_model_values(self):
        assert MiniMaxChatModel.MINIMAX_M2_7 == "MiniMax-M2.7"
        assert MiniMaxChatModel.MINIMAX_M2_5 == "MiniMax-M2.5"
        assert MiniMaxChatModel.MINIMAX_M2_5_HIGHSPEED == "MiniMax-M2.5-highspeed"

    def test_model_count(self):
        assert len(MiniMaxChatModel) == 3


class TestMiniMaxConfig:
    """Tests for MiniMaxConfig."""

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key-123"})
    def test_config_from_env(self):
        config = MiniMaxConfig()
        assert config.api_key == "test-key-123"
        assert config.llm_type == LLMType.MINIMAX
        assert config.api_base == "https://api.minimax.io/v1"
        assert config.chat_model == MiniMaxChatModel.MINIMAX_M2_7

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "key", "MINIMAX_CHAT_MODEL": "MiniMax-M2.5"})
    def test_config_custom_model(self):
        config = MiniMaxConfig()
        assert config.chat_model == "MiniMax-M2.5"

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "key", "MINIMAX_API_BASE": "https://custom.api.io/v1"})
    def test_config_custom_api_base(self):
        config = MiniMaxConfig()
        assert config.api_base == "https://custom.api.io/v1"

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "key", "MINIMAX_TEMPERATURE": "0.5"})
    def test_config_custom_temperature(self):
        config = MiniMaxConfig()
        assert config.temperature == 0.5

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "key", "MINIMAX_MAX_TOKENS": "8192"})
    def test_config_custom_max_tokens(self):
        config = MiniMaxConfig()
        assert config.max_tokens == 8192

    def test_config_missing_api_key(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("MINIMAX_")}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="must not be empty"):
                MiniMaxConfig()

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "key", "MINIMAX_TEMPERATURE": "1.5"})
    def test_temperature_clamped_high(self):
        config = MiniMaxConfig()
        assert config.temperature == 1.0

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "key", "MINIMAX_TEMPERATURE": "-0.5"})
    def test_temperature_clamped_low(self):
        config = MiniMaxConfig()
        assert config.temperature == 0.0

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "key", "MINIMAX_TEMPERATURE": "0"})
    def test_temperature_zero_accepted(self):
        config = MiniMaxConfig()
        assert config.temperature == 0.0

    def test_env_prefix(self):
        assert EnvPrefix.MINIMAX_ == "MINIMAX_"


class TestMiniMaxThinkTagStripping:
    """Tests for _strip_think_tags static method."""

    def test_strip_think_tags(self):
        content = "<think>Let me reason about this...</think>\nHello world"
        assert MiniMax._strip_think_tags(content) == "Hello world"

    def test_strip_multiline_think_tags(self):
        content = "<think>\nStep 1: analyze\nStep 2: respond\n</think>\nThe answer is 42."
        assert MiniMax._strip_think_tags(content) == "The answer is 42."

    def test_no_think_tags(self):
        content = "Just a normal response."
        assert MiniMax._strip_think_tags(content) == "Just a normal response."

    def test_empty_content(self):
        assert MiniMax._strip_think_tags("") == ""

    def test_none_content(self):
        assert MiniMax._strip_think_tags(None) is None

    def test_multiple_think_tags(self):
        content = "<think>first</think>Hello <think>second</think>world"
        assert MiniMax._strip_think_tags(content) == "Hello world"


@pytest.fixture
def minimax_llm():
    """Create a MiniMax LLM instance with mocked OpenAI client."""
    with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            llm = MiniMax()
            llm._mock_client = mock_client
            return llm


class TestMiniMaxFormatMessages:
    """Tests for _format_messages method."""

    def test_format_simple_messages(self, minimax_llm):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        formatted = minimax_llm._format_messages(messages)
        assert formatted == messages

    def test_format_tool_call_messages(self, minimax_llm):
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "tool": {
                            "name": "search_video",
                            "arguments": {"query": "funny cat"},
                        },
                        "type": "function",
                    }
                ],
            }
        ]
        formatted = minimax_llm._format_messages(messages)
        assert formatted[0]["tool_calls"][0]["function"]["name"] == "search_video"
        assert formatted[0]["tool_calls"][0]["function"]["arguments"] == json.dumps(
            {"query": "funny cat"}
        )

    def test_format_system_message(self, minimax_llm):
        messages = [
            {"role": "system", "content": "You are a video assistant."},
            {"role": "user", "content": "Summarize this video."},
        ]
        formatted = minimax_llm._format_messages(messages)
        assert len(formatted) == 2
        assert formatted[0]["role"] == "system"


class TestMiniMaxFormatTools:
    """Tests for _format_tools method."""

    def test_format_tools(self, minimax_llm):
        tools = [
            {
                "name": "search_video",
                "description": "Search for videos",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"],
                },
            }
        ]
        formatted = minimax_llm._format_tools(tools)
        assert len(formatted) == 1
        assert formatted[0]["type"] == "function"
        assert formatted[0]["function"]["name"] == "search_video"
        # No strict mode for MiniMax (unlike OpenAI)
        assert "strict" not in formatted[0]

    def test_format_empty_tools(self, minimax_llm):
        assert minimax_llm._format_tools([]) == []

    def test_skip_tools_without_name(self, minimax_llm):
        tools = [
            {"description": "No name tool", "parameters": {}},
            {"name": "valid_tool", "description": "Valid", "parameters": {}},
        ]
        formatted = minimax_llm._format_tools(tools)
        assert len(formatted) == 1
        assert formatted[0]["function"]["name"] == "valid_tool"


class TestMiniMaxChatCompletions:
    """Tests for chat_completions method."""

    def _make_mock_response(self, content="OK", tool_calls=None, finish_reason="stop",
                            prompt_tokens=10, completion_tokens=20, total_tokens=30):
        mock_message = MagicMock()
        mock_message.content = content
        mock_message.tool_calls = tool_calls

        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = finish_reason

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = prompt_tokens
        mock_usage.completion_tokens = completion_tokens
        mock_usage.total_tokens = total_tokens

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        return mock_response

    def test_chat_completions_success(self, minimax_llm):
        minimax_llm._mock_client.chat.completions.create.return_value = (
            self._make_mock_response("This is a video summary.")
        )

        result = minimax_llm.chat_completions(
            [{"role": "user", "content": "Summarize the video"}]
        )

        assert result.status == LLMResponseStatus.SUCCESS
        assert result.content == "This is a video summary."
        assert result.tool_calls == []
        assert result.send_tokens == 10
        assert result.recv_tokens == 20
        assert result.total_tokens == 30

    def test_chat_completions_with_think_tags(self, minimax_llm):
        minimax_llm._mock_client.chat.completions.create.return_value = (
            self._make_mock_response("<think>Let me think...</think>\nThe answer is 42.")
        )

        result = minimax_llm.chat_completions(
            [{"role": "user", "content": "What is the meaning of life?"}]
        )

        assert result.content == "The answer is 42."

    def test_chat_completions_with_tool_calls(self, minimax_llm):
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_abc123"
        mock_tool_call.function.name = "search_video"
        mock_tool_call.function.arguments = json.dumps({"query": "cat"})
        mock_tool_call.type = "function"

        minimax_llm._mock_client.chat.completions.create.return_value = (
            self._make_mock_response(
                content="",
                tool_calls=[mock_tool_call],
                finish_reason="tool_calls",
                prompt_tokens=15, completion_tokens=25, total_tokens=40,
            )
        )

        tools = [
            {
                "name": "search_video",
                "description": "Search for videos",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            }
        ]

        result = minimax_llm.chat_completions(
            [{"role": "user", "content": "Find cat videos"}],
            tools=tools,
        )

        assert result.status == LLMResponseStatus.SUCCESS
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["tool"]["name"] == "search_video"
        assert result.tool_calls[0]["tool"]["arguments"] == {"query": "cat"}

    def test_chat_completions_with_response_format(self, minimax_llm):
        minimax_llm._mock_client.chat.completions.create.return_value = (
            self._make_mock_response('{"clips": [{"start": 0, "end": 10}]}')
        )

        result = minimax_llm.chat_completions(
            [{"role": "user", "content": "Find the highlights"}],
            response_format={"type": "json_object"},
        )

        assert result.status == LLMResponseStatus.SUCCESS
        call_kwargs = minimax_llm._mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}

    def test_chat_completions_error(self, minimax_llm):
        minimax_llm._mock_client.chat.completions.create.side_effect = Exception(
            "API rate limit exceeded"
        )

        result = minimax_llm.chat_completions(
            [{"role": "user", "content": "Hello"}]
        )

        assert result.status == LLMResponseStatus.ERROR
        assert "API rate limit exceeded" in result.content

    def test_chat_completions_params(self, minimax_llm):
        minimax_llm._mock_client.chat.completions.create.return_value = (
            self._make_mock_response()
        )

        minimax_llm.chat_completions(
            [{"role": "user", "content": "Hi"}]
        )

        call_kwargs = minimax_llm._mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "MiniMax-M2.7"
        assert call_kwargs["temperature"] == 0.9
        assert call_kwargs["max_tokens"] == 4096


class TestGetDefaultLLM:
    """Tests for get_default_llm with MiniMax support."""

    @patch.dict(os.environ, {"MINIMAX_API_KEY": "test-key"}, clear=True)
    def test_minimax_auto_detect(self):
        with patch("director.llm.minimax.MiniMax.__init__", return_value=None):
            from director.llm import get_default_llm
            llm = get_default_llm()
            assert isinstance(llm, MiniMax)

    @patch.dict(os.environ, {"DEFAULT_LLM": "minimax", "MINIMAX_API_KEY": "key"}, clear=True)
    def test_minimax_default_llm_env(self):
        with patch("director.llm.minimax.MiniMax.__init__", return_value=None):
            from director.llm import get_default_llm
            llm = get_default_llm()
            assert isinstance(llm, MiniMax)

    @patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "oai-key", "MINIMAX_API_KEY": "mm-key"},
        clear=True,
    )
    def test_openai_takes_priority_over_minimax(self):
        from director.llm import get_default_llm
        from director.llm.openai import OpenAI

        with patch("director.llm.openai.OpenAI.__init__", return_value=None):
            llm = get_default_llm()
            assert isinstance(llm, OpenAI)


class TestLLMTypeEnum:
    """Tests for LLMType enum with MiniMax."""

    def test_minimax_in_llm_type(self):
        assert LLMType.MINIMAX == "minimax"

    def test_all_providers_present(self):
        providers = [e.value for e in LLMType]
        assert "openai" in providers
        assert "anthropic" in providers
        assert "googleai" in providers
        assert "minimax" in providers
        assert "videodb_proxy" in providers
