"""
Test WR-15: vLLM adapter sends prompt via OpenAI-compatible API.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestVLLMAdapter:
    """Tests for vLLM adapter."""

    def test_send_prompt_success(self):
        """WR-15a: Send prompt returns completion."""
        from worker_registry.llm_adapters import VLLMAdapter

        adapter = VLLMAdapter(endpoint="http://localhost:8000")
        adapter._default_model = "llama-70b"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "cmpl-123",
            "model": "llama-70b",
            "choices": [
                {"text": "Generated text", "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20}
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = adapter.send_prompt("Generate something")

            assert result["content"] == "Generated text"
            assert result["model"] == "llama-70b"
            assert result["finish_reason"] == "stop"

    def test_send_chat_success(self):
        """WR-15b: Chat completions endpoint works."""
        from worker_registry.llm_adapters import VLLMAdapter

        adapter = VLLMAdapter(endpoint="http://localhost:8000")
        adapter._default_model = "llama-70b"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "chat-123",
            "model": "llama-70b",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10}
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = adapter.send_chat([{"role": "user", "content": "Hi"}])

            assert result["content"] == "Hello!"

    def test_auth_header_included(self):
        """WR-15c: Auth credentials sent as Bearer token."""
        from worker_registry.llm_adapters import VLLMAdapter

        adapter = VLLMAdapter(
            endpoint="http://localhost:8000",
            auth_credentials="secret-token"
        )
        adapter._default_model = "llama-70b"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"text": "ok"}]}

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            adapter.send_prompt("Test")

            call_args = mock_instance.post.call_args
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer secret-token"

    def test_health_check(self):
        """WR-15d: Health check uses /health endpoint."""
        from worker_registry.llm_adapters import VLLMAdapter

        adapter = VLLMAdapter(endpoint="http://localhost:8000")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.get.return_value = mock_response

            assert adapter.health_check() is True
            mock_instance.get.assert_called_once()

    def test_list_models(self):
        """WR-15e: List models returns model IDs."""
        from worker_registry.llm_adapters import VLLMAdapter

        adapter = VLLMAdapter(endpoint="http://localhost:8000")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "llama-70b"},
                {"id": "mistral-7b"}
            ]
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__.return_value = mock_instance
            mock_instance.get.return_value = mock_response

            models = adapter.list_models()

            assert "llama-70b" in models
            assert "mistral-7b" in models
