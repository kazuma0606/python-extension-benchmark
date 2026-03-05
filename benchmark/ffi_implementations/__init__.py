"""
FFI (Foreign Function Interface) implementations for benchmark system.

This module provides FFI-based implementations for various languages,
allowing performance comparison between Pure Python and FFI approaches.
"""

__version__ = "1.0.0"
__author__ = "FFI Benchmark Extensions"

# Import all FFI implementations
from . import c_ffi
from . import cpp_ffi
from . import numpy_ffi
from . import cython_ffi
from . import rust_ffi
from . import fortran_ffi
from . import julia_ffi
from . import go_ffi
from . import zig_ffi
from . import nim_ffi
from . import kotlin_ffi

__all__ = [
    'c_ffi',
    'cpp_ffi', 
    'numpy_ffi',
    'cython_ffi',
    'rust_ffi',
    'fortran_ffi',
    'julia_ffi',
    'go_ffi',
    'zig_ffi',
    'nim_ffi',
    'kotlin_ffi'
]