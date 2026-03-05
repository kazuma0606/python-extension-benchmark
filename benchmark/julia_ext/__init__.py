# Julia Extension for Python Benchmark
# This module provides Julia implementations of benchmark functions

import os
import sys
import warnings
from typing import List, Optional

# Julia extension initialization - use lazy loading
_julia_available = None
_julia_main = None

def _initialize_julia():
    """Initialize Julia environment lazily."""
    global _julia_available, _julia_main
    
    if _julia_available is not None:
        return _julia_available
    
    try:
        # Try the simplest possible initialization
        import julia
        
        # Use default initialization
        j = julia.Julia(compiled_modules=False)
        
        # Import Main
        from julia import Main
        
        # Test basic Julia functionality first
        Main.eval("1 + 1")
        
        # Load our Julia functions
        julia_dir = os.path.dirname(__file__)
        julia_file = os.path.join(julia_dir, "functions.jl")
        
        if os.path.exists(julia_file):
            Main.include(julia_file)
            _julia_main = Main
            _julia_available = True
        else:
            _julia_available = False
            warnings.warn("Julia functions file not found")
            
    except ImportError:
        _julia_available = False
        warnings.warn("Julia not available. Install PyJulia to use Julia extensions.")
    except Exception as e:
        _julia_available = False
        warnings.warn(f"Failed to initialize Julia: {e}")
    
    return _julia_available

def is_available() -> bool:
    """Check if Julia extension is available."""
    return _initialize_julia()

def find_primes(n: int) -> List[int]:
    """Find all prime numbers up to n using Sieve of Eratosthenes."""
    if not _initialize_julia():
        raise RuntimeError("Julia extension not available")
    
    try:
        result = _julia_main.find_primes_jl(n)
        return list(result)
    except Exception as e:
        raise RuntimeError(f"Julia find_primes failed: {e}")

def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Multiply two matrices using optimized Julia linear algebra."""
    if not _initialize_julia():
        raise RuntimeError("Julia extension not available")
    
    try:
        result = _julia_main.matrix_multiply_jl(a, b)
        return [list(row) for row in result]
    except Exception as e:
        raise RuntimeError(f"Julia matrix_multiply failed: {e}")

def sort_array(arr: List[int]) -> List[int]:
    """Sort array using Julia's efficient sorting algorithms."""
    if not _initialize_julia():
        raise RuntimeError("Julia extension not available")
    
    try:
        result = _julia_main.sort_array_jl(arr)
        return list(result)
    except Exception as e:
        raise RuntimeError(f"Julia sort_array failed: {e}")

def filter_array(arr: List[int], threshold: int) -> List[int]:
    """Filter array elements above threshold using vectorized operations."""
    if not _initialize_julia():
        raise RuntimeError("Julia extension not available")
    
    try:
        result = _julia_main.filter_array_jl(arr, threshold)
        return list(result)
    except Exception as e:
        raise RuntimeError(f"Julia filter_array failed: {e}")

def parallel_compute(data: List[float], num_threads: int) -> float:
    """Compute sum of data using Julia's multithreading."""
    if not _initialize_julia():
        raise RuntimeError("Julia extension not available")
    
    try:
        result = _julia_main.parallel_compute_jl(data, num_threads)
        return float(result)
    except Exception as e:
        raise RuntimeError(f"Julia parallel_compute failed: {e}")

# Export the interface functions
__all__ = [
    'is_available',
    'find_primes', 
    'matrix_multiply', 
    'sort_array', 
    'filter_array', 
    'parallel_compute'
]