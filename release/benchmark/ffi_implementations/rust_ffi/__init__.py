"""
Rust FFI implementation for benchmark system.

This module provides Rust language functions accessible via FFI (ctypes).
"""

from .ffi_wrapper import RustFFI

__all__ = ['RustFFI']