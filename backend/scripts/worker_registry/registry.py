"""
Worker Registry

Manages LLM worker registration, storage, and lifecycle.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional


# Global state (for singleton pattern in testing)
_registry: Optional["WorkerRegistry"] = None


def get_registry() -> "WorkerRegistry":
    """Get or create WorkerRegistry instance."""
    global _registry
    if _registry is None:
        _registry = WorkerRegistry()
    return _registry


def reset_registry() -> None:
    """Reset WorkerRegistry instance (for testing)."""
    global _registry
    _registry = None


class WorkerRegistry:
    """Registry for custom LLM workers."""

    def __init__(self):
        """Initialize empty registry."""
        self._workers: Dict[str, Dict[str, Any]] = {}

    def register_worker(
        self,
        name: str,
        worker_type: str,
        endpoint: str,
        capabilities: List[str],
        labels: Optional[List[str]] = None,
        auth_method: str = "none",
        auth_credentials: Optional[str] = None,
        gpu_required: bool = False,
        gpu_vram_min: int = 0,
        max_concurrent: int = 1,
        terminal_enabled: bool = False,
        terminal_sandbox: str = "docker"
    ) -> str:
        """
        Register a new LLM worker.

        Returns:
            New worker ID
        """
        worker_id = str(uuid.uuid4())
        self._workers[worker_id] = {
            "worker_id": worker_id,
            "name": name,
            "type": worker_type,
            "endpoint": endpoint,
            "capabilities": capabilities,
            "labels": labels or [],
            "auth_method": auth_method,
            "auth_credentials": auth_credentials,
            "gpu_required": gpu_required,
            "gpu_vram_min": gpu_vram_min,
            "max_concurrent": max_concurrent,
            "terminal_enabled": terminal_enabled,
            "terminal_sandbox": terminal_sandbox,
            "status": "active",
            "active_stories": 0,
            "last_heartbeat": time.time(),
            "created_at": time.time(),
            "missed_heartbeats": 0
        }
        return worker_id

    def get_worker(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get worker by ID."""
        return self._workers.get(worker_id)

    def list_workers(self) -> List[Dict[str, Any]]:
        """List all workers with current status."""
        return list(self._workers.values())

    def update_worker(
        self,
        worker_id: str,
        **updates: Any
    ) -> bool:
        """
        Update worker configuration.

        Returns:
            True if updated, False if worker not found
        """
        if worker_id not in self._workers:
            return False

        # Only update allowed fields
        allowed_fields = {
            "name", "labels", "capabilities", "endpoint",
            "auth_method", "auth_credentials", "gpu_required",
            "gpu_vram_min", "max_concurrent", "terminal_enabled",
            "terminal_sandbox"
        }

        for key, value in updates.items():
            if key in allowed_fields:
                self._workers[worker_id][key] = value

        return True

    def deactivate_worker(self, worker_id: str) -> bool:
        """
        Mark worker as offline, stop routing to it.

        Returns:
            True if deactivated, False if worker not found
        """
        if worker_id not in self._workers:
            return False

        self._workers[worker_id]["status"] = "offline"
        return True

    def activate_worker(self, worker_id: str) -> bool:
        """
        Mark worker as active.

        Returns:
            True if activated, False if worker not found
        """
        if worker_id not in self._workers:
            return False

        self._workers[worker_id]["status"] = "active"
        self._workers[worker_id]["missed_heartbeats"] = 0
        return True

    def delete_worker(self, worker_id: str) -> Optional[List[int]]:
        """
        Remove worker and return any queued story IDs for reassignment.

        Returns:
            List of story IDs that were assigned, or None if not found
        """
        if worker_id not in self._workers:
            return None

        # Get assigned stories before deletion
        assigned_stories = self._workers[worker_id].get("assigned_stories", [])
        del self._workers[worker_id]
        return assigned_stories

    def assign_story(self, worker_id: str, story_id: int) -> bool:
        """
        Assign a story to a worker.

        Returns:
            True if assigned, False if worker not found or at capacity
        """
        if worker_id not in self._workers:
            return False

        worker = self._workers[worker_id]
        if worker["active_stories"] >= worker["max_concurrent"]:
            return False

        if "assigned_stories" not in worker:
            worker["assigned_stories"] = []

        worker["assigned_stories"].append(story_id)
        worker["active_stories"] += 1
        return True

    def release_story(self, worker_id: str, story_id: int) -> bool:
        """
        Release a story from a worker.

        Returns:
            True if released, False if worker/story not found
        """
        if worker_id not in self._workers:
            return False

        worker = self._workers[worker_id]
        if "assigned_stories" not in worker:
            return False

        if story_id not in worker["assigned_stories"]:
            return False

        worker["assigned_stories"].remove(story_id)
        worker["active_stories"] -= 1
        return True

    def get_active_workers(self) -> List[Dict[str, Any]]:
        """Get all workers with status 'active'."""
        return [w for w in self._workers.values() if w["status"] == "active"]

    def get_available_workers(self) -> List[Dict[str, Any]]:
        """Get all active workers with capacity for more stories."""
        return [
            w for w in self._workers.values()
            if w["status"] == "active" and w["active_stories"] < w["max_concurrent"]
        ]
