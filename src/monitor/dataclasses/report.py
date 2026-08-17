from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class Report:
    tracker_name: str = ""
    function_name: str = ""
    measure: dict[str, Any] = field(default_factory=dict)