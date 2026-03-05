# Zig Extension for Python Benchmark
# This module provides Zig implementations of benchmark functions

import os
import sys
import ctypes
import warnings
from typing import List, Optional

# Zig extension initialization - use lazy loading
_zig_available = None
_zig_lib = None

def _initialize_zig():
    """Initialize Zig shared library lazily."""
    global _zig_available, _zig_lib
    
    if _zig_available is not None:
        return _zig_available
    
    try:
        # Find the shared library
        zig_dir = os.path.dirname(__file__)
        
        # Try different possible library names
        lib_names = [
            "libzigfunctions.so",      # Linux
            "libzigfunctions.dylib",   # macOS
            "zigfunctions.dll",        # Windows
            "libzigfunctions.dll"      # Windows alternative
        ]
        
        lib_path = None
        for lib_name in lib_names:
            potential_path = os.path.join(zig_dir, lib_name)
            if os.path.exists(potential_path):
                lib_path = potential_path
                break
        
        if lib_path is None:
            _zig_available = False
            warnings.warn("Zig shared library not found. Build the Zig extension first.")
            return False
        
        # Load the shared library
        _zig_lib = ctypes.CDLL(lib_path)
        
        # Define function signatures
        # find_primes(n: int, result: *int, count: *int) -> void
        _zig_lib.find_primes.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        _zig_lib.find_primes.restype = None
        
        # matrix_multiply(a: *double, rows_a: int, cols_a: int, b: *double, rows_b: int, cols_b: int, result: *double) -> void
        _zig_lib.matrix_multiply.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_double)
        ]
        _zig_lib.matrix_multiply.restype = None
        
        # sort_array(arr: *int, length: int) -> void
        _zig_lib.sort_array.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
        _zig_lib.sort_array.restype = None
        
        # filter_array(arr: *int, length: int, threshold: int, result: *int, count: *int) -> void
        _zig_lib.filter_array.argtypes = [
            ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
        ]
        _zig_lib.filter_array.restype = None
        
        # parallel_compute(data: *double, length: int, num_threads: int) -> double
        _zig_lib.parallel_compute.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        _zig_lib.parallel_compute.restype = ctypes.c_double
        
        _zig_available = True
        
    except Exception as e:
        _zig_available = False
        warnings.warn(f"Failed to initialize Zig extension: {e}")
    
    return _zig_available

def is_available() -> bool:
    """Check if Zig extension is available."""
    return _initialize_zig()

def find_primes(n: int) -> List[int]:
    """Find all prime numbers up to n using Sieve of Eratosthenes."""
    if not _initialize_zig():
        raise RuntimeError("Zig extension not available")
    
    if n < 2:
        return []
    
    try:
        # Allocate result array (worst case: all numbers are prime)
        max_primes = n // 2 + 1  # Conservative estimate
        result_array = (ctypes.c_int * max_primes)()
        count = ctypes.c_int(0)
        
        _zig_lib.find_primes(ctypes.c_int(n), result_array, ctypes.byref(count))
        
        # Convert to Python list
        return [result_array[i] for i in range(count.value)]
        
    except Exception as e:
        raise RuntimeError(f"Zig find_primes failed: {e}")

def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Multiply two matrices using optimized Zig implementation."""
    if not _initialize_zig():
        raise RuntimeError("Zig extension not available")
    
    if not a or not b or not a[0] or not b[0]:
        return []
    
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    
    if cols_a != rows_b:
        raise ValueError("Matrix dimensions incompatible for multiplication")
    
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
        
        _zig_lib.matrix_multiply(
            a_flat, ctypes.c_int(rows_a), ctypes.c_int(cols_a),
            b_flat, ctypes.c_int(rows_b), ctypes.c_int(cols_b),
            result_flat
        )
        
        # Convert back to 2D list
        result = []
        for i in range(rows_a):
            row = []
            for j in range(cols_b):
                row.append(result_flat[i * cols_b + j])
            result.append(row)
        
        return result
        
    except Exception as e:
        raise RuntimeError(f"Zig matrix_multiply failed: {e}")

def sort_array(arr: List[int]) -> List[int]:
    """Sort array using Zig's memory-safe sorting algorithms."""
    if not _initialize_zig():
        raise RuntimeError("Zig extension not available")
    
    if not arr:
        return []
    
    try:
        # Create a copy for in-place sorting
        n = len(arr)
        c_array = (ctypes.c_int * n)(*arr)
        
        _zig_lib.sort_array(c_array, ctypes.c_int(n))
        
        # Convert back to Python list
        return [c_array[i] for i in range(n)]
        
    except Exception as e:
        raise RuntimeError(f"Zig sort_array failed: {e}")

def filter_array(arr: List[int], threshold: int) -> List[int]:
    """Filter array elements above threshold using memory-safe operations."""
    if not _initialize_zig():
        raise RuntimeError("Zig extension not available")
    
    if not arr:
        return []
    
    try:
        n = len(arr)
        input_array = (ctypes.c_int * n)(*arr)
        result_array = (ctypes.c_int * n)()  # Worst case: all elements pass
        count = ctypes.c_int(0)
        
        _zig_lib.filter_array(
            input_array, ctypes.c_int(n), ctypes.c_int(threshold),
            result_array, ctypes.byref(count)
        )
        
        # Convert to Python list
        return [result_array[i] for i in range(count.value)]
        
    except Exception as e:
        raise RuntimeError(f"Zig filter_array failed: {e}")

def parallel_compute(data: List[float], num_threads: int) -> float:
    """Compute sum of data using Zig's thread functionality."""
    if not _initialize_zig():
        raise RuntimeError("Zig extension not available")
    
    if not data:
        return 0.0
    
    try:
        n = len(data)
        c_array = (ctypes.c_double * n)(*data)
        
        result = _zig_lib.parallel_compute(c_array, ctypes.c_int(n), ctypes.c_int(num_threads))
        
        return float(result)
        
    except Exception as e:
        raise RuntimeError(f"Zig parallel_compute failed: {e}")

# Export the interface functions
__all__ = [
    'is_available',
    'find_primes', 
    'matrix_multiply', 
    'sort_array', 
    'filter_array', 
    'parallel_compute'
]