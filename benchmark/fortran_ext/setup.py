"""Setup script for building Fortran extensions using f2py."""

import os
import sys
from pathlib import Path
from numpy.distutils.core import setup, Extension
from numpy.distutils import fcompiler


def build_fortran_extensions():
    """Build Fortran extensions using f2py."""
    
    # Define extensions with OpenMP support
    extensions = [
        Extension(
            name='benchmark.fortran_ext.numeric',
            sources=['numeric.f90'],
            extra_f90_compile_args=['-O3', '-ffast-math'],
            extra_link_args=[],
        ),
        Extension(
            name='benchmark.fortran_ext.memory',
            sources=['memory.f90'],
            extra_f90_compile_args=['-O3', '-ffast-math'],
            extra_link_args=[],
        ),
        Extension(
            name='benchmark.fortran_ext.parallel',
            sources=['parallel.f90'],
            extra_f90_compile_args=['-O3', '-ffast-math', '-fopenmp'],
            extra_link_args=['-fopenmp'],
        ),
    ]
    
    setup(
        name='fortran_benchmark_extensions',
        ext_modules=extensions,
        zip_safe=False,
    )


if __name__ == "__main__":
    build_fortran_extensions()