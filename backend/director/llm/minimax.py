import json
import re
from enum import Enum

from pydantic import Field, field_validator, FieldValidationInfo
from pydantic_settings import SettingsConfigDict


from director.llm.base import BaseLLM, BaseLLMConfig, LLMResponse, LLMResponseStatus
from director.constants import (
    LLMType,
    EnvPrefix,
)


class MiniMaxChatModel(str, Enum):
    """Enum for MiniMax Chat models"""

    MINIMAX_M2_7 = "MiniMax-M2.7"
    MINIMAX_M2_5 = "MiniMax-M2.5"
    MINIMAX_M2_5_HIGHSPEED = "MiniMax-M2.5-highspeed"


class MiniMaxConfig(BaseLLMConfig):
    """MiniMax Config"""

    model_config = SettingsConfigDict(
        env_prefix=EnvPrefix.MINIMAX_,
        extra="ignore",
    )

    llm_type: str = LLMType.MINIMAX
    api_key: str = ""
    api_base: str = "https://api.minimax.io/v1"
    chat_model: str = Field(default=MiniMaxChatModel.MINIMAX_M2_7)
    max_tokens: int = 4096
    temperature: float = 0.9

    @field_validator("api_key")
    @classmethod
    def validate_non_empty(cls, v, info: FieldValidationInfo):
        if not v:
            raise ValueError(
                f"{info.field_name} must not be empty. Please set {EnvPrefix.MINIMAX_.value}{info.field_name.upper()} environment variable."
            )
        return v

    @field_validator("temperature")
    @classmethod
    def clamp_temperature(cls, v):
        """Clamp temperature to MiniMax's accepted range [0, 1]."""
        return max(0.0, min(1.0, v))


class MiniMax(BaseLLM):
    def __init__(self, config: MiniMaxConfig = None):
        """
        :param config: MiniMax Config
        """
        if config is None:
            config = MiniMaxConfig()
        super().__init__(config=config)
        try:
            import openai
        except ImportError:
            raise ImportError("Please install OpenAI python library.")

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base
        )

    def _format_messages(self, messages: list):
        """Format the messages to the format that MiniMax expects via OpenAI-compatible API."""
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
        """Format the tools to the format that MiniMax expects.

        **Example**::

            [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get the weather in a given location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The city and state"
                                }
                            },
                            "required": ["location"]
                        }
                    }
                }
            ]
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {}),
                },
            }
            for tool in tools
            if tool.get("name")
        ]

    @staticmethod
    def _strip_think_tags(content: str) -> str:
        """Strip <think>...</think> tags from MiniMax M2.7 reasoning output."""
        if not content:
            return content
        return re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL).strip()

    def chat_completions(
        self, messages: list, tools: list = [], stop=None, response_format=None
    ):
        """Get chat completions using MiniMax.

        MiniMax provides an OpenAI-compatible API at https://api.minimax.io/v1.
        docs: https://platform.minimaxi.com/document/ChatCompletion%20v2
        """
        params = {
            "model": self.chat_model,
            "messages": self._format_messages(messages),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "timeout": self.timeout,
        }

        if tools:
            params["tools"] = self._format_tools(tools)
            params["tool_choice"] = "auto"

        if response_format:
            params["response_format"] = response_format

        try:
            response = self.client.chat.completions.create(**params)
        except Exception as e:
            print(f"Error: {e}")
            return LLMResponse(content=f"Error: {e}")

        content = response.choices[0].message.content or ""
        content = self._strip_think_tags(content)

        return LLMResponse(
            content=content,
            tool_calls=[
                {
                    "id": tool_call.id,
                    "tool": {
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments),
                    },
                    "type": tool_call.type,
                }
                for tool_call in response.choices[0].message.tool_calls
            ]
            if response.choices[0].message.tool_calls
            else [],
            finish_reason=response.choices[0].finish_reason,
            send_tokens=response.usage.prompt_tokens,
            recv_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            status=LLMResponseStatus.SUCCESS,
        )
