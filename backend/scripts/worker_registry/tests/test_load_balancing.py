"""
Test WR-12: Load balancer routes to worker with lowest active stories.
"""
import pytest


class TestLoadBalancing:
    """Tests for load balancing."""

    def test_routes_to_lowest_load(self):
        """WR-12a: Routes to worker with fewest active stories."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        busy_id = registry.register_worker(
            name="busy-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            max_concurrent=5
        )

        idle_id = registry.register_worker(
            name="idle-worker",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            max_concurrent=5
        )

        # Load up the first worker
        registry.assign_story(busy_id, 100)
        registry.assign_story(busy_id, 101)
        registry.assign_story(busy_id, 102)

        # idle_id has 0 stories, should be selected
        result = router.route_story()
        assert result == idle_id

    def test_distributes_evenly(self):
        """WR-12b: Load is distributed evenly across workers."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        worker1 = registry.register_worker(
            name="worker-1",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            max_concurrent=10
        )

        worker2 = registry.register_worker(
            name="worker-2",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            max_concurrent=10
        )

        # Route 4 stories - should distribute 2 each (or close)
        assignments = {}
        for i in range(4):
            worker_id = router.route_story()
            registry.assign_story(worker_id, i + 1000)
            assignments[worker_id] = assignments.get(worker_id, 0) + 1

        # Each worker should have 2 stories
        assert assignments[worker1] == 2
        assert assignments[worker2] == 2

    def test_skips_full_workers(self):
        """WR-12c: Workers at capacity are skipped."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        full_id = registry.register_worker(
            name="full-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            max_concurrent=1
        )

        available_id = registry.register_worker(
            name="available-worker",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            max_concurrent=10
        )

        # Fill first worker
        registry.assign_story(full_id, 100)

        result = router.route_story()
        assert result == available_id

    def test_none_when_all_full(self):
        """WR-12d: Returns None when all workers at capacity."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        worker_id = registry.register_worker(
            name="worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            max_concurrent=1
        )

        registry.assign_story(worker_id, 100)

        result = router.route_story()
        assert result is None
