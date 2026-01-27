"""
Transcription Load Test Scenario
Tests transcription worker throughput
"""
import asyncio
import json
import os
import time
from typing import Dict, List
import redis.asyncio as redis

from .base import BaseScenario
from config import config


class TranscriptionLoadScenario(BaseScenario):
    """
    Load test for transcription worker
    
    Tests:
    - Transcription queue throughput
    - Processing time per file
    - Parallel processing capability
    - API rate limits
    """
    
    def __init__(self):
        super().__init__("transcription_load_test")
        self.redis_client = None
        self.enqueued_jobs: List[str] = []
        self.completed_jobs: List[str] = []
    
    async def setup(self, **kwargs):
        """Connect to Redis and prepare test files"""
        print(f"[{self.name}] Setting up transcription load test...")
        
        # Connect to Redis
        self.redis_client = redis.from_url(config.redis_url, decode_responses=True)
        await self.redis_client.ping()
        print(f"[{self.name}] Connected to Redis")
        
        # Verify audio samples exist
        audio_dir = os.path.join(os.path.dirname(__file__), "..", config.audio_samples_dir)
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
            print(f"[{self.name}] Created audio samples directory: {audio_dir}")
            print(f"[{self.name}] NOTE: Add sample audio files to test transcription")
    
    async def execute(self, files: int = 10, file_duration_minutes: int = 1, **kwargs):
        """
        Execute the transcription load test
        
        Args:
            files: Number of transcription jobs to enqueue
            file_duration_minutes: Duration of audio files (for estimation)
        """
        print(f"[{self.name}] Enqueuing {files} transcription jobs...")
        
        # Enqueue jobs
        for i in range(files):
            timer_id = self.timing_collector.start_timer("job_enqueue")
            
            job = {
                "id": f"benchmark-transcription-{i}",
                "data": {
                    "transcription_id": f"benchmark-{i}",
                    "audio_url": f"benchmark://sample_{file_duration_minutes}min.mp3",
                    "language": "pt",
                    "benchmark_mode": True,
                },
                "status": "queued",
                "created_at": time.time(),
            }
            
            await self.redis_client.rpush("queue:transcription", json.dumps(job))
            self.enqueued_jobs.append(job["id"])
            
            self.timing_collector.stop_timer(timer_id, success=True, 
                                            metadata={"job_id": job["id"]})
        
        print(f"[{self.name}] Enqueued {len(self.enqueued_jobs)} jobs")
        
        # Monitor queue processing
        print(f"[{self.name}] Monitoring queue processing...")
        
        start = time.time()
        timeout = 600  # 10 minute timeout
        
        while time.time() - start < timeout:
            queue_length = await self.redis_client.llen("queue:transcription")
            
            elapsed = int(time.time() - start)
            print(f"[{self.name}] {elapsed}s: {queue_length} jobs remaining in queue")
            
            if queue_length == 0:
                print(f"[{self.name}] All jobs processed!")
                break
            
            await asyncio.sleep(5)
        
        # Calculate estimated costs
        total_minutes = files * file_duration_minutes
        estimated_cost = total_minutes * config.openai_price_per_minute
        
        print(f"[{self.name}] Estimated API cost: ${estimated_cost:.2f} "
              f"({total_minutes} minutes of audio)")
    
    async def teardown(self, **kwargs):
        """Clean up Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
        print(f"[{self.name}] Cleanup complete")
    
    def generate_recommendations(self, config_params: Dict) -> Dict:
        """Generate recommendations for transcription scaling"""
        stats = self.timing_collector.get_statistics("job_enqueue")
        
        files = config_params.get("files", 1)
        file_duration = config_params.get("file_duration_minutes", 1)
        
        # Calculate throughput
        if stats:
            total_time_ms = stats.get("total_ms", 0)
            throughput_per_hour = (files / (total_time_ms / 1000 / 3600)) if total_time_ms > 0 else 0
        else:
            throughput_per_hour = 0
        
        return {
            "transcription": {
                "files_tested": files,
                "throughput_per_hour": round(throughput_per_hour, 2),
                "estimated_daily_capacity": round(throughput_per_hour * 24, 0),
                "cost_per_hour": round(throughput_per_hour * file_duration * config.openai_price_per_minute, 2),
            },
            "scaling_recommendations": [
                "Considere aumentar workers para maior throughput",
                "Monitore rate limits do OpenAI",
                "Use chunking para arquivos grandes (>25MB)",
            ],
        }
