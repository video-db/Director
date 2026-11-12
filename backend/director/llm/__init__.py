import os

from director.constants import LLMType

from director.llm.openai import OpenAI
from director.llm.anthropic import AnthropicAI
from director.llm.googleai import GoogleAI
from director.llm.videodb_proxy import VideoDBProxy


def get_default_llm():
    """Get default LLM"""

    default_llm = os.getenv("DEFAULT_LLM")

    # An explicit DEFAULT_LLM wins; otherwise pick by which API key is set.
    if default_llm == LLMType.OPENAI:
        return OpenAI()
    if default_llm == LLMType.ANTHROPIC:
        return AnthropicAI()
    if default_llm == LLMType.GOOGLEAI:
        return GoogleAI()
    if default_llm == LLMType.VIDEODB_PROXY:
        return VideoDBProxy()

    if os.getenv("OPENAI_API_KEY"):
        return OpenAI()
    if os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicAI()
    if os.getenv("GOOGLEAI_API_KEY"):
        return GoogleAI()
    return VideoDBProxy()
