# NumPy FFI Implementation

This directory contains the NumPy FFI implementation for the benchmark system.

## Overview

The NumPy FFI implementation provides NumPy-optimized Cython code compiled to a shared library that can be accessed via Python's ctypes FFI interface. This approach leverages NumPy's vectorized operations and optimized BLAS/LAPACK backends.

## Files

- `functions.pyx` - NumPy-based Cython implementation of benchmark functions
- `setup.py` - Build script for compiling Cython to shared library
- `ffi_wrapper.py` - Python ctypes wrapper for the shared library
- `__init__.py` - Module initialization

## Building

The shared library is built automatically when the NumPyFFI class is first instantiated. You can also build it manually:

```bash
cd benchmark/ffi_implementations/numpy_ffi
python setup.py build_ext --inplace
```

## Requirements

- Cython
- NumPy
- A C compiler (gcc, clang, or MSVC)

## Implementation Details

### NumPy Optimizations

The NumPy FFI implementation uses several optimization techniques:

1. **Vectorized Operations**: Uses NumPy's vectorized operations for maximum performance
2. **BLAS/LAPACK**: Leverages optimized linear algebra libraries through NumPy
3. **Memory Layout**: Efficient memory access patterns for cache optimization
4. **Boolean Indexing**: Fast filtering using NumPy's boolean indexing

### Key Features

- **Sieve of Eratosthenes**: Vectorized prime finding using NumPy slicing
- **Matrix Multiplication**: Uses NumPy's optimized `matmul` function
- **Array Operations**: Leverages NumPy's optimized sorting and filtering
- **Parallel Sum**: Uses NumPy's sum which may utilize parallel operations

### FFI Interface

All functions follow the standard C ABI interface:

- `find_primes_ffi(int n, int* count) -> int*`
- `matrix_multiply_ffi(double* a, int rows_a, int cols_a, double* b, int rows_b, int cols_b, int* result_rows, int* result_cols) -> double*`
- `sort_array_ffi(int* arr, int size) -> int*`
- `filter_array_ffi(int* arr, int size, int threshold, int* result_size) -> int*`
- `parallel_compute_ffi(double* data, int size, int num_threads) -> double`
- `free_memory_ffi(void* ptr) -> void`

### Performance Characteristics

NumPy FFI typically provides:
- 5-20x speedup over Pure Python (depending on operation)
- Excellent performance for vectorizable operations
- Automatic use of optimized BLAS/LAPACK libraries
- Efficient memory usage through NumPy arrays

### Comparison with Pure NumPy

This FFI implementation differs from direct NumPy usage in that:
- Data must be converted between C arrays and NumPy arrays
- Additional overhead from FFI calls
- But provides consistent interface with other FFI implementations
- Allows fair comparison of FFI overhead vs direct library usage

## Usage

```python
from benchmark.ffi_implementations.numpy_ffi import NumPyFFI

# Create FFI instance
numpy_ffi = NumPyFFI()

# Use the functions
primes = numpy_ffi.find_primes(100)
result = numpy_ffi.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
```

## Troubleshooting

### Build Issues

1. **Missing Cython**: Install with `pip install cython`
2. **Missing NumPy**: Install with `pip install numpy`
3. **Compiler Issues**: Ensure you have a C compiler installed
4. **BLAS/LAPACK**: NumPy should automatically find optimized libraries

### Runtime Issues

1. **Library Not Found**: The build process may have failed silently
2. **Symbol Errors**: Check that all functions are properly exported
3. **Memory Errors**: Ensure proper cleanup of allocated memory
4. **Performance**: Make sure NumPy is using optimized BLAS (check with `numpy.show_config()`)

### Performance Notes

- Performance depends heavily on NumPy's underlying BLAS/LAPACK implementation
- Intel MKL, OpenBLAS, or Apple Accelerate provide best performance
- For small arrays, FFI overhead may dominate
- For large arrays, NumPy optimizations should provide significant speedup