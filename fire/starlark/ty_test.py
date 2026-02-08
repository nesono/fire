"""Test file to verify ty type checking."""


def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


# This should pass type checking
result: int = add_numbers(5, 10)
