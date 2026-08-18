import ast
from typing import Callable, Optional

from monitor.complexity_runner import ComplexityRunner


class Serie:
    def __init__(self):
        """Initialize series bounds and operation state."""
        self.k = 0
        self.n = 0
        self.operation: Optional[Callable[[int], float]] = None
        self.operation_expression = "x"


    def set_k(self, k: int) -> None:
        """Set the lower bound index for the series."""
        self.k = k

    def set_n(self, n: int) -> None:
        """Set the upper bound index for the series."""
        self.n = n

    def set_operation(self, operation: Callable[[int], float]) -> None:
        """Set the callable operation applied to each index."""
        self.operation = operation

    def apply(self) -> float:
        """Compute a series by applying an injected operation on each index."""
        if self.k < 0 or self.n < 0:
            raise ValueError("k and n must be positive")
        if self.k > self.n:
            raise ValueError("k must be less than or equal to n")
        if self.operation is None:
            raise ValueError("Operation is not defined.")

        total = 0.0
        for value in range(self.k, self.n + 1):
            total += self.operation(value)
        return total

    @staticmethod
    def _build_expression_operation(expression: str):
        """Create a safe callable operation f(x) from a math expression."""
        try:
            parsed = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise ValueError("Invalid expression syntax.") from exc

        def evaluate_node(node: ast.AST, x_value: float) -> float:
            if isinstance(node, ast.Expression):
                return evaluate_node(node.body, x_value)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return float(node.value)
            if isinstance(node, ast.Name):
                if node.id != "x":
                    raise ValueError("Only variable 'x' is allowed.")
                return float(x_value)
            if isinstance(node, ast.BinOp):
                left = evaluate_node(node.left, x_value)
                right = evaluate_node(node.right, x_value)
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                if isinstance(node.op, ast.Div):
                    return left / right
                raise ValueError("Only +, -, * and / operators are allowed.")
            if isinstance(node, ast.UnaryOp):
                operand = evaluate_node(node.operand, x_value)
                if isinstance(node.op, ast.UAdd):
                    return operand
                if isinstance(node.op, ast.USub):
                    return -operand
                raise ValueError("Unsupported unary operator.")
            raise ValueError("Unsupported expression.")

        for ast_node in ast.walk(parsed):
            allowed_nodes = (
                ast.Expression,
                ast.BinOp,
                ast.UnaryOp,
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.Div,
                ast.UAdd,
                ast.USub,
                ast.Constant,
                ast.Name,
                ast.Load,
            )
            if not isinstance(ast_node, allowed_nodes):
                raise ValueError("Expression contains forbidden operations.")

        return lambda x: evaluate_node(parsed, x)

    def execute(self, complexity_runner: ComplexityRunner) -> None:
        """Collect CLI inputs, compute the series, and print report."""
        self.display_init()
        k = input("1. Enter first index of x=")
        try:
            k = int(k)
            if k < 0:
                print("value must be positive")
                return
        except ValueError:
            print("value must be a valid integer")
            return

        n = input("2. Enter last index of x=")
        try:
            n = int(n)
            if n < 0:
                print("value must be positive")
                return
        except ValueError:
            print("value must be a valid integer")
            return

        if k > n:
            print("value must be less than or equal to n")
            return

        examples = (
            "Expression examples:"
            "  - Addition: x + 4\n"
            "  - Subtraction: x - 2\n"
            "  - Multiplication: x * 7\n"
            "  - Division: x / 3\n"
            "  - Parentheses: (x + 4) * 7"
        )
        print(examples)
        expression = input("3. Enter operation in terms of x: ")
        try:
            operation = self._build_expression_operation(expression)
            self.set_k(k)
            self.set_n(n)
            self.set_operation(operation)
            self.operation_expression = expression
            result, report = complexity_runner.run(self.apply)
        except ZeroDivisionError:
            print("Division by zero is not allowed.")
            return
        except ValueError as exc:
            print(str(exc))
            return

        self.display_result(result)
        print(f"\n{report}")

    def display_result(self, result: float) -> None:
        """Render a sigma-style output for the computed series."""
        print("\nSeries result:")
        print(f" {self.n}")
        print("____")
        print("\\")
        print(f"/    {self.operation_expression} = {result:.6f}")
        print("____")
        print(f"x = {self.k}")

    def display_init(self) -> None:
        """Display a small visual guide before user input."""
        print(f"2. ???")
        print("____")
        print("\\")
        print(f"/    3. ???")
        print("____")
        print(f"1. x = ???")
        print("You will be guided through each step in sequence.")
   
