"""
Meeting Assistant - Redis Client
Async Redis connection management
"""
import redis.asyncio as redis
from typing import Optional
import logging

from ..config import settings

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def init_redis() -> redis.Redis:
    """Initialize Redis connection"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        # Test connection
        await _redis_client.ping()
        logger.info(f"Connected to Redis at {settings.REDIS_URL}")
    
    return _redis_client


async def get_redis() -> redis.Redis:
    """Get Redis client instance"""
    global _redis_client
    
    if _redis_client is None:
        return await init_redis()
    
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")


# Queue names
class Queues:
    """Queue name constants"""
    CALENDAR_SYNC = "calendar_sync"
    JOIN_MEETING = "join_meeting"
    RECORDING = "recording"
    MEDIA_PROCESSING = "media_processing"
    TRANSCRIPTION = "transcription"
    NOTIFICATION = "notification"


async def enqueue_job(queue: str, data: dict) -> str:
    """
    Add a job to a queue
    Returns the job ID
    """
    import json
    import uuid
    
    client = await get_redis()
    job_id = str(uuid.uuid4())
    
    job = {
        "id": job_id,
        "data": data,
        "status": "queued",
        "created_at": str(__import__('datetime').datetime.utcnow().isoformat())
    }
    
    await client.rpush(f"queue:{queue}", json.dumps(job))
    logger.info(f"Enqueued job {job_id} to {queue}")
    
    return job_id


async def dequeue_job(queue: str, timeout: int = 0) -> Optional[dict]:
    """
    Get a job from a queue (blocking)
    Returns None if timeout reached
    """
    import json
    
    client = await get_redis()
    result = await client.blpop(f"queue:{queue}", timeout=timeout)
    
    if result:
        _, job_json = result
        return json.loads(job_json)
    
    return None
