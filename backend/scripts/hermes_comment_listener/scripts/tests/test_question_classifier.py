"""
Tests for QuestionClassifier - TDD: Write failing tests first.

Acceptance Criteria:
- HR-01: Detects coding questions (code, function, debug, implement, fix, error, test)
- HR-02: Detects general questions (greetings, explanations, summaries)
- HR-03: Detects tool-requiring questions (run, execute, clone, deploy, kubectl, git)
- HR-04: Returns enum: GENERAL | CODING | TOOL_REQUIRED
"""
from __future__ import annotations

import pytest

from scripts.hermes_comment_listener.scripts.question_classifier import (
    QuestionClassifier,
    QuestionType,
)


class TestQuestionClassifier:
    """Tests for question classification."""

    @pytest.fixture
    def classifier(self) -> QuestionClassifier:
        return QuestionClassifier()

    # HR-04: Classification returns enum
    def test_question_type_enum_exists(self):
        """QuestionType enum has all required values."""
        assert hasattr(QuestionType, "GENERAL")
        assert hasattr(QuestionType, "CODING")
        assert hasattr(QuestionType, "TOOL_REQUIRED")

    # HR-01: Coding questions
    @pytest.mark.parametrize("question", [
        "@hermes can you fix this bug in my Python code?",
        "@hermes implement a function to parse JSON",
        "@hermes debug this error: TypeError undefined",
        "@hermes write a test for the login function",
        "@hermes what's wrong with this code snippet?",
        "@hermes help me refactor this class",
        "@hermes how do I implement async/await here?",
    ])
    def test_detects_coding_questions(self, classifier, question):
        """HR-01: Classifier detects coding/technical questions."""
        result = classifier.classify(question)
        assert result == QuestionType.CODING, f"Expected CODING for: {question}"

    # HR-02: General questions
    @pytest.mark.parametrize("question", [
        "@hermes hello, how are you?",
        "@hermes what time is it?",
        "@hermes explain the concept of microservices",
        "@hermes summarize this document",
        "@hermes hi there!",
        "@hermes thanks for your help",
        "@hermes what is machine learning?",
    ])
    def test_detects_general_questions(self, classifier, question):
        """HR-02: Classifier detects general/chat questions."""
        result = classifier.classify(question)
        assert result == QuestionType.GENERAL, f"Expected GENERAL for: {question}"

    # HR-03: Tool-requiring questions
    @pytest.mark.parametrize("question", [
        "@hermes run kubectl get pods",
        "@hermes execute this shell command: ls -la",
        "@hermes clone the repo and build it",
        "@hermes deploy this to kubernetes",
        "@hermes git status && git pull",
        "@hermes run the tests and show me output",
        "@hermes create a file called test.py",
        "@hermes check the logs in /var/log",
    ])
    def test_detects_tool_questions(self, classifier, question):
        """HR-03: Classifier detects tool-requiring questions."""
        result = classifier.classify(question)
        assert result == QuestionType.TOOL_REQUIRED, f"Expected TOOL_REQUIRED for: {question}"

    # Edge cases
    def test_empty_string_returns_general(self, classifier):
        """Empty input defaults to GENERAL."""
        result = classifier.classify("")
        assert result == QuestionType.GENERAL

    def test_mixed_signals_prioritizes_tools(self, classifier):
        """When both coding and tool signals present, prioritize tools."""
        question = "@hermes run this code and debug any errors"
        result = classifier.classify(question)
        # Tools take priority because they need MCP execution
        assert result == QuestionType.TOOL_REQUIRED

    def test_case_insensitive(self, classifier):
        """Classification is case-insensitive."""
        assert classifier.classify("@hermes RUN kubectl") == QuestionType.TOOL_REQUIRED
        assert classifier.classify("@hermes FIX this BUG") == QuestionType.CODING
        assert classifier.classify("@hermes HELLO") == QuestionType.GENERAL
