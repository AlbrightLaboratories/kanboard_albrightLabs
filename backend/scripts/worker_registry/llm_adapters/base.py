"""
Base LLM Adapter

Abstract base class for LLM provider adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseLLMAdapter(ABC):
    """Abstract base class for LLM adapters."""

    def __init__(self, endpoint: str, auth_credentials: Optional[str] = None):
        """
        Initialize adapter.

        Args:
            endpoint: API endpoint URL
            auth_credentials: Optional authentication credentials
        """
        self.endpoint = endpoint
        self.auth_credentials = auth_credentials

    @abstractmethod
    def send_prompt(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send prompt to LLM and get response.

        Args:
            prompt: The prompt text
            model: Optional model name override
            **kwargs: Additional provider-specific parameters

        Returns:
            Response dict with at least 'content' key
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the LLM endpoint is healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def list_models(self) -> list:
        """
        List available models on this endpoint.

        Returns:
            List of model names
        """
        pass
