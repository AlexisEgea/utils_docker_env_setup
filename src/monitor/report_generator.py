from monitor.dataclasses.report import Report


class ReportGenerator:
    """Builds human-readable reports from tracker measurements."""

    def generate_report(self, reports: list[Report]) -> str:
        """Build a full boxed Unicode report from one or more tracker outputs."""
        if not reports:
            return ""

        function_name = reports[0].function_name if reports[0].function_name else "unknown"
        lines: list[str] = []

        lines.append("COMPLEXITY PROFILER")
        lines.append("")
        lines.append(f"Function : {function_name}")

        for report_index, tracker_report in enumerate(reports):
            lines.append("")
            tracker_name = tracker_report.tracker_name if tracker_report.tracker_name else "Tracker"
            lines.append(tracker_name)

            measure_items = list(tracker_report.measure.items())
            for item_index, (key, value) in enumerate(measure_items):
                branch = "└──" if item_index == len(measure_items) - 1 else "├──"
                formatted_key = self._format_label(str(key))
                lines.append(f"{branch} {formatted_key:<12} : {value}")
            if report_index != len(reports) - 1:
                lines.append("")

        return self._build_box(lines)

    def _build_box(self, lines: list[str]) -> str:
        """Render a Unicode text box with dynamic width and aligned borders."""
        inner_width = max(len(line) for line in lines)
        top_border = "╔" + "═" * (inner_width + 2) + "╗"
        separator = "╠" + "═" * (inner_width + 2) + "╣"
        bottom_border = "╚" + "═" * (inner_width + 2) + "╝"

        boxed_lines = [top_border]
        for index, line in enumerate(lines):
            if index == 0:
                line = line.center(inner_width)
            padded_line = line.ljust(inner_width)
            boxed_lines.append(f"║ {padded_line} ║")
            if index == 0:
                boxed_lines.append(separator)
        boxed_lines.append(bottom_border)
        return "\n".join(boxed_lines)

    @staticmethod
    def _format_label(raw_label: str) -> str:
        """Normalize metric labels for display."""
        normalized = raw_label.replace("_", " ").strip()
        return normalized.capitalize()
