"""
NumPy FFI wrapper implementation.

This module provides a Python wrapper for NumPy-based functions using ctypes FFI.
Falls back to NumPy implementation if the compiled library is not available.
"""

import os
import numpy as np
from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class NumPyFFI(FFIBase):
    """NumPy FFI implementation using ctypes with NumPy fallback."""

    def __init__(self, skip_uv_check=False):
        """Initialize NumPy FFI implementation.

        Args:
            skip_uv_check: If True, skip uv environment check (for testing)
        """
        if not skip_uv_check and not os.environ.get('PYTEST_CURRENT_TEST'):
            require_uv_environment()

        library_dir = os.path.dirname(__file__)

        # Try to load the ctypes library; fall back to NumPy if unavailable
        self.use_fallback = False
        try:
            # Check for the Cython-generated .so file first
            import glob
            so_files = glob.glob(os.path.join(library_dir, "numpy_functions*.so"))
            if so_files:
                # Use the Cython-generated library directly - but fall back to NumPy
                # since Cython extensions are not compatible with ctypes FFI
                self.use_fallback = True
                self.library_dir = library_dir
                self.memory_manager = None
            else:
                # Fallback to standard FFI loading
                super().__init__("libnumpyfunctions", library_dir)
                if self.lib is None:
                    self.use_fallback = True
                    self.library_dir = library_dir
        except Exception as e:
            print(f"Warning: NumPy FFI library not available, using NumPy fallback: {e}")
            self.use_fallback = True
            self.library_dir = library_dir
            self.memory_manager = None
            self.memory_manager = None

    def find_primes(self, n: int) -> list:
        """Find all prime numbers up to n using Sieve of Eratosthenes."""
        if self.use_fallback:
            return self._find_primes_fallback(n)
        return super().find_primes(n)

    def matrix_multiply(self, a: list, b: list) -> list:
        """Multiply two matrices."""
        if self.use_fallback:
            return self._matrix_multiply_fallback(a, b)
        return super().matrix_multiply(a, b)

    def sort_array(self, arr: list) -> list:
        """Sort an array of integers."""
        if self.use_fallback:
            return self._sort_array_fallback(arr)
        return super().sort_array(arr)

    def filter_array(self, arr: list, threshold: int) -> list:
        """Filter array elements >= threshold."""
        if self.use_fallback:
            return self._filter_array_fallback(arr, threshold)
        return super().filter_array(arr, threshold)

    def parallel_compute(self, data: list, num_threads: int = 2) -> float:
        """Compute sum of array elements."""
        if self.use_fallback:
            return self._parallel_compute_fallback(data, num_threads)
        return super().parallel_compute(data, num_threads)

    def _filter_array_fallback(self, arr: list, threshold: int) -> list:
        arr_np = np.array(arr, dtype=np.int32)
        return arr_np[arr_np >= threshold].tolist()

    def _find_primes_fallback(self, n: int) -> list:
        if n < 2:
            return []
        is_prime = np.ones(n + 1, dtype=bool)
        is_prime[0] = is_prime[1] = False
        for i in range(2, int(n**0.5) + 1):
            if is_prime[i]:
                is_prime[i*i:n+1:i] = False
        return np.where(is_prime)[0].tolist()

    def _matrix_multiply_fallback(self, a: list, b: list) -> list:
        return np.dot(np.array(a, dtype=np.float64), np.array(b, dtype=np.float64)).tolist()

    def _sort_array_fallback(self, arr: list) -> list:
        return np.sort(np.array(arr, dtype=np.int32)).tolist()

    def _parallel_compute_fallback(self, data: list, num_threads: int = 2) -> float:
        return float(np.sum(np.array(data, dtype=np.float64)))

    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        if self.use_fallback:
            return "NumPy FFI (NumPy Fallback)"
        return "NumPy FFI"
