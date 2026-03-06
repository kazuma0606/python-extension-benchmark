"""
Setup script for building Cython FFI shared library.

This script compiles the Cython code into a Python extension module that can be
imported and used directly from Python.
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy
import os
import platform

# Define the extension
extensions = [
    Extension(
        "cython_functions",
        ["functions.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3"] if platform.system() != 'Windows' else ["/O2"],
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