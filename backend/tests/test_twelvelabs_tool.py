"""Tests for the TwelveLabs tool wrapper.

The unit tests stub the SDK client and run without network access. The
embedding test is gated on ``TWELVELABS_API_KEY`` and is skipped when the key
is not set, so the default test run requires no credentials.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from director.tools.twelvelabs_tool import (
    TwelveLabsTool,
    PARAMS_CONFIG,
    PEGASUS_MODEL,
    MARENGO_MODEL,
)


def test_requires_api_key():
    with pytest.raises(Exception):
        TwelveLabsTool(api_key="")


def test_params_config_shape():
    assert "analyze" in PARAMS_CONFIG
    assert "embed" in PARAMS_CONFIG
    assert PARAMS_CONFIG["analyze"]["model_name"]["default"] == PEGASUS_MODEL
    assert PARAMS_CONFIG["embed"]["model_name"]["default"] == MARENGO_MODEL


def _tool_with_mock_client():
    """Build a TwelveLabsTool whose SDK client is a MagicMock (no network)."""
    with patch("twelvelabs.TwelveLabs"):
        tool = TwelveLabsTool(api_key="dummy-key")
    tool.client = MagicMock()
    return tool


def test_analyze_video_wiring():
    tool = _tool_with_mock_client()
    tool.client.analyze.return_value = MagicMock(data="A cat plays the piano.")

    result = tool.analyze_video(
        video_url="https://example.com/video.mp4",
        prompt="Describe this video",
        config={"max_tokens": 1024},
    )

    assert result == "A cat plays the piano."
    _, kwargs = tool.client.analyze.call_args
    assert kwargs["model_name"] == PEGASUS_MODEL
    assert kwargs["prompt"] == "Describe this video"
    assert kwargs["max_tokens"] == 1024
    # The video must be passed as a URL VideoContext.
    assert kwargs["video"].url == "https://example.com/video.mp4"


def test_get_text_embedding_wiring():
    tool = _tool_with_mock_client()
    segment = MagicMock(float_=[0.1, 0.2, 0.3])
    tool.client.embed.create.return_value = MagicMock(
        text_embedding=MagicMock(segments=[segment])
    )

    vector = tool.get_text_embedding("a cat")

    assert vector == [0.1, 0.2, 0.3]
    _, kwargs = tool.client.embed.create.call_args
    assert kwargs["model_name"] == MARENGO_MODEL
    assert kwargs["text"] == "a cat"


@pytest.mark.skipif(
    not os.getenv("TWELVELABS_API_KEY"),
    reason="TWELVELABS_API_KEY not set; skipping live TwelveLabs call",
)
def test_marengo_text_embedding_live():
    tool = TwelveLabsTool(api_key=os.environ["TWELVELABS_API_KEY"])
    vector = tool.get_text_embedding("a cat playing the piano")
    assert isinstance(vector, list)
    assert len(vector) == 512
    assert all(isinstance(v, float) for v in vector)
