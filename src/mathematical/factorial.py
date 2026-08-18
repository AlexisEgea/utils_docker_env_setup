from monitor.complexity_runner import ComplexityRunner

class Factorial:
    def __init__(self, n: int = 0):
        """Initialize the factorial input value."""
        self.n = n

    def set_n(self, n: int) -> None:
        """Set the input value used by apply()."""
        self.n = n

    def apply(self) -> int:
        """Compute n! with an iterative descending loop."""
        result = 1
        if self.n == 0:
            return 1
        for i in range(self.n, 0, -1):
            result *= i
        return result
 
    def execute(self, complexity_runner: ComplexityRunner):
        """Handle user input, execute computation, and print report."""
        n = input("Enter number n= ")
        try: 
            n = int(n)
            if n < 0:
                print("Number must be positive")
                return
        except ValueError:
            print("Number must be a valid integer")
            return
        self.set_n(n)
        result, report = complexity_runner.run(self.apply)
        self.display_result(result)
        print(f"\n{report}")

    def display_result(self, result: int) -> None:
        """Display the factorial result in terminal."""
        print("\nFactorial result:")
        print(f"{self.n}! = {result}")