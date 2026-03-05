"""
Kotlin/Native Extension for Python Benchmark System

This module provides Kotlin/Native implementations of benchmark functions using
C ABI compatibility for high-performance computation.
"""

import ctypes
import os
import sys
import warnings
from typing import List, Optional

# Get the directory containing this module
_module_dir = os.path.dirname(os.path.abspath(__file__))

# Try to load the shared library
_lib = None
_lib_path = None
_kotlin_available = None

# Possible library names based on platform
if sys.platform.startswith('win'):
    lib_names = ['libkotlinfunctions.dll', 'kotlinfunctions.dll']
elif sys.platform.startswith('darwin'):
    lib_names = ['libkotlinfunctions.dylib', 'kotlinfunctions.dylib']
else:
    lib_names = ['libkotlinfunctions.so', 'kotlinfunctions.so']

def _load_kotlin_library():
    """Load the Kotlin/Native shared library"""
    global _lib, _lib_path, _kotlin_available
    
    if _kotlin_available is not None:
        return _lib
    
    for lib_name in lib_names:
        try:
            _lib_path = os.path.join(_module_dir, lib_name)
            if os.path.exists(_lib_path):
                _lib = ctypes.CDLL(_lib_path)
                _kotlin_available = True
                return _lib
        except OSError:
            continue
    
    _kotlin_available = False
    warnings.warn(f"Kotlin/Native shared library not found in {_module_dir}")
    return None

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
    
    # parallel_compute(data []double, num_threads int) -> double
    _lib.parallel_compute.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
    _lib.parallel_compute.restype = ctypes.c_double

def is_available() -> bool:
    """Check if Kotlin/Native extension is available."""
    return _load_kotlin_library() is not None

def find_primes(n: int) -> List[int]:
    """
    Find all prime numbers up to n using the Sieve of Eratosthenes algorithm.
    
    Args:
        n: Upper limit for prime search
        
    Returns:
        List of prime numbers up to n
    """
    if not is_available():
        warnings.warn("Kotlin/Native extension not available, using Python fallback")
        return _python_find_primes(n)
    
    if n < 2:
        return []
    
    try:
        # Allocate memory for result
        max_primes = n // 2  # Upper bound estimate
        result_array = (ctypes.c_int * max_primes)()
        result_count = ctypes.c_int(0)
        
        # Call Kotlin function
        _lib.find_primes(ctypes.c_int(n), result_array, ctypes.byref(result_count))
        
        # Convert result to Python list
        return [result_array[i] for i in range(result_count.value)]
    except Exception as e:
        warnings.warn(f"Kotlin find_primes failed: {e}, using Python fallback")
        return _python_find_primes(n)

def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """
    Multiply two matrices using Kotlin/Native implementation.
    
    Args:
        a: First matrix (m x n)
        b: Second matrix (n x p)
        
    Returns:
        Result matrix (m x p)
    """
    if not is_available():
        warnings.warn("Kotlin/Native extension not available, using Python fallback")
        return _python_matrix_multiply(a, b)
    
    if not a or not b or not a[0] or not b[0]:
        return []
    
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    
    if cols_a != rows_b:
        raise ValueError(f"Matrix dimensions incompatible: {rows_a}x{cols_a} * {rows_b}x{cols_b}")
    
    try:
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
        
        # Call Kotlin function
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
    except Exception as e:
        warnings.warn(f"Kotlin matrix_multiply failed: {e}, using Python fallback")
        return _python_matrix_multiply(a, b)

def sort_array(arr: List[int]) -> List[int]:
    """
    Sort an array using Kotlin/Native standard library.
    
    Args:
        arr: Array to sort
        
    Returns:
        Sorted array
    """
    if not is_available():
        warnings.warn("Kotlin/Native extension not available, using Python fallback")
        return sorted(arr)
    
    if not arr:
        return []
    
    try:
        # Create C array
        c_array = (ctypes.c_int * len(arr))()
        for i, val in enumerate(arr):
            c_array[i] = val
        
        # Call Kotlin function (sorts in-place)
        _lib.sort_array(c_array, ctypes.c_int(len(arr)))
        
        # Convert back to Python list
        return [c_array[i] for i in range(len(arr))]
    except Exception as e:
        warnings.warn(f"Kotlin sort_array failed: {e}, using Python fallback")
        return sorted(arr)

def filter_array(arr: List[int], threshold: int) -> List[int]:
    """
    Filter array elements that are >= threshold using functional programming.
    
    Args:
        arr: Array to filter
        threshold: Minimum value to keep
        
    Returns:
        Filtered array
    """
    if not is_available():
        warnings.warn("Kotlin/Native extension not available, using Python fallback")
        return [x for x in arr if x >= threshold]
    
    if not arr:
        return []
    
    try:
        # Create input array
        c_array = (ctypes.c_int * len(arr))()
        for i, val in enumerate(arr):
            c_array[i] = val
        
        # Create result array
        result_array = (ctypes.c_int * len(arr))()
        result_count = ctypes.c_int(0)
        
        # Call Kotlin function
        _lib.filter_array(
            c_array, ctypes.c_int(len(arr)), ctypes.c_int(threshold),
            result_array, ctypes.byref(result_count)
        )
        
        # Convert result to Python list
        return [result_array[i] for i in range(result_count.value)]
    except Exception as e:
        warnings.warn(f"Kotlin filter_array failed: {e}, using Python fallback")
        return [x for x in arr if x >= threshold]

def parallel_compute(data: List[float], num_threads: int) -> float:
    """
    Compute sum of array elements using Kotlin coroutines.
    
    Args:
        data: Array of numbers to sum
        num_threads: Number of coroutines to use
        
    Returns:
        Sum of all elements
    """
    if not is_available():
        warnings.warn("Kotlin/Native extension not available, using Python fallback")
        return sum(data)
    
    if not data:
        return 0.0
    
    try:
        # Create C array
        c_array = (ctypes.c_double * len(data))()
        for i, val in enumerate(data):
            c_array[i] = val
        
        # Call Kotlin function
        result = _lib.parallel_compute(c_array, ctypes.c_int(len(data)), ctypes.c_int(num_threads))
        
        return float(result)
    except Exception as e:
        warnings.warn(f"Kotlin parallel_compute failed: {e}, using Python fallback")
        return sum(data)

# Python fallback implementations
def _python_find_primes(n: int) -> List[int]:
    """Python fallback for prime finding"""
    if n < 2:
        return []
    
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, n + 1, i):
                sieve[j] = False
    
    return [i for i in range(2, n + 1) if sieve[i]]

def _python_matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Python fallback for matrix multiplication"""
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    
    if cols_a != rows_b:
        raise ValueError("Matrix dimensions don't match for multiplication")
    
    result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
    
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    
    return result

# Initialize the library on import
_load_kotlin_library()
if _lib is not None:
    _setup_function_signatures()

# Export the interface functions
__all__ = [
    'is_available',
    'find_primes', 
    'matrix_multiply', 
    'sort_array', 
    'filter_array', 
    'parallel_compute'
]