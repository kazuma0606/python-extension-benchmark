"""C++ extension modules for Python benchmark using pybind11."""

try:
    from .numeric import find_primes, matrix_multiply
    from .memory import sort_array, filter_array
    from .parallel import parallel_compute
    
    __all__ = ['find_primes', 'matrix_multiply', 'sort_array', 'filter_array', 'parallel_compute']
    
except ImportError as e:
    import warnings
    warnings.warn(f"Failed to import C++ extensions: {e}. "
                  "Make sure to build the extensions first using: "
                  "cd benchmark/cpp_ext && python setup.py build_ext --inplace")
    
    # Define placeholder functions that raise NotImplementedError
    def find_primes(n):
        raise NotImplementedError("C++ extension not built")
    
    def matrix_multiply(a, b):
        raise NotImplementedError("C++ extension not built")
    
    def sort_array(arr):
        raise NotImplementedError("C++ extension not built")
    
    def filter_array(arr, threshold):
        raise NotImplementedError("C++ extension not built")
    
    def parallel_compute(data, num_threads):
        raise NotImplementedError("C++ extension not built")
    
    __all__ = ['find_primes', 'matrix_multiply', 'sort_array', 'filter_array', 'parallel_compute']
