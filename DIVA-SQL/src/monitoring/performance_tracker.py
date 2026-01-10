"""
Performance Tracker for DIVA-SQL

Monitors and tracks performance metrics to ensure latency targets are met:
- Simple queries: 2.3 seconds target
- Complex queries: 5.8 seconds target
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import time
from enum import Enum
import json


class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    timestamp: datetime
    query_id: str
    complexity: QueryComplexity
    total_time_ms: float
    breakdown: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Aggregated performance statistics"""
    total_queries: int
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    p50_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    by_complexity: Dict[str, Dict[str, float]]


class PerformanceTracker:
    """
    Track and analyze DIVA-SQL performance
    
    Monitors:
    - End-to-end query generation time
    - Per-stage timing (decomposition, generation, verification)
    - Complexity-based performance
    - Target achievement (2.3s simple, 5.8s complex)
    """
    
    # Performance targets from research
    TARGET_SIMPLE_MS = 2300  # 2.3 seconds
    TARGET_COMPLEX_MS = 5800  # 5.8 seconds
    
    def __init__(self):
        """Initialize performance tracker"""
        self.metrics: List[PerformanceMetric] = []
        self.active_timers: Dict[str, Dict[str, Any]] = {}
    
    def start_tracking(self, query_id: str, complexity: QueryComplexity = QueryComplexity.MODERATE) -> str:
        """
        Start tracking a query
        
        Args:
            query_id: Unique identifier for the query
            complexity: Query complexity level
            
        Returns:
            Tracking ID
        """
        tracking_id = f"{query_id}_{int(time.time() * 1000)}"
        
        self.active_timers[tracking_id] = {
            "query_id": query_id,
            "complexity": complexity,
            "start_time": time.time(),
            "stages": {},
            "metadata": {}
        }
        
        return tracking_id
    
    def start_stage(self, tracking_id: str, stage_name: str):
        """Start timing a specific stage"""
        if tracking_id in self.active_timers:
            self.active_timers[tracking_id]["stages"][stage_name] = {
                "start_time": time.time()
            }
    
    def end_stage(self, tracking_id: str, stage_name: str):
        """End timing a specific stage"""
        if tracking_id in self.active_timers:
            timer = self.active_timers[tracking_id]
            if stage_name in timer["stages"]:
                stage = timer["stages"][stage_name]
                stage["end_time"] = time.time()
                stage["duration_ms"] = (stage["end_time"] - stage["start_time"]) * 1000
    
    def end_tracking(self, tracking_id: str, metadata: Optional[Dict[str, Any]] = None) -> PerformanceMetric:
        """
        End tracking and record metric
        
        Args:
            tracking_id: Tracking ID from start_tracking
            metadata: Additional metadata to store
            
        Returns:
            PerformanceMetric with recorded data
        """
        if tracking_id not in self.active_timers:
            raise ValueError(f"No active timer for tracking_id: {tracking_id}")
        
        timer = self.active_timers[tracking_id]
        end_time = time.time()
        total_time_ms = (end_time - timer["start_time"]) * 1000
        
        # Build breakdown
        breakdown = {}
        for stage_name, stage_data in timer["stages"].items():
            if "duration_ms" in stage_data:
                breakdown[stage_name] = stage_data["duration_ms"]
        
        # Merge metadata
        combined_metadata = {**timer.get("metadata", {}), **(metadata or {})}
        
        # Create metric
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            query_id=timer["query_id"],
            complexity=timer["complexity"],
            total_time_ms=total_time_ms,
            breakdown=breakdown,
            metadata=combined_metadata
        )
        
        self.metrics.append(metric)
        del self.active_timers[tracking_id]
        
        return metric
    
    def get_statistics(self, 
                      complexity: Optional[QueryComplexity] = None,
                      since: Optional[datetime] = None) -> PerformanceStats:
        """
        Get performance statistics
        
        Args:
            complexity: Filter by complexity (None for all)
            since: Only include metrics after this time
            
        Returns:
            PerformanceStats with aggregated data
        """
        # Filter metrics
        filtered = self.metrics
        
        if complexity:
            filtered = [m for m in filtered if m.complexity == complexity]
        
        if since:
            filtered = [m for m in filtered if m.timestamp >= since]
        
        if not filtered:
            return PerformanceStats(
                total_queries=0,
                avg_time_ms=0.0,
                min_time_ms=0.0,
                max_time_ms=0.0,
                p50_time_ms=0.0,
                p95_time_ms=0.0,
                p99_time_ms=0.0,
                by_complexity={}
            )
        
        # Calculate statistics
        times = sorted([m.total_time_ms for m in filtered])
        
        stats = PerformanceStats(
            total_queries=len(filtered),
            avg_time_ms=sum(times) / len(times),
            min_time_ms=min(times),
            max_time_ms=max(times),
            p50_time_ms=self._percentile(times, 50),
            p95_time_ms=self._percentile(times, 95),
            p99_time_ms=self._percentile(times, 99),
            by_complexity=self._stats_by_complexity(filtered)
        )
        
        return stats
    
    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0
        
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def _stats_by_complexity(self, metrics: List[PerformanceMetric]) -> Dict[str, Dict[str, float]]:
        """Calculate statistics grouped by complexity"""
        by_complexity = {}
        
        for complexity in QueryComplexity:
            complexity_metrics = [m for m in metrics if m.complexity == complexity]
            
            if complexity_metrics:
                times = sorted([m.total_time_ms for m in complexity_metrics])
                by_complexity[complexity.value] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "p50_ms": self._percentile(times, 50),
                    "p95_ms": self._percentile(times, 95)
                }
        
        return by_complexity
    
    def check_targets(self) -> Dict[str, Any]:
        """
        Check if performance targets are being met
        
        Returns:
            Dictionary with target achievement status
        """
        simple_metrics = [m for m in self.metrics if m.complexity == QueryComplexity.SIMPLE]
        complex_metrics = [m for m in self.metrics if m.complexity == QueryComplexity.COMPLEX]
        
        results = {
            "simple_queries": {
                "target_ms": self.TARGET_SIMPLE_MS,
                "count": len(simple_metrics),
                "avg_ms": 0.0,
                "target_met": False,
                "percentage_within_target": 0.0
            },
            "complex_queries": {
                "target_ms": self.TARGET_COMPLEX_MS,
                "count": len(complex_metrics),
                "avg_ms": 0.0,
                "target_met": False,
                "percentage_within_target": 0.0
            }
        }
        
        if simple_metrics:
            avg_simple = sum(m.total_time_ms for m in simple_metrics) / len(simple_metrics)
            within_target = sum(1 for m in simple_metrics if m.total_time_ms <= self.TARGET_SIMPLE_MS)
            
            results["simple_queries"]["avg_ms"] = avg_simple
            results["simple_queries"]["target_met"] = avg_simple <= self.TARGET_SIMPLE_MS
            results["simple_queries"]["percentage_within_target"] = (within_target / len(simple_metrics)) * 100
        
        if complex_metrics:
            avg_complex = sum(m.total_time_ms for m in complex_metrics) / len(complex_metrics)
            within_target = sum(1 for m in complex_metrics if m.total_time_ms <= self.TARGET_COMPLEX_MS)
            
            results["complex_queries"]["avg_ms"] = avg_complex
            results["complex_queries"]["target_met"] = avg_complex <= self.TARGET_COMPLEX_MS
            results["complex_queries"]["percentage_within_target"] = (within_target / len(complex_metrics)) * 100
        
        return results
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        data = {
            "metrics": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "query_id": m.query_id,
                    "complexity": m.complexity.value,
                    "total_time_ms": m.total_time_ms,
                    "breakdown": m.breakdown,
                    "metadata": m.metadata
                }
                for m in self.metrics
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_report(self) -> str:
        """Generate human-readable performance report"""
        lines = []
        lines.append("=" * 70)
        lines.append("DIVA-SQL Performance Report")
        lines.append("=" * 70)
        
        # Overall statistics
        stats = self.get_statistics()
        lines.append(f"\nTotal Queries Processed: {stats.total_queries}")
        lines.append(f"Average Time: {stats.avg_time_ms:.2f}ms")
        lines.append(f"Min Time: {stats.min_time_ms:.2f}ms")
        lines.append(f"Max Time: {stats.max_time_ms:.2f}ms")
        lines.append(f"P50 (Median): {stats.p50_time_ms:.2f}ms")
        lines.append(f"P95: {stats.p95_time_ms:.2f}ms")
        lines.append(f"P99: {stats.p99_time_ms:.2f}ms")
        
        # By complexity
        if stats.by_complexity:
            lines.append("\n" + "-" * 70)
            lines.append("Performance by Complexity:")
            lines.append("-" * 70)
            
            for complexity, comp_stats in stats.by_complexity.items():
                lines.append(f"\n{complexity.upper()}:")
                lines.append(f"  Count: {comp_stats['count']}")
                lines.append(f"  Average: {comp_stats['avg_ms']:.2f}ms")
                lines.append(f"  Min: {comp_stats['min_ms']:.2f}ms")
                lines.append(f"  Max: {comp_stats['max_ms']:.2f}ms")
                lines.append(f"  P50: {comp_stats['p50_ms']:.2f}ms")
                lines.append(f"  P95: {comp_stats['p95_ms']:.2f}ms")
        
        # Target achievement
        targets = self.check_targets()
        lines.append("\n" + "-" * 70)
        lines.append("Target Achievement:")
        lines.append("-" * 70)
        
        for query_type, target_data in targets.items():
            status = "✓ MET" if target_data["target_met"] else "✗ NOT MET"
            lines.append(f"\n{query_type.replace('_', ' ').title()}:")
            lines.append(f"  Target: {target_data['target_ms']}ms")
            lines.append(f"  Average: {target_data['avg_ms']:.2f}ms")
            lines.append(f"  Status: {status}")
            lines.append(f"  Within Target: {target_data['percentage_within_target']:.1f}%")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    tracker = PerformanceTracker()
    
    # Simulate tracking a simple query
    tracking_id = tracker.start_tracking("query_001", QueryComplexity.SIMPLE)
    
    tracker.start_stage(tracking_id, "decomposition")
    time.sleep(0.1)  # Simulate work
    tracker.end_stage(tracking_id, "decomposition")
    
    tracker.start_stage(tracking_id, "generation")
    time.sleep(0.15)  # Simulate work
    tracker.end_stage(tracking_id, "generation")
    
    tracker.start_stage(tracking_id, "verification")
    time.sleep(0.05)  # Simulate work
    tracker.end_stage(tracking_id, "verification")
    
    metric = tracker.end_tracking(tracking_id, metadata={"success": True})
    
    print(f"Query completed in {metric.total_time_ms:.2f}ms")
    print(f"Breakdown: {metric.breakdown}")
    
    # Generate report
    print("\n" + tracker.generate_report())
    
    # Check targets
    targets = tracker.check_targets()
    print(f"\nTargets: {json.dumps(targets, indent=2)}")
