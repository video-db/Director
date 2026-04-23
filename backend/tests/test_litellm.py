"""Tests for the LiteLLM provider."""

import json
import types as builtin_types
from unittest import mock

import pytest

from director.llm.base import LLMResponse, LLMResponseStatus


# ---------------------------------------------------------------------------
# Fake response helpers (matches OpenAI response shape)
# ---------------------------------------------------------------------------


class _FnCall:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.function = _FnCall(name, json.dumps(arguments))
        self.type = "function"


class _Msg:
    def __init__(self, content="hello", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _Usage:
    def __init__(self, prompt=10, completion=5, total=15):
        self.prompt_tokens = prompt
        self.completion_tokens = completion
        self.total_tokens = total


class _Choice:
    def __init__(self, content="hello", finish_reason="stop", tool_calls=None):
        self.message = _Msg(content=content, tool_calls=tool_calls)
        self.finish_reason = finish_reason


class _Response:
    def __init__(self, content="hello", finish_reason="stop", tool_calls=None):
        self.choices = [_Choice(content=content, finish_reason=finish_reason, tool_calls=tool_calls)]
        self.usage = _Usage()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _install_fake_litellm(response_content="hello"):
    import sys

    fake = builtin_types.ModuleType("litellm")
    fake.completion = mock.MagicMock(return_value=_Response(response_content))
    sys.modules["litellm"] = fake
    return fake


def _uninstall_fake_litellm():
    import sys

    sys.modules.pop("litellm", None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLiteLLMChatCompletions:
    def setup_method(self):
        self.fake = _install_fake_litellm("test response")

    def teardown_method(self):
        _uninstall_fake_litellm()

    def _make_llm(self, **overrides):
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        defaults = {
            "chat_model": "openai/gpt-4o",
            "api_key": "test-key",
        }
        defaults.update(overrides)
        config = LiteLLMConfig(**defaults)
        return LiteLLM(config=config)

    def test_basic_completion(self):
        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "hi"}],
        )
        assert isinstance(result, LLMResponse)
        assert result.content == "test response"
        assert result.status == LLMResponseStatus.SUCCESS

    def test_passes_drop_params(self):
        llm = self._make_llm()
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["drop_params"] is True

    def test_passes_model(self):
        llm = self._make_llm(chat_model="anthropic/claude-3-haiku")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["model"] == "anthropic/claude-3-haiku"

    def test_forwards_api_key(self):
        llm = self._make_llm(api_key="sk-test")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["api_key"] == "sk-test"

    def test_omits_api_key_when_empty(self):
        llm = self._make_llm(api_key="")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert "api_key" not in call_kwargs

    def test_forwards_api_base(self):
        llm = self._make_llm(api_base="http://localhost:4000")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["api_base"] == "http://localhost:4000"

    def test_omits_api_base_when_empty(self):
        llm = self._make_llm(api_base="")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert "api_base" not in call_kwargs

    def test_passes_temperature(self):
        llm = self._make_llm()
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["temperature"] == llm.temperature

    def test_tool_calls_returned(self):
        tc = _ToolCall("tc1", "search", {"query": "test"})
        self.fake.completion.return_value = _Response(
            content="", tool_calls=[tc]
        )
        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "search"}],
            tools=[{"name": "search", "description": "Search", "parameters": {}}],
        )
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["tool"]["name"] == "search"

    def test_token_usage_populated(self):
        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "hi"}],
        )
        assert result.send_tokens == 10
        assert result.recv_tokens == 5
        assert result.total_tokens == 15

    def test_error_returns_llm_response(self):
        self.fake.completion.side_effect = Exception("connection failed")
        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "hi"}],
        )
        assert "Error" in result.content
        assert result.status == LLMResponseStatus.ERROR


class TestLiteLLMRegistration:
    def setup_method(self):
        _install_fake_litellm()

    def teardown_method(self):
        _uninstall_fake_litellm()

    def test_llm_type_exists(self):
        from director.constants import LLMType

        assert hasattr(LLMType, "LITELLM")
        assert LLMType.LITELLM == "litellm"

    def test_env_prefix_exists(self):
        from director.constants import EnvPrefix

        assert hasattr(EnvPrefix, "LITELLM_")
        assert EnvPrefix.LITELLM_ == "LITELLM_"

    def test_get_default_llm_returns_litellm(self):
        from director.llm.litellm import LiteLLM

        with mock.patch.dict("os.environ", {"DEFAULT_LLM": "litellm"}, clear=False):
            from director.llm import get_default_llm

            llm = get_default_llm()
            assert isinstance(llm, LiteLLM)


class TestLiteLLMMessageFormatting:
    def setup_method(self):
        self.fake = _install_fake_litellm()

    def teardown_method(self):
        _uninstall_fake_litellm()

    def test_tool_call_messages_formatted(self):
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        config = LiteLLMConfig(chat_model="openai/gpt-4o", api_key="k")
        llm = LiteLLM(config=config)
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "tc1",
                        "tool": {"name": "search", "arguments": {"q": "test"}},
                        "type": "function",
                    }
                ],
            }
        ]
        formatted = llm._format_messages(messages)
        assert formatted[0]["tool_calls"][0]["function"]["name"] == "search"
        assert "arguments" in formatted[0]["tool_calls"][0]["function"]
