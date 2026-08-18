from __future__ import annotations

import tracemalloc
from typing import Optional

from monitor.trackers.tracker import Tracker
from monitor.types.type_variables import T


class AllocationTracker(Tracker):
    """Tracks allocation/deallocation events and bytes."""

    def __init__(self) -> None:
        """Initialize snapshot state for allocation measurement."""
        super().__init__()
        self._start_snapshot: Optional[tracemalloc.Snapshot] = None

    def start(self) -> T:
        """Capture baseline allocation snapshot."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        self._start_snapshot = tracemalloc.take_snapshot()
        return None

    def stop(self) -> T:
        """Return allocation metrics based on snapshot differences."""
        if self._start_snapshot is None:
            return {
                "allocations": 0,
                "deallocations": 0,
                "net_allocations": 0,
                "allocated_bytes": 0,
                "freed_bytes": 0,
                "net_bytes": 0,
            }

        end_snapshot = tracemalloc.take_snapshot()
        stats = end_snapshot.compare_to(self._start_snapshot, "lineno")

        allocations = sum(stat.count_diff for stat in stats if stat.count_diff > 0)
        deallocations = -sum(stat.count_diff for stat in stats if stat.count_diff < 0)
        net_allocations = sum(stat.count_diff for stat in stats)

        allocated_bytes = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
        freed_bytes = -sum(stat.size_diff for stat in stats if stat.size_diff < 0)
        net_bytes = sum(stat.size_diff for stat in stats)

        self._start_snapshot = None
        return {
            "allocations": allocations,
            "deallocations": deallocations,
            "net_allocations": net_allocations,
            "allocated_bytes": allocated_bytes,
            "freed_bytes": freed_bytes,
            "net_bytes": net_bytes,
        }

    def create_report(self, function_name: str, measurement: dict[str, int]) -> None:
        """Populate tracker report with allocation metrics."""
        self.report.tracker_name = "Allocation Tracker"
        self.report.function_name = function_name
        self.report.measure["allocations"] = measurement["allocations"]
        self.report.measure["deallocations"] = measurement["deallocations"]
        self.report.measure["net_allocations"] = measurement["net_allocations"]
        self.report.measure["allocated_bytes"] = self._format_bytes(measurement["allocated_bytes"])
        self.report.measure["freed_bytes"] = self._format_bytes(measurement["freed_bytes"])
        self.report.measure["net_bytes"] = self._format_signed_bytes(measurement["net_bytes"])

    
