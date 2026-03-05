"""
NumPy FFI wrapper implementation.

This module provides a Python wrapper for NumPy-optimized functions using ctypes FFI.
"""

from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class NumpyFFI(FFIBase):
    """NumPy FFI implementation using ctypes."""
    
    def __init__(self):
        """Initialize NumPy FFI implementation."""
        # Ensure uv environment is active
        require_uv_environment()
        
        # Initialize with library name (without extension)
        super().__init__("libfunctions")
    
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        return "NumPy FFI"