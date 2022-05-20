# tests for the dashboard
from dashboard_helpers import *


def test_decomposition_into_primes():
    primes = [2, 3, 5, 7]
    assert list(decompose_into_small_primes(1, primes)) == [0, 0, 0, 0]
    assert list(decompose_into_small_primes(2, primes)) == [1, 0, 0, 0]
    assert list(decompose_into_small_primes(3, primes)) == [0, 1, 0, 0]
    assert list(decompose_into_small_primes(4, primes)) == [2, 0, 0, 0]
    assert list(decompose_into_small_primes(5, primes)) == [0, 0, 1, 0]
    assert list(decompose_into_small_primes(6, primes)) == [1, 1, 0, 0]
    assert list(decompose_into_small_primes(7, primes)) == [0, 0, 0, 1]
    assert list(decompose_into_small_primes(8, primes)) == [3, 0, 0, 0]
    assert list(decompose_into_small_primes(9, primes)) == [0, 2, 0, 0]
    assert list(decompose_into_small_primes(10, primes)) == [1, 0, 1, 0]
    assert decompose_into_small_primes(11, primes) == None
    assert list(decompose_into_small_primes(12, primes)) == [2, 1, 0, 0]
    assert decompose_into_small_primes(13, primes) == None
    assert list(decompose_into_small_primes(14, primes)) == [1, 0, 0, 1]
