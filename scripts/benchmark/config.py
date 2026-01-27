"""
Benchmark Configuration
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests"""
    
    # Docker settings
    docker_host: str = os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock")
    bot_image: str = os.getenv("BOT_IMAGE", "meet-bot:latest")
    network_name: str = os.getenv("DOCKER_NETWORK", "rkj-ai-network")
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Supabase settings
    supabase_url: str = os.getenv("SUPABASE_URL", "http://localhost:54321")
    supabase_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # OpenAI settings (for transcription cost estimation)
    openai_price_per_minute: float = 0.006  # USD per minute of audio
    
    # Benchmark defaults
    default_duration_seconds: int = 300  # 5 minutes
    metrics_interval_seconds: float = 1.0  # Collect metrics every second
    max_concurrent_bots: int = 50
    
    # Paths
    audio_samples_dir: str = "audio_samples"
    results_dir: str = "results"
    
    # Resource limits per bot (for estimation)
    estimated_ram_per_bot_mb: int = 1000
    estimated_cpu_per_bot: float = 0.5


@dataclass
class TestResult:
    """Result of a single test operation"""
    operation: str
    success: bool
    duration_ms: float
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class BotMetrics:
    """Metrics for a single bot container"""
    container_id: str
    container_name: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    network_rx_mb: float = 0.0
    network_tx_mb: float = 0.0
    status: str = "unknown"


@dataclass  
class AggregatedMetrics:
    """Aggregated metrics across all containers"""
    timestamp: float
    total_containers: int
    total_cpu_percent: float
    total_memory_mb: float
    total_memory_percent: float
    total_network_rx_mb: float
    total_network_tx_mb: float
    individual_bots: list = field(default_factory=list)


config = BenchmarkConfig()
