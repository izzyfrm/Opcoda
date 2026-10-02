# Tiny starter data only. Replace/add far more original or permissively licensed code.

def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b


def is_even(number):
    return number % 2 == 0


def clamp(value, low, high):
    return max(low, min(value, high))
