# cython: language_level=3
"""Cython implementation of parallel computation functions."""

from typing import List
cimport cython
from cython.parallel import prange
from libc.stdlib cimport malloc, free
import numpy as np
cimport numpy as cnp


@cython.boundscheck(False)
@cython.wraparound(False)
def parallel_compute(data: List[float], int num_threads) -> float:
    """Perform parallel computation (sum) using multiple threads.
    
    Args:
        data: Data to process
        num_threads: Number of threads to use
        
    Returns:
        Sum of all elements in data
    """
    if not data:
        return 0.0
    
    if num_threads <= 0:
        raise ValueError("num_threads must be positive")
    
    cdef int n = len(data)
    cdef int i
    cdef double total_sum = 0.0
    cdef double partial_sum
    
    # Convert to numpy array for efficient access
    cdef cnp.ndarray[double, ndim=1] arr = np.array(data, dtype=np.float64)
    
    # Use prange for parallel computation
    with cython.nogil:
        for i in prange(n, num_threads=num_threads):
            total_sum += arr[i]
    
    return total_sum