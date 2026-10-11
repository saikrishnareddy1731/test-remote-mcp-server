"""A small, typed FastMCP arithmetic server."""

from __future__ import annotations

import math

from fastmcp import FastMCP


mcp = FastMCP("Math Server")


def _as_number(value: float | int | str) -> float:
    """Convert numeric input to a finite float and raise a clear error."""
    if isinstance(value, bool):
        raise TypeError("Expected a number, not a boolean")

    try:
        number = float(value.strip() if isinstance(value, str) else value)
    except (TypeError, ValueError) as exc:
        raise TypeError("Expected a number or numeric string") from exc

    if not math.isfinite(number):
        raise ValueError("Number must be finite")

    return number


@mcp.tool()
async def add(a: float, b: float) -> float:
    """Return a + b."""
    return _as_number(a) + _as_number(b)


@mcp.tool()
async def subtract(a: float, b: float) -> float:
    """Return a - b."""
    return _as_number(a) - _as_number(b)


@mcp.tool()
async def multiply(a: float, b: float) -> float:
    """Return a * b."""
    return _as_number(a) * _as_number(b)


@mcp.tool()
async def divide(a: float, b: float) -> float:
    """Return a / b. Raises an error when b is zero."""
    numerator = _as_number(a)
    denominator = _as_number(b)
    if denominator == 0:
        raise ValueError("Cannot divide by zero")
    return numerator / denominator


@mcp.tool()
async def power(base: float, exponent: float) -> float:
    """Return base raised to exponent."""
    result = _as_number(base) ** _as_number(exponent)
    if isinstance(result, complex):
        raise ValueError("Result must be a real number")
    if not math.isfinite(result):
        raise ValueError("Result is too large")
    return result


@mcp.tool()
async def modulo(a: float, b: float) -> float:
    """Return the remainder of a divided by b."""
    dividend = _as_number(a)
    divisor = _as_number(b)
    if divisor == 0:
        raise ValueError("Cannot calculate modulo by zero")
    return dividend % divisor


@mcp.tool()
async def square_root(value: float) -> float:
    """Return the square root of a non-negative number."""
    number = _as_number(value)
    if number < 0:
        raise ValueError("Cannot calculate the square root of a negative number")
    return math.sqrt(number)


if __name__ == "__main__":
    # STDIO is ideal when an MCP host or Inspector starts this process.
    mcp.run(transport="stdio", show_banner=False)
