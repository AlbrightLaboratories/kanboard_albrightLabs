"""Tests for worker_registry module."""
import pytest


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    from worker_registry.registry import reset_registry
    reset_registry()
    yield
    reset_registry()
