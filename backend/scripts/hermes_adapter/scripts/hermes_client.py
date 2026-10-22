"""
Hermes Client - OpenAI-compatible client for Mac Mini Hermes agent.

Hermes runs on Mac Mini (172.100.10.21:8642) with:
- Terminal tool (runs shell commands)
- File tool (filesystem operations)
- GitHub access (Chief-of-staff read+write)
- 49 MCP tools total

Retry policy: On transient failures (timeout, connection error), retry
up to 3 times with exponential backoff (2s, 4s, 8s). Mac Mini WiFi is unstable;
retries handle transient drops without failing the request.

API contract: OpenAI `/v1/chat/completions` with Bearer auth (HERMES_API_KEY).
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import NamedTuple

import httpx

logger = logging.getLogger(__name__)


class HermesResult(NamedTuple):
    """Result from Hermes complete() with failure visibility."""
    reply: str
    model: str
    failure_reason: str | None = None  # None = success


# Mac Mini Hermes Gateway
HERMES_URL = os.getenv(
    "HERMES_URL",
    "http://172.100.10.21:8642",
)

# API key from the api_server platform config
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "")

# Feature flag: when false, Hermes calls are disabled
HERMES_ENABLED = os.getenv("HERMES_ENABLED", "1") == "1"

# Timeout for Hermes calls. Hermes may run multiple tool iterations,
# so allow longer than direct LLM calls. Default 180s = 3 minutes.
HERMES_TIMEOUT_S = float(os.getenv("HERMES_TIMEOUT_S", "180"))

# Retry configuration for transient failures
HERMES_MAX_RETRIES = int(os.getenv("HERMES_MAX_RETRIES", "3"))
HERMES_RETRY_BASE_DELAY_S = float(os.getenv("HERMES_RETRY_BASE_DELAY_S", "2.0"))


def hermes_enabled() -> bool:
    """Check if Hermes is enabled and configured."""
    return HERMES_ENABLED and bool(HERMES_API_KEY)


def _endpoint() -> str:
    return f"{HERMES_URL.rstrip('/')}/v1/chat/completions"


def _health_endpoint() -> str:
    return f"{HERMES_URL.rstrip('/')}/health"


def _parse_reply(data: dict) -> str:
    """Extract reply from OpenAI response format."""
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        msg = (choices[0] or {}).get("message") or {}
        content = msg.get("content")
        if content and isinstance(content, str):
            return content
    return ""


async def health_check(timeout_s: float = 10.0) -> bool:
    """
    Check if Hermes is reachable and healthy.

    Args:
        timeout_s: Timeout for health check request

    Returns:
        True if Hermes is healthy, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.get(_health_endpoint())
            return r.status_code == 200
    except Exception as e:
        logger.warning(f"Hermes health check failed: {e}")
        return False


async def complete(
    messages: list[dict],
    model: str | None = None,
    timeout_s: float = HERMES_TIMEOUT_S,
    max_retries: int = HERMES_MAX_RETRIES,
    retry_base_delay_s: float = HERMES_RETRY_BASE_DELAY_S,
) -> HermesResult:
    """
    Send messages to Mac Mini Hermes and return HermesResult.

    Hermes handles tool execution internally via its ReAct loop. The model
    parameter selects the underlying model:
    - None or "hermes-agent" → default agent with full tool context
    - Other models → forwarded to corey-router

    Retry policy: On transient failures (timeout, connection error), retries
    up to max_retries times with exponential backoff.

    Args:
        messages: Chat messages in OpenAI format
        model: Model to use (default: hermes-agent)
        timeout_s: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_base_delay_s: Base delay for exponential backoff

    Returns:
        HermesResult with reply, model, and optional failure_reason
    """
    if not HERMES_API_KEY:
        logger.warning("Hermes API key not configured")
        return HermesResult("", "hermes", "no_api_key")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HERMES_API_KEY}",
        "User-Agent": "kanboard-hermes-adapter/1.0",
    }
    last_error: str = ""

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                effective_model = model if model else "hermes-agent"
                r = await client.post(
                    _endpoint(),
                    headers=headers,
                    json={
                        "model": effective_model,
                        "messages": messages,
                        "stream": False,
                        # agent_mode forces full tool context regardless of
                        # request content. Required for tool execution.
                        "agent_mode": True,
                    },
                )
                if r.status_code >= 300:
                    # HTTP errors are not retried (server explicitly rejected)
                    logger.warning(f"Hermes HTTP {r.status_code}: {r.text[:200]}")
                    return HermesResult("", "hermes", f"http_{r.status_code}")

                reply = _parse_reply(r.json())
                if not reply:
                    logger.warning("Hermes returned empty response")
                    return HermesResult("", "hermes", "empty_response")

                # Success — log if we needed retries
                if attempt > 0:
                    logger.info(f"Hermes succeeded on attempt {attempt + 1}")
                return HermesResult(reply, effective_model, None)

        except httpx.TimeoutException as e:
            last_error = "timeout"
            logger.warning(f"Hermes timeout (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except httpx.ConnectError as e:
            last_error = f"connection_error: {e}"
            logger.warning(f"Hermes connection error (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except httpx.HTTPError as e:
            last_error = f"http_error: {e}"
            logger.warning(f"Hermes HTTP error (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except ValueError as e:
            # JSON parse errors are not retried
            logger.error(f"Hermes JSON parse error: {e}")
            return HermesResult("", "hermes", f"parse_error: {e}")

        # Exponential backoff before retry (skip on last attempt)
        if attempt < max_retries:
            delay = retry_base_delay_s * (2 ** attempt)  # 2s, 4s, 8s
            logger.info(f"Retrying Hermes in {delay:.1f}s...")
            await asyncio.sleep(delay)

    # All retries exhausted
    logger.error(f"Hermes failed after {max_retries + 1} attempts: {last_error}")
    return HermesResult("", "hermes", last_error)
