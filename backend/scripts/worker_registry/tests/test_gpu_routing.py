"""
Test WR-13: GPU-aware routing checks gpu_vram_min against available VRAM.
"""
import pytest


class TestGpuRouting:
    """Tests for GPU-aware routing."""

    def test_routes_to_gpu_worker(self):
        """WR-13a: Routes to GPU worker when GPU required."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        cpu_id = registry.register_worker(
            name="cpu-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            gpu_required=False
        )

        gpu_id = registry.register_worker(
            name="gpu-worker",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            gpu_required=True,
            gpu_vram_min=32
        )

        result = router.route_story(gpu_required=True)
        assert result == gpu_id

    def test_filters_by_vram(self):
        """WR-13b: Filters out workers with insufficient VRAM."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        small_gpu_id = registry.register_worker(
            name="small-gpu",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            gpu_required=True,
            gpu_vram_min=24
        )

        large_gpu_id = registry.register_worker(
            name="large-gpu",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            gpu_required=True,
            gpu_vram_min=128
        )

        # Requires 64GB VRAM
        result = router.route_story(gpu_required=True, gpu_vram_min=64)
        assert result == large_gpu_id

    def test_none_when_insufficient_vram(self):
        """WR-13c: Returns None when no worker has enough VRAM."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        registry.register_worker(
            name="small-gpu",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            gpu_required=True,
            gpu_vram_min=32
        )

        # Requires more VRAM than any worker has
        result = router.route_story(gpu_required=True, gpu_vram_min=256)
        assert result is None

    def test_gpu_combined_with_labels(self):
        """WR-13d: GPU requirements combine with label requirements."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        # GPU but wrong labels
        registry.register_worker(
            name="gpu-rust",
            worker_type="vllm",
            endpoint="http://localhost:8000",
            capabilities=["code_generation"],
            gpu_required=True,
            gpu_vram_min=48,
            labels=["rust"]
        )

        # GPU with right labels
        python_gpu_id = registry.register_worker(
            name="gpu-python",
            worker_type="vllm",
            endpoint="http://localhost:8001",
            capabilities=["code_generation"],
            gpu_required=True,
            gpu_vram_min=48,
            labels=["python"]
        )

        result = router.route_story(
            story_labels=["python"],
            gpu_required=True,
            gpu_vram_min=32
        )
        assert result == python_gpu_id

    def test_non_gpu_story_skips_gpu_check(self):
        """WR-13e: Non-GPU stories can use any worker."""
        from worker_registry import WorkerRegistry, WorkerRouter

        registry = WorkerRegistry()
        router = WorkerRouter(registry)

        cpu_id = registry.register_worker(
            name="cpu-worker",
            worker_type="ollama",
            endpoint="http://localhost:11434",
            capabilities=["code_generation"],
            gpu_required=False
        )

        # Non-GPU story can use CPU worker
        result = router.route_story(gpu_required=False)
        assert result == cpu_id
