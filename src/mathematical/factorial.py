class Factorial:
    def __init__(self):
        pass

    def apply(self, n: int) -> int:
        # Recursive implementation to calculate the factorial of a non-negative integer n
        if n == 0:
            return 1
        return n * self.apply(n - 1)
 