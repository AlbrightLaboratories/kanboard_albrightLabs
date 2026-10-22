"""
Tests for ModelSelector - TDD: Write failing tests first.

Acceptance Criteria:
- HR-05: ModelSelector maps GENERAL -> qwen3:7b
- HR-06: ModelSelector maps CODING -> qwen3-coder:30b
- HR-07: ModelSelector maps TOOL_REQUIRED -> hermes-agent
"""
from __future__ import annotations

import pytest

from scripts.hermes_comment_listener.scripts.question_classifier import QuestionType
from scripts.hermes_comment_listener.scripts.model_selector import (
    ModelSelector,
    ModelConfig,
)


class TestModelSelector:
    """Tests for model selection based on question type."""

    @pytest.fixture
    def selector(self) -> ModelSelector:
        return ModelSelector()

    # HR-05: GENERAL -> qwen3:7b
    def test_general_maps_to_small_model(self, selector):
        """HR-05: GENERAL questions use small/fast model."""
        config = selector.select(QuestionType.GENERAL)
        assert config.model == "qwen3:7b"
        assert config.provider is None  # Let corey-router decide

    # HR-06: CODING -> qwen3-coder:30b
    def test_coding_maps_to_coder_model(self, selector):
        """HR-06: CODING questions use coding model."""
        config = selector.select(QuestionType.CODING)
        assert config.model == "qwen3-coder:30b"
        assert config.provider is None  # Let corey-router decide

    # HR-07: TOOL_REQUIRED -> hermes-agent
    def test_tool_required_maps_to_hermes(self, selector):
        """HR-07: TOOL_REQUIRED questions use hermes-agent."""
        config = selector.select(QuestionType.TOOL_REQUIRED)
        assert config.model == "hermes-agent"
        # hermes-agent should force hermes provider
        assert config.provider == "hermes"

    def test_model_config_has_required_fields(self):
        """ModelConfig has model and optional provider."""
        config = ModelConfig(model="test-model", provider="test-provider")
        assert config.model == "test-model"
        assert config.provider == "test-provider"

    def test_model_config_provider_optional(self):
        """ModelConfig provider is optional."""
        config = ModelConfig(model="test-model")
        assert config.model == "test-model"
        assert config.provider is None

    def test_custom_model_mapping(self):
        """Custom model mapping can be provided."""
        custom_selector = ModelSelector(
            general_model="custom-general:1b",
            coding_model="custom-coder:10b",
            tool_model="custom-tool-agent",
        )
        assert custom_selector.select(QuestionType.GENERAL).model == "custom-general:1b"
        assert custom_selector.select(QuestionType.CODING).model == "custom-coder:10b"
        assert custom_selector.select(QuestionType.TOOL_REQUIRED).model == "custom-tool-agent"

    def test_select_with_override(self, selector):
        """Override model when explicitly requested."""
        config = selector.select(QuestionType.GENERAL, override_model="claude-3-opus")
        assert config.model == "claude-3-opus"

    def test_get_all_models(self, selector):
        """Return all configured models."""
        models = selector.get_models()
        assert "qwen3:7b" in models
        assert "qwen3-coder:30b" in models
        assert "hermes-agent" in models
