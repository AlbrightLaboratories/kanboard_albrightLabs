"""
Memory Client - Interface to hermes-memory service for CoT persistence.

Stores and recalls:
- Chain of Thought (CoT) entries per task
- Progress updates
- Work history for context
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import httpx

logger = logging.getLogger(__name__)

# hermes-memory service URL
HERMES_MEMORY_URL = os.getenv(
    "HERMES_MEMORY_URL",
    "http://hermes-memory.hermes-tools.svc.cluster.local:8080"
)

# Memory types
MEMORY_TYPE_COT = "chain_of_thought"
MEMORY_TYPE_PROGRESS = "progress"
MEMORY_TYPE_ACTION = "action"


class MemoryClient:
    """
    Interface to hermes-memory for persistent Chain of Thought.

    Enables Hermes to:
    - Store thoughts/reasoning as work progresses
    - Recall previous context when resuming work
    - Track progress through tasks
    """

    def __init__(self, base_url: str = HERMES_MEMORY_URL, timeout: float = 10.0):
        """
        Initialize MemoryClient.

        Args:
            base_url: hermes-memory service URL
            timeout: Request timeout in seconds
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def store_thought(
        self,
        task_id: int,
        thought: str,
        phase: str = "execution",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store a Chain of Thought entry.

        Args:
            task_id: Kanboard task ID
            thought: The thought/reasoning to store
            phase: Work phase (planning, execution, review)
            metadata: Additional context

        Returns:
            True if stored successfully
        """
        try:
            payload = {
                "task_id": task_id,
                "type": MEMORY_TYPE_COT,
                "content": thought,
                "metadata": {
                    "agent": "hermes",
                    "phase": phase,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **(metadata or {}),
                },
            }

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/memories",
                    json=payload,
                )

                if response.status_code in (200, 201):
                    logger.debug(f"Stored thought for task {task_id}")
                    return True
                else:
                    logger.warning(
                        f"Failed to store thought: {response.status_code} {response.text}"
                    )
                    return False

        except Exception as e:
            logger.warning(f"Error storing thought for task {task_id}: {e}")
            return False

    async def recall_thoughts(
        self,
        task_id: int,
        limit: int = 10,
        memory_type: str = MEMORY_TYPE_COT,
    ) -> List[str]:
        """
        Recall previous thoughts for context.

        Args:
            task_id: Kanboard task ID
            limit: Maximum number of thoughts to retrieve
            memory_type: Type of memory to recall

        Returns:
            List of thought strings (most recent last)
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"{self._base_url}/memories",
                    params={
                        "task_id": task_id,
                        "type": memory_type,
                        "limit": limit,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    memories = data if isinstance(data, list) else data.get("memories", [])
                    return [m.get("content", "") for m in memories if m.get("content")]
                else:
                    logger.debug(f"No memories found for task {task_id}")
                    return []

        except Exception as e:
            logger.warning(f"Error recalling thoughts for task {task_id}: {e}")
            return []

    async def store_progress(
        self,
        task_id: int,
        progress: int,
        message: str,
    ) -> bool:
        """
        Store a progress update.

        Args:
            task_id: Kanboard task ID
            progress: Progress percentage (0-100)
            message: Progress description

        Returns:
            True if stored successfully
        """
        return await self.store_thought(
            task_id=task_id,
            thought=f"[{progress}%] {message}",
            phase="progress",
            metadata={"progress": progress},
        )

    async def store_action(
        self,
        task_id: int,
        action: str,
        result: str,
    ) -> bool:
        """
        Store an action taken by Hermes.

        Args:
            task_id: Kanboard task ID
            action: Action description (e.g., "Moved to In Progress")
            result: Action result

        Returns:
            True if stored successfully
        """
        try:
            payload = {
                "task_id": task_id,
                "type": MEMORY_TYPE_ACTION,
                "content": f"{action}: {result}",
                "metadata": {
                    "agent": "hermes",
                    "action": action,
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/memories",
                    json=payload,
                )
                return response.status_code in (200, 201)

        except Exception as e:
            logger.warning(f"Error storing action for task {task_id}: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if hermes-memory is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    def format_context(self, thoughts: List[str], max_chars: int = 2000) -> str:
        """
        Format recalled thoughts as context for prompts.

        Args:
            thoughts: List of previous thoughts
            max_chars: Maximum characters to include

        Returns:
            Formatted context string
        """
        if not thoughts:
            return ""

        context = "## Previous Work on This Task\n\n"
        total_len = len(context)

        for i, thought in enumerate(thoughts, 1):
            entry = f"{i}. {thought}\n"
            if total_len + len(entry) > max_chars:
                context += "... (earlier context truncated)\n"
                break
            context += entry
            total_len += len(entry)

        return context
