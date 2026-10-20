"""
Label Matcher

Matches story worker labels to worker labels for routing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set


class LabelMatcher:
    """Matches story labels to worker labels."""

    def match_labels(
        self,
        story_labels: List[str],
        worker_labels: List[str]
    ) -> bool:
        """
        Check if worker labels satisfy story requirements.

        A worker matches if it has ALL required story labels.

        Returns:
            True if worker matches all story labels
        """
        if not story_labels:
            return True  # No requirements = any worker matches

        story_set = set(story_labels)
        worker_set = set(worker_labels)

        return story_set.issubset(worker_set)

    def score_match(
        self,
        story_labels: List[str],
        worker_labels: List[str]
    ) -> int:
        """
        Score how well worker labels match story requirements.

        Higher score = better match.
        Returns -1 if worker doesn't have all required labels.

        Returns:
            Match score or -1 if not a match
        """
        if not self.match_labels(story_labels, worker_labels):
            return -1

        if not story_labels:
            return 0  # No requirements

        # Score = number of matching labels
        story_set = set(story_labels)
        worker_set = set(worker_labels)

        return len(story_set.intersection(worker_set))

    def filter_workers(
        self,
        workers: List[Dict[str, Any]],
        story_labels: List[str],
        preferred_worker: str = None,
        excluded_workers: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter workers by story labels and preferences.

        Returns workers sorted by match score (best first).

        Args:
            workers: List of worker dicts
            story_labels: Required labels
            preferred_worker: Worker ID to prioritize
            excluded_workers: Worker IDs to exclude

        Returns:
            Filtered and sorted list of matching workers
        """
        excluded = set(excluded_workers or [])
        matching = []

        for worker in workers:
            worker_id = worker["worker_id"]

            # Skip excluded workers
            if worker_id in excluded:
                continue

            # Check label match
            score = self.score_match(story_labels, worker.get("labels", []))
            if score >= 0:
                matching.append((score, worker))

        # Sort by score (descending), then by worker_id for consistency
        matching.sort(key=lambda x: (-x[0], x[1]["worker_id"]))

        # Move preferred worker to front if present
        if preferred_worker:
            result = []
            preferred = None
            for score, worker in matching:
                if worker["worker_id"] == preferred_worker:
                    preferred = worker
                else:
                    result.append(worker)
            if preferred:
                result.insert(0, preferred)
            return result

        return [w for _, w in matching]
