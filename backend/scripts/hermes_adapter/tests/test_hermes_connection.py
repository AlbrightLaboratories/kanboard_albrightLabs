"""
Tests for Hermes client connection and retry logic.

AC-HA-01: Connect to Hermes at 172.100.10.21:8642
AC-HA-02: Retry 3x on timeout
AC-HA-03: Response within 180s timeout
AC-HA-04: Returns HermesResult with failure_reason
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from ..scripts.hermes_client import (
    complete,
    health_check,
    hermes_enabled,
    HermesResult,
    _parse_reply,
)


class TestHermesEnabled:
    """Tests for hermes_enabled() function."""

    def test_enabled_with_api_key(self):
        """Hermes enabled when API key is set."""
        with patch.dict("os.environ", {"HERMES_API_KEY": "test-key", "HERMES_ENABLED": "1"}):
            # Need to reload to pick up env changes
            from ..scripts import hermes_client
            hermes_client.HERMES_API_KEY = "test-key"
            hermes_client.HERMES_ENABLED = True
            assert hermes_client.hermes_enabled() is True

    def test_disabled_without_api_key(self):
        """Hermes disabled without API key."""
        from ..scripts import hermes_client
        hermes_client.HERMES_API_KEY = ""
        hermes_client.HERMES_ENABLED = True
        assert hermes_client.hermes_enabled() is False


class TestParseReply:
    """Tests for _parse_reply helper."""

    def test_parse_valid_response(self):
        """Extracts content from valid OpenAI response."""
        data = {
            "choices": [
                {
                    "message": {
                        "content": "Hello, I'm Hermes!"
                    }
                }
            ]
        }
        reply, provider = _parse_reply(data)
        assert reply == "Hello, I'm Hermes!"

    def test_parse_empty_choices(self):
        """Returns empty string for empty choices."""
        reply1, _ = _parse_reply({"choices": []})
        reply2, _ = _parse_reply({})
        assert reply1 == ""
        assert reply2 == ""

    def test_parse_missing_content(self):
        """Returns empty string when content is missing."""
        data = {"choices": [{"message": {}}]}
        reply, _ = _parse_reply(data)
        assert reply == ""


class TestHealthCheck:
    """Tests for health_check() function."""

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """AC-HA-05: Health check returns True when Hermes is healthy."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await health_check(timeout_s=5.0)
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Health check returns False on connection error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await health_check(timeout_s=5.0)
            assert result is False


class TestComplete:
    """Tests for complete() function."""

    @pytest.mark.asyncio
    async def test_complete_no_api_key(self):
        """AC-HA-04: Returns failure_reason when no API key."""
        from ..scripts import hermes_client
        hermes_client.HERMES_API_KEY = ""
        hermes_client.HERMES_URL = ""  # Also disable hermes URL
        hermes_client.COREY_ROUTER_URL = ""  # Also disable corey-router
        hermes_client.USE_COREY_ROUTER = False  # Use direct mode

        result = await complete([{"role": "user", "content": "Hello"}])

        # With empty URL and no API key, should fail with connection error
        assert result.failure_reason is not None
        assert result.reply == ""

    @pytest.mark.asyncio
    async def test_complete_success(self):
        """AC-HA-01: Successfully connects and returns response."""
        from ..scripts import hermes_client
        hermes_client.HERMES_API_KEY = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "I can hear you!"}}]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # Use explicit model to bypass classification
            result = await complete(
                [{"role": "user", "content": "@hermes can you hear me"}],
                model="hermes-agent"
            )

            assert result.failure_reason is None
            assert result.reply == "I can hear you!"
            assert result.model == "hermes-agent"

    @pytest.mark.asyncio
    async def test_complete_retry_on_timeout(self):
        """AC-HA-02: Retries 3x on timeout before failing."""
        from ..scripts import hermes_client
        hermes_client.HERMES_API_KEY = "test-key"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # Use minimal retry delays for test speed
            result = await complete(
                [{"role": "user", "content": "test"}],
                max_retries=3,
                retry_base_delay_s=0.01,  # 10ms for tests
            )

            assert result.failure_reason == "timeout"
            # Should have been called 4 times (initial + 3 retries)
            assert mock_instance.post.call_count == 4

    @pytest.mark.asyncio
    async def test_complete_http_error_no_retry(self):
        """AC-HA-04: HTTP errors (like 400) are not retried."""
        from ..scripts import hermes_client
        hermes_client.HERMES_API_KEY = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await complete([{"role": "user", "content": "test"}])

            assert result.failure_reason == "http_400"
            # Should only be called once (no retry for HTTP errors)
            assert mock_instance.post.call_count == 1

    @pytest.mark.asyncio
    async def test_complete_empty_response(self):
        """Returns failure when response has no content."""
        from ..scripts import hermes_client
        hermes_client.HERMES_API_KEY = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await complete([{"role": "user", "content": "test"}])

            assert result.failure_reason == "empty_response"

    @pytest.mark.asyncio
    async def test_complete_sends_agent_mode(self):
        """AC-HA-03: Sends agent_mode=True for hermes-agent model."""
        from ..scripts import hermes_client
        hermes_client.HERMES_API_KEY = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            # Use hermes-agent model explicitly to trigger agent_mode
            await complete(
                [{"role": "user", "content": "@hermes execute this command"}],
                model="hermes-agent"
            )

            # Check that agent_mode=True was sent
            call_args = mock_instance.post.call_args
            json_data = call_args.kwargs.get("json", {})
            assert json_data.get("agent_mode") is True
