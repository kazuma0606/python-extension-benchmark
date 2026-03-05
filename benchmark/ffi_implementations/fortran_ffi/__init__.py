"""
Fortran FFI implementation for benchmark system.

This module provides Fortran language functions accessible via FFI (ctypes).
"""

from .ffi_wrapper import FortranFFI

__all__ = ['FortranFFI']