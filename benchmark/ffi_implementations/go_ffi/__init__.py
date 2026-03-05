"""
Go FFI implementation for benchmark system.

This module provides Go language functions accessible via FFI (ctypes).
"""

from .ffi_wrapper import GoFFI

__all__ = ['GoFFI']