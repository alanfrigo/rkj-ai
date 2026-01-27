"""
Bot Orchestrator - Main Entry Point
Consumes join_meeting jobs from Redis and spawns bot containers
"""
import asyncio
import json
import logging
import os
from datetime import datetime

import redis.asyncio as redis
from supabase import create_client

from .config import config
from .container_manager import ContainerManager

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BotOrchestrator:
    """
    Orchestrates meeting bots
    
    - Consumes jobs from join_meeting queue
    - Spawns Meet Bot containers via Docker SDK
    - Monitors container health
    """
    
    def __init__(self):
        self.redis_client = None
        self.supabase = None
        self.container_manager = ContainerManager()
        self.running = True
    
    async def initialize(self):
        """Initialize clients"""
        # Redis
        self.redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
        await self.redis_client.ping()
        logger.info("Connected to Redis")
        
        # Supabase
        self.supabase = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
        logger.info("Connected to Supabase")
    
    async def run(self):
        """Main orchestrator loop"""
        logger.info("Bot Orchestrator started, waiting for jobs...")
        
        # Start health check task
        health_task = asyncio.create_task(self.health_check_loop())
        
        try:
            while self.running:
                try:
                    # Blocking pop from queue
                    result = await self.redis_client.blpop(
                        config.JOIN_MEETING_QUEUE, 
                        timeout=10
                    )
                    
                    if result:
                        _, job_json = result
                        job = json.loads(job_json)
                        
                        logger.info(f"Received job: {job['id']}")
                        await self.process_job(job)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in orchestrator loop: {e}")
                    await asyncio.sleep(5)
        finally:
            health_task.cancel()
            try:
                await health_task
            except asyncio.CancelledError:
                pass
    
    async def process_job(self, job: dict):
        """Process a single job"""
        data = job.get("data", {})
        
        meeting_id = data.get("meeting_id")
        meeting_url = data.get("meeting_url")
        user_id = data.get("user_id")
        bot_display_name = data.get("bot_display_name")
        bot_camera_enabled = data.get("bot_camera_enabled", False)
        
        if not all([meeting_id, meeting_url, user_id]):
            logger.error(f"Invalid job data: {data}")
            return
        
        logger.info(f"Processing meeting: {meeting_id}")
        logger.info(f"  Bot Name: {bot_display_name}")
        logger.info(f"  Camera Enabled: {bot_camera_enabled}")
        
        # Spawn bot container
        container = self.container_manager.spawn_bot(
            meeting_id=meeting_id,
            meeting_url=meeting_url,
            user_id=user_id,
            bot_display_name=bot_display_name,
            bot_camera_enabled=bot_camera_enabled
        )
        
        if container:
            logger.info(f"Bot spawned successfully for meeting {meeting_id}")
            
            # Update meeting status
            self.update_meeting_status(meeting_id, "joining", 
                                       bot_container_id=container.id[:12])
        else:
            logger.error(f"Failed to spawn bot for meeting {meeting_id}")
            self.update_meeting_status(meeting_id, "failed",
                                       error_message="Failed to spawn bot container")
    
    def update_meeting_status(self, meeting_id: str, status: str, **kwargs):
        """Update meeting status in database"""
        try:
            update_data = {"status": status}
            update_data.update(kwargs)
            
            self.supabase.table('meetings').update(update_data).eq('id', meeting_id).execute()
            logger.info(f"Updated meeting {meeting_id} status to: {status}")
        except Exception as e:
            logger.error(f"Failed to update meeting status: {e}")
    
    async def health_check_loop(self):
        """Periodic health check of active containers"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                active_count = self.container_manager.get_active_count()
                logger.debug(f"Active bot containers: {active_count}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        self.running = False
        
        if self.redis_client:
            await self.redis_client.aclose()


async def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("Bot Orchestrator Starting")
    logger.info("=" * 50)
    
    orchestrator = BotOrchestrator()
    
    try:
        await orchestrator.initialize()
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
