from mathematical.factorial import Factorial

class BinomialCoefficient:
    def __init__(self):
        pass

    def apply(self, n: int, k: int) -> int:
        # Calculate the binomial coefficient C(n, k) = n! / (k! * (n-k)!)
        if k == 0 or n == k:
            return 1
        if k > n:
            return 0
        factorial = Factorial()
        n_factorial = factorial.apply(n)
        k_factorial = factorial.apply(k)
        n_k_factorial = factorial.apply(n - k)
        binomial_coefficient = n_factorial // (k_factorial * n_k_factorial)
        return binomial_coefficient