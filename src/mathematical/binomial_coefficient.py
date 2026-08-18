from mathematical.factorial import Factorial
from monitor.complexity_runner import ComplexityRunner

class BinomialCoefficient:
    def __init__(self):
        """Initialize n and k values for C(n, k)."""
        self.n = 0
        self.k = 0

    def set_k(self, k: int) -> None:
        """Set the k value used by apply()."""
        self.k = k

    def set_n(self, n: int) -> None:
        """Set the n value used by apply()."""
        self.n = n

    def apply(self) -> int:
        """Compute the binomial coefficient C(n, k)."""
        if self.k == 0 or self.n == self.k:
            return 1
        if self.k > self.n:
            return 0
        n_factorial = Factorial(self.n).apply()
        k_factorial = Factorial(self.k).apply()
        n_k_factorial = Factorial(self.n - self.k).apply()
        binomial_coefficient = n_factorial // (k_factorial * n_k_factorial)
        return binomial_coefficient


    def execute(self, complexity_runner: ComplexityRunner):
        """Handle user input, execute computation, and print report."""
        n = int(input("Enter number n= "))
        try: 
            n = int(n)
            if n < 0:
                print("Number must be positive")
                return
        except ValueError:
            print("Number must be a valid integer")
            return
        k = input("Enter number k= ")
        try: 
            k = int(k)
            if k < 0:
                print("Number must be positive")
                return
        except ValueError:
            print("Number must be a valid integer")
            return
        self.set_n(n)
        self.set_k(k)
        result, report = complexity_runner.run(self.apply)

        self.display_result(result)
        print(f"\n{report}")
        
    def display_result(self, result: int) -> None:
        """Display the binomial coefficient result in terminal."""
        print("\nBinomial coefficient result:")
        print(f"C({self.n}, {self.k}) = {result}")
        max_len = max(len(str(self.n)), len(str(self.k)))
        if len(str(self.n)) > len(str(self.k)):
            self.k = str(self.k) + " " * (len(str(self.n)) - len(str(self.k)))
        else:
            self.n = str(self.n) + " " * (len(str(self.k)) - len(str(self.n)))
        print(f"( {self.n} )")
        print("| " + " " * (max_len) + f" | = {result}")
        print(f"( {self.k} )")
