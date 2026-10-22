"""
Comment Tracker - Tracks processed comment IDs to avoid duplicates.

Uses Redis for persistence across restarts, with in-memory fallback
for development/testing.
"""
from __future__ import annotations

import logging
import os
from typing import Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "")

# How long to keep processed comment IDs (7 days default)
COMMENT_TTL_DAYS = int(os.getenv("COMMENT_TTL_DAYS", "7"))


class CommentTracker:
    """
    Tracks which comments have been processed.

    Uses Redis when available for persistence across restarts.
    Falls back to in-memory set when Redis is unavailable.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        key_prefix: str = "hermes:processed_comments:",
    ):
        """
        Initialize the comment tracker.

        Args:
            redis_url: Redis connection URL (optional)
            key_prefix: Prefix for Redis keys
        """
        self._redis_url = redis_url or REDIS_URL
        self._key_prefix = key_prefix
        self._redis_client = None
        self._memory_set: Set[str] = set()
        self._use_redis = bool(self._redis_url)

        if self._use_redis:
            try:
                import redis
                self._redis_client = redis.from_url(self._redis_url)
                # Test connection
                self._redis_client.ping()
                logger.info("CommentTracker: Using Redis for persistence")
            except Exception as e:
                logger.warning(f"CommentTracker: Redis unavailable ({e}), using in-memory")
                self._use_redis = False

    def _redis_key(self, comment_id: str) -> str:
        """Generate Redis key for a comment ID."""
        return f"{self._key_prefix}{comment_id}"

    def is_processed(self, comment_id: str) -> bool:
        """
        Check if a comment has already been processed.

        Args:
            comment_id: The comment ID to check

        Returns:
            True if the comment has been processed
        """
        if self._use_redis and self._redis_client:
            try:
                return self._redis_client.exists(self._redis_key(comment_id)) > 0
            except Exception as e:
                logger.warning(f"Redis check failed: {e}")
                return comment_id in self._memory_set
        return comment_id in self._memory_set

    def mark_processed(self, comment_id: str) -> None:
        """
        Mark a comment as processed.

        Args:
            comment_id: The comment ID to mark
        """
        if self._use_redis and self._redis_client:
            try:
                ttl_seconds = COMMENT_TTL_DAYS * 24 * 60 * 60
                self._redis_client.setex(
                    self._redis_key(comment_id),
                    ttl_seconds,
                    datetime.utcnow().isoformat(),
                )
                logger.debug(f"Marked comment {comment_id} as processed (Redis)")
            except Exception as e:
                logger.warning(f"Redis mark failed: {e}")
                self._memory_set.add(comment_id)
        else:
            self._memory_set.add(comment_id)
            logger.debug(f"Marked comment {comment_id} as processed (memory)")

    def mark_processing(self, comment_id: str) -> bool:
        """
        Atomically mark a comment as being processed (processing lock).

        Returns True if the lock was acquired, False if already processing.
        This prevents duplicate processing in concurrent scenarios.

        Args:
            comment_id: The comment ID to lock

        Returns:
            True if lock acquired, False if already locked
        """
        lock_key = f"{self._key_prefix}lock:{comment_id}"

        if self._use_redis and self._redis_client:
            try:
                # Use SETNX for atomic lock - 5 minute TTL for processing
                acquired = self._redis_client.set(
                    lock_key,
                    datetime.utcnow().isoformat(),
                    nx=True,  # Only set if not exists
                    ex=300,   # 5 minute TTL
                )
                return bool(acquired)
            except Exception as e:
                logger.warning(f"Redis lock failed: {e}")
                # Fall through to memory

        # In-memory fallback
        if comment_id in self._memory_set:
            return False
        self._memory_set.add(comment_id)
        return True

    def clear_all(self) -> None:
        """
        Clear all tracked comments (for testing).
        """
        self._memory_set.clear()
        if self._use_redis and self._redis_client:
            try:
                # Get all keys with our prefix and delete them
                keys = self._redis_client.keys(f"{self._key_prefix}*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

    @property
    def count(self) -> int:
        """Get count of tracked comments (for monitoring)."""
        if self._use_redis and self._redis_client:
            try:
                keys = self._redis_client.keys(f"{self._key_prefix}*")
                return len(keys)
            except Exception:
                pass
        return len(self._memory_set)
