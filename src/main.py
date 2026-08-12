from mathematical.factorial import Factorial
from mathematical.binomial_coefficient import BinomialCoefficient

def get_explanation():
    return """
    -----------------------------------------------------------------------------
    |                          Factorial Calculator                             |
    | Author : Alexis EGEA                                                      |
    |                                                                           |
    | Explanation: This program can calculate the factorial of a number (n!) or |
    | the binomial coefficient (C(n, k)).                         |
    | Enter "exit" to exit the program.                                         |
    -----------------------------------------------------------------------------"""

def factorial_execution():
    n = input("Enter number n= ")
    try: 
        n = int(n)
        if n < 0:
            print("Number must be positive")
            return
        result = factorial.apply(n)
        print(f"{n}! = {result}")
    except ValueError:
        print("Number must be a valid integer")
        return

def binomial_coefficient_execution():
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
    result = binomial_coefficient.apply(n, k)
    print(f"C({n}, {k}) = {result}")
    max_len = max(len(str(n)), len(str(k)))
    if len(str(n)) > len(str(k)):
        k = str(k) + " " * (len(str(n)) - len(str(k)))
    else:
        n = str(n) + " " * (len(str(k)) - len(str(n)))
    print(f"( {n} )")
    print("| " + " " * (max_len) + f" | = {result}")
    print(f"( {k} )")

if __name__ == "__main__":
    is_running = True
    factorial = Factorial()
    binomial_coefficient = BinomialCoefficient()
    print(get_explanation())
    while is_running:
        operation = input(
            "\nSelect an operation:\n"
            " 1. Factorial\n"
            " 2. Binomial Coefficient\n"
            " 3. 'exit' to end the program\n\n"
            "Operation: "
        )
        if operation == "1":
            print("Factorial selected")
            factorial_execution()
        elif operation == "2":
            print("Binomial Coefficient selected")
            binomial_coefficient_execution()
        elif operation == "3" or operation == "exit":
            is_running = False
        else:
            print("Invalid operation")
            continue
