from mathematical.factorial import Factorial
from mathematical.binomial_coefficient import BinomialCoefficient
from mathematical.serie import Serie
from monitor.complexity_runner import ComplexityRunner

def get_explanation():
    return """
    -----------------------------------------------------------------------------
    |                    Mathematical Toolkit and Profiler                      |
    | Author : Alexis EGEA                                                      |
    |                                                                           |
    | This program computes factorial, binomial coefficient, and custom series  |
    | expressions (+, -, *, /, parentheses).                                    |
    | It also prints a complexity profiler report with timing, loops, memory,   |
    | allocations, and affectations for each execution.                         |
    | Enter "exit" to exit the program.                                         |
    -----------------------------------------------------------------------------"""

if __name__ == "__main__":
    is_running = True
    factorial = Factorial()
    binomial_coefficient = BinomialCoefficient()
    serie = Serie()
    complexity_runner = ComplexityRunner(strict=True)
    print(get_explanation())
    while is_running:
        operation = input(
            "\nSelect an operation:\n"
            " 1. Factorial\n"
            " 2. Binomial Coefficient\n"
            " 3. Serie (custom expression)\n"
            " 4. 'exit' to end the program\n\n"
            "Operation: "
        )
        if operation == "1":
            print("Factorial selected")
            factorial.execute(complexity_runner)
        elif operation == "2":
            print("Binomial Coefficient selected")
            binomial_coefficient.execute(complexity_runner)
        elif operation == "3":
            print("Serie selected")
            serie.execute(complexity_runner)
        elif operation == "4" or operation == "exit":
            is_running = False
        else:
            print("Invalid operation")
            continue
