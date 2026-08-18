from __future__ import annotations

from time import perf_counter_ns
from typing import Optional

from monitor.types.type_variables import T

from monitor.trackers.tracker import Tracker

class ExecutionTimeTracker(Tracker):
    """Tracks execution time for a function run."""

    def __init__(self, strict: bool = True) -> None:
        """Initialize tracker state and strict-mode behavior."""
        super().__init__()
        self.strict = strict
        self._start_ns: Optional[int] = None

    def start(self) -> T:
        """Start a new timing window."""
        if self._start_ns is not None:
            if self.strict:
                raise RuntimeError("ExecutionTimeTracker is already running.")
            print("Warning: ExecutionTimeTracker.start() called while already running.")
            return
        self._start_ns = perf_counter_ns()

    def stop(self) -> T:
        """Close the timing window and return measured duration."""
        if self._start_ns is None:
            if self.strict:
                raise RuntimeError("ExecutionTimeTracker was not started.")
            print("Warning: ExecutionTimeTracker.stop() called before start().")
            return 0

        execution_time_ns = perf_counter_ns() - self._start_ns
        self._start_ns = None
        return execution_time_ns

    def create_report(self, function_name: str, measurement: int) -> None:
        """Populate the tracker report with formatted execution metrics."""
        self.report.tracker_name = "Time Tracker"
        self.report.function_name = function_name
        self.report.measure["execution_time"] = self._format_duration(measurement)