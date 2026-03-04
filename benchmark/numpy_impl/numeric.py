"""NumPy implementation of numeric computation functions."""

import numpy as np
from typing import List


def find_primes(n: int) -> List[int]:
    """Find all prime numbers up to n using vectorized Sieve of Eratosthenes.
    
    Args:
        n: Upper limit for prime search
        
    Returns:
        List of all prime numbers <= n
    """
    if n < 2:
        return []
    
    # Initialize sieve using NumPy array: True means potentially prime
    is_prime = np.ones(n + 1, dtype=bool)
    is_prime[0] = is_prime[1] = False
    
    # Vectorized Sieve of Eratosthenes
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            # Mark all multiples of i as not prime using vectorized operations
            is_prime[i*i::i] = False
    
    # Use NumPy's where to get indices of primes
    primes = np.where(is_prime)[0]
    
    # Return as Python list to match interface
    return primes.tolist()


def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Multiply two matrices using NumPy's optimized matmul.
    
    Args:
        a: First matrix (m x n)
        b: Second matrix (n x p)
        
    Returns:
        Result matrix (m x p)
    """
    if not a or not b or not a[0] or not b[0]:
        return [[]]
    
    # Convert to NumPy arrays
    a_np = np.array(a, dtype=float)
    b_np = np.array(b, dtype=float)
    
    # Verify dimensions are compatible
    if a_np.shape[1] != b_np.shape[0]:
        raise ValueError(
            f"Incompatible matrix dimensions: {a_np.shape[0]}x{a_np.shape[1]} "
            f"and {b_np.shape[0]}x{b_np.shape[1]}"
        )
    
    # Use NumPy's optimized matrix multiplication
    result = np.matmul(a_np, b_np)
    
    # Convert back to Python list of lists
    return result.tolist()
