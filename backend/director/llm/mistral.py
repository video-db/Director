from enum import Enum

from pydantic import Field, field_validator, FieldValidationInfo
from pydantic_settings import SettingsConfigDict

from director.core.session import RoleTypes
from director.llm.base import BaseLLM, BaseLLMConfig, LLMResponse, LLMResponseStatus
from director.constants import (
    LLMType,
    EnvPrefix,
)
import json


class MistralChatModel(str, Enum):
    """Enum for Mistral Chat models"""

    MINISTRAL_8B = "ministral-8b-latest"
    MINISTRAL_3B = "ministral-3b-latest"
    # PIXTRAL_12B = "pixtral-12b-2409"
  


class MistralAIConfig(BaseLLMConfig):
    """MistralAI Config"""

    model_config = SettingsConfigDict(
        env_prefix=EnvPrefix.MISTRAL_,
        extra="ignore",
    )

    llm_type: str = LLMType.MISTRAL
    api_key: str = ""
    api_base: str = ""
    chat_model: str = Field(default=MistralChatModel.MINISTRAL_8B)

    @field_validator("api_key")
    @classmethod
    def validate_non_empty(cls, v, info: FieldValidationInfo):
        if not v:
            raise ValueError(
                f"{info.field_name} must not be empty. please set {EnvPrefix.MISTRAL_.value}{info.field_name.upper()} environment variable."
            )
        return v


class MistralAI(BaseLLM):
    def __init__(self, config: MistralAIConfig = None):
        """
        :param config: MistralAI Config
        """
        if config is None:
            config = MistralAIConfig()
        super().__init__(config=config)
        try:
            import mistralai
        except ImportError:
            raise ImportError("Please install mistralai python library.")

        self.client = mistralai.Mistral(api_key=self.api_key)
       

    def _format_messages(self, messages: list):
        formatted_messages = []
        # if messages[0]["role"] == RoleTypes.system:
        #     system = messages[0]["content"]
        #     messages = messages[1:]

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

        return formatted_messages

    def _format_tools(self, tools: list):
        """Format the tools to the format that Mistral expects.

        **Example**::

            [
                {
                    "type": "function",
                    "function": {
                        "name": "retrieve_payment_status",
                        "description": "Get payment status of a transaction",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "transaction_id": {
                                    "type": "string",
                                    "description": "The transaction id.",
                                }
                            },
                            "required": ["transaction_id"],
                        },
                    },
                }
            ]
        """
        formatted_tools = []
        for tool in tools:
            formatted_tools.append(
                {
                    "type": "function",
                    "function": 
                        {
                            "name": tool["name"],
                            "description": tool["description"],
                            "parameters": tool["parameters"],
                        }
                
                }
            )
        return formatted_tools
    
        # formatted_tools = []
        # for tool in tools:
        #     formatted_tools.append(
        #         {
        #             "type": tool["type"],
        #             "name": tool["function"]["name"],
        #             "description": tool["function"]["description"],
        #             "parameters": tool["function"]["parameters"],
        #         }
        #     )
        # return formatted_tools

    def chat_completions(
        self, messages: list, tools: list = [], stop=None, response_format=None
    ):
        """Get completions for chat.

        tools docs: https://docs.mistral.ai/capabilities/function_calling/
        """
        messages = self._format_messages(messages)
        params = {
            "model": self.chat_model,
            "messages": messages,
            "max_tokens": self.max_tokens,
        }
        if tools:
            params["tools"] = self._format_tools(tools)

        try:
            response = self.client.chat.complete(**params)
        except Exception as e:
            raise e
            return LLMResponse(content=f"Error: {e}")

        return LLMResponse(
            content=response.choices[0].message.content,
            tool_calls=[
                {
                    "id": response.choices[0].message.tool_calls[0].id,
                    "tool": {
                        "name": response.choices[0].message.tool_calls[0].function.name,
                        "arguments": json.loads(response.choices[0].message.tool_calls[0].function.arguments),
                    },
                    "type": response.choices[0].message.tool_calls[0].type,
                }
            ]
            if next(
                (choice.message.tool_calls for choice in response.choices if choice.finish_reason == 'tool_calls'), None
            )
            is not None
            else [],
            finish_reason=response.choices[0].finish_reason,
            send_tokens=response.usage.prompt_tokens,
            recv_tokens=response.usage.completion_tokens,
            total_tokens=(response.usage.prompt_tokens + response.usage.completion_tokens),
            status=LLMResponseStatus.SUCCESS,
        )
