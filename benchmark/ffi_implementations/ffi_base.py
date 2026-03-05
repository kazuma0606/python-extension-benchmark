"""
Unified ctypes base class for FFI implementations.

This module provides the common foundation for all FFI implementations,
including memory management, type conversion, and error handling.
"""

import ctypes
import os
import platform
from typing import List, Optional, Tuple, Any
from abc import ABC, abstractmethod
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FFIMemoryManager:
    """Manages memory allocation and cleanup for FFI operations."""
    
    def __init__(self):
        self._allocated_pointers = []
        self._cleanup_functions = []
    
    def track_pointer(self, ptr: ctypes.POINTER, cleanup_func: Optional[callable] = None):
        """Track a pointer for automatic cleanup.
        
        Args:
            ptr: Pointer to track
            cleanup_func: Optional cleanup function to call
        """
        self._allocated_pointers.append(ptr)
        if cleanup_func:
            self._cleanup_functions.append((ptr, cleanup_func))
    
    def cleanup(self):
        """Clean up all tracked pointers."""
        for ptr, cleanup_func in self._cleanup_functions:
            try:
                cleanup_func(ptr)
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
        
        self._allocated_pointers.clear()
        self._cleanup_functions.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class FFIDataConverter:
    """Handles data conversion between Python and C types."""
    
    @staticmethod
    def python_to_c_int_array(py_list: List[int]) -> Tuple[ctypes.POINTER(ctypes.c_int), int]:
        """Convert Python list to C int array.
        
        Args:
            py_list: Python list of integers
            
        Returns:
            Tuple of (C array pointer, size)
        """
        if not py_list:
            return None, 0
        
        size = len(py_list)
        c_array = (ctypes.c_int * size)(*py_list)
        return ctypes.cast(c_array, ctypes.POINTER(ctypes.c_int)), size
    
    @staticmethod
    def python_to_c_double_array(py_list: List[float]) -> Tuple[ctypes.POINTER(ctypes.c_double), int]:
        """Convert Python list to C double array.
        
        Args:
            py_list: Python list of floats
            
        Returns:
            Tuple of (C array pointer, size)
        """
        if not py_list:
            return None, 0
        
        size = len(py_list)
        c_array = (ctypes.c_double * size)(*py_list)
        return ctypes.cast(c_array, ctypes.POINTER(ctypes.c_double)), size
    
    @staticmethod
    def python_to_c_matrix(py_matrix: List[List[float]]) -> Tuple[ctypes.POINTER(ctypes.c_double), int, int]:
        """Convert Python 2D list to C double array (flattened).
        
        Args:
            py_matrix: Python 2D list
            
        Returns:
            Tuple of (C array pointer, rows, cols)
        """
        if not py_matrix or not py_matrix[0]:
            return None, 0, 0
        
        rows = len(py_matrix)
        cols = len(py_matrix[0])
        
        # Flatten matrix row-wise
        flattened = []
        for row in py_matrix:
            if len(row) != cols:
                raise ValueError("Matrix rows must have equal length")
            flattened.extend(row)
        
        c_array = (ctypes.c_double * len(flattened))(*flattened)
        return ctypes.cast(c_array, ctypes.POINTER(ctypes.c_double)), rows, cols
    
    @staticmethod
    def c_to_python_int_array(c_ptr: ctypes.POINTER(ctypes.c_int), size: int) -> List[int]:
        """Convert C int array to Python list.
        
        Args:
            c_ptr: C array pointer
            size: Array size
            
        Returns:
            Python list of integers
        """
        if not c_ptr or size <= 0:
            return []
        
        return [c_ptr[i] for i in range(size)]
    
    @staticmethod
    def c_to_python_double_array(c_ptr: ctypes.POINTER(ctypes.c_double), size: int) -> List[float]:
        """Convert C double array to Python list.
        
        Args:
            c_ptr: C array pointer
            size: Array size
            
        Returns:
            Python list of floats
        """
        if not c_ptr or size <= 0:
            return []
        
        return [c_ptr[i] for i in range(size)]
    
    @staticmethod
    def c_to_python_matrix(c_ptr: ctypes.POINTER(ctypes.c_double), rows: int, cols: int) -> List[List[float]]:
        """Convert C double array to Python 2D list.
        
        Args:
            c_ptr: C array pointer (flattened matrix)
            rows: Number of rows
            cols: Number of columns
            
        Returns:
            Python 2D list
        """
        if not c_ptr or rows <= 0 or cols <= 0:
            return []
        
        result = []
        for i in range(rows):
            row = []
            for j in range(cols):
                row.append(c_ptr[i * cols + j])
            result.append(row)
        
        return result


