"""
NumPy FFI implementation for benchmark system.

This module provides NumPy-optimized functions accessible via FFI (ctypes).
"""

from .ffi_wrapper import NumpyFFI

__all__ = ['NumpyFFI']