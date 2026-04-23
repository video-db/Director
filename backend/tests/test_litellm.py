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
    def __init__(self, content="hello", finish_reason="stop", tool_calls=None,
                 prompt_tokens=10, completion_tokens=5, total_tokens=15):
        self.choices = [_Choice(content=content, finish_reason=finish_reason, tool_calls=tool_calls)]
        self.usage = _Usage(prompt=prompt_tokens, completion=completion_tokens, total=total_tokens)


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
# Chat completions
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

    def test_basic_completion_returns_content(self):
        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "hi"}],
        )
        assert isinstance(result, LLMResponse)
        assert result.content == "test response"
        assert result.status == LLMResponseStatus.SUCCESS

    def test_drop_params_always_true(self):
        llm = self._make_llm()
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["drop_params"] is True

    def test_model_forwarded(self):
        llm = self._make_llm(chat_model="anthropic/claude-3-haiku")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["model"] == "anthropic/claude-3-haiku"

    def test_api_key_forwarded_when_set(self):
        llm = self._make_llm(api_key="sk-test")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["api_key"] == "sk-test"

    def test_api_key_omitted_when_empty(self):
        llm = self._make_llm(api_key="")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert "api_key" not in call_kwargs

    def test_api_base_forwarded_when_set(self):
        llm = self._make_llm(api_base="http://localhost:4000")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["api_base"] == "http://localhost:4000"

    def test_api_base_omitted_when_empty(self):
        llm = self._make_llm(api_base="")
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert "api_base" not in call_kwargs

    def test_temperature_forwarded(self):
        llm = self._make_llm(temperature=0.7)
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["temperature"] == 0.7

    def test_max_tokens_forwarded(self):
        llm = self._make_llm(max_tokens=2048)
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["max_tokens"] == 2048

    def test_timeout_forwarded(self):
        llm = self._make_llm(timeout=60)
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["timeout"] == 60

    def test_stop_forwarded(self):
        llm = self._make_llm()
        llm.chat_completions(
            messages=[{"role": "user", "content": "hi"}],
            stop=["STOP"],
        )
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["stop"] == ["STOP"]

    def test_response_format_forwarded(self):
        llm = self._make_llm()
        rf = {"type": "json_object"}
        llm.chat_completions(
            messages=[{"role": "user", "content": "hi"}],
            response_format=rf,
        )
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["response_format"] == rf

    def test_top_p_forwarded(self):
        """top_p is forwarded; drop_params=True handles provider conflicts."""
        llm = self._make_llm(top_p=0.95)
        llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["top_p"] == 0.95


# ---------------------------------------------------------------------------
# Tool calling
# ---------------------------------------------------------------------------


