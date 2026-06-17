from enum import Enum

from pydantic import Field, FieldValidationInfo, field_validator
from pydantic_settings import SettingsConfigDict

from director.constants import EnvPrefix, LLMType
from director.llm.openai import OpenAI, OpenaiConfig


class EvolinkChatModel(str, Enum):
    """Enum for EvoLink chat models."""

    GPT5_2 = "gpt-5.2"
    GPT5_1 = "gpt-5.1"
    GEMINI_3_1_PRO = "gemini-3.1-pro"
    DEEPSEEK_V4_PRO = "deepseek-v4-pro"
    DOUBAO_SEED_2_0_PRO = "doubao-seed-2.0-pro"


class EvolinkConfig(OpenaiConfig):
    """EvoLink Config."""

    model_config = SettingsConfigDict(
        env_prefix=EnvPrefix.EVOLINK_,
        extra="ignore",
    )

    llm_type: str = LLMType.EVOLINK
    api_key: str = ""
    api_base: str = "https://direct.evolink.ai/v1"
    chat_model: str = Field(default=EvolinkChatModel.GPT5_2)

    @field_validator("api_key")
    @classmethod
    def validate_non_empty(cls, v, info: FieldValidationInfo):
        if not v:
            raise ValueError(
                f"{info.field_name} must not be empty. Please set {EnvPrefix.EVOLINK_.value}{info.field_name.upper()} environment variable."
            )
        return v


class Evolink(OpenAI):
    """EvoLink LLM integration using the OpenAI-compatible Chat Completions API."""

    def __init__(self, config: EvolinkConfig = None):
        """
        :param config: EvoLink Config
        """
        if config is None:
            config = EvolinkConfig()
        super().__init__(config=config)
