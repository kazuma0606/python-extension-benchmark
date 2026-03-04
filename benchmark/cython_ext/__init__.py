"""Cython implementation module for benchmark.

This module provides Cython implementations of the benchmark functions
with type annotations and optimizations for better performance.
"""

try:
    # Import compiled Cython modules
    from .numeric import find_primes, matrix_multiply
    from .memory import sort_array, filter_array
    from .parallel import parallel_compute
    
    __all__ = [
        'find_primes',
        'matrix_multiply', 
        'sort_array',
        'filter_array',
        'parallel_compute'
    ]
    
except ImportError as e:
    # Fallback message if Cython modules are not compiled
    import warnings
    warnings.warn(
        f"Cython extensions not available: {e}. "
        "Please build the extensions using: python benchmark/cython_ext/setup.py build_ext --inplace",
        ImportWarning
    )
    
    # Provide dummy functions that raise NotImplementedError
    def find_primes(n):
        raise NotImplementedError("Cython extensions not compiled")
    
    def matrix_multiply(a, b):
        raise NotImplementedError("Cython extensions not compiled")
    
    def sort_array(arr):
        raise NotImplementedError("Cython extensions not compiled")
    
    def filter_array(arr, threshold):
        raise NotImplementedError("Cython extensions not compiled")
    
    def parallel_compute(data, num_threads):
        raise NotImplementedError("Cython extensions not compiled")
    
    __all__ = [
        'find_primes',
        'matrix_multiply', 
        'sort_array',
        'filter_array',
        'parallel_compute'
    ]
