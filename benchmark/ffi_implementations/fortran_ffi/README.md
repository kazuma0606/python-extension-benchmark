# Fortran FFI Implementation

This directory contains the Fortran FFI implementation for the benchmark system, providing high-performance scientific computing functions accessible via Python's ctypes FFI.

## Overview

The Fortran FFI implementation leverages Fortran's strengths in scientific computing while maintaining C ABI compatibility through `iso_c_binding`. This approach allows Python to call optimized Fortran functions directly via shared libraries.

## Features

- **iso_c_binding**: Full C ABI compatibility for seamless FFI integration
- **OpenMP Support**: Parallel computation using OpenMP directives
- **Scientific Computing Optimized**: Leverages Fortran's numerical computation strengths
- **Memory Management**: Proper memory allocation and deallocation handling
- **Cross-Platform**: Supports Linux, macOS, and Windows

## Requirements

- **gfortran**: GNU Fortran compiler (part of GCC)
- **OpenMP**: For parallel computation support (usually included with gfortran)
- **uv environment**: Active uv virtual environment

### Installing gfortran

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install gfortran
```

#### macOS (with Homebrew)
```bash
brew install gcc
```

#### Windows (with MSYS2)
```bash
pacman -S mingw-w64-x86_64-gcc-fortran
```

## Building

### Automatic Build
```bash
make
```

### Manual Build
```bash
# Check if gfortran is available
make check

# Build the shared library
gfortran -fPIC -O3 -fopenmp -std=f2008 -fno-underscoring -c functions.f90
gfortran -shared -fopenmp -o libfortranfunctions.so functions.o  # Linux
# or
gfortran -shared -fopenmp -o libfortranfunctions.dylib functions.o  # macOS
# or
gfortran -shared -fopenmp -o libfortranfunctions.dll functions.o  # Windows
```

### Build Options
- `-fPIC`: Position Independent Code (required for shared libraries)
- `-O3`: Maximum optimization for performance
- `-fopenmp`: Enable OpenMP parallel processing
- `-std=f2008`: Use Fortran 2008 standard
- `-fno-underscoring`: Disable name mangling for C compatibility

## Functions

All functions follow the unified C ABI specification:

### find_primes_ffi
```fortran
function find_primes_ffi(n, count) result(primes_ptr) bind(c)
```
- **Purpose**: Find all prime numbers up to n using Sieve of Eratosthenes
- **Algorithm**: Optimized sieve with early termination
- **Performance**: O(n log log n) time complexity

### matrix_multiply_ffi
```fortran
function matrix_multiply_ffi(a_ptr, rows_a, cols_a, b_ptr, rows_b, cols_b, &
                            result_rows, result_cols) result(c_ptr) bind(c)
```
- **Purpose**: Multiply two matrices with optimal loop ordering
- **Algorithm**: Cache-friendly loop ordering (j-k-i)
- **Performance**: O(n³) with excellent cache locality

### sort_array_ffi
```fortran
function sort_array_ffi(arr_ptr, size) result(result_ptr) bind(c)
```
- **Purpose**: Sort integer array using quicksort
- **Algorithm**: In-place recursive quicksort
- **Performance**: O(n log n) average case

### filter_array_ffi
```fortran
function filter_array_ffi(arr_ptr, size, threshold, result_size) result(result_ptr) bind(c)
```
- **Purpose**: Filter array elements >= threshold
- **Algorithm**: Single-pass linear scan
- **Performance**: O(n) time complexity

### parallel_compute_ffi
```fortran
function parallel_compute_ffi(data_ptr, size, num_threads) result(sum_result) bind(c)
```
- **Purpose**: Parallel sum computation using OpenMP
- **Algorithm**: OpenMP reduction for optimal parallelization
- **Performance**: O(n/p) where p is number of threads

## Usage

```python
from benchmark.ffi_implementations.fortran_ffi import FortranFFI

