import pytest

from director.constants import LLMType
from director.llm.evolink import Evolink, EvolinkConfig, EvolinkChatModel


def test_evolink_config_uses_direct_api_defaults(monkeypatch):
    monkeypatch.setenv("EVOLINK_API_KEY", "test-key")

    config = EvolinkConfig()

    assert config.llm_type == LLMType.EVOLINK
    assert config.api_key == "test-key"
    assert config.api_base == "https://direct.evolink.ai/v1"
    assert config.chat_model == EvolinkChatModel.GPT5_2


def test_evolink_config_supports_env_overrides(monkeypatch):
    monkeypatch.setenv("EVOLINK_API_KEY", "test-key")
    monkeypatch.setenv("EVOLINK_API_BASE", "https://example.com/v1")
    monkeypatch.setenv("EVOLINK_CHAT_MODEL", "deepseek-v4-pro")

    config = EvolinkConfig()

    assert config.api_base == "https://example.com/v1"
    assert config.chat_model == "deepseek-v4-pro"


def test_evolink_config_requires_api_key(monkeypatch):
    monkeypatch.delenv("EVOLINK_API_KEY", raising=False)

    with pytest.raises(ValueError, match="EVOLINK_API_KEY"):
        EvolinkConfig()


def test_default_llm_can_select_evolink(monkeypatch):
    import director.llm as llm_module

    monkeypatch.setenv("DEFAULT_LLM", LLMType.EVOLINK)
    monkeypatch.setenv("EVOLINK_API_KEY", "test-key")

    assert isinstance(llm_module.get_default_llm(), Evolink)
