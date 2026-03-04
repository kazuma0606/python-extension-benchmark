"""Setup script for building Cython extensions."""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

# Define extensions
extensions = [
    Extension(
        "benchmark.cython_ext.numeric",
        ["benchmark/cython_ext/numeric.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3", "-fopenmp"],
        extra_link_args=["-fopenmp"],
    ),
    Extension(
        "benchmark.cython_ext.memory",
        ["benchmark/cython_ext/memory.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3"],
    ),
    Extension(
        "benchmark.cython_ext.parallel",
        ["benchmark/cython_ext/parallel.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-O3", "-fopenmp"],
        extra_link_args=["-fopenmp"],
    ),
]

setup(
    name="cython_benchmark_extensions",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": 3,
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        }
    ),
    zip_safe=False,
)