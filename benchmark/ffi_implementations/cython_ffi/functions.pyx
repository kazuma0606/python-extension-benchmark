# cython: language_level=3
"""
Cython implementation of benchmark functions for FFI.

This module provides optimized Cython implementations that are compiled
to a shared library for FFI access via ctypes.
"""

import numpy as np
cimport numpy as cnp
from libc.stdlib cimport malloc, free
from libc.math cimport sqrt
import cython

# Initialize NumPy C API
cnp.import_array()

# C function declarations for FFI interface
cdef extern from "Python.h":
    pass

@cython.boundscheck(False)
@cython.wraparound(False)
cdef int* _find_primes_impl(int n, int* count):
    """Internal Cython implementation of prime finding."""
    if n < 2:
        count[0] = 0
        return NULL
    
    # Use Sieve of Eratosthenes with Cython optimizations
    cdef cnp.ndarray[cnp.uint8_t, ndim=1] is_prime = np.ones(n + 1, dtype=np.uint8)
    is_prime[0] = is_prime[1] = 0
    
    cdef int i, j
    cdef int sqrt_n = int(sqrt(n)) + 1
    
    for i in range(2, sqrt_n):
        if is_prime[i]:
            for j in range(i * i, n + 1, i):
                is_prime[j] = 0
    
    # Count primes
    cdef int prime_count = 0
    for i in range(2, n + 1):
        if is_prime[i]:
            prime_count += 1
    
    # Allocate result array
    cdef int* result = <int*>malloc(prime_count * sizeof(int))
    if result == NULL:
        count[0] = 0
        return NULL
    
    # Fill result array
    cdef int idx = 0
    for i in range(2, n + 1):
        if is_prime[i]:
            result[idx] = i
            idx += 1
    
    count[0] = prime_count
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
cdef double* _matrix_multiply_impl(double* a, int rows_a, int cols_a,
                                   double* b, int rows_b, int cols_b,
                                   int* result_rows, int* result_cols):
    """Internal Cython implementation of matrix multiplication."""
    if cols_a != rows_b:
        result_rows[0] = 0
        result_cols[0] = 0
        return NULL
    
    result_rows[0] = rows_a
    result_cols[0] = cols_b
    
    cdef int result_size = rows_a * cols_b
    cdef double* result = <double*>malloc(result_size * sizeof(double))
    if result == NULL:
        result_rows[0] = 0
        result_cols[0] = 0
        return NULL
    
    # Initialize result to zero
    cdef int i, j, k
    for i in range(result_size):
        result[i] = 0.0
    
    # Perform matrix multiplication with loop optimization
    for i in range(rows_a):
        for k in range(cols_a):
            for j in range(cols_b):
                result[i * cols_b + j] += a[i * cols_a + k] * b[k * cols_b + j]
    
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
cdef int* _sort_array_impl(int* arr, int size):
    """Internal Cython implementation of array sorting."""
    if size <= 0:
        return NULL
    
    # Allocate result array
    cdef int* result = <int*>malloc(size * sizeof(int))
    if result == NULL:
        return NULL
    
    # Copy input array
    cdef int i
    for i in range(size):
        result[i] = arr[i]
    
    # Simple quicksort implementation
    _quicksort(result, 0, size - 1)
    
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
cdef void _quicksort(int* arr, int low, int high):
    """Quicksort implementation."""
    if low < high:
        cdef int pi = _partition(arr, low, high)
        _quicksort(arr, low, pi - 1)
        _quicksort(arr, pi + 1, high)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef int _partition(int* arr, int low, int high):
    """Partition function for quicksort."""
    cdef int pivot = arr[high]
    cdef int i = low - 1
    cdef int j, temp
    
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            temp = arr[i]
            arr[i] = arr[j]
            arr[j] = temp
    
    temp = arr[i + 1]
    arr[i + 1] = arr[high]
    arr[high] = temp
    
    return i + 1

@cython.boundscheck(False)
@cython.wraparound(False)
cdef int* _filter_array_impl(int* arr, int size, int threshold, int* result_size):
    """Internal Cython implementation of array filtering."""
    if size <= 0:
        result_size[0] = 0
        return NULL
    
    # Count elements >= threshold
    cdef int count = 0
    cdef int i
    for i in range(size):
        if arr[i] >= threshold:
            count += 1
    
    if count == 0:
        result_size[0] = 0
        return NULL
    
    # Allocate result array
    cdef int* result = <int*>malloc(count * sizeof(int))
    if result == NULL:
        result_size[0] = 0
        return NULL
    
    # Fill result array
    cdef int idx = 0
    for i in range(size):
        if arr[i] >= threshold:
            result[idx] = arr[i]
            idx += 1
    
    result_size[0] = count
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
cdef double _parallel_compute_impl(double* data, int size, int num_threads):
    """Internal Cython implementation of parallel computation (sum)."""
    if size <= 0:
        return 0.0
    
    cdef double result = 0.0
    cdef int i
    
    # Simple sum - Cython will optimize this
    for i in range(size):
        result += data[i]
    
    return result

# C-compatible FFI interface functions
cdef public int* find_primes_ffi(int n, int* count):
    """FFI interface for prime finding."""
    return _find_primes_impl(n, count)

cdef public double* matrix_multiply_ffi(double* a, int rows_a, int cols_a,
                                        double* b, int rows_b, int cols_b,
                                        int* result_rows, int* result_cols):
    """FFI interface for matrix multiplication."""
    return _matrix_multiply_impl(a, rows_a, cols_a, b, rows_b, cols_b, result_rows, result_cols)

cdef public int* sort_array_ffi(int* arr, int size):
    """FFI interface for array sorting."""
    return _sort_array_impl(arr, size)

cdef public int* filter_array_ffi(int* arr, int size, int threshold, int* result_size):
    """FFI interface for array filtering."""
    return _filter_array_impl(arr, size, threshold, result_size)

cdef public double parallel_compute_ffi(double* data, int size, int num_threads):
    """FFI interface for parallel computation."""
    return _parallel_compute_impl(data, size, num_threads)

cdef public void free_memory_ffi(void* ptr):
    """FFI interface for memory deallocation."""
    if ptr != NULL:
        free(ptr)