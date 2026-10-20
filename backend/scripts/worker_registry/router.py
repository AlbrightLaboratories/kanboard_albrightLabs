"""
Worker Router

Routes stories to appropriate workers based on labels, preferences, and load.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .labels import LabelMatcher


class WorkerRouter:
    """Routes stories to workers based on labels and capacity."""

    def __init__(self, registry: "WorkerRegistry"):
        """Initialize with a worker registry."""
        self._registry = registry
        self._matcher = LabelMatcher()

    def route_story(
        self,
        story_labels: List[str] = None,
        preferred_worker: str = None,
        excluded_workers: List[str] = None,
        gpu_required: bool = False,
        gpu_vram_min: int = 0,
        required_capabilities: List[str] = None
    ) -> Optional[str]:
        """
        Route a story to an appropriate worker.

        Args:
            story_labels: Required worker labels
            preferred_worker: Worker ID to prioritize
            excluded_workers: Worker IDs to exclude
            gpu_required: Story requires GPU
            gpu_vram_min: Minimum VRAM in GB
            required_capabilities: Required worker capabilities

        Returns:
            Worker ID or None if no suitable worker found
        """
        # Get available workers (active with capacity)
        workers = self._registry.get_available_workers()

        if not workers:
            return None

        # Filter by capabilities
        if required_capabilities:
            workers = self._filter_by_capabilities(workers, required_capabilities)

        # Filter by GPU requirements
        if gpu_required or gpu_vram_min > 0:
            workers = self._filter_by_gpu(workers, gpu_required, gpu_vram_min)

        if not workers:
            return None

        # Filter by labels and preferences
        workers = self._matcher.filter_workers(
            workers,
            story_labels or [],
            preferred_worker,
            excluded_workers
        )

        if not workers:
            # Fallback: try any capable worker without label requirements
            fallback = self._registry.get_available_workers()
            if required_capabilities:
                fallback = self._filter_by_capabilities(fallback, required_capabilities)
            if gpu_required or gpu_vram_min > 0:
                fallback = self._filter_by_gpu(fallback, gpu_required, gpu_vram_min)
            if excluded_workers:
                fallback = [w for w in fallback if w["worker_id"] not in excluded_workers]

            if fallback:
                # Use load balancing for fallback
                return self._select_by_load(fallback)
            return None

        # Check for preferred worker first
        if preferred_worker:
            for worker in workers:
                if worker["worker_id"] == preferred_worker:
                    return preferred_worker

        # Use load balancing
        return self._select_by_load(workers)

    def _filter_by_capabilities(
        self,
        workers: List[Dict[str, Any]],
        required: List[str]
    ) -> List[Dict[str, Any]]:
        """Filter workers by required capabilities."""
        required_set = set(required)
        return [
            w for w in workers
            if required_set.issubset(set(w.get("capabilities", [])))
        ]

    def _filter_by_gpu(
        self,
        workers: List[Dict[str, Any]],
        gpu_required: bool,
        gpu_vram_min: int
    ) -> List[Dict[str, Any]]:
        """Filter workers by GPU requirements."""
        result = []
        for worker in workers:
            if gpu_required and not worker.get("gpu_required", False):
                continue
            if gpu_vram_min > 0 and worker.get("gpu_vram_min", 0) < gpu_vram_min:
                continue
            result.append(worker)
        return result

    def _select_by_load(self, workers: List[Dict[str, Any]]) -> str:
        """
        Select worker with lowest current load.

        Uses least-connections algorithm.
        """
        if not workers:
            return None

        # Sort by active stories (ascending), then by worker_id for consistency
        workers.sort(key=lambda w: (w["active_stories"], w["worker_id"]))
        return workers[0]["worker_id"]
