"""
Hermes Comment Listener - Main Entry Point

Runs the polling loop that detects @hermes mentions in Kanboard comments
and posts responses from the Hermes agent.

Usage:
    python -m scripts.hermes_comment_listener.orchestration

Environment Variables:
    KANBOARD_URL: Kanboard JSON-RPC endpoint
    KANBOARD_USERNAME: API username
    KANBOARD_API_TOKEN: API token
    HERMES_URL: Hermes agent URL
    HERMES_API_KEY: Hermes API key
    REDIS_URL: Redis URL for persistence (optional)
    POLL_INTERVAL_SECONDS: Seconds between polls (default: 5)
"""
import asyncio
import logging
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Reduce noise from httpx
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


async def main():
    """Main entry point for the comment listener."""
    from .scripts.comment_poller import CommentPoller
    from .scripts.comment_tracker import CommentTracker

    logger.info("=" * 60)
    logger.info("Hermes Comment Listener Starting")
    logger.info("=" * 60)

    # Log configuration
    logger.info(f"KANBOARD_URL: {os.getenv('KANBOARD_URL', 'not set')}")
    logger.info(f"HERMES_URL: {os.getenv('HERMES_URL', 'not set')}")
    logger.info(f"POLL_INTERVAL: {os.getenv('POLL_INTERVAL_SECONDS', '5')}s")
    logger.info(f"REDIS_URL: {'set' if os.getenv('REDIS_URL') else 'not set (using memory)'}")

    # Validate required config
    if not os.getenv("KANBOARD_API_TOKEN"):
        logger.error("KANBOARD_API_TOKEN not set!")
        sys.exit(1)

    if not os.getenv("HERMES_API_KEY"):
        logger.warning("HERMES_API_KEY not set - Hermes calls will fail")

    # Initialize components
    tracker = CommentTracker()
    poller = CommentPoller(tracker=tracker)

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, poller.stop)

    logger.info("Starting polling loop...")
    logger.info("Press Ctrl+C to stop")
    logger.info("-" * 60)

    try:
        await poller.run()
    except asyncio.CancelledError:
        logger.info("Polling cancelled")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

    logger.info("Hermes Comment Listener stopped")


if __name__ == "__main__":
    asyncio.run(main())
