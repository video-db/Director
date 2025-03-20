import json
from enum import Enum

from pydantic import Field, field_validator, FieldValidationInfo
from pydantic_settings import SettingsConfigDict


from director.llm.base import BaseLLM, BaseLLMConfig, LLMResponse, LLMResponseStatus
from director.constants import (
    LLMType,
    EnvPrefix,
)


class GoogleChatModel(str, Enum):
    """Enum for Google Gemini Chat models"""

    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_002 = "gemini-1.5-flash-002"
    GEMINI_1_5_PRO_002 = "gemini-1.5-pro-002"


class GoogleAIConfig(BaseLLMConfig):
    """GoogleAI Config"""

    model_config = SettingsConfigDict(
        env_prefix=EnvPrefix.GOOGLEAI_,
        extra="ignore",
    )

    llm_type: str = LLMType.GOOGLEAI
    api_key: str = ""
    api_base: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    chat_model: str = Field(default=GoogleChatModel.GEMINI_1_5_PRO_002)
    max_tokens: int = 4096

    @field_validator("api_key")
    @classmethod
    def validate_non_empty(cls, v, info: FieldValidationInfo):
        if not v:
            raise ValueError(
                f"{info.field_name} must not be empty. Please set {EnvPrefix.GOOGLEAI_.value}{info.field_name.upper()} environment variable."
            )
        return v


class GoogleAI(BaseLLM):
    def __init__(self, config: GoogleAIConfig = None):
        """
        :param config: GoogleAI Config
        """
        if config is None:
            config = GoogleAIConfig()
        super().__init__(config=config)
        try:
            import openai
        except ImportError:
            raise ImportError("Please install OpenAI python library.")

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base
        )

    def _format_messages(self, messages: list):
        """Format the messages to the format that Google Gemini expects."""
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
        """Format the tools to the format that Gemini expects.

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
                                    "description": "The city and state, e.g. Chicago, IL"
                                },
                                "unit": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"]
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

    def chat_completions(
        self, messages: list, tools: list = [], stop=None, response_format=None
    ):
        """Get chat completions using Gemini.

        docs: https://ai.google.dev/gemini-api/docs/openai
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

        return LLMResponse(
            content=response.choices[0].message.content or "",
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
