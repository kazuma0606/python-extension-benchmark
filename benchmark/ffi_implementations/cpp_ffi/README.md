# C++ FFI Implementation

This directory contains the C++ implementation for FFI (Foreign Function Interface) benchmarking.

## Files

- `functions.cpp` - C++ implementation of benchmark functions
- `functions.h` - Header file with C ABI function declarations
- `Makefile` - Build script for creating shared library
- `ffi_wrapper.py` - Python ctypes wrapper
- `__init__.py` - Python module initialization

## Building

To build the shared library:

```bash
cd benchmark/ffi_implementations/cpp_ffi
make
```

This will create:
- `libfunctions.so` on Linux
- `libfunctions.dylib` on macOS  
- `libfunctions.dll` on Windows

## Functions

The C++ implementation provides the same C ABI functions as the C version but uses modern C++ features internally:

### find_primes_ffi(int n, int* count)
Finds all prime numbers up to n using C++ std::vector.
- **Input**: n (upper limit), count (output parameter for result size)
- **Output**: Array of prime numbers
- **Memory**: Caller must free returned pointer using free_memory_ffi()

### matrix_multiply_ffi(double* a, int rows_a, int cols_a, double* b, int rows_b, int cols_b, int* result_rows, int* result_cols)
Multiplies two matrices using C++ loops and memory management.
- **Input**: Matrix a (rows_a × cols_a), Matrix b (rows_b × cols_b)
- **Output**: Result matrix, dimensions in result_rows/result_cols
- **Memory**: Caller must free returned pointer using free_memory_ffi()

### sort_array_ffi(int* arr, int size)
Sorts an integer array using C++ STL std::sort.
- **Input**: Array and size
- **Output**: Sorted array copy
- **Memory**: Caller must free returned pointer using free_memory_ffi()

### filter_array_ffi(int* arr, int size, int threshold, int* result_size)
Filters array elements >= threshold using C++ std::vector.
- **Input**: Array, size, threshold, result_size (output parameter)
- **Output**: Filtered array
- **Memory**: Caller must free returned pointer using free_memory_ffi()

### parallel_compute_ffi(double* data, int size, int num_threads)
Computes sum of squares using C++ features.
- **Input**: Data array, size, number of threads
- **Output**: Sum of squares (double)
- **Note**: Current implementation is sequential

### free_memory_ffi(void* ptr)
Frees memory allocated by FFI functions using C++ std::free.
- **Input**: Pointer to free
- **Output**: None

## C++ Features Used

- **STL Containers**: std::vector for dynamic arrays
- **STL Algorithms**: std::sort, std::copy for efficient operations
- **Modern C++**: C++11 features, nullptr, static_cast
- **Memory Safety**: RAII principles where possible
- **C ABI Compatibility**: extern "C" linkage for Python interop

## Usage

```python
from benchmark.ffi_implementations.cpp_ffi import CppFFI

# Create FFI instance
cpp_ffi = CppFFI()

# Check if available
if cpp_ffi.is_available():
    # Use FFI functions
    primes = cpp_ffi.find_primes(100)
    print(f"Primes up to 100: {primes}")
else:
    print("C++ FFI not available - shared library not built")
```

## Requirements

- G++ compiler with C++11 support
- Make utility
- Standard C++ library

## Performance

The C++ implementation provides:
- Native performance with C++ optimizations
- STL algorithm efficiency (e.g., std::sort is typically highly optimized)
- Modern C++ memory management
- Expected 10-50x speedup over Pure Python
- Comparable performance to C implementation with potential STL advantages