"""
Julia FFI implementation for benchmark system.

This module provides Julia language functions accessible via FFI (ctypes).
"""

from .ffi_wrapper import JuliaFFI

__all__ = ['JuliaFFI']