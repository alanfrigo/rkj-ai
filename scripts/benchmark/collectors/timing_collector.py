"""
Timing Collector
Measures execution time of operations
"""
import time
import functools
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class TimingEntry:
    """A single timing measurement"""
    operation: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool = True
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class TimingCollector:
    """Collects timing measurements for various operations"""
    
    def __init__(self):
        self.timings: List[TimingEntry] = []
        self._active_timers: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> str:
        """Start a timer for an operation, returns timer ID"""
        timer_id = f"{operation}_{time.time()}"
        self._active_timers[timer_id] = time.time()
        return timer_id
    
    def stop_timer(self, timer_id: str, success: bool = True, 
                   error: Optional[str] = None, metadata: dict = None) -> TimingEntry:
        """Stop a timer and record the measurement"""
        if timer_id not in self._active_timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        start_time = self._active_timers.pop(timer_id)
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Extract operation name from timer_id
        operation = timer_id.rsplit('_', 1)[0]
        
        entry = TimingEntry(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            duration_ms=round(duration_ms, 2),
            success=success,
            error=error,
            metadata=metadata or {}
        )
        self.timings.append(entry)
        return entry
    
    @contextmanager
    def measure(self, operation: str, metadata: dict = None):
        """Context manager for measuring operation time"""
        timer_id = self.start_timer(operation)
        success = True
        error = None
        try:
            yield
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            self.stop_timer(timer_id, success=success, error=error, metadata=metadata or {})
    
    def timed(self, operation: str = None):
        """Decorator for measuring function execution time"""
        def decorator(func: Callable):
            op_name = operation or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                timer_id = self.start_timer(op_name)
                success = True
                error = None
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    self.stop_timer(timer_id, success=success, error=error)
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                timer_id = self.start_timer(op_name)
                success = True
                error = None
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    self.stop_timer(timer_id, success=success, error=error)
            
            if asyncio_iscoroutinefunction(func):
                return async_wrapper
            return wrapper
        return decorator
    
    def record(self, operation: str, duration_ms: float, success: bool = True,
               error: Optional[str] = None, metadata: dict = None):
        """Manually record a timing entry"""
        entry = TimingEntry(
            operation=operation,
            start_time=time.time() - (duration_ms / 1000),
            end_time=time.time(),
            duration_ms=round(duration_ms, 2),
            success=success,
            error=error,
            metadata=metadata or {}
        )
        self.timings.append(entry)
        return entry
    
    def get_timings_by_operation(self, operation: str) -> List[TimingEntry]:
        """Get all timings for a specific operation"""
        return [t for t in self.timings if t.operation == operation]
    
    def get_statistics(self, operation: str = None) -> Dict:
        """Get statistics for timings, optionally filtered by operation"""
        timings = self.get_timings_by_operation(operation) if operation else self.timings
        
        if not timings:
            return {}
        
        durations = [t.duration_ms for t in timings]
        successful = [t for t in timings if t.success]
        failed = [t for t in timings if not t.success]
        
        # Calculate percentiles
        sorted_durations = sorted(durations)
        n = len(sorted_durations)
        
        return {
            "count": len(timings),
            "success_count": len(successful),
            "failure_count": len(failed),
            "success_rate": round(len(successful) / len(timings) * 100, 2) if timings else 0,
            "min_ms": round(min(durations), 2),
            "max_ms": round(max(durations), 2),
            "avg_ms": round(sum(durations) / len(durations), 2),
            "p50_ms": round(sorted_durations[int(n * 0.5)], 2),
            "p90_ms": round(sorted_durations[int(n * 0.9)], 2),
            "p95_ms": round(sorted_durations[int(n * 0.95)], 2),
            "p99_ms": round(sorted_durations[min(int(n * 0.99), n-1)], 2),
            "total_ms": round(sum(durations), 2),
        }
    
    def get_all_operations(self) -> List[str]:
        """Get list of all unique operations"""
        return list(set(t.operation for t in self.timings))
    
    def get_summary(self) -> Dict:
        """Get summary of all operations"""
        summary = {}
        for operation in self.get_all_operations():
            summary[operation] = self.get_statistics(operation)
        return summary
    
    def clear(self):
        """Clear all timings"""
        self.timings = []
        self._active_timers = {}


def asyncio_iscoroutinefunction(func):
    """Check if function is async"""
    import asyncio
    return asyncio.iscoroutinefunction(func)
