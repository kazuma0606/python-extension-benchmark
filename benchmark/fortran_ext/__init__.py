"""Fortran extension modules for Python benchmark using f2py."""

try:
    # Import compiled Fortran modules
    from .numeric import numeric_functions
    from .memory import memory_functions
    from .parallel import parallel_functions
    import numpy as np
    
    def find_primes(n):
        """Find all prime numbers up to n using Sieve of Eratosthenes."""
        primes, count = numeric_functions.find_primes_impl(n)
        return primes[:count].tolist()
    
    def matrix_multiply(a, b):
        """Multiply two matrices."""
        a_array = np.array(a, dtype=np.float64)
        b_array = np.array(b, dtype=np.float64)
        m, n = a_array.shape
        n2, p = b_array.shape
        
        if n != n2:
            raise ValueError(f"Incompatible matrix dimensions: {m}x{n} and {n2}x{p}")
        
        c = numeric_functions.matrix_multiply_impl(a_array, b_array)
        return c.tolist()
    
    def sort_array(arr):
        """Sort an array of integers."""
        arr_copy = np.array(arr, dtype=np.int32)
        memory_functions.sort_array_impl(arr_copy)
        return arr_copy.tolist()
    
    def filter_array(arr, threshold):
        """Filter array elements >= threshold."""
        arr_array = np.array(arr, dtype=np.int32)
        result, count = memory_functions.filter_array_impl(arr_array, threshold)
        return result[:count].tolist()
    
    def parallel_compute(data, num_threads):
        """Perform parallel computation (sum) using multiple threads."""
        data_array = np.array(data, dtype=np.float64)
        result = parallel_functions.parallel_compute_impl(data_array, num_threads)
        return float(result)
    
    __all__ = [
        'find_primes',
        'matrix_multiply', 
        'sort_array',
        'filter_array',
        'parallel_compute'
    ]
    
except ImportError as e:
    # Fallback message if Fortran modules are not compiled
    import warnings
    warnings.warn(
        f"Fortran extensions not available: {e}. "
        "Please build the extensions using: python build_fortran_ext.py",
        ImportWarning
    )
    
    # Provide dummy functions that raise NotImplementedError
    def find_primes(n):
        raise NotImplementedError("Fortran extensions not compiled")
    
    def matrix_multiply(a, b):
        raise NotImplementedError("Fortran extensions not compiled")
    
    def sort_array(arr):
        raise NotImplementedError("Fortran extensions not compiled")
    
    def filter_array(arr, threshold):
        raise NotImplementedError("Fortran extensions not compiled")
    
    def parallel_compute(data, num_threads):
        raise NotImplementedError("Fortran extensions not compiled")
    
    __all__ = [
        'find_primes',
        'matrix_multiply', 
        'sort_array',
        'filter_array',
        'parallel_compute'
    ]