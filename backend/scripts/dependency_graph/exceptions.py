"""
Dependency Graph Exceptions
"""


class CircularDependencyError(Exception):
    """Raised when adding a dependency would create a cycle."""

    def __init__(self, message: str = "Circular dependency detected"):
        self.message = message
        super().__init__(self.message)
