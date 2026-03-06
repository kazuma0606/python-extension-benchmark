"""
Julia FFI wrapper implementation.

This module provides a Python wrapper for Julia functions using ctypes FFI.
Falls back to Python implementation if Julia library is not available.
"""

import os
import numpy as np
from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class JuliaFFI(FFIBase):
    """Julia FFI implementation using ctypes with Python fallback."""
    
    def __init__(self, skip_uv_check=False):
        """Initialize Julia FFI implementation.
        
        Args:
            skip_uv_check: If True, skip uv environment check (for testing)
        """
        # Ensure uv environment is active (unless skipped for testing)
        if not skip_uv_check and not os.environ.get('PYTEST_CURRENT_TEST'):
            require_uv_environment()
        
        # Get the directory where this file is located
        library_dir = os.path.dirname(__file__)

        # Add lib_build/bin to PATH so Julia's internal LoadLibraryW calls find
        # the correct DLL versions (os.add_dll_directory only helps LoadLibraryEx)
        _julia_lib_bin = os.path.join(library_dir, "lib_build", "bin")
        if os.path.isdir(_julia_lib_bin):
            os.environ['PATH'] = _julia_lib_bin + os.pathsep + os.environ.get('PATH', '')
            try:
                os.add_dll_directory(_julia_lib_bin)
            except (AttributeError, OSError):
                pass

        # Try to load the library, fall back to Python if not available
        self.use_fallback = False
        self._julia_initialized = False
        try:
            # Check for PackageCompiler builds first (lib_build/bin/)
            _lib_build_bin = os.path.join(library_dir, "lib_build", "bin")
            if os.path.isdir(_lib_build_bin):
                # Linux: look for .so files
                julia_so = os.path.join(_lib_build_bin, "juliafunctions.so")
                julia_dll = os.path.join(_lib_build_bin, "juliafunctions.dll")
                if os.path.exists(julia_so):
                    super().__init__("juliafunctions", _lib_build_bin)
                elif os.path.exists(julia_dll):
                    super().__init__("juliafunctions", _lib_build_bin)
                else:
                    # Fallback to direct library
                    super().__init__("libjuliafunctions", library_dir)
            else:
                # Fallback: use the pre-built library in current directory
                super().__init__("libjuliafunctions", library_dir)
            # Initialize the Julia runtime (required for PackageCompiler libraries)
            if self.lib is not None:
                self._init_julia_runtime()
        except Exception as e:
            print(f"Warning: Julia FFI library not available, using Python fallback: {e}")
            self.use_fallback = True
            # Initialize base class without library
            self.library_dir = library_dir

    def _init_julia_runtime(self):
        """Initialize the Julia runtime embedded in the shared library."""
        import ctypes
        try:
            self.lib.init_julia.argtypes = [ctypes.c_int, ctypes.c_void_p]
            self.lib.init_julia.restype = None
            self.lib.init_julia(0, None)
            self._julia_initialized = True
        except AttributeError:
            # No init_julia function - older build, try to use as-is
            self._julia_initialized = True
        except Exception as e:
            raise RuntimeError(f"Julia runtime initialization failed: {e}")
    
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
        """Python fallback implementation of prime finding (Julia-style)."""
        if n < 2:
            return []
        
        # Use NumPy for better performance (Julia-style vectorized operations)
        is_prime = np.ones(n + 1, dtype=bool)
        is_prime[0] = is_prime[1] = False
        
        for i in range(2, int(n**0.5) + 1):
            if is_prime[i]:
                is_prime[i*i:n+1:i] = False
        
        return np.where(is_prime)[0].tolist()
    
    def _matrix_multiply_fallback(self, a: list, b: list) -> list:
        """Python fallback implementation of matrix multiplication (Julia-style)."""
        # Convert to NumPy arrays for better performance
        a_np = np.array(a, dtype=np.float64)
        b_np = np.array(b, dtype=np.float64)
        
        # Use optimized matrix multiplication (similar to Julia's BLAS)
        result_np = np.dot(a_np, b_np)
        
        return result_np.tolist()
    
    def _sort_array_fallback(self, arr: list) -> list:
        """Python fallback implementation of array sorting."""
        # Use NumPy for better performance (Julia-style)
        arr_np = np.array(arr, dtype=np.int32)
        return np.sort(arr_np).tolist()
    
    def _parallel_compute_fallback(self, data: list, num_threads: int = 2) -> float:
        """Python fallback implementation of parallel computation."""
        # Use NumPy for better performance (Julia-style vectorized operations)
        data_np = np.array(data, dtype=np.float64)
        return float(np.sum(data_np))
    
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        if self.use_fallback:
            return "Julia FFI (Python Fallback)"
        else:
            return "Julia FFI"