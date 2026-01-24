"""
Bot Orchestrator - Configuration
"""
import os


class Config:
    """Configuration for the Bot Orchestrator"""
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # R2
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "meeting-assistant")
    R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Bot Configuration
    BOT_IMAGE: str = os.getenv("BOT_IMAGE", "docker-meet-bot:latest")
    BOT_DISPLAY_NAME: str = os.getenv("BOT_DISPLAY_NAME", "Meeting Assistant Bot 🤖")
    BOT_MAX_DURATION_HOURS: int = int(os.getenv("BOT_MAX_DURATION_HOURS", "4"))
    
    # Docker
    DOCKER_NETWORK: str = os.getenv("DOCKER_NETWORK", "meeting-assistant-network")
    RECORDINGS_VOLUME: str = os.getenv("RECORDINGS_VOLUME", "docker_recordings")
    
    # Queue
    JOIN_MEETING_QUEUE: str = "queue:join_meeting"
    
    # Timeouts
    CONTAINER_TIMEOUT_SECONDS: int = int(os.getenv("CONTAINER_TIMEOUT", "14400"))  # 4 hours

    # Google Authentication
    GOOGLE_AUTH_LOGIN: str = os.getenv("GOOGLE_AUTH_LOGIN", "")
    GOOGLE_AUTH_PASSWORD: str = os.getenv("GOOGLE_AUTH_PASSWORD", "")


config = Config()
