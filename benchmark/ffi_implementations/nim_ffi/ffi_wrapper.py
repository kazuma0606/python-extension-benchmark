"""
Nim FFI wrapper implementation.

This module provides a Python wrapper for Nim functions using ctypes FFI.
"""

import os
from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class NimFFI(FFIBase):
    """Nim FFI implementation using ctypes."""

    def __init__(self, skip_uv_check=False):
        """Initialize Nim FFI implementation."""
        if not skip_uv_check and not os.environ.get('PYTEST_CURRENT_TEST'):
            require_uv_environment()

        library_dir = os.path.dirname(__file__)
        super().__init__("libfunctions", library_dir)

    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        return "Nim FFI"
