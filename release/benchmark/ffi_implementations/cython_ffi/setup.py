"""
Setup script for building Cython FFI shared library.

This script compiles the Cython code into a shared library that can be
accessed via ctypes FFI.
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy
import os
import platform

# Determine the output library name based on platform
system = platform.system().lower()
if system == 'windows':
    library_name = 'libcythonfunctions.dll'
elif system == 'darwin':
    library_name = 'libcythonfunctions.dylib'
else:
    library_name = 'libcythonfunctions.so'

# Get the directory where this setup.py is located
current_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(current_dir, library_name)

# Define the extension
extensions = [
    Extension(
        "cython_functions",
        ["functions.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3", "-ffast-math"],
        extra_link_args=[],
        language="c"
    )
]

# Compiler directives for optimization
compiler_directives = {
    'language_level': 3,
    'boundscheck': False,
    'wraparound': False,
    'cdivision': True,
    'nonecheck': False,
}

if __name__ == "__main__":
    setup(
        name="cython_ffi_functions",
        ext_modules=cythonize(
            extensions,
            compiler_directives=compiler_directives,
            build_dir="build"
        ),
        zip_safe=False,
        include_dirs=[numpy.get_include()],
    )