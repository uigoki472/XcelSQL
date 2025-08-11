"""Performance profiling utilities for the xcelsql application."""
from __future__ import annotations
from typing import Dict, List, Optional
import time
import logging
import contextlib
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ProfileStats:
    """Statistics for a profiled operation."""
    name: str
    calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    
    @property
    def avg_time(self) -> float:
        """Calculate average execution time."""
        return self.total_time / self.calls if self.calls > 0 else 0

class Profiler:
    """Simple performance profiler for measuring operation execution time."""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.stats: Dict[str, ProfileStats] = {}
        self._start_times: Dict[str, float] = {}
    
    def start(self, name: str) -> None:
        """Start timing an operation."""
        if not self.enabled:
            return
        self._start_times[name] = time.time()
    
    def stop(self, name: str) -> None:
        """Stop timing an operation and record statistics."""
        if not self.enabled or name not in self._start_times:
            return
            
        elapsed = time.time() - self._start_times[name]
        del self._start_times[name]
        
        if name not in self.stats:
            self.stats[name] = ProfileStats(name=name)
        
        stat = self.stats[name]
        stat.calls += 1
        stat.total_time += elapsed
        stat.min_time = min(stat.min_time, elapsed)
        stat.max_time = max(stat.max_time, elapsed)
    
    @contextlib.contextmanager
    def profile(self, name: str):
        """Context manager for profiling a block of code."""
        self.start(name)
        try:
            yield
        finally:
            self.stop(name)
    
    def reset(self) -> None:
        """Reset all profiling statistics."""
        self.stats.clear()
        self._start_times.clear()
    
    def report(self) -> List[Dict[str, float]]:
        """Generate a report of profiling statistics."""
        result = []
        for name, stat in sorted(self.stats.items(), key=lambda x: x[1].total_time, reverse=True):
            result.append({
                'name': name,
                'calls': stat.calls,
                'total_time': round(stat.total_time, 4),
                'avg_time': round(stat.avg_time, 4),
                'min_time': round(stat.min_time, 4),
                'max_time': round(stat.max_time, 4)
            })
        return result
    
    def print_report(self) -> None:
        """Print profiling statistics to the log."""
        if not self.enabled or not self.stats:
            return
            
        report = self.report()
        
        logger.info("Performance Profile:")
        logger.info("%-25s %10s %10s %10s %10s %10s", 
                   "Operation", "Calls", "Total(s)", "Avg(s)", "Min(s)", "Max(s)")
        logger.info("-" * 80)
        
        for entry in report:
            logger.info("%-25s %10d %10.4f %10.4f %10.4f %10.4f",
                      entry['name'], entry['calls'], entry['total_time'],
                      entry['avg_time'], entry['min_time'], entry['max_time'])

# Global profiler instance
profiler = Profiler()