"""
Completion Detector - Detect task completion signals in Hermes responses.

When Hermes indicates work is complete, the task moves to Validation/Review.
NOTE: Tasks are NEVER moved to Done automatically - only humans do that.

Workflow:
- Backlog → In Progress (when @hermes starts work)
- In Progress → Validation (when Hermes says work is complete)
- Validation → Done (human only)
"""
from __future__ import annotations

import re
import logging
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskAction(Enum):
    """Actions Hermes can take on a task."""
    START_WORK = "start_work"        # Move to In Progress
    SUBMIT_FOR_REVIEW = "submit"     # Move to Validation/Review
    REQUEST_INFO = "request_info"    # Stay in current column, need input
    CONTINUE_WORK = "continue"       # Stay in In Progress
    NONE = "none"                    # No action needed


@dataclass
class DetectionResult:
    """Result of completion detection."""
    action: TaskAction
    confidence: float  # 0.0 - 1.0
    reason: str


class CompletionDetector:
    """
    Detect task completion signals in Hermes responses.

    Analyzes response text to determine if:
    - Work has been started (move to In Progress)
    - Work is complete and ready for review (move to Validation)
    - More information is needed (stay in place)
    """

    # Signals that work is starting
    START_SIGNALS = [
        r"(?:i am|i'm|i will|let me) (?:start|begin|work)",
        r"starting (?:work|task|implementation)",
        r"beginning (?:work|task|implementation)",
        r"picking up this task",
        r"claiming this (?:task|story)",
    ]

    # Signals that work is complete and ready for validation
    COMPLETION_SIGNALS = [
        r"(?:task|work|implementation|feature) (?:is )?(?:complete|completed|done|finished)",
        r"(?:i have|i've) (?:completed|finished|done)",
        r"ready for (?:review|validation|testing|qa)",
        r"submitting for (?:review|validation)",
        r"please (?:review|validate|test|check)",
        r"moving to (?:review|validation)",
        r"implementation (?:is )?(?:complete|ready)",
        r"all (?:changes|updates) (?:are )?(?:complete|done)",
        r"✅.*(?:complete|done|ready)",
    ]

    # Signals that more info is needed
    INFO_NEEDED_SIGNALS = [
        r"(?:i need|need|require|please provide)",
        r"(?:can you|could you) (?:clarify|explain|provide)",
        r"what (?:do you|should|would)",
        r"which (?:option|approach|method)",
        r"before i (?:can|proceed|continue)",
        r"waiting for (?:input|clarification|info)",
    ]

    # Signals that work is continuing
    CONTINUE_SIGNALS = [
        r"(?:still|currently) (?:working|implementing)",
        r"(?:in progress|ongoing)",
        r"working on it",
        r"will continue",
        r"next step",
    ]

    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize CompletionDetector.

        Args:
            confidence_threshold: Minimum confidence to trigger action
        """
        self._threshold = confidence_threshold
        self._start_patterns = [re.compile(p, re.IGNORECASE) for p in self.START_SIGNALS]
        self._completion_patterns = [re.compile(p, re.IGNORECASE) for p in self.COMPLETION_SIGNALS]
        self._info_patterns = [re.compile(p, re.IGNORECASE) for p in self.INFO_NEEDED_SIGNALS]
        self._continue_patterns = [re.compile(p, re.IGNORECASE) for p in self.CONTINUE_SIGNALS]

    def _count_matches(self, text: str, patterns: List[re.Pattern]) -> int:
        """Count how many patterns match in text."""
        return sum(1 for p in patterns if p.search(text))

    def detect(self, response_text: str) -> DetectionResult:
        """
        Analyze Hermes response to detect task action.

        Args:
            response_text: The Hermes response text

        Returns:
            DetectionResult with action, confidence, and reason
        """
        if not response_text:
            return DetectionResult(TaskAction.NONE, 0.0, "Empty response")

        text = response_text.lower()

        # Count matches for each category
        start_matches = self._count_matches(text, self._start_patterns)
        completion_matches = self._count_matches(text, self._completion_patterns)
        info_matches = self._count_matches(text, self._info_patterns)
        continue_matches = self._count_matches(text, self._continue_patterns)

        # Calculate confidences
        total_patterns = max(
            len(self._start_patterns),
            len(self._completion_patterns),
            len(self._info_patterns),
            len(self._continue_patterns),
        )

        start_conf = min(start_matches / 3, 1.0)  # 3 matches = 100%
        completion_conf = min(completion_matches / 2, 1.0)  # 2 matches = 100%
        info_conf = min(info_matches / 2, 1.0)
        continue_conf = min(continue_matches / 2, 1.0)

        # Priority: completion > info_needed > continue > start
        if completion_conf >= self._threshold:
            logger.info(f"Detected completion signal (confidence: {completion_conf:.2f})")
            return DetectionResult(
                TaskAction.SUBMIT_FOR_REVIEW,
                completion_conf,
                "Work appears complete, moving to validation"
            )

        if info_conf >= self._threshold:
            logger.info(f"Detected info request (confidence: {info_conf:.2f})")
            return DetectionResult(
                TaskAction.REQUEST_INFO,
                info_conf,
                "More information needed before proceeding"
            )

        if continue_conf >= self._threshold:
            logger.info(f"Detected work in progress (confidence: {continue_conf:.2f})")
            return DetectionResult(
                TaskAction.CONTINUE_WORK,
                continue_conf,
                "Work is ongoing"
            )

        if start_conf >= self._threshold:
            logger.info(f"Detected work starting (confidence: {start_conf:.2f})")
            return DetectionResult(
                TaskAction.START_WORK,
                start_conf,
                "Starting work on task"
            )

        return DetectionResult(TaskAction.NONE, 0.0, "No clear action detected")

    def should_move_to_in_progress(self, response_text: str) -> bool:
        """Check if task should move to In Progress."""
        result = self.detect(response_text)
        return result.action == TaskAction.START_WORK

    def should_submit_for_review(self, response_text: str) -> bool:
        """Check if task should move to Validation/Review."""
        result = self.detect(response_text)
        return result.action == TaskAction.SUBMIT_FOR_REVIEW

    def needs_more_info(self, response_text: str) -> bool:
        """Check if Hermes needs more information."""
        result = self.detect(response_text)
        return result.action == TaskAction.REQUEST_INFO
