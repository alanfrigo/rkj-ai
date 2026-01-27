"""
Meet Bot - Configuration
"""
import os


class Config:
    """Configuration for the Meet Bot"""
    
    # Meeting Configuration
    MEETING_URL: str = os.getenv("MEETING_URL", "")
    MEETING_ID: str = os.getenv("MEETING_ID", "")
    USER_ID: str = os.getenv("USER_ID", "")
    
    # Bot Display
    BOT_NAME: str = os.getenv("BOT_DISPLAY_NAME", "RKJ.AI")
    BOT_CAMERA_ENABLED: bool = os.getenv("BOT_CAMERA_ENABLED", "false").lower() == "true"
    
    # Recording
    RECORDING_DIR: str = os.getenv("RECORDING_DIR", "/recordings")
    RECORDING_QUALITY: str = os.getenv("BOT_RECORDING_QUALITY", "1080p")
    MAX_DURATION_HOURS: int = int(os.getenv("BOT_MAX_DURATION_HOURS", "4"))
    
    # Timeouts (seconds)
    JOIN_TIMEOUT: int = int(os.getenv("JOIN_TIMEOUT", "120"))
    PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))

    # Retry Configuration
    MAX_JOIN_RETRIES: int = int(os.getenv("MAX_JOIN_RETRIES", "3"))
    INITIAL_RETRY_DELAY: int = int(os.getenv("INITIAL_RETRY_DELAY", "5"))
    MAX_RETRY_DELAY: int = int(os.getenv("MAX_RETRY_DELAY", "30"))

    # Early Recording Mode (start recording before confirming join)
    EARLY_RECORDING_MODE: bool = os.getenv("EARLY_RECORDING_MODE", "false").lower() == "true"
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Cloudflare R2
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "meeting-assistant")
    R2_PUBLIC_URL: str = os.getenv("R2_PUBLIC_URL", "")  # Public URL for R2 (e.g., https://pub-xxx.r2.dev)
    
    # OpenAI (Transcription)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_WHISPER_MODEL: str = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
    TRANSCRIPTION_LANGUAGE: str = os.getenv("TRANSCRIPTION_LANGUAGE", "pt")
    
    # Display
    DISPLAY: str = os.getenv("DISPLAY", ":99")
    RESOLUTION: tuple = (1920, 1080)

    
    # FFmpeg settings based on quality
    @classmethod
    def get_ffmpeg_settings(cls) -> dict:
        # Allow env var override for bitrate, default to 1000k for size optimization
        video_bitrate = os.getenv("VIDEO_BITRATE", "1000k")
        
        if cls.RECORDING_QUALITY == "1080p":
            return {
                "resolution": "1920x1080",
                "framerate": "30",
                "video_bitrate": video_bitrate,
                "audio_bitrate": "128k"
            }
        else:  # 720p
            return {
                "resolution": "1280x720",
                "framerate": "25",
                "video_bitrate": "800k", # Lower for 720p too
                "audio_bitrate": "128k"
            }


config = Config()
