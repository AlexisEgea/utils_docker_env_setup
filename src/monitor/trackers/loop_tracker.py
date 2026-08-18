import ast
import inspect
import textwrap
from typing import Any, Callable, Optional

from monitor.trackers.tracker import Tracker
from monitor.types.type_variables import T


class _LoopVisitor(ast.NodeVisitor):
    def __init__(
        self,
        bound_instance: object,
        call_arguments: dict[str, object],
        owner_method_name: str,
    ) -> None:
        """Initialize loop and recursion counters for AST traversal."""
        self.loop_count = 0
        self.max_depth = 0
        self.total_iterations = 0
        self.recursive_iterations = 0
        self.has_unknown_iterations = False
        self._current_depth = 0
        self._bound_instance = bound_instance
        self._call_arguments = call_arguments
        self._owner_method_name = owner_method_name

    def visit_For(self, node: ast.For) -> None:
        """Handle for-loop nodes."""
        self._enter_loop(node)

    def visit_While(self, node: ast.While) -> None:
        """Handle while-loop nodes."""
        self._enter_loop(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Track recursive call occurrences."""
        if self._is_recursive_call(node):
            self.recursive_iterations += 1

        self.generic_visit(node)

    def _enter_loop(self, node: ast.AST) -> None:
        """Register loop metrics and visit nested loop content."""
        self.loop_count += 1
        if isinstance(node, ast.For):
            iterations = self._estimate_for_iterations(node)
            if iterations is None:
                self.has_unknown_iterations = True
            else:
                self.total_iterations += iterations
        else:
            self.has_unknown_iterations = True
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
        self.generic_visit(node)
        self._current_depth -= 1

    def _estimate_for_iterations(self, node: ast.For) -> Optional[int]:
        """Estimate iteration count for range-based for-loops."""
        if not isinstance(node.iter, ast.Call):
            return None
        if not isinstance(node.iter.func, ast.Name) or node.iter.func.id != "range":
            return None

        evaluated_args = []
        for arg in node.iter.args:
            value = self._eval_numeric_expr(arg)
            if value is None:
                return None
            evaluated_args.append(int(value))

        if len(evaluated_args) == 1:
            start, stop, step = 0, evaluated_args[0], 1
        elif len(evaluated_args) == 2:
            start, stop = evaluated_args
            step = 1
        elif len(evaluated_args) == 3:
            start, stop, step = evaluated_args
        else:
            return None

        if step == 0:
            return None
        return len(range(start, stop, step))

    def _is_recursive_call(self, node: ast.Call) -> bool:
        """Detect whether a call node is recursive for the current method."""
        if isinstance(node.func, ast.Name):
            return node.func.id == self._owner_method_name
        if isinstance(node.func, ast.Attribute):
            return (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
                and node.func.attr == self._owner_method_name
            )
        return False

    def _eval_numeric_expr(self, node: ast.AST) -> Optional[float]:
        """Evaluate numeric AST expressions from known argument context."""
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)

        if isinstance(node, ast.Name):
            value = self._call_arguments.get(node.id)
            if isinstance(value, (int, float)):
                return float(value)
            return None

        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            if self._bound_instance is None:
                return None
            value = getattr(self._bound_instance, node.attr, None)
            if isinstance(value, (int, float)):
                return float(value)
            return None

        if isinstance(node, ast.UnaryOp):
            operand = self._eval_numeric_expr(node.operand)
            if operand is None:
                return None
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.UAdd):
                return operand
            return None

        if isinstance(node, ast.BinOp):
            left = self._eval_numeric_expr(node.left)
            right = self._eval_numeric_expr(node.right)
            if left is None or right is None:
                return None
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    return None
                return left // right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    return None
                return left / right
            return None

        return None


class LoopTracker(Tracker):
    """Tracks loop structures through static AST analysis."""

    def __init__(self) -> None:
        """Initialize default loop measurement values."""
        super().__init__()
        self._measurement: dict[str, object] = {
            "loops": 0,
            "max_depth": 0,
            "iterations": 0,
            "recursive_iterations": 0,
        }

    def start(self) -> dict[str, object]:
        """No-op start for static analysis tracker."""
        return self._measurement

    def stop(self) -> dict[str, object]:
        """No-op stop for static analysis tracker."""
        return self._measurement

    def analyze(self, func: Callable[..., T], *args: object, **kwargs: object) -> None:
        """Analyze target callable source and generate loop report."""
        self._measurement = self._extract_loop_metrics(func, *args, **kwargs)
        self.create_report(self._resolve_callable_name(func), self._measurement)

    def create_report(self, function_name: str, measurement: dict[str, object]) -> None:
        """Populate the tracker report with loop-related metrics."""
        self.report.tracker_name = "Loop Tracker"
        self.report.function_name = function_name
        self.report.measure["loops"] = measurement["loops"]
        self.report.measure["max_depth"] = measurement["max_depth"]
        self.report.measure["iterations"] = measurement["iterations"]
        self.report.measure["recursive_iterations"] = measurement["recursive_iterations"]

    def _extract_loop_metrics(self, func: Callable[..., T], *args: object, **kwargs: object) -> dict[str, object]:
        """Extract loop metrics for the target function and nested apply calls."""
        try:
            source = inspect.getsource(func)
        except (OSError, TypeError):
            return {
                "loops": 0,
                "max_depth": 0,
                "iterations": "unknown",
                "recursive_iterations": 0,
            }

        tree = ast.parse(textwrap.dedent(source))
        bound_instance = getattr(func, "__self__", None)
        call_arguments: dict[str, object] = {}
        try:
            signature = inspect.signature(func)
            bound = signature.bind_partial(*args, **kwargs)
            call_arguments = dict(bound.arguments)
        except (TypeError, ValueError):
            call_arguments = {}

        owner_method_name = getattr(func, "__name__", "callable")
        visitor = _LoopVisitor(bound_instance, call_arguments, owner_method_name)
        visitor.visit(tree)
        called_metrics = self._extract_called_apply_metrics(
            tree=tree,
            function_globals=getattr(func, "__globals__", {}),
            bound_instance=bound_instance,
            call_arguments=call_arguments,
        )
        visitor.loop_count += called_metrics["loops"]
        visitor.max_depth = max(visitor.max_depth, called_metrics["max_depth"])
        visitor.total_iterations += called_metrics["iterations"]
        visitor.recursive_iterations += called_metrics["recursive_iterations"]
        visitor.has_unknown_iterations = visitor.has_unknown_iterations or called_metrics["has_unknown_iterations"]

        iterations: object = visitor.total_iterations
        if visitor.has_unknown_iterations:
            iterations = "unknown" if visitor.total_iterations == 0 else f"{visitor.total_iterations}+"

        return {
            "loops": visitor.loop_count,
            "max_depth": visitor.max_depth,
            "iterations": iterations,
            "recursive_iterations": visitor.recursive_iterations,
        }

    def _extract_called_apply_metrics(
        self,
        tree: ast.AST,
        function_globals: dict[str, Any],
        bound_instance: object,
        call_arguments: dict[str, object],
    ) -> dict[str, object]:
        """Aggregate loop metrics from constructor(...).apply() nested calls."""
        loops = 0
        max_depth = 0
        iterations = 0
        recursive_iterations = 0
        has_unknown_iterations = False

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "apply":
                continue
            if not isinstance(node.func.value, ast.Call):
                continue

            constructor_call = node.func.value
            if not isinstance(constructor_call.func, ast.Name):
                has_unknown_iterations = True
                continue

            class_name = constructor_call.func.id
            class_obj = function_globals.get(class_name)
            if class_obj is None:
                has_unknown_iterations = True
                continue

            constructor_values: list[object] = []
            ctor_has_unknown = False
            for ctor_arg in constructor_call.args:
                value = self._eval_numeric_expr(ctor_arg, bound_instance, call_arguments)
                if value is None:
                    ctor_has_unknown = True
                    break
                constructor_values.append(int(value))
            if ctor_has_unknown:
                has_unknown_iterations = True
                continue

            try:
                called_instance = class_obj(*constructor_values)
                called_apply = getattr(called_instance, "apply", None)
            except Exception:
                has_unknown_iterations = True
                continue

            if not callable(called_apply):
                has_unknown_iterations = True
                continue

            try:
                called_source = inspect.getsource(called_apply)
            except (OSError, TypeError):
                has_unknown_iterations = True
                continue

            called_tree = ast.parse(textwrap.dedent(called_source))
            called_visitor = _LoopVisitor(called_instance, {}, "apply")
            called_visitor.visit(called_tree)

            loops += called_visitor.loop_count
            max_depth = max(max_depth, called_visitor.max_depth)
            iterations += called_visitor.total_iterations
            recursive_iterations += called_visitor.recursive_iterations
            has_unknown_iterations = has_unknown_iterations or called_visitor.has_unknown_iterations

        return {
            "loops": loops,
            "max_depth": max_depth,
            "iterations": iterations,
            "recursive_iterations": recursive_iterations,
            "has_unknown_iterations": has_unknown_iterations,
        }

    def _eval_numeric_expr(
        self,
        node: ast.AST,
        bound_instance: object,
        call_arguments: dict[str, object],
    ) -> Optional[float]:
        """Evaluate numeric AST expressions from known runtime values."""
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)

        if isinstance(node, ast.Name):
            value = call_arguments.get(node.id)
            if isinstance(value, (int, float)):
                return float(value)
            return None

        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            if bound_instance is None:
                return None
            value = getattr(bound_instance, node.attr, None)
            if isinstance(value, (int, float)):
                return float(value)
            return None

        if isinstance(node, ast.UnaryOp):
            operand = self._eval_numeric_expr(node.operand, bound_instance, call_arguments)
            if operand is None:
                return None
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.UAdd):
                return operand
            return None

        if isinstance(node, ast.BinOp):
            left = self._eval_numeric_expr(node.left, bound_instance, call_arguments)
            right = self._eval_numeric_expr(node.right, bound_instance, call_arguments)
            if left is None or right is None:
                return None
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    return None
                return left // right
            if isinstance(node.op, ast.Div):
                if right == 0:
                    return None
                return left / right
            return None

        return None
