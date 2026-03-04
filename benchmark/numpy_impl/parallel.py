"""NumPy implementation of parallel computation functions."""

import numpy as np
from typing import List


def parallel_compute(data: List[float], num_threads: int) -> float:
    """Perform parallel computation (sum) using NumPy array operations.
    
    Note: NumPy internally uses optimized BLAS/LAPACK libraries which may
    utilize multiple threads. The num_threads parameter is accepted for
    interface compatibility but NumPy's threading is controlled by
    environment variables (OMP_NUM_THREADS, MKL_NUM_THREADS, etc.).
    
    Args:
        data: Data to process
        num_threads: Number of threads to use (for interface compatibility)
        
    Returns:
        Sum of all elements in data
    """
    if not data:
        return 0.0
    
    if num_threads <= 0:
        raise ValueError("num_threads must be positive")
    
    # Convert to NumPy array
    data_np = np.array(data, dtype=float)
    
    # Use NumPy's optimized sum (may use parallel operations internally)
    result = np.sum(data_np)
    
    # Convert to Python float
    return float(result)
