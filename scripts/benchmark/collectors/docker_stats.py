"""
Docker Stats Collector
Collects CPU, RAM, Network I/O metrics from Docker containers
"""
import asyncio
import time
from typing import Dict, List, Optional
import docker
from docker.errors import NotFound, APIError

from config import BotMetrics, AggregatedMetrics, config


class DockerStatsCollector:
    """Collects metrics from Docker containers in real-time"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.metrics_history: List[AggregatedMetrics] = []
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None
    
    def get_container_stats(self, container_id: str) -> Optional[BotMetrics]:
        """Get current stats for a single container"""
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_count = stats['cpu_stats'].get('online_cpus', 1) or 1
            
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100
            
            # Calculate memory
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 1)
            memory_mb = memory_usage / (1024 * 1024)
            memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
            
            # Calculate network I/O
            networks = stats.get('networks', {})
            rx_bytes = sum(net.get('rx_bytes', 0) for net in networks.values())
            tx_bytes = sum(net.get('tx_bytes', 0) for net in networks.values())
            
            return BotMetrics(
                container_id=container_id[:12],
                container_name=container.name,
                cpu_percent=round(cpu_percent, 2),
                memory_mb=round(memory_mb, 2),
                memory_percent=round(memory_percent, 2),
                network_rx_mb=round(rx_bytes / (1024 * 1024), 2),
                network_tx_mb=round(tx_bytes / (1024 * 1024), 2),
                status=container.status
            )
        except NotFound:
            return None
        except APIError as e:
            print(f"API error getting stats for {container_id}: {e}")
            return None
    
    def get_all_bot_stats(self, name_filter: str = "rkj-bot-") -> List[BotMetrics]:
        """Get stats for all bot containers matching the filter"""
        metrics = []
        try:
            containers = self.client.containers.list(
                filters={"name": name_filter}
            )
            for container in containers:
                bot_metrics = self.get_container_stats(container.id)
                if bot_metrics:
                    metrics.append(bot_metrics)
        except Exception as e:
            print(f"Error listing containers: {e}")
        return metrics
    
    def get_aggregated_metrics(self, name_filter: str = "rkj-bot-") -> AggregatedMetrics:
        """Get aggregated metrics across all bot containers"""
        bot_metrics = self.get_all_bot_stats(name_filter)
        
        return AggregatedMetrics(
            timestamp=time.time(),
            total_containers=len(bot_metrics),
            total_cpu_percent=sum(m.cpu_percent for m in bot_metrics),
            total_memory_mb=sum(m.memory_mb for m in bot_metrics),
            total_memory_percent=sum(m.memory_percent for m in bot_metrics) / max(len(bot_metrics), 1),
            total_network_rx_mb=sum(m.network_rx_mb for m in bot_metrics),
            total_network_tx_mb=sum(m.network_tx_mb for m in bot_metrics),
            individual_bots=[vars(m) for m in bot_metrics]
        )
    
    async def start_collection(self, interval: float = 1.0, name_filter: str = "rkj-bot-"):
        """Start collecting metrics at regular intervals"""
        self._running = True
        self.metrics_history = []
        
        while self._running:
            metrics = self.get_aggregated_metrics(name_filter)
            self.metrics_history.append(metrics)
            await asyncio.sleep(interval)
    
    def stop_collection(self):
        """Stop the metrics collection"""
        self._running = False
    
    def get_history(self) -> List[AggregatedMetrics]:
        """Get collected metrics history"""
        return self.metrics_history
    
    def get_peak_metrics(self) -> Dict:
        """Get peak values from the metrics history"""
        if not self.metrics_history:
            return {}
        
        return {
            "peak_containers": max(m.total_containers for m in self.metrics_history),
            "peak_cpu_percent": max(m.total_cpu_percent for m in self.metrics_history),
            "peak_memory_mb": max(m.total_memory_mb for m in self.metrics_history),
            "peak_memory_gb": round(max(m.total_memory_mb for m in self.metrics_history) / 1024, 2),
            "peak_network_rx_mb": max(m.total_network_rx_mb for m in self.metrics_history),
            "peak_network_tx_mb": max(m.total_network_tx_mb for m in self.metrics_history),
        }
    
    def get_average_metrics(self) -> Dict:
        """Get average values from the metrics history"""
        if not self.metrics_history:
            return {}
        
        n = len(self.metrics_history)
        return {
            "avg_containers": sum(m.total_containers for m in self.metrics_history) / n,
            "avg_cpu_percent": round(sum(m.total_cpu_percent for m in self.metrics_history) / n, 2),
            "avg_memory_mb": round(sum(m.total_memory_mb for m in self.metrics_history) / n, 2),
            "avg_memory_gb": round(sum(m.total_memory_mb for m in self.metrics_history) / n / 1024, 2),
        }


class SystemStatsCollector:
    """Collects system-wide stats (host machine)"""
    
    def __init__(self):
        import psutil
        self.psutil = psutil
    
    def get_system_stats(self) -> Dict:
        """Get current system stats"""
        cpu_percent = self.psutil.cpu_percent(interval=0.1)
        memory = self.psutil.virtual_memory()
        disk = self.psutil.disk_usage('/')
        
        return {
            "timestamp": time.time(),
            "cpu_percent": cpu_percent,
            "cpu_count": self.psutil.cpu_count(),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_percent": round(disk.percent, 1),
        }