class FFIBase(ABC):
    """Base class for all FFI implementations."""
    
    def __init__(self, library_name: str, library_dir: str = None):
        """Initialize FFI base with library name.
        
        Args:
            library_name: Name of the shared library (without extension)
            library_dir: Directory containing the library (if None, auto-detect)
        """
        self.library_name = library_name
        self.library_dir = library_dir
        self.lib = None
        self.memory_manager = FFIMemoryManager()
        self.converter = FFIDataConverter()
        
        # Try to load the library
        self._load_library()
        
        if self.lib:
            self._setup_function_signatures()
    
    def _get_library_path(self) -> str:
        """Get the platform-specific library path."""
        if self.library_dir:
            base_dir = self.library_dir
        else:
            # Get the directory where this FFI implementation is located
            import inspect
            frame = inspect.currentframe()
            caller_frame = frame.f_back.f_back  # Go up two frames to get the actual FFI implementation
            caller_file = caller_frame.f_globals['__file__']
            base_dir = os.path.dirname(caller_file)
        
        # Determine library extension based on platform
        system = platform.system().lower()
        if system == 'windows':
            ext = '.dll'
        elif system == 'darwin':
            ext = '.dylib'
        else:
            ext = '.so'
        
        library_path = os.path.join(base_dir, f"{self.library_name}{ext}")
        return library_path
    
    def _load_library(self):
        """Load the shared library."""
        library_path = self._get_library_path()
        
        if not os.path.exists(library_path):
            logger.warning(f"Shared library not found: {library_path}")
            logger.info(f"FFI implementation '{self.library_name}' will be skipped")
            return
        
        try:
            self.lib = ctypes.CDLL(library_path)
            logger.info(f"Successfully loaded FFI library: {library_path}")
        except Exception as e:
            logger.error(f"Failed to load library {library_path}: {e}")
            self.lib = None
    
    def _setup_function_signatures(self):
        """Setup ctypes function signatures for all FFI functions."""
        if not self.lib:
            return
        
        try:
            # find_primes_ffi(int n, int* count) -> int*
            self.lib.find_primes_ffi.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            self.lib.find_primes_ffi.restype = ctypes.POINTER(ctypes.c_int)
            
            # matrix_multiply_ffi(double* a, int rows_a, int cols_a, double* b, int rows_b, int cols_b, int* result_rows, int* result_cols) -> double*
            self.lib.matrix_multiply_ffi.argtypes = [
                ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
                ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
                ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
            ]
            self.lib.matrix_multiply_ffi.restype = ctypes.POINTER(ctypes.c_double)
            
            # sort_array_ffi(int* arr, int size) -> int*
            self.lib.sort_array_ffi.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
            self.lib.sort_array_ffi.restype = ctypes.POINTER(ctypes.c_int)
            
            # filter_array_ffi(int* arr, int size, int threshold, int* result_size) -> int*
            self.lib.filter_array_ffi.argtypes = [
                ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
            ]
            self.lib.filter_array_ffi.restype = ctypes.POINTER(ctypes.c_int)
            
            # parallel_compute_ffi(double* data, int size, int num_threads) -> double
            self.lib.parallel_compute_ffi.argtypes = [
                ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int
            ]
            self.lib.parallel_compute_ffi.restype = ctypes.c_double
            
            # free_memory_ffi(void* ptr) -> void
            self.lib.free_memory_ffi.argtypes = [ctypes.c_void_p]
            self.lib.free_memory_ffi.restype = None
            
        except AttributeError as e:
            logger.error(f"Failed to setup function signatures: {e}")
            self.lib = None
    
    def is_available(self) -> bool:
        """Check if the FFI implementation is available."""
        return self.lib is not None
    
    def find_primes(self, n: int) -> List[int]:
        """Find all prime numbers up to n using FFI implementation."""
        if not self.is_available():
            raise RuntimeError(f"FFI implementation '{self.library_name}' is not available")
        
        with self.memory_manager:
            count = ctypes.c_int()
            result_ptr = self.lib.find_primes_ffi(n, ctypes.byref(count))
            
            if not result_ptr:
                return []
            
            # Convert result to Python list
            primes = self.converter.c_to_python_int_array(result_ptr, count.value)
            
            # Free memory
            self.lib.free_memory_ffi(result_ptr)
            
            return primes
    
    def matrix_multiply(self, a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        """Multiply two matrices using FFI implementation."""
        if not self.is_available():
            raise RuntimeError(f"FFI implementation '{self.library_name}' is not available")
        
        with self.memory_manager:
            # Convert matrices to C arrays
            a_ptr, rows_a, cols_a = self.converter.python_to_c_matrix(a)
            b_ptr, rows_b, cols_b = self.converter.python_to_c_matrix(b)
            
            if cols_a != rows_b:
                raise ValueError("Matrix dimensions incompatible for multiplication")
            
            # Prepare result dimensions
            result_rows = ctypes.c_int()
            result_cols = ctypes.c_int()
            
            # Call FFI function
            result_ptr = self.lib.matrix_multiply_ffi(
                a_ptr, rows_a, cols_a,
                b_ptr, rows_b, cols_b,
                ctypes.byref(result_rows), ctypes.byref(result_cols)
            )
            
            if not result_ptr:
                return []
            
            # Convert result to Python matrix
            result = self.converter.c_to_python_matrix(
                result_ptr, result_rows.value, result_cols.value
            )
            
            # Free memory
            self.lib.free_memory_ffi(result_ptr)
            
            return result
    
    def sort_array(self, arr: List[int]) -> List[int]:
        """Sort an array using FFI implementation."""
        if not self.is_available():
            raise RuntimeError(f"FFI implementation '{self.library_name}' is not available")
        
        with self.memory_manager:
            # Convert to C array
            arr_ptr, size = self.converter.python_to_c_int_array(arr)
            
            if size == 0:
                return []
            
            # Call FFI function
            result_ptr = self.lib.sort_array_ffi(arr_ptr, size)
            
            if not result_ptr:
                return []
            
            # Convert result to Python list
            result = self.converter.c_to_python_int_array(result_ptr, size)
            
            # Free memory
            self.lib.free_memory_ffi(result_ptr)
            
            return result
    
    def filter_array(self, arr: List[int], threshold: int) -> List[int]:
        """Filter array elements >= threshold using FFI implementation."""
        if not self.is_available():
            raise RuntimeError(f"FFI implementation '{self.library_name}' is not available")
        
        with self.memory_manager:
            # Convert to C array
            arr_ptr, size = self.converter.python_to_c_int_array(arr)
            
            if size == 0:
                return []
            
            # Prepare result size
            result_size = ctypes.c_int()
            
            # Call FFI function
            result_ptr = self.lib.filter_array_ffi(arr_ptr, size, threshold, ctypes.byref(result_size))
            
            if not result_ptr or result_size.value == 0:
                return []
            
            # Convert result to Python list
            result = self.converter.c_to_python_int_array(result_ptr, result_size.value)
            
            # Free memory
            self.lib.free_memory_ffi(result_ptr)
            
            return result
    
    def parallel_compute(self, data: List[float], num_threads: int) -> float:
        """Perform parallel computation using FFI implementation."""
        if not self.is_available():
            raise RuntimeError(f"FFI implementation '{self.library_name}' is not available")
        
        with self.memory_manager:
            # Convert to C array
            data_ptr, size = self.converter.python_to_c_double_array(data)
            
            if size == 0:
                return 0.0
            
            # Call FFI function
            result = self.lib.parallel_compute_ffi(data_ptr, size, num_threads)
            
            return float(result)
    
    @abstractmethod
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        pass