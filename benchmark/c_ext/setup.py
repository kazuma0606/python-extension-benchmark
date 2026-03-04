"""Setup script for C extension modules."""

from setuptools import setup, Extension
import platform

# Define the extensions
extensions = [
    Extension(
        'numeric',
        sources=['numeric.c'],
        include_dirs=[],
        libraries=[],
        library_dirs=[],
        extra_compile_args=['/O2'] if platform.system() == 'Windows' else ['-O3'],
        extra_link_args=[]
    ),
    Extension(
        'memory',
        sources=['memory.c'],
        include_dirs=[],
        libraries=[],
        library_dirs=[],
        extra_compile_args=['/O2'] if platform.system() == 'Windows' else ['-O3'],
        extra_link_args=[]
    ),
    Extension(
        'parallel',
        sources=['parallel.c'],
        include_dirs=[],
        libraries=[] if platform.system() == 'Windows' else ['pthread'],
        library_dirs=[],
        extra_compile_args=(['/O2', '/DWINDOWS_THREADS'] if platform.system() == 'Windows' 
                           else ['-O3']),
        extra_link_args=[] if platform.system() == 'Windows' else ['-lpthread']
    )
]

setup(
    name='benchmark-c-ext',
    version='1.0',
    description='C extension modules for Python benchmark',
    ext_modules=extensions,
    zip_safe=False
)