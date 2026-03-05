"""
Setup script for Nim extension

This script provides an alternative way to build the Nim extension
using Python's setuptools infrastructure.
"""

from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext
import subprocess
import os
import sys

def check_nim_available():
    """Check if Nim compiler is available"""
    try:
        subprocess.run(['nim', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def compile_nim_library():
    """Compile Nim source to shared library"""
    if not check_nim_available():
        print("Warning: Nim compiler not found. Skipping Nim extension build.")
        return False
    
    try:
        # Compile Nim source to shared library
        compile_cmd = [
            'nim', 'c',
            '--app:lib',
            '--gc:arc',
            '--opt:speed',
            '--threads:on',
            '--tlsEmulation:off',
            '--passC:-fPIC',
            '--passL:-shared',
            '--out:libnimfunctions.so',
            'functions.nim'
        ]
        
        subprocess.run(compile_cmd, check=True, cwd=os.path.dirname(__file__))
        print("Nim library compiled successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to compile Nim library: {e}")
        return False

class CustomBuildExt(build_ext):
    """Custom build extension that compiles Nim first"""
    
    def run(self):
        # Compile Nim library first
        compile_nim_library()
        # Then run the standard build
        super().run()

setup(
    name="nim_ext",
    version="1.0.0",
    description="Nim extension for Python benchmark system",
    author="Benchmark Team",
    packages=["nim_ext"],
    package_dir={"nim_ext": "."},
    install_requires=[
        "nimpy",
    ],
    cmdclass={"build_ext": CustomBuildExt},
    zip_safe=False,
    python_requires=">=3.8",
)