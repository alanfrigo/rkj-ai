"""
Base Scenario Class
"""
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

from collectors import DockerStatsCollector, TimingCollector, SystemStatsCollector
from config import config


@dataclass
class ScenarioResult:
    """Result of a benchmark scenario"""
    scenario_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    config: Dict
    success: bool
    error: Optional[str] = None
    
    # Metrics
    timing_summary: Dict = field(default_factory=dict)
    docker_metrics: Dict = field(default_factory=dict)
    system_metrics: Dict = field(default_factory=dict)
    
    # Recommendations
    recommendations: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "scenario_name": self.scenario_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "config": self.config,
            "success": self.success,
            "error": self.error,
            "timing_summary": self.timing_summary,
            "docker_metrics": self.docker_metrics,
            "system_metrics": self.system_metrics,
            "recommendations": self.recommendations,
        }
    
    def save(self, filepath: str):
        """Save result to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class BaseScenario(ABC):
    """Base class for benchmark scenarios"""
    
    def __init__(self, name: str):
        self.name = name
        self.docker_collector = DockerStatsCollector()
        self.timing_collector = TimingCollector()
        self.system_collector = SystemStatsCollector()
        self._metrics_task: Optional[asyncio.Task] = None
    
    @abstractmethod
    async def setup(self, **kwargs):
        """Setup the scenario"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs):
        """Execute the main benchmark logic"""
        pass
    
    @abstractmethod
    async def teardown(self, **kwargs):
        """Cleanup after the scenario"""
        pass
    
    async def run(self, **kwargs) -> ScenarioResult:
        """Run the complete scenario"""
        start_time = datetime.now()
        success = True
        error = None
        
        # Start metrics collection in background
        self._metrics_task = asyncio.create_task(
            self.docker_collector.start_collection(
                interval=config.metrics_interval_seconds
            )
        )
        
        try:
            # Record initial system state
            initial_system = self.system_collector.get_system_stats()
            
            # Run scenario phases
            await self.setup(**kwargs)
            await self.execute(**kwargs)
            
        except Exception as e:
            success = False
            error = str(e)
            import traceback
            traceback.print_exc()
        finally:
            # Stop metrics collection
            self.docker_collector.stop_collection()
            if self._metrics_task:
                self._metrics_task.cancel()
                try:
                    await self._metrics_task
                except asyncio.CancelledError:
                    pass
            
            # Teardown
            try:
                await self.teardown(**kwargs)
            except Exception as e:
                print(f"Error during teardown: {e}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Compile results
        result = ScenarioResult(
            scenario_name=self.name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            config=kwargs,
            success=success,
            error=error,
            timing_summary=self.timing_collector.get_summary(),
            docker_metrics={
                "peak": self.docker_collector.get_peak_metrics(),
                "average": self.docker_collector.get_average_metrics(),
                "samples_count": len(self.docker_collector.get_history()),
            },
            system_metrics={
                "initial": initial_system,
                "final": self.system_collector.get_system_stats(),
            },
            recommendations=self.generate_recommendations(kwargs),
        )
        
        return result
    
    def generate_recommendations(self, config_params: Dict) -> Dict:
        """Generate sizing recommendations based on results"""
        peak = self.docker_collector.get_peak_metrics()
        
        if not peak:
            return {"error": "No metrics collected"}
        
        bots = config_params.get("bots", 1)
        
        # Calculate per-bot resources
        ram_per_bot = peak.get("peak_memory_mb", 0) / max(bots, 1)
        cpu_per_bot = peak.get("peak_cpu_percent", 0) / max(bots, 1)
        
        # Project for different scales
        scales = [10, 20, 30, 50]
        projections = {}
        
        for scale in scales:
            projections[f"{scale}_bots"] = {
                "estimated_ram_gb": round((ram_per_bot * scale) / 1024, 1),
                "estimated_cpu_cores": round((cpu_per_bot * scale) / 100, 1),
            }
        
        # VPS recommendations
        vps_recs = []
        ram_gb = peak.get("peak_memory_gb", 0)
        
        if ram_gb <= 8:
            vps_recs.append("4GB VPS suficiente para carga atual")
        elif ram_gb <= 16:
            vps_recs.append("8-16GB VPS recomendado")
        elif ram_gb <= 32:
            vps_recs.append("32GB VPS ou múltiplas instâncias recomendado")
        else:
            vps_recs.append("64GB+ VPS ou arquitetura distribuída necessária")
        
        return {
            "per_bot_resources": {
                "ram_mb": round(ram_per_bot, 2),
                "cpu_percent": round(cpu_per_bot, 2),
            },
            "projections": projections,
            "vps_recommendations": vps_recs,
        }
