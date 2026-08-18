import ast
import inspect
import textwrap
from typing import Any, Callable, Optional

from monitor.trackers.tracker import Tracker
from monitor.types.type_variables import T


class _AffectationVisitor(ast.NodeVisitor):
    def __init__(self, bound_instance: object, call_arguments: dict[str, object]) -> None:
        """Prepare dynamic assignment counting context."""
        self.affectations = 0
        self._multiplier_stack = [1]
        self._bound_instance = bound_instance
        self._call_arguments = call_arguments

    @property
    def _multiplier(self) -> int:
        """Return the current multiplicative execution factor."""
        return self._multiplier_stack[-1]

    def _eval_numeric_expr(self, node: ast.AST) -> Optional[float]:
        """Evaluate a numeric AST node using known call context values."""
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

    def _estimate_range_iterations(self, node: ast.For) -> Optional[int]:
        """Estimate iteration count for range(...) loops."""
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

    def _target_count(self, target: ast.AST) -> int:
        """Count how many target variables are assigned in a loop target."""
        if isinstance(target, (ast.Tuple, ast.List)):
            return sum(self._target_count(elt) for elt in target.elts)
        return 1

    def visit_Assign(self, node: ast.Assign) -> None:
        """Count plain assignment operations."""
        self.affectations += self._multiplier * len(node.targets)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Count annotated assignments."""
        self.affectations += self._multiplier
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Count augmented assignments (e.g., +=, *=)."""
        self.affectations += self._multiplier
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        """Count walrus operator assignments."""
        self.affectations += self._multiplier
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Count loop-variable assignments and scaled body assignments."""
        iterations = self._estimate_range_iterations(node)
        if iterations is None:
            iterations = 1

        # Loop variable assignment happens for each iteration.
        self.affectations += self._multiplier * iterations * self._target_count(node.target)

        self._multiplier_stack.append(self._multiplier * iterations)
        for stmt in node.body:
            self.visit(stmt)
        self._multiplier_stack.pop()

        for stmt in node.orelse:
            self.visit(stmt)

    def visit_While(self, node: ast.While) -> None:
        """Count while-loop body once when dynamic iterations are unknown."""
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)


class AffectationTracker(Tracker):
    """Tracks assignment operations in the analyzed function."""

    def __init__(self) -> None:
        """Initialize assignment measurement state."""
        super().__init__()
        self._measurement: dict[str, int] = {"affectations": 0}

    def start(self) -> dict[str, int]:
        """No-op start to keep tracker interface consistent."""
        return self._measurement

    def stop(self) -> dict[str, int]:
        """No-op stop to keep tracker interface consistent."""
        return self._measurement

    def analyze(self, func: Callable[..., T], *args: object, **kwargs: object) -> None:
        """Analyze target function and update assignment report."""
        self._measurement = self._extract_affectation_metrics(func, set())
        self.create_report(self._resolve_callable_name(func), self._measurement)

    def create_report(self, function_name: str, measurement: dict[str, int]) -> None:
        """Populate tracker report with assignment metrics."""
        self.report.tracker_name = "Affectation Tracker"
        self.report.function_name = function_name
        self.report.measure["affectations"] = measurement["affectations"]

    def _extract_affectation_metrics(
        self,
        func: Callable[..., T],
        visited: set[int],
        *args: object,
        **kwargs: object,
    ) -> dict[str, int]:
        """Extract assignment count from function and nested apply calls."""
        func_id = id(func)
        if func_id in visited:
            return {"affectations": 0}
        visited.add(func_id)

        try:
            source = inspect.getsource(func)
        except (OSError, TypeError):
            return {"affectations": 0}

        tree = ast.parse(textwrap.dedent(source))
        bound_instance = getattr(func, "__self__", None)
        call_arguments: dict[str, object] = {}
        try:
            signature = inspect.signature(func)
            bound = signature.bind_partial(*args, **kwargs)
            call_arguments = dict(bound.arguments)
        except (TypeError, ValueError):
            call_arguments = {}

        visitor = _AffectationVisitor(bound_instance, call_arguments)
        visitor.visit(tree)

        nested_affectations = self._extract_called_apply_affectations(
            tree=tree,
            function_globals=getattr(func, "__globals__", {}),
            bound_instance=bound_instance,
            call_arguments=call_arguments,
            visited=visited,
        )
        return {"affectations": visitor.affectations + nested_affectations}

    def _extract_called_apply_affectations(
        self,
        tree: ast.AST,
        function_globals: dict[str, Any],
        bound_instance: object,
        call_arguments: dict[str, object],
        visited: set[int],
    ) -> int:
        """Extract assignment count from constructor().apply() nested calls."""
        nested_total = 0

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "apply":
                continue
            if not isinstance(node.func.value, ast.Call):
                continue
            if not isinstance(node.func.value.func, ast.Name):
                continue

            class_name = node.func.value.func.id
            class_obj = function_globals.get(class_name)
            if class_obj is None:
                continue

            constructor_values: list[object] = []
            ctor_has_unknown = False
            for ctor_arg in node.func.value.args:
                value = self._eval_numeric_expr(ctor_arg, bound_instance, call_arguments)
                if value is None:
                    ctor_has_unknown = True
                    break
                constructor_values.append(int(value))
            if ctor_has_unknown:
                continue

            try:
                called_instance = class_obj(*constructor_values)
                called_apply = getattr(called_instance, "apply", None)
            except Exception:
                continue

            if callable(called_apply):
                nested_total += self._extract_affectation_metrics(called_apply, visited)["affectations"]

        return nested_total

    def _eval_numeric_expr(
        self,
        node: ast.AST,
        bound_instance: object,
        call_arguments: dict[str, object],
    ) -> Optional[float]:
        """Evaluate a numeric AST node using function call context."""
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
