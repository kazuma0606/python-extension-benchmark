"""NumPy implementation of memory operation functions."""

import numpy as np
from typing import List


def sort_array(arr: List[int]) -> List[int]:
    """Sort an array of integers using NumPy's optimized sort.
    
    Args:
        arr: Array to sort
        
    Returns:
        Sorted array
    """
    # Convert to NumPy array
    arr_np = np.array(arr, dtype=int)
    
    # Use NumPy's optimized sort (returns sorted copy)
    sorted_arr = np.sort(arr_np)
    
    # Convert back to Python list
    return sorted_arr.tolist()


def filter_array(arr: List[int], threshold: int) -> List[int]:
    """Filter array elements >= threshold using NumPy boolean indexing.
    
    Args:
        arr: Array to filter
        threshold: Minimum value to keep
        
    Returns:
        Filtered array containing only elements >= threshold
    """
    # Convert to NumPy array
    arr_np = np.array(arr, dtype=int)
    
    # Use NumPy boolean indexing for efficient filtering
    filtered = arr_np[arr_np >= threshold]
    
    # Convert back to Python list
    return filtered.tolist()
