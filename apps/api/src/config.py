"""
Meeting Assistant - Configuration
Environment variables and settings using Pydantic
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # -------------------------------------------
    # Supabase
    # -------------------------------------------
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anonymous key")
    SUPABASE_SERVICE_KEY: str = Field(..., description="Supabase service role key")
    
    # -------------------------------------------
    # Cloudflare R2
    # -------------------------------------------
    R2_ACCOUNT_ID: str = Field(..., description="Cloudflare account ID")
    R2_ACCESS_KEY_ID: str = Field(..., description="R2 access key ID")
    R2_SECRET_ACCESS_KEY: str = Field(..., description="R2 secret access key")
    R2_BUCKET_NAME: str = Field(default="meeting-assistant", description="R2 bucket name")
    R2_PUBLIC_URL: str = Field(default="", description="R2 public URL for downloads")
    
    @property
    def R2_ENDPOINT(self) -> str:
        """Generate R2 endpoint URL"""
        return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    # -------------------------------------------
    # OpenAI
    # -------------------------------------------
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_WHISPER_MODEL: str = Field(default="whisper-1", description="Whisper model to use")
    
    # -------------------------------------------
    # Google OAuth
    # -------------------------------------------
    GOOGLE_CLIENT_ID: str = Field(..., description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: str = Field(..., description="Google OAuth client secret")
    
    # -------------------------------------------
    # Redis
    # -------------------------------------------
    REDIS_URL: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    
    # -------------------------------------------
    # Application
    # -------------------------------------------
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="Frontend URL for CORS")
    API_URL: str = Field(default="http://localhost:8000", description="This API's URL")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # -------------------------------------------
    # Bot Configuration
    # -------------------------------------------
    BOT_DISPLAY_NAME: str = Field(
        default="RKJ.AI",
        description="Bot display name in meetings"
    )
    BOT_JOIN_BEFORE_MINUTES: int = Field(
        default=2,
        description="Minutes before meeting to join"
    )
    BOT_MAX_DURATION_HOURS: int = Field(
        default=4,
        description="Maximum meeting duration before auto-leave"
    )
    BOT_RECORDING_QUALITY: str = Field(
        default="1080p",
        description="Recording quality (720p, 1080p)"
    )
    
    # -------------------------------------------
    # Feature Flags
    # -------------------------------------------
    FEATURE_ZOOM_BOT: bool = Field(default=False, description="Enable Zoom bot")
    FEATURE_SPEAKER_DIARIZATION: bool = Field(default=False, description="Enable speaker diarization")
    FEATURE_AI_SUMMARY: bool = Field(default=False, description="Enable AI summaries")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
