from typing import Callable, Tuple

from monitor.trackers.execution_time_tracker import ExecutionTimeTracker
from monitor.report_generator import ReportGenerator
from monitor.types.type_variables import T


class ComplexityRunner:
    """Minimal runner wired to the execution-time tracker."""

    def __init__(self, strict: bool = True) -> None:
        """Create runner and initialize core tracker dependencies."""
        self.execution_time_tracker = ExecutionTimeTracker(strict=strict)
        self.report_generator = ReportGenerator()

    def run(self, func: Callable[..., T], *args: object, **kwargs: object) -> Tuple[T, str]:
        """Run a target function and return its result with formatted report."""
        result = self.execution_time_tracker.measure(func, *args, **kwargs)
        report = self.report_generator.generate_report([self.execution_time_tracker.get_report()])
        return result, report