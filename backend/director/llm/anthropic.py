from enum import Enum

from pydantic import Field, field_validator, FieldValidationInfo
from pydantic_settings import SettingsConfigDict

from director.core.session import RoleTypes
from director.llm.base import BaseLLM, BaseLLMConfig, LLMResponse, LLMResponseStatus
from director.constants import (
    LLMType,
    EnvPrefix,
)


class AnthropicChatModel(str, Enum):
    """Enum for Anthropic Chat models"""

    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20240620"
    CLAUDE_3_5_SONNET_LATEST = "claude-3-5-sonnet-20241022"


class AnthropicAIConfig(BaseLLMConfig):
    """AnthropicAI Config"""

    model_config = SettingsConfigDict(
        env_prefix=EnvPrefix.ANTHROPIC_,
        extra="ignore",
    )

    llm_type: str = LLMType.ANTHROPIC
    api_key: str = ""
    api_base: str = ""
    chat_model: str = Field(default=AnthropicChatModel.CLAUDE_3_5_SONNET)

    @field_validator("api_key")
    @classmethod
    def validate_non_empty(cls, v, info: FieldValidationInfo):
        if not v:
            raise ValueError(
                f"{info.field_name} must not be empty. please set {EnvPrefix.OPENAI_.value}{info.field_name.upper()} environment variable."
            )
        return v


class AnthropicAI(BaseLLM):
    def __init__(self, config: AnthropicAIConfig = None):
        """
        :param config: AnthropicAI Config
        """
        if config is None:
            config = AnthropicAIConfig()
        super().__init__(config=config)
        try:
            import anthropic
        except ImportError:
            raise ImportError("Please install Anthropic python library.")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def _format_messages(self, messages: list):
        system = ""
        formatted_messages = []
        if messages[0]["role"] == RoleTypes.system:
            system = messages[0]["content"]
            messages = messages[1:]

        for message in messages:
            if message["role"] == RoleTypes.assistant and message.get("tool_calls"):
                tool = message["tool_calls"][0]["tool"]
                formatted_messages.append(
                    {
                        "role": message["role"],
                        "content": [
                            {
                                "type": "text",
                                "text": message["content"],
                            },
                            {
                                "id": message["tool_calls"][0]["id"],
                                "type": message["tool_calls"][0]["type"],
                                "name": tool["name"],
                                "input": tool["arguments"],
                            },
                        ],
                    }
                )

            elif message["role"] == RoleTypes.tool:
                formatted_messages.append(
                    {
                        "role": RoleTypes.user,
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": message["tool_call_id"],
                                "content": message["content"],
                            }
                        ],
                    }
                )
            else:
                formatted_messages.append(message)

        return system, formatted_messages

    def _format_tools(self, tools: list):
        """Format the tools to the format that Anthropic expects.

        **Example**::

            [
                {
                    "name": "get_weather",
                    "description": "Get the current weather in a given location",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            }
                        },
                        "required": ["location"],
                    },
                }
            ]
        """
        formatted_tools = []
        for tool in tools:
            formatted_tools.append(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["parameters"],
                }
            )
        return formatted_tools

    def chat_completions(
        self, messages: list, tools: list = [], stop=None, response_format=None
    ):
        """Get completions for chat.

        tools docs: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
        """
        system, messages = self._format_messages(messages)
        params = {
            "model": self.chat_model,
            "messages": messages,
            "system": system,
            "max_tokens": self.max_tokens,
        }
        if tools:
            params["tools"] = self._format_tools(tools)

        try:
            response = self.client.messages.create(**params)
        except Exception as e:
            logger.exception("Anthropic LLM call failed")
            return LLMResponse(content=f"Error: {e}")

        return LLMResponse(
            content=response.content[0].text,
            tool_calls=[
                {
                    "id": response.content[1].id,
                    "tool": {
                        "name": response.content[1].name,
                        "arguments": response.content[1].input,
                    },
                    "type": response.content[1].type,
                }
            ]
            if next(
                (block for block in response.content if block.type == "tool_use"), None
            )
            is not None
            else [],
            finish_reason=response.stop_reason,
            send_tokens=response.usage.input_tokens,
            recv_tokens=response.usage.output_tokens,
            total_tokens=(response.usage.input_tokens + response.usage.output_tokens),
            status=LLMResponseStatus.SUCCESS,
        )
