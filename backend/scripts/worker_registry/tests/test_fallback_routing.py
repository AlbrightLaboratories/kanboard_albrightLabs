"""
Test WR-11: Router falls back to any capable worker if no label match.
"""
import pytest


class TestFallbackRouting:
    """Tests for fallback routing."""

    def test_fallback_when_no_label_match(self):
        """WR-11a: Falls back to any capable worker when no labels match."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        # Worker with different labels
        worker_id = registry.register_worker(
            name="generic-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["javascript"]
        )

        # Request python worker, but should fall back to generic
        result = router.route_story(
            story_labels=["python"],
            required_capabilities=["code_generation"]
        )
        assert result == worker_id

    def test_fallback_respects_capabilities(self):
        """WR-11b: Fallback still requires matching capabilities."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        # Worker without required capability
        registry.register_worker(
            name="no-terminal",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=[]
        )

        # Worker with required capability
        capable_id = registry.register_worker(
            name="with-terminal",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation", "terminal_execution"],
            labels=[]
        )

        result = router.route_story(
            story_labels=["python"],
            required_capabilities=["terminal_execution"]
        )
        assert result == capable_id

    def test_fallback_excludes_blocked(self):
        """WR-11c: Fallback respects exclusion list."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        excluded_id = registry.register_worker(
            name="excluded",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["javascript"]
        )

        allowed_id = registry.register_worker(
            name="allowed",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            labels=["rust"]
        )

        result = router.route_story(
            story_labels=["python"],  # Neither has python
            excluded_workers=[excluded_id]
        )
        assert result == allowed_id

    def test_no_fallback_no_workers(self):
        """WR-11d: Returns None when no workers available."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        result = router.route_story(story_labels=["python"])
        assert result is None
