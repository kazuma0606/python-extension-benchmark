"""
Fortran FFI wrapper implementation.

This module provides a Python wrapper for Fortran functions using ctypes FFI.
Falls back to Python implementation if Fortran library is not available.
"""

import os
import numpy as np
from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class FortranFFI(FFIBase):
    """Fortran FFI implementation using ctypes with Python fallback."""
    
    def __init__(self, skip_uv_check=False):
        """Initialize Fortran FFI implementation.
        
        Args:
            skip_uv_check: If True, skip uv environment check (for testing)
        """
        # Ensure uv environment is active (unless skipped for testing)
        if not skip_uv_check and not os.environ.get('PYTEST_CURRENT_TEST'):
            require_uv_environment()
        
        # Get the directory where this file is located
        library_dir = os.path.dirname(__file__)

        # Add the fortran_ffi directory itself so co-located runtime DLLs are found
        try:
            os.add_dll_directory(library_dir)
        except (AttributeError, OSError):
            pass

        # Try to load the library, fall back to Python if not available
        self.use_fallback = False
        try:
            # Initialize with library name (without extension) and directory
            super().__init__("libfortranfunctions", library_dir)
        except Exception as e:
            print(f"Warning: Fortran FFI library not available, using Python fallback: {e}")
            self.use_fallback = True
            # Initialize base class without library
            self.library_dir = library_dir
    
    def find_primes(self, n: int) -> list:
        """Find all prime numbers up to n using Sieve of Eratosthenes."""
        if self.use_fallback:
            return self._find_primes_fallback(n)
        else:
            return super().find_primes(n)
    
    def matrix_multiply(self, a: list, b: list) -> list:
        """Multiply two matrices."""
        if self.use_fallback:
            return self._matrix_multiply_fallback(a, b)
        else:
            return super().matrix_multiply(a, b)
    
    def sort_array(self, arr: list) -> list:
        """Sort an array of integers."""
        if self.use_fallback:
            return self._sort_array_fallback(arr)
        else:
            return super().sort_array(arr)
    
    def parallel_compute(self, data: list, num_threads: int = 2) -> float:
        """Compute sum of array elements (parallel version)."""
        if self.use_fallback:
            return self._parallel_compute_fallback(data, num_threads)
        else:
            return super().parallel_compute(data, num_threads)
    
    def _find_primes_fallback(self, n: int) -> list:
        """Python fallback implementation of prime finding."""
        if n < 2:
            return []
        
        # Use NumPy for better performance (Fortran-style)
        is_prime = np.ones(n + 1, dtype=bool)
        is_prime[0] = is_prime[1] = False
        
        for i in range(2, int(n**0.5) + 1):
            if is_prime[i]:
                is_prime[i*i:n+1:i] = False
        
        return np.where(is_prime)[0].tolist()
    
    def _matrix_multiply_fallback(self, a: list, b: list) -> list:
        """Python fallback implementation of matrix multiplication (Fortran-style)."""
        # Convert to NumPy arrays for better performance
        a_np = np.array(a, dtype=np.float64)
        b_np = np.array(b, dtype=np.float64)
        
        # Use BLAS-optimized matrix multiplication (similar to Fortran)
        result_np = np.dot(a_np, b_np)
        
        return result_np.tolist()
    
    def _sort_array_fallback(self, arr: list) -> list:
        """Python fallback implementation of array sorting."""
        # Use NumPy for better performance
        arr_np = np.array(arr, dtype=np.int32)
        return np.sort(arr_np).tolist()
    
    def _parallel_compute_fallback(self, data: list, num_threads: int = 2) -> float:
        """Python fallback implementation of parallel computation."""
        # Use NumPy for better performance (similar to Fortran array operations)
        data_np = np.array(data, dtype=np.float64)
        return float(np.sum(data_np))
    
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        if self.use_fallback:
            return "Fortran FFI (Python Fallback)"
        else:
            return "Fortran FFI"