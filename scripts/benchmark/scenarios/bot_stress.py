"""
Bot Stress Test Scenario
Spawns multiple bot containers to test resource usage
"""
import asyncio
import time
from typing import List, Optional
import docker
from docker.types import Mount

from .base import BaseScenario
from config import config


class BotStressScenario(BaseScenario):
    """
    Stress test for bot container spawning
    
    Tests:
    - Container spawn time
    - Resource usage per container
    - Maximum concurrent containers
    - System stability under load
    """
    
    def __init__(self):
        super().__init__("bot_stress_test")
        self.docker_client = docker.from_env()
        self.spawned_containers: List[str] = []
    
    async def setup(self, **kwargs):
        """Prepare for the stress test"""
        print(f"[{self.name}] Setting up stress test...")
        
        # Verify bot image exists
        try:
            self.docker_client.images.get(config.bot_image)
            print(f"[{self.name}] Bot image '{config.bot_image}' found")
        except docker.errors.ImageNotFound:
            raise RuntimeError(f"Bot image '{config.bot_image}' not found. Please build it first.")
        
        # Clean up any leftover containers from previous runs
        await self._cleanup_old_containers()
    
    async def execute(self, bots: int = 10, duration: int = 300, **kwargs):
        """
        Execute the stress test
        
        Args:
            bots: Number of bot containers to spawn
            duration: How long to keep containers running (seconds)
        """
        print(f"[{self.name}] Starting stress test with {bots} bots for {duration}s...")
        
        # Spawn bots in parallel
        spawn_tasks = []
        for i in range(bots):
            task = asyncio.create_task(self._spawn_bot(i))
            spawn_tasks.append(task)
            # Small delay between spawns to avoid overwhelming Docker
            await asyncio.sleep(0.5)
        
        # Wait for all spawns to complete
        results = await asyncio.gather(*spawn_tasks, return_exceptions=True)
        
        successful_spawns = sum(1 for r in results if r is True)
        failed_spawns = sum(1 for r in results if r is not True)
        
        print(f"[{self.name}] Spawned {successful_spawns}/{bots} bots successfully")
        
        if failed_spawns > 0:
            print(f"[{self.name}] WARNING: {failed_spawns} bots failed to spawn")
        
        # Keep containers running for the specified duration
        print(f"[{self.name}] Keeping containers running for {duration}s...")
        
        start = time.time()
        while time.time() - start < duration:
            elapsed = int(time.time() - start)
            remaining = duration - elapsed
            
            # Log progress every 30 seconds
            if elapsed % 30 == 0:
                metrics = self.docker_collector.get_aggregated_metrics()
                print(f"[{self.name}] {elapsed}s elapsed, {remaining}s remaining | "
                      f"Containers: {metrics.total_containers} | "
                      f"CPU: {metrics.total_cpu_percent:.1f}% | "
                      f"RAM: {metrics.total_memory_mb:.0f}MB")
            
            await asyncio.sleep(1)
        
        print(f"[{self.name}] Stress test duration completed")
    
    async def teardown(self, **kwargs):
        """Clean up spawned containers"""
        print(f"[{self.name}] Cleaning up {len(self.spawned_containers)} containers...")
        
        for container_id in self.spawned_containers:
            try:
                container = self.docker_client.containers.get(container_id)
                container.remove(force=True)
            except docker.errors.NotFound:
                pass
            except Exception as e:
                print(f"[{self.name}] Error removing container {container_id}: {e}")
        
        self.spawned_containers = []
        print(f"[{self.name}] Cleanup complete")
    
    async def _spawn_bot(self, index: int) -> bool:
        """Spawn a single bot container"""
        container_name = f"rkj-bot-benchmark-{index}"
        
        timer_id = self.timing_collector.start_timer("container_spawn")
        
        try:
            # Remove existing container with same name if exists
            try:
                existing = self.docker_client.containers.get(container_name)
                existing.remove(force=True)
            except docker.errors.NotFound:
                pass
            
            # Spawn container in idle mode (no actual meeting join)
            container = self.docker_client.containers.run(
                config.bot_image,
                name=container_name,
                detach=True,
                network=config.network_name,
                environment={
                    "BENCHMARK_MODE": "true",
                    "MEETING_URL": "",  # No meeting to join
                    "MEETING_ID": f"benchmark-{index}",
                },
                # Resource limits for safety
                mem_limit="2g",
                cpu_quota=100000,  # 1 CPU
                shm_size="1g",  # Shared memory for Chrome
            )
            
            self.spawned_containers.append(container.id)
            self.timing_collector.stop_timer(timer_id, success=True, 
                                            metadata={"container_id": container.id[:12]})
            
            return True
            
        except Exception as e:
            self.timing_collector.stop_timer(timer_id, success=False, error=str(e))
            print(f"[{self.name}] Failed to spawn bot {index}: {e}")
            return False
    
    async def _cleanup_old_containers(self):
        """Remove old benchmark containers"""
        try:
            containers = self.docker_client.containers.list(
                all=True,
                filters={"name": "rkj-bot-benchmark-"}
            )
            for container in containers:
                container.remove(force=True)
                print(f"[{self.name}] Removed old container: {container.name}")
        except Exception as e:
            print(f"[{self.name}] Error cleaning old containers: {e}")
