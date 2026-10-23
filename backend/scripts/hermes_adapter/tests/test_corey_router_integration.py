"""
Tests for corey-router integration - HR-08 to HR-10, HR-15.

Acceptance Criteria:
- HR-08: hermes_client routes through corey-router URL
- HR-09: Request includes model parameter based on classification
- HR-10: Fallback chain activates when primary provider fails
- HR-15: Response includes _meta.provider showing which provider served
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from hermes_client import (
    complete,
    HermesResult,
    _parse_reply,
    _classify_and_select_model,
    _corey_router_endpoint,
    COREY_ROUTER_URL,
)


class TestCoreyRouterIntegration:
    """Tests for corey-router integration."""

    # HR-08: Routes through corey-router
    def test_corey_router_endpoint_default(self):
        """HR-08: Default endpoint points to corey-router."""
        endpoint = _corey_router_endpoint()
        assert "corey-router" in endpoint or "8081" in endpoint
        assert endpoint.endswith("/v1/chat/completions")

    # HR-09: Model parameter based on classification
    def test_classify_and_select_general(self):
        """HR-09: General question selects qwen3:7b."""
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        model = _classify_and_select_model(messages)
        assert model == "qwen3:7b"

    def test_classify_and_select_coding(self):
        """HR-09: Coding question selects qwen3-coder:30b."""
        messages = [{"role": "user", "content": "Fix this Python bug in my code"}]
        model = _classify_and_select_model(messages)
        assert model == "qwen3-coder:30b"

    def test_classify_and_select_tool(self):
        """HR-09: Tool question selects hermes-agent."""
        messages = [{"role": "user", "content": "Run kubectl get pods"}]
        model = _classify_and_select_model(messages)
        assert model == "hermes-agent"

    # HR-15: Response includes _meta.provider
    def test_parse_reply_extracts_provider(self):
        """HR-15: _parse_reply extracts provider from _meta."""
        data = {
            "choices": [{"message": {"content": "Hello!"}}],
            "_meta": {"provider": "ollama"}
        }
        reply, provider = _parse_reply(data)
        assert reply == "Hello!"
        assert provider == "ollama"

    def test_parse_reply_handles_missing_meta(self):
        """HR-15: _parse_reply handles missing _meta gracefully."""
        data = {
            "choices": [{"message": {"content": "Hello!"}}]
        }
        reply, provider = _parse_reply(data)
        assert reply == "Hello!"
        assert provider is None

    def test_parse_reply_handles_empty_response(self):
        """_parse_reply handles empty response."""
        data = {"choices": []}
        reply, provider = _parse_reply(data)
        assert reply == ""
        assert provider is None

    # HR-10: Fallback chain (mocked test)
    @pytest.mark.asyncio
    async def test_complete_returns_provider_in_result(self):
        """HR-10/15: Complete returns provider info in HermesResult."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "_meta": {"provider": "spark_glm"}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await complete(
                messages=[{"role": "user", "content": "test"}],
                model="qwen3:7b",
                use_classification=False,
            )

            assert result.reply == "Test response"
            assert result.provider == "spark_glm"
            assert result.failure_reason is None

    @pytest.mark.asyncio
    async def test_complete_with_classification(self):
        """Complete uses classification when model not specified."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Coding help"}}],
            "_meta": {"provider": "ollama"}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            # Coding question should classify to qwen3-coder:30b
            result = await complete(
                messages=[{"role": "user", "content": "Fix this bug in my Python code"}],
                model=None,  # Let classification decide
                use_classification=True,
            )

            # Check model was classified correctly
            assert result.model == "qwen3-coder:30b"
            assert result.reply == "Coding help"

    @pytest.mark.asyncio
    async def test_complete_hermes_agent_sets_agent_mode(self):
        """hermes-agent requests include agent_mode=True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Tool result"}}],
            "_meta": {"provider": "hermes"}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await complete(
                messages=[{"role": "user", "content": "Run kubectl get pods"}],
                model="hermes-agent",
                use_classification=False,
            )

            # Verify agent_mode was set in payload
            call_args = mock_instance.post.call_args
            payload = call_args.kwargs.get("json", {})
            assert payload.get("agent_mode") is True
            assert result.model == "hermes-agent"

    @pytest.mark.asyncio
    async def test_complete_non_hermes_no_agent_mode(self):
        """Non-hermes models don't include agent_mode."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello"}}],
            "_meta": {"provider": "ollama"}
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await complete(
                messages=[{"role": "user", "content": "Hello"}],
                model="qwen3:7b",
                use_classification=False,
            )

            # Verify agent_mode was NOT set
            call_args = mock_instance.post.call_args
            payload = call_args.kwargs.get("json", {})
            assert "agent_mode" not in payload
            assert result.model == "qwen3:7b"

    @pytest.mark.asyncio
    async def test_complete_retry_on_timeout(self):
        """Complete retries on timeout."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}],
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            # First call times out, second succeeds
            mock_instance.post.side_effect = [
                httpx.TimeoutException("Timeout"),
                mock_response,
            ]
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await complete(
                    messages=[{"role": "user", "content": "test"}],
                    model="qwen3:7b",
                    max_retries=3,
                    retry_base_delay_s=0.01,  # Fast for test
                    use_classification=False,
                )

            assert result.reply == "Success after retry"
            assert result.failure_reason is None
            assert mock_instance.post.call_count == 2
