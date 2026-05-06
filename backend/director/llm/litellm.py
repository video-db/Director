import json
import logging

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from director.llm.base import BaseLLM, BaseLLMConfig, LLMResponse, LLMResponseStatus
from director.constants import LLMType, EnvPrefix

logger = logging.getLogger(__name__)


class LiteLLMConfig(BaseLLMConfig):
    """LiteLLM Config.

    Reads from LITELLM_ prefixed environment variables.
    Set LITELLM_CHAT_MODEL to any LiteLLM-supported model string
    (e.g. anthropic/claude-3-haiku, openai/gpt-4o, bedrock/anthropic.claude-v2).

    API keys are read from standard provider environment variables
    automatically (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.).
    Optionally set LITELLM_API_KEY to override.
    """

    model_config = SettingsConfigDict(
        env_prefix=EnvPrefix.LITELLM_,
        extra="ignore",
    )

    llm_type: str = LLMType.LITELLM
    api_key: str = ""
    api_base: str = ""
    chat_model: str = Field(default="openai/gpt-4o")
    max_tokens: int = 4096


class LiteLLM(BaseLLM):
    def __init__(self, config: LiteLLMConfig = None):
        """
        :param config: LiteLLM Config
        """
        if config is None:
            config = LiteLLMConfig()
        super().__init__(config=config)

    def _format_messages(self, messages: list):
        """Format messages to OpenAI chat format.

        LiteLLM accepts OpenAI-format messages and translates
        them for each provider internally.
        """
        formatted_messages = []
        for message in messages:
            if message["role"] == "assistant" and message.get("tool_calls"):
                formatted_messages.append(
                    {
                        "role": message["role"],
                        "content": message["content"],
                        "tool_calls": [
                            {
                                "id": tool_call["id"],
                                "function": {
                                    "name": tool_call["tool"]["name"],
                                    "arguments": json.dumps(
                                        tool_call["tool"]["arguments"]
                                    ),
                                },
                                "type": tool_call["type"],
                            }
                            for tool_call in message["tool_calls"]
                        ],
                    }
                )
            else:
                formatted_messages.append(message)
        return formatted_messages

    def _format_tools(self, tools: list):
        """Format tools to OpenAI function-calling format."""
        formatted_tools = []
        for tool in tools:
            formatted_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"],
                    },
                }
            )
        return formatted_tools

    def chat_completions(
        self, messages: list, tools: list | None = None, stop=None, response_format=None
    ):
        """Get chat completions via LiteLLM.

        Routes to 100+ providers (OpenAI, Anthropic, Azure, Bedrock, etc.)
        based on the model string in LITELLM_CHAT_MODEL.
        """
        import litellm

        params = {
            "model": self.chat_model,
            "messages": self._format_messages(messages),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "stop": stop,
            "timeout": self.timeout,
            "drop_params": True,
        }

        if self.api_key:
            params["api_key"] = self.api_key
        if self.api_base:
            params["api_base"] = self.api_base
        if tools:
            params["tools"] = self._format_tools(tools)
            params["tool_choice"] = "auto"
        if response_format:
            params["response_format"] = response_format

        try:
            response = litellm.completion(**params)

            usage = getattr(response, "usage", None)
            tool_calls = []
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    args_raw = tool_call.function.arguments
                    try:
                        arguments = json.loads(args_raw) if args_raw else {}
                    except (json.JSONDecodeError, TypeError):
                        arguments = {}
                    tool_calls.append(
                        {
                            "id": tool_call.id,
                            "tool": {
                                "name": tool_call.function.name,
                                "arguments": arguments,
                            },
                            "type": tool_call.type,
                        }
                    )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                tool_calls=tool_calls,
                finish_reason=response.choices[0].finish_reason,
                send_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                recv_tokens=getattr(usage, "completion_tokens", 0) or 0,
                total_tokens=getattr(usage, "total_tokens", 0) or 0,
                status=LLMResponseStatus.SUCCESS,
            )
        except Exception as e:
            logger.error("LiteLLM completion failed: %s", e)
            return LLMResponse(content=f"Error: {e}")
