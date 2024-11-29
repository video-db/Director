from abc import ABC, abstractmethod
from typing import List, Dict

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class LLMResponseStatus:
    SUCCESS: bool = True
    ERROR: bool = False


class LLMResponse(BaseModel):
    """Response model for completions from LLMs."""

    content: str = ""
    tool_calls: List[Dict] = []
    send_tokens: int = 0
    recv_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = ""
    status: int = LLMResponseStatus.ERROR


class BaseLLMConfig(BaseSettings):
    """Base configuration for all LLMs.

    :param str llm_type: Type of LLM. e.g. "openai", "anthropic", etc.
    :param str api_key: API key for the LLM.
    :param str api_base: Base URL for the LLM API.
    :param str chat_model: Model name for chat completions.
    :param str temperature: Sampling temperature for completions.
    :param float top_p: Top p sampling for completions.
    :param int max_tokens: Maximum tokens to generate.
    :param int timeout: Timeout for the request.
    """

    llm_type: str = ""
    api_key: str = ""
    api_base: str = ""
    chat_model: str = ""
    temperature: float = 0.9
    top_p: float = 1
    max_tokens: int = 4096
    timeout: int = 120
    enable_langfuse: bool = False


class BaseLLM(ABC):
    """Interface for all LLMs. All LLMs should inherit from this class."""

    def __init__(self, config: BaseLLMConfig):
        """
        :param config: Configuration for the LLM.
        """
        self.config = config
        self.llm_type = config.llm_type
        self.api_key = config.api_key
        self.api_base = config.api_base
        self.chat_model = config.chat_model
        self.temperature = config.temperature
        self.top_p = config.top_p
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout
        self.enable_langfuse = config.enable_langfuse

    @abstractmethod
    def chat_completions(self, messages: List[Dict], tools: List[Dict]) -> LLMResponse:
        """Abstract method for chat completions"""
        pass
