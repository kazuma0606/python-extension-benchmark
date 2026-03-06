"""
C FFI implementation for benchmark system.

This module provides C language functions accessible via FFI (ctypes).
"""

from .ffi_wrapper import CFFI

__all__ = ['CFFI', 'find_primes', 'matrix_multiply', 'sort_array', 'filter_array', 'parallel_compute']

# Module-level singleton instance for benchmark runner compatibility
_instance = None

def _get_instance():
    global _instance
    if _instance is None:
        _instance = CFFI(skip_uv_check=True)
    return _instance

def find_primes(n: int):
    return _get_instance().find_primes(n)

def matrix_multiply(a, b):
    return _get_instance().matrix_multiply(a, b)

def sort_array(arr):
    return _get_instance().sort_array(arr)

def filter_array(arr, threshold: int):
    return _get_instance().filter_array(arr, threshold)

def parallel_compute(data, num_threads: int = 2):
    return _get_instance().parallel_compute(data, num_threads)
