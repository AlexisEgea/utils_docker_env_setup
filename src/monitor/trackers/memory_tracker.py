from __future__ import annotations

import tracemalloc
from typing import Optional

from monitor.trackers.tracker import Tracker
from monitor.types.type_variables import T


class MemoryTracker(Tracker):
    """Tracks memory usage (current, peak, and net delta)."""

    def __init__(self) -> None:
        """Initialize snapshot state for memory measurement."""
        super().__init__()
        self._start_snapshot: Optional[tracemalloc.Snapshot] = None

    def start(self) -> T:
        """Capture a baseline memory snapshot."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        self._start_snapshot = tracemalloc.take_snapshot()
        return None

    def stop(self) -> T:
        """Capture end snapshot and return memory metrics."""
        if self._start_snapshot is None:
            return {"current_bytes": 0, "peak_bytes": 0, "net_bytes": 0}

        end_snapshot = tracemalloc.take_snapshot()
        current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        stats = end_snapshot.compare_to(self._start_snapshot, "filename")
        net_bytes = sum(stat.size_diff for stat in stats)

        self._start_snapshot = None
        return {
            "current_bytes": current_bytes,
            "peak_bytes": peak_bytes,
            "net_bytes": net_bytes,
        }

    def create_report(self, function_name: str, measurement: dict[str, int]) -> None:
        """Populate the tracker report with memory metrics."""
        self.report.tracker_name = "Memory Tracker"
        self.report.function_name = function_name
        self.report.measure["current_memory"] = self._format_bytes(measurement["current_bytes"])
        self.report.measure["peak_memory"] = self._format_bytes(measurement["peak_bytes"])
        self.report.measure["net_memory_change"] = self._format_signed_bytes(measurement["net_bytes"])
