"""
Question Classifier - Classify questions to select optimal model.

Routes questions to appropriate models:
- GENERAL: Simple questions → small/fast model (qwen3:7b)
- CODING: Technical/code questions → coding model (qwen3-coder:30b)
- TOOL_REQUIRED: Commands needing execution → hermes-agent (has MCP tools)
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Set


class QuestionType(Enum):
    """Question type determines model selection."""
    GENERAL = "general"
    CODING = "coding"
    TOOL_REQUIRED = "tool_required"


class QuestionClassifier:
    """
    Classify questions to determine optimal model routing.

    Priority order: TOOL_REQUIRED > CODING > GENERAL
    (Tools need MCP, coding needs reasoning, general is fast path)
    """

    # Keywords indicating tool execution needed
    TOOL_KEYWORDS: Set[str] = {
        # Shell/command execution
        "run", "execute", "shell", "bash", "terminal",
        # Kubernetes/Docker
        "kubectl", "docker", "helm", "k8s", "kubernetes", "pod", "deploy",
        # Git operations
        "git", "clone", "pull", "push", "commit", "checkout",
        # File operations (need tool execution)
        "create file", "delete file", "read file", "write file",
        "create a file", "make a file", "write a file",
        "mkdir", "touch", "rm ", "cp ", "mv ",
        # System operations
        "logs", "restart", "stop", "start service",
    }

    # Patterns indicating tool execution (regex)
    TOOL_PATTERNS = [
        r"\b(run|execute)\s+(this|the|my|a)\b",  # "run this command"
        r"\bkubectl\s+\w+",  # kubectl commands
        r"\bgit\s+(status|pull|push|clone|commit)",  # git commands
        r"\bdocker\s+(run|build|push|pull)",  # docker commands
        r"&&|\||\$\(",  # shell operators
        r"\bsudo\s+",  # sudo commands
    ]

    # Keywords indicating coding/technical questions
    CODING_KEYWORDS: Set[str] = {
        # Programming
        "code", "function", "class", "method", "variable",
        "implement", "refactor", "optimize",
        # Debugging
        "debug", "error", "bug", "fix", "issue", "exception",
        "traceback", "stack trace", "crash",
        # Testing
        "test", "unittest", "pytest", "assertion",
        # Languages/frameworks
        "python", "javascript", "typescript", "java", "rust", "go",
        "react", "django", "fastapi", "flask",
        # Code review
        "review", "improve", "best practice", "pattern",
    }

    # Patterns indicating coding questions
    CODING_PATTERNS = [
        r"\b(fix|debug|implement)\s+(this|the|my|a)\b",
        r"\bwhat('s| is)\s+wrong\s+with",
        r"\bhow\s+(do|can|to)\s+i\s+(implement|fix|write)",
        r"```",  # Code blocks
        r"\bdef\s+\w+\(|function\s+\w+\(|class\s+\w+",  # Code snippets
    ]

    # General/chat indicators (lowest priority, default)
    GENERAL_KEYWORDS: Set[str] = {
        "hello", "hi", "hey", "thanks", "thank you",
        "explain", "what is", "summarize", "describe",
        "how does", "why does", "when", "where",
    }

    def __init__(self):
        """Initialize classifier with compiled patterns."""
        self._tool_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.TOOL_PATTERNS
        ]
        self._coding_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.CODING_PATTERNS
        ]

    def classify(self, text: str) -> QuestionType:
        """
        Classify a question to determine optimal model routing.

        Priority: TOOL_REQUIRED > CODING > GENERAL

        Args:
            text: The question text to classify

        Returns:
            QuestionType enum value
        """
        if not text or not text.strip():
            return QuestionType.GENERAL

        text_lower = text.lower()

        # Check for tool requirements first (highest priority)
        if self._has_tool_signals(text_lower, text):
            return QuestionType.TOOL_REQUIRED

        # Check for coding signals
        if self._has_coding_signals(text_lower, text):
            return QuestionType.CODING

        # Default to general
        return QuestionType.GENERAL

    def _has_tool_signals(self, text_lower: str, original: str) -> bool:
        """Check if text indicates tool execution is needed."""
        # Check keywords
        for keyword in self.TOOL_KEYWORDS:
            if keyword in text_lower:
                return True

        # Check patterns
        for pattern in self._tool_patterns:
            if pattern.search(original):
                return True

        return False

    def _has_coding_signals(self, text_lower: str, original: str) -> bool:
        """Check if text indicates a coding/technical question."""
        # Check keywords
        for keyword in self.CODING_KEYWORDS:
            if keyword in text_lower:
                return True

        # Check patterns
        for pattern in self._coding_patterns:
            if pattern.search(original):
                return True

        return False
