"""
Ollama Adapter

Adapter for Ollama local LLM inference.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from .base import BaseLLMAdapter


class OllamaAdapter(BaseLLMAdapter):
    """Adapter for Ollama API."""

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        auth_credentials: Optional[str] = None,
        timeout: float = 120.0,
        default_model: str = "llama3.2"
    ):
        """
        Initialize Ollama adapter.

        Args:
            endpoint: Ollama API endpoint
            auth_credentials: Not used by Ollama (no auth)
            timeout: Request timeout in seconds
            default_model: Default model to use
        """
        super().__init__(endpoint, auth_credentials)
        self.timeout = timeout
        self.default_model = default_model

    def send_prompt(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send prompt to Ollama and get response.

        Args:
            prompt: The prompt text
            model: Model name (defaults to default_model)
            stream: Whether to stream response (not implemented)
            **kwargs: Additional Ollama parameters (temperature, etc.)

        Returns:
            Response dict with 'content' and metadata
        """
        model_name = model or self.default_model

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.endpoint}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "content": data.get("response", ""),
                    "model": data.get("model", model_name),
                    "total_duration": data.get("total_duration"),
                    "load_duration": data.get("load_duration"),
                    "eval_count": data.get("eval_count"),
                    "done": data.get("done", True)
                }
        except httpx.TimeoutException as e:
            raise TimeoutError(f"Ollama request timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama HTTP error: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")

    def health_check(self) -> bool:
        """
        Check if Ollama is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.endpoint}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """
        List available models on Ollama.

        Returns:
            List of model names
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.endpoint}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def pull_model(self, model: str) -> bool:
        """
        Pull a model to Ollama.

        Args:
            model: Model name to pull

        Returns:
            True if successful
        """
        try:
            with httpx.Client(timeout=600.0) as client:  # Long timeout for pulls
                response = client.post(
                    f"{self.endpoint}/api/pull",
                    json={"name": model, "stream": False}
                )
                return response.status_code == 200
        except Exception:
            return False
