"""
Model Selector - Select optimal model based on question classification.

Routes questions to appropriate models via corey-router:
- GENERAL: qwen3:7b (fast, cheap, good for simple questions)
- CODING: qwen3-coder:30b (better reasoning, code generation)
- TOOL_REQUIRED: hermes-agent (has 49 MCP tools for execution)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    from .question_classifier import QuestionType
except ImportError:
    from question_classifier import QuestionType


@dataclass
class ModelConfig:
    """Configuration for a selected model."""
    model: str
    provider: Optional[str] = None  # None = let corey-router decide


class ModelSelector:
    """
    Select optimal model based on question type.

    Integrates with corey-router's provider chain for fallback.
    """

    # Default model mappings
    DEFAULT_GENERAL_MODEL = "qwen3:7b"
    DEFAULT_CODING_MODEL = "qwen3-coder:30b"
    DEFAULT_TOOL_MODEL = "hermes-agent"

    def __init__(
        self,
        general_model: Optional[str] = None,
        coding_model: Optional[str] = None,
        tool_model: Optional[str] = None,
    ):
        """
        Initialize model selector with optional custom mappings.

        Args:
            general_model: Model for GENERAL questions
            coding_model: Model for CODING questions
            tool_model: Model for TOOL_REQUIRED questions
        """
        self._general = general_model or self.DEFAULT_GENERAL_MODEL
        self._coding = coding_model or self.DEFAULT_CODING_MODEL
        self._tool = tool_model or self.DEFAULT_TOOL_MODEL

        # Model to provider mapping (for explicit routing)
        self._provider_map: Dict[str, str] = {
            "hermes-agent": "hermes",
        }

    def select(
        self,
        question_type: QuestionType,
        override_model: Optional[str] = None,
    ) -> ModelConfig:
        """
        Select model configuration based on question type.

        Args:
            question_type: Classified question type
            override_model: Optional explicit model override

        Returns:
            ModelConfig with model and optional provider
        """
        if override_model:
            provider = self._provider_map.get(override_model)
            return ModelConfig(model=override_model, provider=provider)

        model = self._get_model_for_type(question_type)
        provider = self._provider_map.get(model)

        return ModelConfig(model=model, provider=provider)

    def _get_model_for_type(self, question_type: QuestionType) -> str:
        """Get model name for question type."""
        mapping = {
            QuestionType.GENERAL: self._general,
            QuestionType.CODING: self._coding,
            QuestionType.TOOL_REQUIRED: self._tool,
        }
        return mapping.get(question_type, self._general)

    def get_models(self) -> List[str]:
        """Return all configured models."""
        return [self._general, self._coding, self._tool]
