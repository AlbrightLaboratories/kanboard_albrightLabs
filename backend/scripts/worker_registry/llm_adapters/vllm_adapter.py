"""
vLLM Adapter

Adapter for vLLM OpenAI-compatible API.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from .base import BaseLLMAdapter


class VLLMAdapter(BaseLLMAdapter):
    """Adapter for vLLM OpenAI-compatible API."""

    def __init__(
        self,
        endpoint: str = "http://localhost:8000",
        auth_credentials: Optional[str] = None,
        timeout: float = 120.0,
        default_model: Optional[str] = None
    ):
        """
        Initialize vLLM adapter.

        Args:
            endpoint: vLLM API endpoint
            auth_credentials: Bearer token if required
            timeout: Request timeout in seconds
            default_model: Default model (auto-detected if None)
        """
        super().__init__(endpoint, auth_credentials)
        self.timeout = timeout
        self._default_model = default_model
        self._cached_models: Optional[List[str]] = None

    @property
    def default_model(self) -> str:
        """Get default model, fetching from API if needed."""
        if self._default_model:
            return self._default_model

        models = self.list_models()
        if models:
            self._default_model = models[0]
            return self._default_model

        raise RuntimeError("No models available on vLLM endpoint")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth if configured."""
        headers = {"Content-Type": "application/json"}
        if self.auth_credentials:
            headers["Authorization"] = f"Bearer {self.auth_credentials}"
        return headers

    def send_prompt(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send prompt to vLLM and get response.

        Uses the OpenAI-compatible /v1/completions endpoint.

        Args:
            prompt: The prompt text
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Response dict with 'content' and metadata
        """
        model_name = model or self.default_model

        payload = {
            "model": model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.endpoint}/v1/completions",
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                choices = data.get("choices", [])
                content = choices[0]["text"] if choices else ""

                return {
                    "content": content,
                    "model": data.get("model", model_name),
                    "usage": data.get("usage", {}),
                    "id": data.get("id"),
                    "finish_reason": choices[0].get("finish_reason") if choices else None
                }
        except httpx.TimeoutException as e:
            raise TimeoutError(f"vLLM request timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"vLLM HTTP error: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"vLLM error: {e}")

    def send_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send chat messages to vLLM (chat completions endpoint).

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Response dict with 'content' and metadata
        """
        model_name = model or self.default_model

        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.endpoint}/v1/chat/completions",
                    json=payload,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()

                choices = data.get("choices", [])
                message = choices[0].get("message", {}) if choices else {}
                content = message.get("content", "")

                return {
                    "content": content,
                    "model": data.get("model", model_name),
                    "usage": data.get("usage", {}),
                    "id": data.get("id"),
                    "finish_reason": choices[0].get("finish_reason") if choices else None
                }
        except httpx.TimeoutException as e:
            raise TimeoutError(f"vLLM request timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"vLLM HTTP error: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"vLLM error: {e}")

    def health_check(self) -> bool:
        """
        Check if vLLM is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    f"{self.endpoint}/health",
                    headers=self._get_headers()
                )
                return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """
        List available models on vLLM.

        Returns:
            List of model names
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.endpoint}/v1/models",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                models = [m["id"] for m in data.get("data", [])]
                self._cached_models = models
                return models
        except Exception:
            return self._cached_models or []
