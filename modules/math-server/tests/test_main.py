import asyncio

import pytest

from main import add, divide, modulo, multiply, power, square_root, subtract


def run(coroutine):
    return asyncio.run(coroutine)


def test_arithmetic_tools():
    assert run(add(2, 3)) == 5
    assert run(subtract(10, 4)) == 6
    assert run(multiply(6, 7)) == 42
    assert run(divide(9, 3)) == 3
    assert run(power(2, 8)) == 256
    assert run(modulo(10, 3)) == 1
    assert run(square_root(81)) == 9


def test_zero_division_errors():
    with pytest.raises(ValueError, match="divide by zero"):
        run(divide(1, 0))

    with pytest.raises(ValueError, match="modulo by zero"):
        run(modulo(1, 0))


def test_negative_square_root_errors():
    with pytest.raises(ValueError, match="negative number"):
        run(square_root(-1))
