"""
C++ FFI wrapper implementation.

This module provides a Python wrapper for C++ functions using ctypes FFI.
"""

import os
from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class CppFFI(FFIBase):
    """C++ FFI implementation using ctypes."""
    
    def __init__(self, skip_uv_check=False):
        """Initialize C++ FFI implementation.
        
        Args:
            skip_uv_check: If True, skip uv environment check (for testing)
        """
        # Ensure uv environment is active (unless skipped for testing)
        if not skip_uv_check and not os.environ.get('PYTEST_CURRENT_TEST'):
            require_uv_environment()
        
        # Get the directory where this file is located
        library_dir = os.path.dirname(__file__)
        
        # Initialize with library name (without extension) and directory
        super().__init__("libfunctions", library_dir)
    
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        return "C++ FFI"