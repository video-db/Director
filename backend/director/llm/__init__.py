import os

from director.constants import LLMType

from director.llm.openai import OpenAI
from director.llm.anthropic import AnthropicAI
from director.llm.xai import XAI


def get_default_llm():
    """Get default LLM"""

    default_llm = os.getenv("DEFAULT_LLM", LLMType.DEFAULT)

    if default_llm == LLMType.OPENAI:
        return OpenAI()
    elif default_llm == LLMType.ANTHROPIC:
        return AnthropicAI()
    elif default_llm == LLMType.XAI:
        return XAI()
    else:
        raise ValueError(f"Invalid LLM type: {default_llm}")
