"""Common interface definition for all implementation modules.

All language implementations (Pure Python, NumPy, C, C++, Cython, Rust)
must provide these functions with the specified signatures.
"""

from typing import List, Protocol


class ImplementationModule(Protocol):
    """Protocol defining the common interface for all implementations."""
    
    def find_primes(self, n: int) -> List[int]:
        """Find all prime numbers up to n using Sieve of Eratosthenes.
        
        Args:
            n: Upper limit for prime search
            
        Returns:
            List of all prime numbers <= n
        """
        ...
    
    def matrix_multiply(
        self,
        a: List[List[float]],
        b: List[List[float]]
    ) -> List[List[float]]:
        """Multiply two matrices.
        
        Args:
            a: First matrix (m x n)
            b: Second matrix (n x p)
            
        Returns:
            Result matrix (m x p)
        """
        ...
    
    def sort_array(self, arr: List[int]) -> List[int]:
        """Sort an array of integers.
        
        Args:
            arr: Array to sort
            
        Returns:
            Sorted array
        """
        ...
    
    def filter_array(self, arr: List[int], threshold: int) -> List[int]:
        """Filter array elements >= threshold.
        
        Args:
            arr: Array to filter
            threshold: Minimum value to keep
            
        Returns:
            Filtered array containing only elements >= threshold
        """
        ...
    
    def parallel_compute(self, data: List[float], num_threads: int) -> float:
        """Perform parallel computation (sum) using multiple threads.
        
        Args:
            data: Data to process
            num_threads: Number of threads to use
            
        Returns:
            Sum of all elements in data
        """
        ...