class TestLiteLLMToolCalling:
    def setup_method(self):
        self.fake = _install_fake_litellm()

    def teardown_method(self):
        _uninstall_fake_litellm()

    def _make_llm(self):
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        config = LiteLLMConfig(chat_model="openai/gpt-4o", api_key="k")
        return LiteLLM(config=config)

    def test_tool_calls_parsed_correctly(self):
        tc = _ToolCall("tc1", "search", {"query": "test"})
        self.fake.completion.return_value = _Response(content="", tool_calls=[tc])

        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "search"}],
            tools=[{"name": "search", "description": "Search", "parameters": {}}],
        )
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["id"] == "tc1"
        assert result.tool_calls[0]["tool"]["name"] == "search"
        assert result.tool_calls[0]["tool"]["arguments"] == {"query": "test"}
        assert result.tool_calls[0]["type"] == "function"

    def test_multiple_tool_calls(self):
        tc1 = _ToolCall("tc1", "search", {"q": "a"})
        tc2 = _ToolCall("tc2", "fetch", {"url": "http://x"})
        self.fake.completion.return_value = _Response(content="", tool_calls=[tc1, tc2])

        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "do stuff"}],
            tools=[
                {"name": "search", "description": "S", "parameters": {}},
                {"name": "fetch", "description": "F", "parameters": {}},
            ],
        )
        assert len(result.tool_calls) == 2
        assert result.tool_calls[0]["tool"]["name"] == "search"
        assert result.tool_calls[1]["tool"]["name"] == "fetch"

    def test_no_tool_calls_returns_empty_list(self):
        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "hi"}],
        )
        assert result.tool_calls == []

    def test_tools_formatted_with_tool_choice_auto(self):
        llm = self._make_llm()
        llm.chat_completions(
            messages=[{"role": "user", "content": "hi"}],
            tools=[{"name": "t", "description": "d", "parameters": {"type": "object"}}],
        )
        call_kwargs = self.fake.completion.call_args[1]
        assert call_kwargs["tool_choice"] == "auto"
        assert call_kwargs["tools"][0]["type"] == "function"
        assert call_kwargs["tools"][0]["function"]["name"] == "t"

    def test_no_tools_omits_tool_choice(self):
        llm = self._make_llm()
        llm.chat_completions(
            messages=[{"role": "user", "content": "hi"}],
        )
        call_kwargs = self.fake.completion.call_args[1]
        assert "tools" not in call_kwargs
        assert "tool_choice" not in call_kwargs

    def test_empty_tool_arguments_handled(self):
        """Empty string arguments should not crash json.loads."""
        tc = _ToolCall("tc1", "ping", {})
        tc.function.arguments = ""
        self.fake.completion.return_value = _Response(content="", tool_calls=[tc])

        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "ping"}],
            tools=[{"name": "ping", "description": "Ping", "parameters": {}}],
        )
        assert result.tool_calls[0]["tool"]["arguments"] == {}

    def test_none_tool_arguments_handled(self):
        """None arguments should not crash."""
        tc = _ToolCall("tc1", "ping", {})
        tc.function.arguments = None
        self.fake.completion.return_value = _Response(content="", tool_calls=[tc])

        llm = self._make_llm()
        result = llm.chat_completions(
            messages=[{"role": "user", "content": "ping"}],
            tools=[{"name": "ping", "description": "Ping", "parameters": {}}],
        )
        assert result.tool_calls[0]["tool"]["arguments"] == {}


# ---------------------------------------------------------------------------
# Token usage and finish reason
# ---------------------------------------------------------------------------


class TestLiteLLMResponseFields:
    def setup_method(self):
        self.fake = _install_fake_litellm()

    def teardown_method(self):
        _uninstall_fake_litellm()

    def test_none_usage_returns_zero_tokens(self):
        """Some providers return None for usage. Should not crash."""
        resp = _Response(content="ok")
        resp.usage = None
        self.fake.completion.return_value = resp

        from director.llm.litellm import LiteLLMConfig, LiteLLM

        llm = LiteLLM(config=LiteLLMConfig(chat_model="x", api_key="k"))
        result = llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        assert result.send_tokens == 0
        assert result.recv_tokens == 0
        assert result.total_tokens == 0
        assert result.status == LLMResponseStatus.SUCCESS

    def test_token_counts(self):
        self.fake.completion.return_value = _Response(
            content="ok", prompt_tokens=100, completion_tokens=50, total_tokens=150
        )
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        llm = LiteLLM(config=LiteLLMConfig(chat_model="x", api_key="k"))
        result = llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        assert result.send_tokens == 100
        assert result.recv_tokens == 50
        assert result.total_tokens == 150

    def test_finish_reason(self):
        self.fake.completion.return_value = _Response(
            content="ok", finish_reason="length"
        )
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        llm = LiteLLM(config=LiteLLMConfig(chat_model="x", api_key="k"))
        result = llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        assert result.finish_reason == "length"

    def test_none_content_becomes_empty_string(self):
        self.fake.completion.return_value = _Response(content=None)
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        llm = LiteLLM(config=LiteLLMConfig(chat_model="x", api_key="k"))
        result = llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        assert result.content == ""


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestLiteLLMErrorHandling:
    def setup_method(self):
        self.fake = _install_fake_litellm()

    def teardown_method(self):
        _uninstall_fake_litellm()

    def test_exception_returns_error_response(self):
        self.fake.completion.side_effect = Exception("connection failed")
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        llm = LiteLLM(config=LiteLLMConfig(chat_model="x", api_key="k"))
        result = llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        assert "Error" in result.content
        assert "connection failed" in result.content
        assert result.status == LLMResponseStatus.ERROR

    def test_error_response_has_zero_tokens(self):
        self.fake.completion.side_effect = Exception("fail")
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        llm = LiteLLM(config=LiteLLMConfig(chat_model="x", api_key="k"))
        result = llm.chat_completions(messages=[{"role": "user", "content": "hi"}])
        assert result.send_tokens == 0
        assert result.recv_tokens == 0
        assert result.total_tokens == 0


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


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

    def test_litellm_not_default_when_openai_key_set(self):
        """LiteLLM should only be selected when DEFAULT_LLM=litellm, not by key presence."""
        from director.llm.litellm import LiteLLM

        with mock.patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test", "DEFAULT_LLM": ""},
            clear=False,
        ):
            from director.llm import get_default_llm

            llm = get_default_llm()
            assert not isinstance(llm, LiteLLM)


