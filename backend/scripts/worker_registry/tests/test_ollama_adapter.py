"""
Test WR-14: Ollama adapter sends prompt, receives completion.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestOllamaAdapter:
    """Tests for Ollama adapter."""

    def test_send_prompt_success(self):
        """WR-14a: Send prompt returns completion."""
        from worker_registry.llm_adapters import OllamaAdapter

        adapter = OllamaAdapter(endpoint="http://localhost:11434")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Hello, world!",
            "model": "llama3.2",
            "done": True,
            "total_duration": 1000000
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = adapter.send_prompt("Say hello")

            assert result["content"] == "Hello, world!"
            assert result["model"] == "llama3.2"
            assert result["done"] is True

    def test_send_prompt_with_model(self):
        """WR-14b: Can specify model in request."""
        from worker_registry.llm_adapters import OllamaAdapter

        adapter = OllamaAdapter(endpoint="http://localhost:11434")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "response",
            "model": "codellama",
            "done": True
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = adapter.send_prompt("Write code", model="codellama")

            call_args = mock_instance.post.call_args
            assert call_args[1]["json"]["model"] == "codellama"

    def test_health_check_healthy(self):
        """WR-14c: Health check returns True when healthy."""
        from worker_registry.llm_adapters import OllamaAdapter

        adapter = OllamaAdapter(endpoint="http://localhost:11434")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.get.return_value = mock_response

            assert adapter.health_check() is True

    def test_health_check_unhealthy(self):
        """WR-14d: Health check returns False when unhealthy."""
        from worker_registry.llm_adapters import OllamaAdapter

        adapter = OllamaAdapter(endpoint="http://localhost:11434")

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.get.side_effect = Exception("Connection refused")

            assert adapter.health_check() is False

    def test_list_models(self):
        """WR-14e: List models returns available models."""
        from worker_registry.llm_adapters import OllamaAdapter

        adapter = OllamaAdapter(endpoint="http://localhost:11434")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2"},
                {"name": "codellama"},
                {"name": "mistral"}
            ]
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.get.return_value = mock_response

            models = adapter.list_models()

            assert "llama3.2" in models
            assert "codellama" in models
            assert len(models) == 3
