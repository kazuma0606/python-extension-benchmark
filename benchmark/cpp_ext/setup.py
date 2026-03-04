"""Setup script for C++ extension modules using pybind11."""

import os
import sys
import subprocess
from pathlib import Path
from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import pybind11
from setuptools import setup, Extension

# The main interface is through Pybind11Extension.
# * You can add cxx_std=14/17/20, or even cxx_std="auto" for automatic detection
# * You can set include_pybind11=false to add the include directory yourself,
#   say from a submodule.
#
# Note:
#   Sort input source files if you glob sources to ensure bit-for-bit
#   reproducible builds (https://github.com/pybind/python_example/pull/53)

ext_modules = [
    Pybind11Extension(
        "numeric",
        [
            "numeric.cpp",
        ],
        # Example: passing in the version to the compiled code
        define_macros = [("VERSION_INFO", '"{}"'.format("dev"))],
        cxx_std=17,
    ),
    Pybind11Extension(
        "memory",
        [
            "memory.cpp",
        ],
        define_macros = [("VERSION_INFO", '"{}"'.format("dev"))],
        cxx_std=17,
    ),
    Pybind11Extension(
        "parallel",
        [
            "parallel.cpp",
        ],
        define_macros = [("VERSION_INFO", '"{}"'.format("dev"))],
        cxx_std=17,
    ),
]

setup(
    name="benchmark-cpp-ext",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.6",
)