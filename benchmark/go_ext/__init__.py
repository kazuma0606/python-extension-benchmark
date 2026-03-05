"""
Go Extension for Python Benchmark System

This module provides Go implementations of benchmark functions using cgo
and shared libraries for high-performance computation.
"""

import ctypes
import os
import sys
from typing import List

# Get the directory containing this module
_module_dir = os.path.dirname(os.path.abspath(__file__))

# Try to load the shared library
_lib = None
_lib_path = None

# Possible library names based on platform
if sys.platform.startswith('win'):
    lib_names = ['libgofunctions.dll', 'gofunctions.dll']
elif sys.platform.startswith('darwin'):
    lib_names = ['libgofunctions.dylib', 'gofunctions.dylib']
else:
    lib_names = ['libgofunctions.so', 'gofunctions.so']

for lib_name in lib_names:
    try:
        _lib_path = os.path.join(_module_dir, lib_name)
        if os.path.exists(_lib_path):
            _lib = ctypes.CDLL(_lib_path)
            break
    except OSError:
        continue

if _lib is None:
    print(f"Warning: Go shared library not found in {_module_dir}")
    print("Available files:", os.listdir(_module_dir) if os.path.exists(_module_dir) else "Directory not found")


def _setup_function_signatures():
    """Setup C function signatures for type safety"""
    if _lib is None:
        return
    
    # find_primes(n int) -> []int
    _lib.find_primes.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    _lib.find_primes.restype = None
    
    # matrix_multiply(a, b matrices) -> matrix
    _lib.matrix_multiply.argtypes = [
        ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,  # matrix a, rows, cols
        ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,  # matrix b, rows, cols
        ctypes.POINTER(ctypes.c_double)  # result matrix
    ]
    _lib.matrix_multiply.restype = None
    
    # sort_array(arr []int) -> []int
    _lib.sort_array.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
    _lib.sort_array.restype = None
    
    # filter_array(arr []int, threshold int) -> []int
    _lib.filter_array.argtypes = [
        ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
    ]
    _lib.filter_array.restype = None
    
    # parallel_compute(data []float64, num_threads int) -> float64
    _lib.parallel_compute.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
    _lib.parallel_compute.restype = ctypes.c_double


# Setup function signatures
_setup_function_signatures()


def find_primes(n: int) -> List[int]:
    """
    Find all prime numbers up to n using the Sieve of Eratosthenes algorithm.
    
    Args:
        n: Upper limit for prime search
        
    Returns:
        List of prime numbers up to n
    """
    if _lib is None:
        raise RuntimeError("Go shared library not available")
    
    if n < 2:
        return []
    
    # Allocate memory for result
    max_primes = n // 2  # Upper bound estimate
    result_array = (ctypes.c_int * max_primes)()
    result_count = ctypes.c_int(0)
    
    # Call Go function
    _lib.find_primes(ctypes.c_int(n), result_array, ctypes.byref(result_count))
    
    # Convert result to Python list
    return [result_array[i] for i in range(result_count.value)]


def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """
    Multiply two matrices using Go's concurrent implementation.
    
    Args:
        a: First matrix (m x n)
        b: Second matrix (n x p)
        
    Returns:
        Result matrix (m x p)
    """
    if _lib is None:
        raise RuntimeError("Go shared library not available")
    
    if not a or not b or not a[0] or not b[0]:
        return []
    
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    
    if cols_a != rows_b:
        raise ValueError(f"Matrix dimensions incompatible: {rows_a}x{cols_a} * {rows_b}x{cols_b}")
    
    # Flatten matrices for C interface
    a_flat = (ctypes.c_double * (rows_a * cols_a))()
    b_flat = (ctypes.c_double * (rows_b * cols_b))()
    result_flat = (ctypes.c_double * (rows_a * cols_b))()
    
    # Fill input arrays
    for i in range(rows_a):
        for j in range(cols_a):
            a_flat[i * cols_a + j] = a[i][j]
    
    for i in range(rows_b):
        for j in range(cols_b):
            b_flat[i * cols_b + j] = b[i][j]
    
    # Call Go function
    _lib.matrix_multiply(
        a_flat, ctypes.c_int(rows_a), ctypes.c_int(cols_a),
        b_flat, ctypes.c_int(rows_b), ctypes.c_int(cols_b),
        result_flat
    )
    
    # Convert result back to 2D list
    result = []
    for i in range(rows_a):
        row = []
        for j in range(cols_b):
            row.append(result_flat[i * cols_b + j])
        result.append(row)
    
    return result


def sort_array(arr: List[int]) -> List[int]:
    """
    Sort an array using Go's standard library sort.
    
    Args:
        arr: Array to sort
        
    Returns:
        Sorted array
    """
    if _lib is None:
        raise RuntimeError("Go shared library not available")
    
    if not arr:
        return []
    
    # Create C array
    c_array = (ctypes.c_int * len(arr))()
    for i, val in enumerate(arr):
        c_array[i] = val
    
    # Call Go function (sorts in-place)
    _lib.sort_array(c_array, ctypes.c_int(len(arr)))
    
    # Convert back to Python list
    return [c_array[i] for i in range(len(arr))]


def filter_array(arr: List[int], threshold: int) -> List[int]:
    """
    Filter array elements that are >= threshold.
    
    Args:
        arr: Array to filter
        threshold: Minimum value to keep
        
    Returns:
        Filtered array
    """
    if _lib is None:
        raise RuntimeError("Go shared library not available")
    
    if not arr:
        return []
    
    # Create input array
    c_array = (ctypes.c_int * len(arr))()
    for i, val in enumerate(arr):
        c_array[i] = val
    
    # Create result array
    result_array = (ctypes.c_int * len(arr))()
    result_count = ctypes.c_int(0)
    
    # Call Go function
    _lib.filter_array(
        c_array, ctypes.c_int(len(arr)), ctypes.c_int(threshold),
        result_array, ctypes.byref(result_count)
    )
    
    # Convert result to Python list
    return [result_array[i] for i in range(result_count.value)]


def parallel_compute(data: List[float], num_threads: int) -> float:
    """
    Compute sum of array elements using Go goroutines.
    
    Args:
        data: Array of numbers to sum
        num_threads: Number of goroutines to use
        
    Returns:
        Sum of all elements
    """
    if _lib is None:
        raise RuntimeError("Go shared library not available")
    
    if not data:
        return 0.0
    
    # Create C array
    c_array = (ctypes.c_double * len(data))()
    for i, val in enumerate(data):
        c_array[i] = val
    
    # Call Go function
    result = _lib.parallel_compute(c_array, ctypes.c_int(len(data)), ctypes.c_int(num_threads))
    
    return float(result)


# Export the interface functions
__all__ = ['find_primes', 'matrix_multiply', 'sort_array', 'filter_array', 'parallel_compute']