# Initialize Fortran FFI
fortran_ffi = FortranFFI()

# Check availability
if fortran_ffi.is_available():
    # Use Fortran functions
    primes = fortran_ffi.find_primes(100)
    result = fortran_ffi.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    sorted_arr = fortran_ffi.sort_array([3, 1, 4, 1, 5])
    filtered = fortran_ffi.filter_array([1, 2, 3, 4, 5], 3)
    sum_result = fortran_ffi.parallel_compute([1.0, 2.0, 3.0, 4.0], 2)
```

## Performance Characteristics

### Expected Performance vs Pure Python
- **Prime Finding**: 20-50x faster (optimized sieve algorithm)
- **Matrix Multiplication**: 30-100x faster (cache-friendly loops)
- **Array Sorting**: 15-40x faster (optimized quicksort)
- **Array Filtering**: 10-25x faster (vectorized operations)
- **Parallel Computation**: 5-20x faster (OpenMP parallelization)

### Fortran Advantages
- **Numerical Optimization**: Compiler optimizations for scientific computing
- **Array Operations**: Native support for multi-dimensional arrays
- **OpenMP Integration**: Seamless parallel processing
- **Memory Layout**: Column-major arrays for better cache performance
- **Mathematical Functions**: Optimized intrinsic mathematical functions

## Memory Management

The Fortran FFI implementation uses careful memory management:

1. **Allocation**: Functions allocate result arrays using Fortran's `allocate`
2. **Tracking**: Pointers are returned via `c_loc()` for C compatibility
3. **Cleanup**: Memory should be freed via `free_memory_ffi()` (limited in Fortran FFI)
4. **Limitation**: Direct deallocation from C pointers is not fully supported

**Note**: Due to Fortran's memory model, proper cleanup requires careful coordination between Fortran and Python. The FFI base class handles this automatically.

## Troubleshooting

### Common Issues

1. **gfortran not found**
   ```
   Error: gfortran not found. Please install gfortran.
   ```
   **Solution**: Install gfortran using your system's package manager

2. **OpenMP not supported**
   ```
   Warning: OpenMP not available, falling back to serial computation
   ```
   **Solution**: Ensure gfortran was compiled with OpenMP support

3. **Library not found**
   ```
   OSError: cannot load library 'libfortranfunctions.so'
   ```
   **Solution**: Run `make` to build the shared library

4. **Symbol not found**
   ```
   AttributeError: function 'find_primes_ffi' not found
   ```
   **Solution**: Check that `-fno-underscoring` flag was used during compilation

### Debug Build
```bash
# Build with debug symbols
gfortran -fPIC -g -fopenmp -std=f2008 -fno-underscoring -c functions.f90
gfortran -shared -fopenmp -o libfortranfunctions.so functions.o
```

### Verify Symbols
```bash
# Check exported symbols (Linux/macOS)
nm -D libfortranfunctions.so | grep ffi
objdump -T libfortranfunctions.so | grep ffi
```

## Integration with Benchmark System

The Fortran FFI implementation integrates seamlessly with the benchmark system:

1. **Automatic Detection**: The system automatically detects and loads the Fortran library
2. **Error Handling**: Graceful fallback if Fortran is not available
3. **Performance Comparison**: Direct comparison with Pure Python implementations
4. **Result Validation**: Automatic verification of numerical correctness

## Scientific Computing Benefits

Fortran's advantages for scientific computing in FFI context:

- **Numerical Stability**: IEEE 754 compliance and robust floating-point handling
- **Array Bounds Checking**: Optional runtime bounds checking for debugging
- **Intrinsic Functions**: Optimized mathematical and array intrinsic functions
- **Compiler Optimizations**: Advanced loop optimizations and vectorization
- **Legacy Code Integration**: Easy integration with existing Fortran scientific libraries

This implementation demonstrates how Fortran's scientific computing strengths can be leveraged in modern Python applications through FFI, providing significant performance improvements for numerical computations.