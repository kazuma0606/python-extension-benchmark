# Cython FFI Implementation

This directory contains the Cython FFI implementation for the benchmark system.

## Overview

The Cython FFI implementation provides optimized Cython code compiled to a shared library that can be accessed via Python's ctypes FFI interface. This approach combines Cython's performance optimizations with the flexibility of FFI.

## Files

- `functions.pyx` - Cython implementation of benchmark functions
- `setup.py` - Build script for compiling Cython to shared library
- `ffi_wrapper.py` - Python ctypes wrapper for the shared library
- `__init__.py` - Module initialization

## Building

The shared library is built automatically when the CythonFFI class is first instantiated. You can also build it manually:

```bash
cd benchmark/ffi_implementations/cython_ffi
python setup.py build_ext --inplace
```

## Requirements

- Cython
- NumPy
- A C compiler (gcc, clang, or MSVC)

## Implementation Details

### Cython Optimizations

The Cython implementation uses several optimization techniques:

1. **Compiler Directives**: Disables bounds checking and wraparound for maximum performance
2. **Static Typing**: Uses `cdef` declarations for C-level performance
3. **Memory Management**: Direct malloc/free for efficient memory usage
4. **Loop Optimization**: Optimized loops with minimal Python overhead

### FFI Interface

All functions follow the standard C ABI interface:

- `find_primes_ffi(int n, int* count) -> int*`
- `matrix_multiply_ffi(double* a, int rows_a, int cols_a, double* b, int rows_b, int cols_b, int* result_rows, int* result_cols) -> double*`
- `sort_array_ffi(int* arr, int size) -> int*`
- `filter_array_ffi(int* arr, int size, int threshold, int* result_size) -> int*`
- `parallel_compute_ffi(double* data, int size, int num_threads) -> double`
- `free_memory_ffi(void* ptr) -> void`

### Performance Characteristics

Cython FFI typically provides:
- 5-30x speedup over Pure Python
- Near C-level performance for numerical computations
- Efficient NumPy integration
- Automatic memory management

## Usage

```python
from benchmark.ffi_implementations.cython_ffi import CythonFFI

# Create FFI instance
cython_ffi = CythonFFI()

# Use the functions
primes = cython_ffi.find_primes(100)
result = cython_ffi.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
```

## Troubleshooting

### Build Issues

1. **Missing Cython**: Install with `pip install cython`
2. **Missing NumPy**: Install with `pip install numpy`
3. **Compiler Issues**: Ensure you have a C compiler installed
4. **Permission Issues**: Make sure you have write permissions in the directory

### Runtime Issues

1. **Library Not Found**: The build process may have failed silently
2. **Symbol Errors**: Check that all functions are properly exported
3. **Memory Errors**: Ensure proper cleanup of allocated memory