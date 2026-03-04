"""Pure Python implementation of memory operation functions."""

from typing import List


def sort_array(arr: List[int]) -> List[int]:
    """Sort an array of integers.
    
    Args:
        arr: Array to sort
        
    Returns:
        Sorted array
    """
    # Create a copy to avoid modifying the original
    result = arr.copy()
    result.sort()
    return result


def filter_array(arr: List[int], threshold: int) -> List[int]:
    """Filter array elements >= threshold.
    
    Args:
        arr: Array to filter
        threshold: Minimum value to keep
        
    Returns:
        Filtered array containing only elements >= threshold
    """
    return [x for x in arr if x >= threshold]
