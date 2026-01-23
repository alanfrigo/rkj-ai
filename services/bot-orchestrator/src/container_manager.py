"""
Bot Orchestrator - Container Manager
Manages Docker containers for meeting bots
"""
import logging
from datetime import datetime
from typing import Dict, Optional

import docker
from docker.models.containers import Container

from .config import config

logger = logging.getLogger(__name__)


class ContainerManager:
    """Manages Docker containers for meeting bots"""
    
    def __init__(self):
        # Use explicit socket path to avoid http+docker URL scheme issue
        self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        self.active_containers: Dict[str, Container] = {}
    
    def spawn_bot(
        self,
        meeting_id: str,
        meeting_url: str,
        user_id: str
    ) -> Optional[Container]:
        """
        Spawn a new Meet Bot container
        
        Returns the container if successful, None otherwise
        """
        container_name = f"ma-meet-bot-{meeting_id[:8]}"
        
        logger.info(f"Spawning bot container: {container_name}")
        logger.info(f"  Meeting URL: {meeting_url}")
        logger.info(f"  User ID: {user_id}")
        
        try:
            # Environment variables for the bot
            environment = {
                "MEETING_ID": meeting_id,
                "MEETING_URL": meeting_url,
                "USER_ID": user_id,
                "BOT_DISPLAY_NAME": config.BOT_DISPLAY_NAME,
                "BOT_MAX_DURATION_HOURS": str(config.BOT_MAX_DURATION_HOURS),
                "SUPABASE_URL": config.SUPABASE_URL,
                "SUPABASE_SERVICE_KEY": config.SUPABASE_SERVICE_KEY,
                "REDIS_URL": config.REDIS_URL,
                "R2_ACCOUNT_ID": config.R2_ACCOUNT_ID,
                "R2_ACCESS_KEY_ID": config.R2_ACCESS_KEY_ID,
                "R2_SECRET_ACCESS_KEY": config.R2_SECRET_ACCESS_KEY,
                "R2_BUCKET_NAME": config.R2_BUCKET_NAME,
                "GOOGLE_AUTH_LOGIN": config.GOOGLE_AUTH_LOGIN,
                "GOOGLE_AUTH_PASSWORD": config.GOOGLE_AUTH_PASSWORD,
            }
            
            # Run the container
            container = self.client.containers.run(
                config.BOT_IMAGE,
                name=container_name,
                environment=environment,
                # Shared memory for Chrome
                shm_size="2g",
                # Network
                network=config.DOCKER_NETWORK,
                # Volumes
                volumes={
                    config.RECORDINGS_VOLUME: {
                        "bind": "/recordings",
                        "mode": "rw"
                    }
                },
                # Auto-remove when done
                auto_remove=True,
                # Detached mode
                detach=True,
                # Labels for identification
                labels={
                    "meeting_id": meeting_id,
                    "user_id": user_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            self.active_containers[meeting_id] = container
            logger.info(f"Bot container started: {container.id[:12]}")
            
            return container
            
        except docker.errors.ImageNotFound:
            logger.error(f"Bot image not found: {config.BOT_IMAGE}")
            logger.error("Please build the meet-bot image first: docker-compose build meet-bot")
            return None
            
        except Exception as e:
            logger.error(f"Failed to spawn bot: {e}")
            return None
    
    def stop_bot(self, meeting_id: str) -> bool:
        """Stop a bot container"""
        container = self.active_containers.get(meeting_id)
        
        if not container:
            logger.warning(f"No active container for meeting {meeting_id}")
            return False
        
        try:
            logger.info(f"Stopping bot container for meeting {meeting_id}")
            container.stop(timeout=30)
            del self.active_containers[meeting_id]
            return True
        except Exception as e:
            logger.error(f"Failed to stop container: {e}")
            return False
    
    def get_container_status(self, meeting_id: str) -> Optional[str]:
        """Get status of a bot container"""
        container = self.active_containers.get(meeting_id)
        
        if not container:
            return None
        
        try:
            container.reload()
            return container.status
        except Exception as e:
            logger.error(f"Failed to get container status: {e}")
            return None
    
    def cleanup_dead_containers(self):
        """Remove dead containers from tracking"""
        dead = []
        
        for meeting_id, container in self.active_containers.items():
            try:
                container.reload()
                if container.status in ["exited", "dead", "removing"]:
                    dead.append(meeting_id)
            except Exception:
                dead.append(meeting_id)
        
        for meeting_id in dead:
            logger.info(f"Removing dead container for meeting {meeting_id}")
            del self.active_containers[meeting_id]
        
        return len(dead)
    
    def get_active_count(self) -> int:
        """Get number of active containers"""
        self.cleanup_dead_containers()
        return len(self.active_containers)
