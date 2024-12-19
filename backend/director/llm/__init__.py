import os

from director.constants import LLMType

from director.llm.openai import OpenAI
from director.llm.anthropic import AnthropicAI
from director.llm.mistral import MistralAI
from director.llm.videodb_proxy import VideoDBProxy


def get_default_llm():
    """Get default LLM"""

    openai = True if os.getenv("OPENAI_API_KEY") else False
    anthropic = True if os.getenv("ANTHROPIC_API_KEY") else False
    mistral = True if os.getenv("MISTRAL_API_KEY") else False

    default_llm = os.getenv("DEFAULT_LLM")

    if openai or default_llm == LLMType.OPENAI:
        return OpenAI()
    elif anthropic or default_llm == LLMType.ANTHROPIC:
        return AnthropicAI()
    elif mistral or default_llm == LLMType.MISTRAL:
        return MistralAI()
    else:
        return VideoDBProxy()
