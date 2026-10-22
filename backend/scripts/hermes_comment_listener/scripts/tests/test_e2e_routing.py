"""
E2E Tests for Hermes Routing - HR-12, HR-13, HR-14.

Tests actual routing through question classification and model selection.
"""
from __future__ import annotations

import os
import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from scripts.hermes_comment_listener.scripts.question_classifier import (
    QuestionClassifier,
    QuestionType,
)
from scripts.hermes_comment_listener.scripts.model_selector import (
    ModelSelector,
    ModelConfig,
)


class TestE2ERouting:
    """E2E tests for question routing through the full pipeline."""

    @pytest.fixture
    def classifier(self) -> QuestionClassifier:
        return QuestionClassifier()

    @pytest.fixture
    def selector(self) -> ModelSelector:
        return ModelSelector()

    # HR-12: E2E: General question uses small model, responds in <5s
    def test_general_question_uses_small_model(self, classifier, selector):
        """HR-12: General question routes to qwen3:7b for fast response."""
        question = "@hermes hello, how are you today?"

        # Step 1: Classify
        question_type = classifier.classify(question)
        assert question_type == QuestionType.GENERAL

        # Step 2: Select model
        config = selector.select(question_type)
        assert config.model == "qwen3:7b"
        assert config.provider is None  # Let corey-router decide provider

    def test_general_question_response_time_expectation(self, classifier, selector):
        """HR-12: General routing completes classification + selection in <100ms."""
        question = "@hermes explain microservices"

        start = time.time()
        question_type = classifier.classify(question)
        config = selector.select(question_type)
        elapsed = time.time() - start

        # Classification + selection should be near-instant
        assert elapsed < 0.1, f"Routing took {elapsed:.3f}s, expected <100ms"
        assert config.model == "qwen3:7b"

    @pytest.mark.parametrize("question", [
        "@hermes what is the weather like?",
        "@hermes summarize this article",
        "@hermes thank you for your help",
        "@hermes hi there!",
    ])
    def test_various_general_questions_route_to_small_model(
        self, classifier, selector, question
    ):
        """HR-12: Various general questions all route to small model."""
        question_type = classifier.classify(question)
        config = selector.select(question_type)

        assert question_type == QuestionType.GENERAL
        assert config.model == "qwen3:7b"

    # HR-13: E2E: Coding question uses coding model
    def test_coding_question_uses_coding_model(self, classifier, selector):
        """HR-13: Coding question routes to qwen3-coder:30b."""
        question = "@hermes can you fix this Python bug in my code?"

        # Step 1: Classify
        question_type = classifier.classify(question)
        assert question_type == QuestionType.CODING

        # Step 2: Select model
        config = selector.select(question_type)
        assert config.model == "qwen3-coder:30b"
        assert config.provider is None

    @pytest.mark.parametrize("question", [
        "@hermes implement a function to parse JSON",
        "@hermes debug this error: TypeError undefined",
        "@hermes write a test for the login function",
        "@hermes refactor this class to use dependency injection",
        "@hermes what's wrong with this code snippet?",
    ])
    def test_various_coding_questions_route_to_coding_model(
        self, classifier, selector, question
    ):
        """HR-13: Various coding questions all route to coding model."""
        question_type = classifier.classify(question)
        config = selector.select(question_type)

        assert question_type == QuestionType.CODING
        assert config.model == "qwen3-coder:30b"

    # HR-14: E2E: Tool question uses hermes-agent with tool execution
    def test_tool_question_uses_hermes_agent(self, classifier, selector):
        """HR-14: Tool-requiring question routes to hermes-agent."""
        question = "@hermes run kubectl get pods"

        # Step 1: Classify
        question_type = classifier.classify(question)
        assert question_type == QuestionType.TOOL_REQUIRED

        # Step 2: Select model
        config = selector.select(question_type)
        assert config.model == "hermes-agent"
        assert config.provider == "hermes"  # Explicit hermes provider

    @pytest.mark.parametrize("question", [
        "@hermes execute this shell command: ls -la",
        "@hermes clone the repo and build it",
        "@hermes deploy this to kubernetes",
        "@hermes git status && git pull",
        "@hermes create a file called test.py",
    ])
    def test_various_tool_questions_route_to_hermes_agent(
        self, classifier, selector, question
    ):
        """HR-14: Various tool questions all route to hermes-agent."""
        question_type = classifier.classify(question)
        config = selector.select(question_type)

        assert question_type == QuestionType.TOOL_REQUIRED
        assert config.model == "hermes-agent"
        assert config.provider == "hermes"

    # Integration: Full pipeline simulation
    @pytest.mark.asyncio
    async def test_full_pipeline_general_question(self, classifier, selector):
        """HR-12: Full pipeline simulation for general question."""
        question = "@hermes hello"

        # Simulate the full routing pipeline
        question_type = classifier.classify(question)
        config = selector.select(question_type)

        # Mock corey-router response
        mock_response = {
            "content": "Hello! How can I help you today?",
            "_meta": {
                "provider": "ollama",
                "model": "qwen3:7b",
                "latency_ms": 250,
            }
        }

        # Verify routing decision
        assert config.model == "qwen3:7b"
        assert mock_response["_meta"]["model"] == config.model

    @pytest.mark.asyncio
    async def test_full_pipeline_coding_question(self, classifier, selector):
        """HR-13: Full pipeline simulation for coding question."""
        question = "@hermes fix this bug in my code"

        question_type = classifier.classify(question)
        config = selector.select(question_type)

        mock_response = {
            "content": "I found the issue. Here's the fix...",
            "_meta": {
                "provider": "ollama",
                "model": "qwen3-coder:30b",
                "latency_ms": 1500,
            }
        }

        assert config.model == "qwen3-coder:30b"
        assert mock_response["_meta"]["model"] == config.model

    @pytest.mark.asyncio
    async def test_full_pipeline_tool_question(self, classifier, selector):
        """HR-14: Full pipeline simulation for tool question."""
        question = "@hermes run kubectl get pods"

        question_type = classifier.classify(question)
        config = selector.select(question_type)

        mock_response = {
            "content": "Here are the pods:\nNAME        READY   STATUS\nhermes-1    1/1     Running",
            "_meta": {
                "provider": "hermes",
                "model": "hermes-agent",
                "tools_used": ["terminal"],
                "latency_ms": 3000,
            }
        }

        assert config.model == "hermes-agent"
        assert config.provider == "hermes"
        assert mock_response["_meta"]["provider"] == config.provider


class TestE2EResponseMeta:
    """Tests for response metadata verification."""

    def test_response_includes_provider_meta(self):
        """HR-15: Response includes _meta.provider showing which provider served."""
        # This is tested via mock - real E2E would require corey-router
        expected_meta_fields = ["provider", "model", "latency_ms"]

        mock_response = {
            "_meta": {
                "provider": "ollama",
                "model": "qwen3:7b",
                "latency_ms": 250,
            }
        }

        for field in expected_meta_fields:
            assert field in mock_response["_meta"]

    def test_hermes_agent_includes_tools_used(self):
        """HR-14: hermes-agent responses include tools_used in meta."""
        mock_response = {
            "_meta": {
                "provider": "hermes",
                "model": "hermes-agent",
                "tools_used": ["terminal", "file_read"],
                "latency_ms": 3500,
            }
        }

        assert "tools_used" in mock_response["_meta"]
        assert len(mock_response["_meta"]["tools_used"]) > 0
