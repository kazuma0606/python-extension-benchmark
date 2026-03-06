# cython: language_level=3
"""
Cython implementation of benchmark functions for FFI.

This module provides optimized Cython implementations that are compiled
to a shared library for FFI access via ctypes.
"""

import numpy as np
cimport numpy as cnp
from libc.stdlib cimport malloc, free, qsort
from libc.math cimport sqrt
import cython

# Initialize NumPy C API
cnp.import_array()

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
cdef int _compare_int(const void* a, const void* b) noexcept nogil:
    """Comparison function for qsort."""
    cdef int ai = (<const int*>a)[0]
    cdef int bi = (<const int*>b)[0]
    if ai < bi:
        return -1
    elif ai > bi:
        return 1
    return 0

cdef int* _sort_array_impl(int* arr, int size):
    """Internal Cython implementation of array sorting using stdlib qsort."""
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

    # Use stdlib qsort (introsort internally, O(n log n) guaranteed)
    qsort(result, size, sizeof(int), _compare_int)

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

# API functions that can be called from Python
def find_primes_py(int n):
    """Python-callable wrapper for prime finding."""
    cdef int count
    cdef int* result = _find_primes_impl(n, &count)
    if result == NULL:
        return []
    
    # Convert to Python list
    py_result = []
    for i in range(count):
        py_result.append(result[i])
    
    free(result)
    return py_result

def matrix_multiply_py(a_list, b_list):
    """Python-callable wrapper for matrix multiplication."""
    # Convert Python lists to C arrays
    cdef int rows_a = len(a_list)
    cdef int cols_a = len(a_list[0]) if rows_a > 0 else 0
    cdef int rows_b = len(b_list)
    cdef int cols_b = len(b_list[0]) if rows_b > 0 else 0
    
    if cols_a != rows_b:
        return []
    
    # Allocate C arrays
    cdef double* a = <double*>malloc(rows_a * cols_a * sizeof(double))
    cdef double* b = <double*>malloc(rows_b * cols_b * sizeof(double))
    
    if a == NULL or b == NULL:
        if a != NULL: free(a)
        if b != NULL: free(b)
        return []
    
    # Fill C arrays
    cdef int i, j
    for i in range(rows_a):
        for j in range(cols_a):
            a[i * cols_a + j] = a_list[i][j]
    
    for i in range(rows_b):
        for j in range(cols_b):
            b[i * cols_b + j] = b_list[i][j]
    
    # Perform multiplication
    cdef int result_rows, result_cols
    cdef double* result = _matrix_multiply_impl(a, rows_a, cols_a, b, rows_b, cols_b, &result_rows, &result_cols)
    
    free(a)
    free(b)
    
    if result == NULL:
        return []
    
    # Convert to Python list
    py_result = []
    for i in range(result_rows):
        row = []
        for j in range(result_cols):
            row.append(result[i * result_cols + j])
        py_result.append(row)
    
    free(result)
    return py_result

def sort_array_py(arr_list):
    """Python-callable wrapper for array sorting."""
    cdef int size = len(arr_list)
    if size <= 0:
        return []
    
    # Allocate C array
    cdef int* arr = <int*>malloc(size * sizeof(int))
    if arr == NULL:
        return []
    
    # Fill C array
    for i in range(size):
        arr[i] = arr_list[i]
    
    # Sort
    cdef int* result = _sort_array_impl(arr, size)
    free(arr)
    
    if result == NULL:
        return []
    
    # Convert to Python list
    py_result = []
    for i in range(size):
        py_result.append(result[i])
    
    free(result)
    return py_result

def parallel_compute_py(data_list, int num_threads=2):
    """Python-callable wrapper for parallel computation."""
    cdef int size = len(data_list)
    if size <= 0:
        return 0.0
    
    # Allocate C array
    cdef double* data = <double*>malloc(size * sizeof(double))
    if data == NULL:
        return 0.0
    
    # Fill C array
    for i in range(size):
        data[i] = data_list[i]
    
    # Compute
    cdef double result = _parallel_compute_impl(data, size, num_threads)
    free(data)
    
    return result