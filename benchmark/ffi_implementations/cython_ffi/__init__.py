"""
Cython FFI implementation for benchmark system.

This module provides Cython-optimized functions accessible via FFI (ctypes).
"""

from .ffi_wrapper import CythonFFI

__all__ = ['CythonFFI']