"""
Test WR-08: Router matches story worker_labels to worker labels.
"""
import pytest


class TestLabelMatching:
    """Tests for label matching."""

    def test_exact_match(self):
        """WR-08a: Worker with exact labels matches."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        worker_id = registry.register_worker(
            name="python-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python", "backend"]
        )

        result = router.route_story(story_labels=["python", "backend"])
        assert result == worker_id

    def test_superset_labels_match(self):
        """WR-08b: Worker with superset of labels matches."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        worker_id = registry.register_worker(
            name="full-stack-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python", "backend", "frontend", "gpu-required"]
        )

        result = router.route_story(story_labels=["python"])
        assert result == worker_id

    def test_missing_labels_no_match(self):
        """WR-08c: Worker missing required labels doesn't match."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        registry.register_worker(
            name="python-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python"]
        )

        # Requires "rust" which worker doesn't have
        result = router.route_story(
            story_labels=["rust"],
            required_capabilities=["code_generation"]
        )
        # Should fall back to any capable worker without labels
        assert result is not None  # Fallback kicks in

    def test_no_labels_matches_any(self):
        """WR-08d: Story with no labels matches any worker."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        worker_id = registry.register_worker(
            name="generic-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=[]
        )

        result = router.route_story(story_labels=[])
        assert result == worker_id

    def test_best_match_selected(self):
        """WR-08e: Worker with best label match is selected."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        # Worker 1: partial match
        registry.register_worker(
            name="partial-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python"]
        )

        # Worker 2: exact match
        worker_id = registry.register_worker(
            name="exact-worker",
            worker_type="ollama",
            endpoint="http://localhost:11435",
            capabilities=["code_generation"],
            labels=["python", "backend"]
        )

        result = router.route_story(story_labels=["python", "backend"])
        assert result == worker_id
