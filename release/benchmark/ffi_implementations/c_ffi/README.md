# C FFI Implementation

This directory contains the C implementation for FFI (Foreign Function Interface) benchmarking.

## Files

- `functions.c` - C implementation of benchmark functions
- `functions.h` - Header file with function declarations
- `Makefile` - Build script for creating shared library
- `ffi_wrapper.py` - Python ctypes wrapper
- `__init__.py` - Python module initialization

## Building

To build the shared library:

```bash
cd benchmark/ffi_implementations/c_ffi
make
```

This will create:
- `libfunctions.so` on Linux
- `libfunctions.dylib` on macOS  
- `libfunctions.dll` on Windows

## Functions

The C implementation provides the following functions:

### find_primes_ffi(int n, int* count)
Finds all prime numbers up to n.
- **Input**: n (upper limit), count (output parameter for result size)
- **Output**: Array of prime numbers
- **Memory**: Caller must free returned pointer using free_memory_ffi()

### matrix_multiply_ffi(double* a, int rows_a, int cols_a, double* b, int rows_b, int cols_b, int* result_rows, int* result_cols)
Multiplies two matrices.
- **Input**: Matrix a (rows_a × cols_a), Matrix b (rows_b × cols_b)
- **Output**: Result matrix, dimensions in result_rows/result_cols
- **Memory**: Caller must free returned pointer using free_memory_ffi()

### sort_array_ffi(int* arr, int size)
Sorts an integer array in ascending order.
- **Input**: Array and size
- **Output**: Sorted array copy
- **Memory**: Caller must free returned pointer using free_memory_ffi()

### filter_array_ffi(int* arr, int size, int threshold, int* result_size)
Filters array elements >= threshold.
- **Input**: Array, size, threshold, result_size (output parameter)
- **Output**: Filtered array
- **Memory**: Caller must free returned pointer using free_memory_ffi()

### parallel_compute_ffi(double* data, int size, int num_threads)
Computes sum of squares of array elements.
- **Input**: Data array, size, number of threads
- **Output**: Sum of squares (double)
- **Note**: Current implementation is sequential

### free_memory_ffi(void* ptr)
Frees memory allocated by FFI functions.
- **Input**: Pointer to free
- **Output**: None

## Usage

```python
from benchmark.ffi_implementations.c_ffi import CFFI

# Create FFI instance
c_ffi = CFFI()

# Check if available
if c_ffi.is_available():
    # Use FFI functions
    primes = c_ffi.find_primes(100)
    print(f"Primes up to 100: {primes}")
else:
    print("C FFI not available - shared library not built")
```

## Requirements

- GCC compiler
- Make utility
- Standard C library with math support (-lm)

## Performance

The C implementation provides direct native performance with minimal overhead:
- No interpretation layer
- Optimized compiler output (-O2)
- Direct memory management
- Expected 10-50x speedup over Pure Python for computational tasks