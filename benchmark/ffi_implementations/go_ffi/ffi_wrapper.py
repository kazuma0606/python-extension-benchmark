"""
Go FFI wrapper implementation.

This module provides a Python wrapper for Go functions using ctypes FFI.
"""

from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class GoFFI(FFIBase):
    """Go FFI implementation using ctypes."""
    
    def __init__(self):
        """Initialize Go FFI implementation."""
        # Ensure uv environment is active
        require_uv_environment()
        
        # Initialize with library name (without extension)
        super().__init__("libfunctions")
    
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        return "Go FFI"