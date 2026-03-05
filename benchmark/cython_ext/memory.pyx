# cython: language_level=3
"""Cython implementation of memory operation functions."""

from typing import List
cimport cython
from libc.stdlib cimport malloc, free, qsort
from libc.string cimport memcpy


cdef int compare_ints(const void* a, const void* b) noexcept nogil:
    """Comparison function for qsort."""
    cdef int ia = (<int*>a)[0]
    cdef int ib = (<int*>b)[0]
    return ia - ib


@cython.boundscheck(False)
@cython.wraparound(False)
def sort_array(arr: List[int]) -> List[int]:
    """Sort an array of integers.
    
    Args:
        arr: Array to sort
        
    Returns:
        Sorted array
    """
    if not arr:
        return []
    
    cdef int n = len(arr)
    cdef int* c_arr = <int*>malloc(n * sizeof(int))
    cdef int i
    
    if c_arr == NULL:
        raise MemoryError("Failed to allocate memory for sorting")
    
    try:
        # Copy Python list to C array
        for i in range(n):
            c_arr[i] = arr[i]
        
        # Sort using C qsort
        qsort(c_arr, n, sizeof(int), compare_ints)
        
        # Copy back to Python list
        result = []
        for i in range(n):
            result.append(c_arr[i])
        
        return result
    
    finally:
        free(c_arr)


@cython.boundscheck(False)
@cython.wraparound(False)
def filter_array(arr: List[int], int threshold) -> List[int]:
    """Filter array elements >= threshold.
    
    Args:
        arr: Array to filter
        threshold: Minimum value to keep
        
    Returns:
        Filtered array containing only elements >= threshold
    """
    cdef int n = len(arr)
    cdef int i
    cdef int value
    result = []
    
    for i in range(n):
        value = arr[i]
        if value >= threshold:
            result.append(value)
    
    return result