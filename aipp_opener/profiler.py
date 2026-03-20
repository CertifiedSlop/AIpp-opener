"""Performance profiling tools for AIpp Opener."""

import time
import cProfile
import pstats
import io
import json
from pathlib import Path
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps

from aipp_opener.logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class ProfileResult:
    """Result of a profiling operation."""

    function_name: str
    total_time: float
    call_count: int
    time_per_call: float
    cumulative_time: float
    callers: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "function_name": self.function_name,
            "total_time_ms": round(self.total_time * 1000, 2),
            "call_count": self.call_count,
            "time_per_call_ms": round(self.time_per_call * 1000, 4),
            "cumulative_time_ms": round(self.cumulative_time * 1000, 2),
            "callers": self.callers,
        }


class PerformanceProfiler:
    """Performance profiler for AIpp Opener."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the performance profiler.

        Args:
            output_dir: Directory for profile output files.
        """
        if output_dir is None:
            output_dir = Path.home() / ".local" / "state" / "aipp_opener" / "profiles"

        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._active_profile: Optional[cProfile.Profile] = None
        self._profile_data: Dict[str, ProfileResult] = {}

    @contextmanager
    def profile_block(self, name: str):
        """
        Context manager for profiling a code block.

        Args:
            name: Name for the profiled block.

        Yields:
            None

        Example:
            with profiler.profile_block("app_detection"):
                apps = detector.detect()
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            logger.info("Profile [%s]: %.3f ms", name, elapsed * 1000)

            if name not in self._profile_data:
                self._profile_data[name] = ProfileResult(
                    function_name=name,
                    total_time=0,
                    call_count=0,
                    time_per_call=0,
                    cumulative_time=0,
                )

            result = self._profile_data[name]
            result.total_time += elapsed
            result.call_count += 1
            result.time_per_call = result.total_time / result.call_count
            result.cumulative_time += elapsed

    def profile_function(self, func: Callable) -> Callable:
        """
        Decorator for profiling a function.

        Args:
            func: Function to profile.

        Returns:
            Wrapped function with profiling.

        Example:
            @profiler.profile_function
            def detect_apps():
                ...
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.profile_block(func.__name__):
                return func(*args, **kwargs)

        return wrapper

    def start_profiling(self) -> None:
        """Start cProfile for detailed profiling."""
        self._active_profile = cProfile.Profile()
        self._active_profile.enable()
        logger.info("Started detailed profiling")

    def stop_profiling(self) -> Optional[ProfileResult]:
        """
        Stop cProfile and return results.

        Returns:
            Profile results or None if not started.
        """
        if not self._active_profile:
            return None

        self._active_profile.disable()

        # Parse stats
        stream = io.StringIO()
        stats = pstats.Stats(self._active_profile, stream=stream)
        stats.sort_stats('cumulative')

        # Get top functions
        results = []
        for func_key, func_stats in stats.stats.items():
            filename, line_no, func_name = func_key
            cc, nc, tt, ct, callers = func_stats

            if tt > 0.001:  # Only include functions taking > 1ms
                result = ProfileResult(
                    function_name=f"{func_name}:{line_no}",
                    total_time=tt,
                    call_count=nc,
                    time_per_call=tt / nc if nc > 0 else 0,
                    cumulative_time=ct,
                )
                results.append(result)

        logger.info("Stopped detailed profiling, found %d functions", len(results))
        return results[0] if results else None

    def save_profile(self, name: str = "profile") -> Path:
        """
        Save profile data to file.

        Args:
            name: Name for the profile file.

        Returns:
            Path to saved profile file.
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.json"
        filepath = self.output_dir / filename

        data = {
            "timestamp": timestamp,
            "profiles": {
                name: result.to_dict()
                for name, result in self._profile_data.items()
            },
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("Saved profile to %s", filepath)
        return filepath

    def get_slowest(self, limit: int = 10) -> list[ProfileResult]:
        """
        Get the slowest profiled operations.

        Args:
            limit: Maximum number of results.

        Returns:
            List of slowest operations.
        """
        sorted_results = sorted(
            self._profile_data.values(),
            key=lambda x: x.cumulative_time,
            reverse=True,
        )
        return sorted_results[:limit]

    def reset(self) -> None:
        """Reset all profile data."""
        self._profile_data.clear()
        self._active_profile = None
        logger.info("Reset profile data")

    def print_report(self, limit: int = 20) -> None:
        """
        Print a profiling report.

        Args:
            limit: Maximum number of entries to print.
        """
        if not self._profile_data:
            print("No profile data available")
            return

        print("\n" + "=" * 80)
        print("PERFORMANCE PROFILE REPORT")
        print("=" * 80)

        sorted_results = sorted(
            self._profile_data.values(),
            key=lambda x: x.cumulative_time,
            reverse=True,
        )

        print(f"\n{'Function':<40} {'Calls':>8} {'Total (ms)':>12} {'Avg (ms)':>12} {'Cumul (ms)':>12}")
        print("-" * 84)

        for result in sorted_results[:limit]:
            print(
                f"{result.function_name:<40} "
                f"{result.call_count:>8} "
                f"{result.total_time * 1000:>12.2f} "
                f"{result.time_per_call * 1000:>12.4f} "
                f"{result.cumulative_time * 1000:>12.2f}"
            )

        print("=" * 80 + "\n")


# Global profiler instance
_profiler: Optional[PerformanceProfiler] = None


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler


def profile_block(name: str):
    """
    Convenience function for profiling a code block.

    Args:
        name: Name for the profiled block.

    Returns:
        Context manager.

    Example:
        with profile_block("my_operation"):
            do_something()
    """
    return get_profiler().profile_block(name)


def profile_function(func: Callable) -> Callable:
    """
    Convenience decorator for profiling a function.

    Args:
        func: Function to profile.

    Returns:
        Wrapped function.
    """
    return get_profiler().profile_function(func)


def print_profile_report(limit: int = 20) -> None:
    """Print profiling report from global profiler."""
    get_profiler().print_report(limit=limit)


def save_profile_report(name: str = "profile") -> Path:
    """Save profiling report from global profiler."""
    return get_profiler().save_profile(name)
