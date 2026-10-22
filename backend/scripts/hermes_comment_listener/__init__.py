"""
Hermes Comment Listener Module

Polls Kanboard for new comments mentioning @hermes and posts responses.
Runs as a Kubernetes deployment in hr-project-tracking namespace.
"""

from .scripts.comment_poller import CommentPoller
from .scripts.comment_tracker import CommentTracker

__all__ = [
    "CommentPoller",
    "CommentTracker",
]
