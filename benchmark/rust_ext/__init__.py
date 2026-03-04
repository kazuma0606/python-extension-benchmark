"""Rust extension implementation module."""

try:
    import rust_ext
    
    # Re-export the functions from the compiled Rust module
    find_primes = rust_ext.find_primes
    matrix_multiply = rust_ext.matrix_multiply
    sort_array = rust_ext.sort_array
    filter_array = rust_ext.filter_array
    parallel_compute = rust_ext.parallel_compute
    
    __all__ = [
        'find_primes',
        'matrix_multiply', 
        'sort_array',
        'filter_array',
        'parallel_compute'
    ]
    
except ImportError as e:
    # If the Rust extension is not built, provide a helpful error message
    import warnings
    warnings.warn(
        f"Rust extension not available: {e}. "
        "Please build it using: python build_rust_ext.py",
        ImportWarning
    )
    
    # Provide stub functions that raise NotImplementedError
    def find_primes(n):
        raise NotImplementedError("Rust extension not built")
    
    def matrix_multiply(a, b):
        raise NotImplementedError("Rust extension not built")
    
    def sort_array(arr):
        raise NotImplementedError("Rust extension not built")
    
    def filter_array(arr, threshold):
        raise NotImplementedError("Rust extension not built")
    
    def parallel_compute(data, num_threads):
        raise NotImplementedError("Rust extension not built")
    
    __all__ = [
        'find_primes',
        'matrix_multiply', 
        'sort_array',
        'filter_array',
        'parallel_compute'
    ]