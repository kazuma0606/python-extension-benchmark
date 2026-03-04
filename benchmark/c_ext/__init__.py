"""C extension implementation module."""

from typing import List

try:
    from . import numeric as _numeric
    from . import memory as _memory
    from . import parallel as _parallel
    
    # Re-export functions with the common interface
    def find_primes(n: int) -> List[int]:
        """Find all prime numbers up to n using Sieve of Eratosthenes."""
        return _numeric.find_primes(n)
    
    def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Multiply two matrices."""
        return _numeric.matrix_multiply(a, b)
    
    def sort_array(arr: List[int]) -> List[int]:
        """Sort an array of integers."""
        return _memory.sort_array(arr)
    
    def filter_array(arr: List[int], threshold: int) -> List[int]:
        """Filter array elements >= threshold."""
        return _memory.filter_array(arr, threshold)
    
    def parallel_compute(data: List[float], num_threads: int) -> float:
        """Perform parallel computation (sum) using multiple threads."""
        return _parallel.parallel_compute(data, num_threads)

except ImportError as e:
    # Fallback if C extensions are not built
    import warnings
    warnings.warn(f"C extensions not available: {e}. Functions will raise NotImplementedError.")
    
    def find_primes(n: int) -> List[int]:
        raise NotImplementedError("C extension not built")
    
    def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        raise NotImplementedError("C extension not built")
    
    def sort_array(arr: List[int]) -> List[int]:
        raise NotImplementedError("C extension not built")
    
    def filter_array(arr: List[int], threshold: int) -> List[int]:
        raise NotImplementedError("C extension not built")
    
    def parallel_compute(data: List[float], num_threads: int) -> float:
        raise NotImplementedError("C extension not built")