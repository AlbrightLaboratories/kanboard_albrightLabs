"""
Health Monitor

Monitors worker health via heartbeats and marks unresponsive workers offline.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class HealthMonitor:
    """Monitors worker health via heartbeats."""

    def __init__(self, registry: "WorkerRegistry"):
        """Initialize with a worker registry."""
        self._registry = registry
        self._heartbeat_interval = 30  # seconds
        self._max_missed = 3

    def heartbeat(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        Record heartbeat for a worker.

        Returns:
            Worker status info or None if not found
        """
        worker = self._registry.get_worker(worker_id)
        if not worker:
            return None

        # Update heartbeat timestamp
        worker["last_heartbeat"] = time.time()
        worker["missed_heartbeats"] = 0

        # Reactivate if was offline due to missed heartbeats
        if worker["status"] == "offline":
            worker["status"] = "active"

        return {
            "status": worker["status"],
            "active_stories": worker["active_stories"],
            "last_heartbeat": worker["last_heartbeat"]
        }

    def check_workers(self, timeout_seconds: Optional[int] = None) -> List[str]:
        """
        Check all workers for missed heartbeats.

        Workers with 3+ missed heartbeats are marked offline.

        Returns:
            List of worker IDs that were marked offline
        """
        if timeout_seconds is None:
            timeout_seconds = self._heartbeat_interval

        now = time.time()
        marked_offline = []

        for worker in self._registry.list_workers():
            if worker["status"] == "offline":
                continue

            time_since_heartbeat = now - worker["last_heartbeat"]
            missed = int(time_since_heartbeat / timeout_seconds)

            if missed > 0:
                worker["missed_heartbeats"] = missed
                if missed >= self._max_missed:
                    self._registry.deactivate_worker(worker["worker_id"])
                    marked_offline.append(worker["worker_id"])

        return marked_offline

    def get_worker_health(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed health info for a worker.

        Returns:
            Health info or None if not found
        """
        worker = self._registry.get_worker(worker_id)
        if not worker:
            return None

        now = time.time()
        time_since_heartbeat = now - worker["last_heartbeat"]

        return {
            "worker_id": worker_id,
            "status": worker["status"],
            "last_heartbeat": worker["last_heartbeat"],
            "seconds_since_heartbeat": int(time_since_heartbeat),
            "missed_heartbeats": worker["missed_heartbeats"],
            "active_stories": worker["active_stories"],
            "max_concurrent": worker["max_concurrent"],
            "healthy": worker["status"] == "active" and worker["missed_heartbeats"] < self._max_missed
        }

    def set_heartbeat_interval(self, seconds: int) -> None:
        """Set heartbeat interval (for testing)."""
        self._heartbeat_interval = seconds

    def set_max_missed(self, count: int) -> None:
        """Set max missed heartbeats before offline (for testing)."""
        self._max_missed = count
