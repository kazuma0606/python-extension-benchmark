# cython: language_level=3
"""Cython implementation of numeric computation functions."""

from typing import List
cimport cython
from libc.math cimport sqrt
from libc.stdlib cimport malloc, free


@cython.boundscheck(False)
@cython.wraparound(False)
def find_primes(int n) -> List[int]:
    """Find all prime numbers up to n using Sieve of Eratosthenes.
    
    Args:
        n: Upper limit for prime search
        
    Returns:
        List of all prime numbers <= n
    """
    if n < 2:
        return []
    
    cdef int i, j
    cdef int sqrt_n = int(sqrt(n)) + 1
    cdef char* is_prime = <char*>malloc((n + 1) * sizeof(char))
    
    if is_prime == NULL:
        raise MemoryError("Failed to allocate memory for sieve")
    
    try:
        # Initialize sieve: 1 means potentially prime
        for i in range(n + 1):
            is_prime[i] = 1
        is_prime[0] = is_prime[1] = 0
        
        # Sieve of Eratosthenes
        for i in range(2, sqrt_n):
            if is_prime[i]:
                # Mark all multiples of i as not prime
                j = i * i
                while j <= n:
                    is_prime[j] = 0
                    j += i
        
        # Collect all primes
        primes = []
        for i in range(n + 1):
            if is_prime[i]:
                primes.append(i)
        
        return primes
    
    finally:
        free(is_prime)


@cython.boundscheck(False)
@cython.wraparound(False)
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
    
    cdef int m = len(a)
    cdef int n = len(a[0])
    cdef int p = len(b[0])
    
    # Verify dimensions are compatible
    if len(b) != n:
        raise ValueError(f"Incompatible matrix dimensions: {m}x{n} and {len(b)}x{p}")
    
    # Initialize result matrix with zeros
    result = [[0.0 for _ in range(p)] for _ in range(m)]
    
    cdef int i, j, k
    cdef double temp
    
    # Perform matrix multiplication
    for i in range(m):
        for j in range(p):
            temp = 0.0
            for k in range(n):
                temp += a[i][k] * b[k][j]
            result[i][j] = temp
    
    return result