"""Pure Python implementation of numeric computation functions."""

from typing import List


def find_primes(n: int) -> List[int]:
    """Find all prime numbers up to n using Sieve of Eratosthenes.
    
    Args:
        n: Upper limit for prime search
        
    Returns:
        List of all prime numbers <= n
    """
    if n < 2:
        return []
    
    # Initialize sieve: True means potentially prime
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    
    # Sieve of Eratosthenes
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            # Mark all multiples of i as not prime
            for j in range(i * i, n + 1, i):
                is_prime[j] = False
    
    # Collect all primes
    return [i for i in range(n + 1) if is_prime[i]]


def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Multiply two matrices.
    
    Args:
        a: First matrix (m x n)
        b: Second matrix (n x p)
        
    Returns:
        Result matrix (m x p)
    """
    if not a or not b or not a[0] or not b[0]:
        return [[]]
    
    m = len(a)
    n = len(a[0])
    p = len(b[0])
    
    # Verify dimensions are compatible
    if len(b) != n:
        raise ValueError(f"Incompatible matrix dimensions: {m}x{n} and {len(b)}x{p}")
    
    # Initialize result matrix with zeros
    result = [[0.0 for _ in range(p)] for _ in range(m)]
    
    # Perform matrix multiplication
    for i in range(m):
        for j in range(p):
            for k in range(n):
                result[i][j] += a[i][k] * b[k][j]
    
    return result
