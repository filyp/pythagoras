import numpy as np


def decompose_into_small_primes(n, primes=[2, 3, 5, 7]):
    factors = np.zeros_like(primes)
    while n != 1:
        updated = False
        for i, prime in enumerate(primes):
            if n % prime == 0:
                n /= prime
                factors[i] += 1 
                updated = True
        if not updated:
            # n cannot be decomposed into those primes
            return None
    return factors