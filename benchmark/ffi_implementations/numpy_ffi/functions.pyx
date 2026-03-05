# cython: language_level=3
"""
NumPy-based Cython implementation of benchmark functions for FFI.

This module provides NumPy-optimized implementations that are compiled
to a shared library for FFI access via ctypes.
"""

import numpy as np
cimport numpy as cnp
from libc.stdlib cimport malloc, free
from libc.math cimport sqrt
import cython

# Initialize NumPy C API
cnp.import_array()

@cython.boundscheck(False)
@cython.wraparound(False)
cdef int* _find_primes_numpy_impl(int n, int* count):
    """NumPy-based implementation of prime finding using vectorized operations."""
    if n < 2:
        count[0] = 0
        return NULL
    
    # Use NumPy's vectorized Sieve of Eratosthenes
    cdef cnp.ndarray[cnp.uint8_t, ndim=1] is_prime = np.ones(n + 1, dtype=np.uint8)
    is_prime[0] = is_prime[1] = 0
    
    cdef int i
    cdef int sqrt_n = int(sqrt(n)) + 1
    
    # Vectorized sieve using NumPy operations
    for i in range(2, sqrt_n):
        if is_prime[i]:
            # Use NumPy slicing for vectorized marking
            is_prime[i*i::i] = 0
    
    # Use NumPy's where to find prime indices
    cdef cnp.ndarray[cnp.intp_t, ndim=1] prime_indices = np.where(is_prime)[0]
    cdef int prime_count = prime_indices.shape[0]
    
    if prime_count == 0:
        count[0] = 0
        return NULL
    
    # Allocate result array
    cdef int* result = <int*>malloc(prime_count * sizeof(int))
    if result == NULL:
        count[0] = 0
        return NULL
    
    # Copy primes to result array
    cdef int idx
    for idx in range(prime_count):
        result[idx] = prime_indices[idx]
    
    count[0] = prime_count
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
cdef double* _matrix_multiply_numpy_impl(double* a, int rows_a, int cols_a,
                                         double* b, int rows_b, int cols_b,
                                         int* result_rows, int* result_cols):
    """NumPy-based implementation of matrix multiplication using optimized matmul."""
    if cols_a != rows_b:
        result_rows[0] = 0
        result_cols[0] = 0
        return NULL
    
    # Convert C arrays to NumPy arrays
    cdef cnp.ndarray[cnp.float64_t, ndim=2] a_np = np.empty((rows_a, cols_a), dtype=np.float64)
    cdef cnp.ndarray[cnp.float64_t, ndim=2] b_np = np.empty((rows_b, cols_b), dtype=np.float64)
    
    cdef int i, j
    # Copy data to NumPy arrays
    for i in range(rows_a):
        for j in range(cols_a):
            a_np[i, j] = a[i * cols_a + j]
    
    for i in range(rows_b):
        for j in range(cols_b):
            b_np[i, j] = b[i * cols_b + j]
    
    # Use NumPy's optimized matrix multiplication
    cdef cnp.ndarray[cnp.float64_t, ndim=2] result_np = np.matmul(a_np, b_np)
    
    result_rows[0] = rows_a
    result_cols[0] = cols_b
    
    cdef int result_size = rows_a * cols_b
    cdef double* result = <double*>malloc(result_size * sizeof(double))
    if result == NULL:
        result_rows[0] = 0
        result_cols[0] = 0
        return NULL
    
    # Copy result back to C array
    for i in range(rows_a):
        for j in range(cols_b):
            result[i * cols_b + j] = result_np[i, j]
    
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
cdef int* _sort_array_numpy_impl(int* arr, int size):
    """NumPy-based implementation of array sorting."""
    if size <= 0:
        return NULL
    
    # Convert to NumPy array
    cdef cnp.ndarray[cnp.int32_t, ndim=1] arr_np = np.empty(size, dtype=np.int32)
    
    cdef int i
    for i in range(size):
        arr_np[i] = arr[i]
    
    # Use NumPy's optimized sort
    cdef cnp.ndarray[cnp.int32_t, ndim=1] sorted_np = np.sort(arr_np)
    
    # Allocate result array
    cdef int* result = <int*>malloc(size * sizeof(int))
    if result == NULL:
        return NULL
    
    # Copy sorted data back
    for i in range(size):
        result[i] = sorted_np[i]
    
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
cdef int* _filter_array_numpy_impl(int* arr, int size, int threshold, int* result_size):
    """NumPy-based implementation of array filtering using boolean indexing."""
    if size <= 0:
        result_size[0] = 0
        return NULL
    
    # Convert to NumPy array
    cdef cnp.ndarray[cnp.int32_t, ndim=1] arr_np = np.empty(size, dtype=np.int32)
    
    cdef int i
    for i in range(size):
        arr_np[i] = arr[i]
    
    # Use NumPy boolean indexing for filtering
    cdef cnp.ndarray[cnp.int32_t, ndim=1] filtered_np = arr_np[arr_np >= threshold]
    cdef int count = filtered_np.shape[0]
    
    if count == 0:
        result_size[0] = 0
        return NULL
    
    # Allocate result array
    cdef int* result = <int*>malloc(count * sizeof(int))
    if result == NULL:
        result_size[0] = 0
        return NULL
    
    # Copy filtered data
    for i in range(count):
        result[i] = filtered_np[i]
    
    result_size[0] = count
    return result

@cython.boundscheck(False)
@cython.wraparound(False)
cdef double _parallel_compute_numpy_impl(double* data, int size, int num_threads):
    """NumPy-based implementation of parallel computation using vectorized sum."""
    if size <= 0:
        return 0.0
    
    # Convert to NumPy array
    cdef cnp.ndarray[cnp.float64_t, ndim=1] data_np = np.empty(size, dtype=np.float64)
    
    cdef int i
    for i in range(size):
        data_np[i] = data[i]
    
    # Use NumPy's optimized sum (may use parallel operations internally)
    cdef double result = np.sum(data_np)
    
    return result

# C-compatible FFI interface functions
cdef public int* find_primes_ffi(int n, int* count):
    """FFI interface for NumPy-based prime finding."""
    return _find_primes_numpy_impl(n, count)

cdef public double* matrix_multiply_ffi(double* a, int rows_a, int cols_a,
                                        double* b, int rows_b, int cols_b,
                                        int* result_rows, int* result_cols):
    """FFI interface for NumPy-based matrix multiplication."""
    return _matrix_multiply_numpy_impl(a, rows_a, cols_a, b, rows_b, cols_b, result_rows, result_cols)

cdef public int* sort_array_ffi(int* arr, int size):
    """FFI interface for NumPy-based array sorting."""
    return _sort_array_numpy_impl(arr, size)

cdef public int* filter_array_ffi(int* arr, int size, int threshold, int* result_size):
    """FFI interface for NumPy-based array filtering."""
    return _filter_array_numpy_impl(arr, size, threshold, result_size)

cdef public double parallel_compute_ffi(double* data, int size, int num_threads):
    """FFI interface for NumPy-based parallel computation."""
    return _parallel_compute_numpy_impl(data, size, num_threads)

cdef public void free_memory_ffi(void* ptr):
    """FFI interface for memory deallocation."""
    if ptr != NULL:
        free(ptr)