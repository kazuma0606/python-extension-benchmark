"""
Cython FFI wrapper implementation.

This module provides a Python wrapper for Cython functions by importing
the compiled Cython extension directly.
"""

import os
import subprocess
import sys
import numpy as np
from ..uv_checker import require_uv_environment


class CythonFFI:
    """Cython FFI implementation using direct Cython extension import."""
    
    def __init__(self, skip_uv_check=False):
        """Initialize Cython FFI implementation.
        
        Args:
            skip_uv_check: If True, skip uv environment check (for testing)
        """
        # Ensure uv environment is active (unless skipped for testing)
        if not skip_uv_check and not os.environ.get('PYTEST_CURRENT_TEST'):
            require_uv_environment()
        
        # Get the directory where this file is located
        self.library_dir = os.path.dirname(__file__)
        
        # Try to build and import the Cython extension
        self.use_fallback = False
        try:
            self._ensure_extension_built()
            self._import_cython_module()
        except Exception as e:
            print(f"Warning: Cython extension not available, using Python fallback: {e}")
            self.use_fallback = True
    
    def _ensure_extension_built(self):
        """Ensure the Cython extension is built."""
        # Check if extension exists
        import glob
        import platform
        
        system = platform.system().lower()
        if system == 'windows':
            pattern = os.path.join(self.library_dir, "cython_functions*.pyd")
        else:
            pattern = os.path.join(self.library_dir, "cython_functions*.so")
        
        built_files = glob.glob(pattern)
        
        if not built_files:
            self._build_extension()
            built_files = glob.glob(pattern)
            
        if not built_files:
            raise FileNotFoundError("Cython extension not found after build attempt")
    
    def _build_extension(self):
        """Build the Cython extension."""
        try:
            # Change to library directory
            original_cwd = os.getcwd()
            os.chdir(self.library_dir)
            
            # Build the extension
            result = subprocess.run([
                sys.executable, 'setup.py', 'build_ext', '--inplace'
            ], capture_output=True, text=True, check=True)
            
            print(f"Successfully built Cython extension")
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to build Cython extension: {e}")
        except Exception as e:
            raise RuntimeError(f"Error building Cython extension: {e}")
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    def _import_cython_module(self):
        """Import the compiled Cython module."""
        # Add the library directory to Python path temporarily
        if self.library_dir not in sys.path:
            sys.path.insert(0, self.library_dir)
        
        try:
            import cython_functions
            self.cython_module = cython_functions
        except ImportError as e:
            raise ImportError(f"Failed to import Cython module: {e}")
    
    def find_primes(self, n: int) -> list:
        """Find all prime numbers up to n using Sieve of Eratosthenes."""
        if self.use_fallback:
            return self._find_primes_fallback(n)
        else:
            return self.cython_module.find_primes_py(n)
    
    def matrix_multiply(self, a: list, b: list) -> list:
        """Multiply two matrices."""
        if self.use_fallback:
            return self._matrix_multiply_fallback(a, b)
        else:
            return self.cython_module.matrix_multiply_py(a, b)
    
    def sort_array(self, arr: list) -> list:
        """Sort an array of integers."""
        if self.use_fallback:
            return self._sort_array_fallback(arr)
        else:
            return self.cython_module.sort_array_py(arr)
    
    def filter_array(self, arr: list, threshold: int) -> list:
        """Filter array elements >= threshold."""
        if self.use_fallback:
            return self._filter_array_fallback(arr, threshold)
        elif hasattr(self.cython_module, 'filter_array_py'):
            return self.cython_module.filter_array_py(arr, threshold)
        else:
            return self._filter_array_fallback(arr, threshold)

    def parallel_compute(self, data: list, num_threads: int = 2) -> float:
        """Compute sum of array elements (parallel version)."""
        if self.use_fallback:
            return self._parallel_compute_fallback(data, num_threads)
        else:
            return self.cython_module.parallel_compute_py(data, num_threads)
    
    def _find_primes_fallback(self, n: int) -> list:
        """Python fallback implementation of prime finding."""
        if n < 2:
            return []
        
        # Use NumPy for better performance
        is_prime = np.ones(n + 1, dtype=bool)
        is_prime[0] = is_prime[1] = False
        
        for i in range(2, int(n**0.5) + 1):
            if is_prime[i]:
                is_prime[i*i:n+1:i] = False
        
        return np.where(is_prime)[0].tolist()
    
    def _matrix_multiply_fallback(self, a: list, b: list) -> list:
        """Python fallback implementation of matrix multiplication."""
        # Convert to NumPy arrays for better performance
        a_np = np.array(a)
        b_np = np.array(b)
        
        # Perform matrix multiplication
        result_np = np.dot(a_np, b_np)
        
        return result_np.tolist()
    
    def _filter_array_fallback(self, arr: list, threshold: int) -> list:
        """Python fallback for array filtering."""
        arr_np = np.array(arr)
        return arr_np[arr_np >= threshold].tolist()

    def _sort_array_fallback(self, arr: list) -> list:
        """Python fallback implementation of array sorting."""
        # Use NumPy for better performance
        arr_np = np.array(arr)
        return np.sort(arr_np).tolist()
    
    def _parallel_compute_fallback(self, data: list, num_threads: int = 2) -> float:
        """Python fallback implementation of parallel computation."""
        # Use NumPy for better performance
        data_np = np.array(data)
        return float(np.sum(data_np))
    
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        if self.use_fallback:
            return "Cython FFI (Python Fallback)"
        else:
            return "Cython FFI"