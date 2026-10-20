"""Tests for maestro_api module."""
import pytest


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    from maestro_api.server import reset_maestro
    reset_maestro()
    yield
    reset_maestro()
