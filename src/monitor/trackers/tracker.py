from monitor.dataclasses.report import Report
from typing import Callable
from monitor.types.type_variables import T
from abc import ABC, abstractmethod

class Tracker(ABC):
    """Base class for all trackers."""

    def __init__(self):
        """Initialize the shared report container."""
        self.report: Report = Report()

    def get_report(self) -> Report:
        """Return the latest tracker report."""
        return self.report

    @abstractmethod
    def start(self) -> T:
        """Begin the measurement process (to be implemented by subclasses)."""
        pass

    @abstractmethod
    def stop(self) -> T:
        """End the measurement process and return a measurement value (to be implemented by subclasses)."""
        pass
   

    def measure(self, func: Callable[..., T], *args: object, **kwargs: object) -> T:
        """Execute a function, measure it, and refresh the report."""
        self.start()
        try:
            result = func(*args, **kwargs)
        finally:
            measurement = self.stop()
            self.create_report(self._resolve_callable_name(func), measurement)
        return result

    @staticmethod
    def _resolve_callable_name(func: Callable[..., T]) -> str:
        """Return a readable callable name, including class for bound methods."""
        bound_instance = getattr(func, "__self__", None)
        method_name = getattr(func, "__name__", "callable")
        if bound_instance is not None:
            class_name = bound_instance.__class__.__name__.lower()
            return f"{class_name}.{method_name}"
        return method_name

    @staticmethod
    def _format_duration(duration_ns: int) -> str:
        """Convert nanoseconds to a compact human-readable duration."""
        if duration_ns >= 3_600_000_000_000:
            total_seconds = duration_ns / 1_000_000_000
            hours = int(total_seconds // 3600)
            remaining_seconds = total_seconds % 3600
            minutes = int(remaining_seconds // 60)
            seconds = remaining_seconds % 60
            return f"{hours} h {minutes} min {seconds:.3f} s"
        if duration_ns >= 60_000_000_000:
            total_seconds = duration_ns / 1_000_000_000
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes} min {seconds:.3f} s"
        if duration_ns >= 1_000_000_000:
            return f"{duration_ns / 1_000_000_000:.3f} s"
        if duration_ns >= 1_000_000:
            return f"{duration_ns / 1_000_000:.3f} ms"
        if duration_ns >= 1_000:
            return f"{duration_ns / 1_000:.3f} us"
        return f"{duration_ns} ns"

    @staticmethod
    def _format_bytes(size_bytes: int) -> str:
        abs_size = float(abs(size_bytes))
        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        while abs_size >= 1024 and unit_index < len(units) - 1:
            abs_size /= 1024
            unit_index += 1
        return f"{abs_size:.3f} {units[unit_index]}"

    @classmethod
    def _format_signed_bytes(cls, size_bytes: int) -> str:
        sign = "+" if size_bytes >= 0 else "-"
        return f"{sign}{cls._format_bytes(size_bytes)}"