"""
Fortran FFI wrapper implementation.

This module provides a Python wrapper for Fortran functions using ctypes FFI.
"""

from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class FortranFFI(FFIBase):
    """Fortran FFI implementation using ctypes."""
    
    def __init__(self):
        """Initialize Fortran FFI implementation."""
        # Ensure uv environment is active
        require_uv_environment()
        
        # Initialize with library name (without extension)
        super().__init__("libfunctions")
    
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        return "Fortran FFI"