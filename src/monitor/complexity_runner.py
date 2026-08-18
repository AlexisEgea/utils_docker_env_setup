from typing import Callable, Tuple

import tracemalloc

from monitor.trackers.affectation_tracker import AffectationTracker
from monitor.trackers.execution_time_tracker import ExecutionTimeTracker
from monitor.trackers.loop_tracker import LoopTracker
from monitor.trackers.memory_tracker import MemoryTracker
from monitor.trackers.allocation_tracker import AllocationTracker
from monitor.report_generator import ReportGenerator
from monitor.types.type_variables import T


class ComplexityRunner:
    """Minimal runner wired to the execution-time tracker."""

    def __init__(self, strict: bool = True) -> None:
        """Create runner and initialize core tracker dependencies."""
        self.execution_time_tracker = ExecutionTimeTracker(strict=strict)
        self.affectation_tracker = AffectationTracker()
        self.loop_tracker = LoopTracker()
        self.memory_tracker = MemoryTracker()
        self.allocation_tracker = AllocationTracker()
        self.report_generator = ReportGenerator()

    def run(self, func: Callable[..., T], *args: object, **kwargs: object) -> Tuple[T, str]:
        """Run a target function and return its result with formatted report."""
        function_name = self.execution_time_tracker._resolve_callable_name(func)
        tracemalloc.start()
        self.memory_tracker.start()
        self.allocation_tracker.start()

        try:
            result = self.execution_time_tracker.measure(func, *args, **kwargs)
        finally:
            memory_measurement = self.memory_tracker.stop()
            allocation_measurement = self.allocation_tracker.stop()
            self.memory_tracker.create_report(function_name, memory_measurement)
            self.allocation_tracker.create_report(function_name, allocation_measurement)
            tracemalloc.stop()

        self.affectation_tracker.analyze(func, *args, **kwargs)
        self.loop_tracker.analyze(func, *args, **kwargs)
        report = self.report_generator.generate_report(
            [
                self.execution_time_tracker.get_report(),
                self.affectation_tracker.get_report(),
                self.loop_tracker.get_report(),
                self.memory_tracker.get_report(),
                self.allocation_tracker.get_report(),
            ]
        )
        return result, report