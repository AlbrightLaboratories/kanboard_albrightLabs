"""
Hermes Client - Intelligent routing through corey-router with question classification.

Routes requests through corey-router for model selection:
- GENERAL questions → qwen3:7b (fast, cheap)
- CODING questions → qwen3-coder:30b (better reasoning)
- TOOL_REQUIRED → hermes-agent on Mac Mini (49 MCP tools)

Fallback chain: corey-router provides automatic fallback between providers.

Hermes on Mac Mini (172.100.10.21:8642) has:
- Terminal tool (runs shell commands)
- File tool (filesystem operations)
- GitHub access (Chief-of-staff read+write)
- 49 MCP tools total

Retry policy: On transient failures (timeout, connection error), retry
up to 3 times with exponential backoff (2s, 4s, 8s).

API contract: OpenAI `/v1/chat/completions` with optional Bearer auth.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import NamedTuple, Optional

import httpx

logger = logging.getLogger(__name__)


class HermesResult(NamedTuple):
    """Result from complete() with failure visibility and provider info."""
    reply: str
    model: str
    failure_reason: str | None = None  # None = success
    provider: str | None = None  # Which provider served the request


# Corey-router for intelligent model routing (preferred)
COREY_ROUTER_URL = os.getenv(
    "COREY_ROUTER_URL",
    "http://corey-router.corey-coder.svc.cluster.local:8081",
)

# Direct Mac Mini Hermes Gateway (fallback for tool-heavy requests)
HERMES_URL = os.getenv(
    "HERMES_URL",
    "http://172.100.10.21:8642",
)

# API key from the api_server platform config
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "")

# Feature flag: when false, Hermes calls are disabled
HERMES_ENABLED = os.getenv("HERMES_ENABLED", "1") == "1"

# Feature flag: use corey-router for intelligent routing (default: true)
USE_COREY_ROUTER = os.getenv("USE_COREY_ROUTER", "1") == "1"

# Timeout for calls. Tool execution needs longer timeout.
DEFAULT_TIMEOUT_S = float(os.getenv("DEFAULT_TIMEOUT_S", "60"))
HERMES_TIMEOUT_S = float(os.getenv("HERMES_TIMEOUT_S", "180"))

# Retry configuration for transient failures
HERMES_MAX_RETRIES = int(os.getenv("HERMES_MAX_RETRIES", "3"))
HERMES_RETRY_BASE_DELAY_S = float(os.getenv("HERMES_RETRY_BASE_DELAY_S", "2.0"))


def hermes_enabled() -> bool:
    """Check if Hermes is enabled and configured."""
    return HERMES_ENABLED and bool(HERMES_API_KEY)


def _corey_router_endpoint() -> str:
    """Get corey-router chat completions endpoint."""
    return f"{COREY_ROUTER_URL.rstrip('/')}/v1/chat/completions"


def _hermes_endpoint() -> str:
    """Get direct Hermes chat completions endpoint."""
    return f"{HERMES_URL.rstrip('/')}/v1/chat/completions"


def _health_endpoint() -> str:
    return f"{HERMES_URL.rstrip('/')}/health"


def _corey_router_health_endpoint() -> str:
    return f"{COREY_ROUTER_URL.rstrip('/')}/health"


def _parse_reply(data: dict) -> tuple[str, Optional[str]]:
    """
    Extract reply and provider from OpenAI response format.

    Returns:
        Tuple of (reply_content, provider_name)
    """
    provider = None

    # Extract provider from _meta if present (corey-router includes this)
    meta = data.get("_meta", {})
    if isinstance(meta, dict):
        provider = meta.get("provider")

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        msg = (choices[0] or {}).get("message") or {}
        content = msg.get("content")
        if content and isinstance(content, str):
            return content, provider
    return "", provider


async def health_check(timeout_s: float = 10.0) -> bool:
    """
    Check if the inference endpoint is reachable and healthy.

    Checks corey-router if USE_COREY_ROUTER is enabled, otherwise Hermes.

    Args:
        timeout_s: Timeout for health check request

    Returns:
        True if healthy, False otherwise
    """
    try:
        endpoint = _corey_router_health_endpoint() if USE_COREY_ROUTER else _health_endpoint()
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.get(endpoint)
            return r.status_code == 200
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return False


async def complete(
    messages: list[dict],
    model: str | None = None,
    timeout_s: float | None = None,
    max_retries: int = HERMES_MAX_RETRIES,
    retry_base_delay_s: float = HERMES_RETRY_BASE_DELAY_S,
    use_classification: bool = True,
) -> HermesResult:
    """
    Send messages to inference endpoint with intelligent model routing.

    When USE_COREY_ROUTER is enabled (default), routes through corey-router
    which provides:
    - Automatic model selection based on question classification
    - Provider fallback chain (ollama → spark_glm → vllm → hermes → claude)
    - Observability via _meta.provider in response

    When USE_COREY_ROUTER is disabled, routes directly to Hermes on Mac Mini.

    Args:
        messages: Chat messages in OpenAI format
        model: Model to use (if None, uses classification to select)
        timeout_s: Request timeout (None = auto based on model)
        max_retries: Maximum number of retry attempts
        retry_base_delay_s: Base delay for exponential backoff
        use_classification: If True and model is None, classify to select model

    Returns:
        HermesResult with reply, model, failure_reason, and provider
    """
    # Determine model if not specified
    effective_model = model
    if effective_model is None and use_classification:
        effective_model = _classify_and_select_model(messages)
    elif effective_model is None:
        effective_model = "hermes-agent"

    # Determine timeout based on model (tools need longer)
    if timeout_s is None:
        timeout_s = HERMES_TIMEOUT_S if effective_model == "hermes-agent" else DEFAULT_TIMEOUT_S

    # Determine endpoint
    if USE_COREY_ROUTER:
        endpoint = _corey_router_endpoint()
    else:
        endpoint = _hermes_endpoint()

    # Build headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "kanboard-hermes-adapter/2.0",
    }
    if HERMES_API_KEY:
        headers["Authorization"] = f"Bearer {HERMES_API_KEY}"

    last_error: str = ""

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                payload = {
                    "model": effective_model,
                    "messages": messages,
                    "stream": False,
                }
                # agent_mode only needed for hermes-agent (forces tool context)
                if effective_model == "hermes-agent":
                    payload["agent_mode"] = True

                r = await client.post(endpoint, headers=headers, json=payload)

                if r.status_code >= 300:
                    logger.warning(f"HTTP {r.status_code}: {r.text[:200]}")
                    return HermesResult("", effective_model, f"http_{r.status_code}", None)

                data = r.json()
                reply, provider = _parse_reply(data)

                if not reply:
                    logger.warning("Empty response received")
                    return HermesResult("", effective_model, "empty_response", provider)

                # Success — log provider and retry info
                if attempt > 0:
                    logger.info(f"Succeeded on attempt {attempt + 1}")
                logger.info(f"Response from provider: {provider or 'unknown'}, model: {effective_model}")

                return HermesResult(reply, effective_model, None, provider)

        except httpx.TimeoutException as e:
            last_error = "timeout"
            logger.warning(f"Timeout (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except httpx.ConnectError as e:
            last_error = f"connection_error: {e}"
            logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except httpx.HTTPError as e:
            last_error = f"http_error: {e}"
            logger.warning(f"HTTP error (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except ValueError as e:
            logger.error(f"JSON parse error: {e}")
            return HermesResult("", effective_model, f"parse_error: {e}", None)

        # Exponential backoff before retry
        if attempt < max_retries:
            delay = retry_base_delay_s * (2 ** attempt)
            logger.info(f"Retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)

    logger.error(f"Failed after {max_retries + 1} attempts: {last_error}")
    return HermesResult("", effective_model, last_error, None)


def _classify_and_select_model(messages: list[dict]) -> str:
    """
    Classify question and select appropriate model.

    Uses QuestionClassifier to analyze the last user message
    and ModelSelector to pick the optimal model.

    Returns:
        Model name string
    """
    from scripts.hermes_comment_listener.scripts.question_classifier import QuestionClassifier
    from scripts.hermes_comment_listener.scripts.model_selector import ModelSelector

    # Extract last user message for classification
    user_content = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_content = msg.get("content", "")
            break

    classifier = QuestionClassifier()
    selector = ModelSelector()

    question_type = classifier.classify(user_content)
    config = selector.select(question_type)

    logger.info(f"Classified as {question_type.value} → model: {config.model}")
    return config.model
