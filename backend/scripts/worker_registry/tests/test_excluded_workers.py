"""
Test WR-10: Router excludes workers in excluded_workers.
"""
import pytest


class TestExcludedWorkers:
    """Tests for worker exclusion."""

    def test_excluded_workers_skipped(self):
        """WR-10a: Excluded workers are not selected."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        excluded_id = registry.register_worker(
            name="excluded-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python"]
        )

        allowed_id = registry.register_worker(
            name="allowed-worker",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            labels=["python"]
        )

        result = router.route_story(
            story_labels=["python"],
            excluded_workers=[excluded_id]
        )
        assert result == allowed_id

    def test_multiple_exclusions(self):
        """WR-10b: Multiple workers can be excluded."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        excluded_1 = registry.register_worker(
            name="excluded-1",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        excluded_2 = registry.register_worker(
            name="excluded-2",
            worker_type="ollama",
            endpoint="http://localhost:11435",
            capabilities=["code_generation"]
        )

        allowed_id = registry.register_worker(
            name="allowed",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"]
        )

        result = router.route_story(
            excluded_workers=[excluded_1, excluded_2]
        )
        assert result == allowed_id

    def test_no_workers_after_exclusion(self):
        """WR-10c: Returns None if all workers excluded."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        worker_id = registry.register_worker(
            name="only-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"]
        )

        result = router.route_story(excluded_workers=[worker_id])
        assert result is None

    def test_exclusion_combined_with_labels(self):
        """WR-10d: Exclusion works with label requirements."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        # Good labels but excluded
        excluded_id = registry.register_worker(
            name="excluded",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            labels=["python", "backend"]
        )

        # Good labels and not excluded
        allowed_id = registry.register_worker(
            name="allowed",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            labels=["python", "backend"]
        )

        result = router.route_story(
            story_labels=["python"],
            excluded_workers=[excluded_id]
        )
        assert result == allowed_id
