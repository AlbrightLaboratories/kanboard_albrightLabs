"""Tests for skill_framework module."""
import pytest


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    from skill_framework.skill_runner import reset_skill_state
    reset_skill_state()
    yield
    reset_skill_state()