# ---------------------------------------------------------------------------
# Message formatting
# ---------------------------------------------------------------------------


class TestLiteLLMMessageFormatting:
    def setup_method(self):
        self.fake = _install_fake_litellm()

    def teardown_method(self):
        _uninstall_fake_litellm()

    def _make_llm(self):
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        return LiteLLM(config=LiteLLMConfig(chat_model="x", api_key="k"))

    def test_regular_messages_pass_through(self):
        llm = self._make_llm()
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        formatted = llm._format_messages(messages)
        assert formatted == messages

    def test_tool_call_messages_reformatted(self):
        llm = self._make_llm()
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
        tc = formatted[0]["tool_calls"][0]
        assert tc["function"]["name"] == "search"
        assert json.loads(tc["function"]["arguments"]) == {"q": "test"}
        assert tc["id"] == "tc1"
        assert tc["type"] == "function"

    def test_tool_result_message_passes_through(self):
        llm = self._make_llm()
        messages = [
            {"role": "tool", "tool_call_id": "tc1", "content": '{"result": "ok"}'}
        ]
        formatted = llm._format_messages(messages)
        assert formatted[0] == messages[0]


# ---------------------------------------------------------------------------
# Tool formatting
# ---------------------------------------------------------------------------


class TestLiteLLMToolFormatting:
    def setup_method(self):
        _install_fake_litellm()

    def teardown_method(self):
        _uninstall_fake_litellm()

    def test_tools_formatted_to_openai_spec(self):
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        llm = LiteLLM(config=LiteLLMConfig(chat_model="x", api_key="k"))
        tools = [
            {
                "name": "get_weather",
                "description": "Get weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            }
        ]
        formatted = llm._format_tools(tools)
        assert len(formatted) == 1
        assert formatted[0]["type"] == "function"
        assert formatted[0]["function"]["name"] == "get_weather"
        assert formatted[0]["function"]["description"] == "Get weather for a city"
        assert formatted[0]["function"]["parameters"]["properties"]["city"]["type"] == "string"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestLiteLLMConfig:
    def setup_method(self):
        _install_fake_litellm()

    def teardown_method(self):
        _uninstall_fake_litellm()

    def test_default_config_values(self):
        from director.llm.litellm import LiteLLMConfig

        config = LiteLLMConfig()
        assert config.llm_type == "litellm"
        assert config.chat_model == "openai/gpt-4o"
        assert config.max_tokens == 4096
        assert config.api_key == ""
        assert config.api_base == ""

    def test_config_reads_from_env(self):
        from director.llm.litellm import LiteLLMConfig

        with mock.patch.dict(
            "os.environ",
            {
                "LITELLM_CHAT_MODEL": "anthropic/claude-3-haiku",
                "LITELLM_API_KEY": "sk-env-key",
                "LITELLM_MAX_TOKENS": "8192",
            },
            clear=False,
        ):
            config = LiteLLMConfig()
            assert config.chat_model == "anthropic/claude-3-haiku"
            assert config.api_key == "sk-env-key"
            assert config.max_tokens == 8192

    def test_config_no_api_key_required(self):
        """Unlike OpenAI/GoogleAI configs, LiteLLM should not require api_key."""
        from director.llm.litellm import LiteLLMConfig, LiteLLM

        config = LiteLLMConfig(chat_model="openai/gpt-4o")
        llm = LiteLLM(config=config)
        assert llm.api_key == ""
