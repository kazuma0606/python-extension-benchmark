# Zig FFI Implementation

This directory contains the Zig FFI (Foreign Function Interface) implementation for the benchmark system. It provides high-performance Zig functions accessible from Python via ctypes.

## Overview

The Zig FFI implementation leverages Zig's memory safety features and performance optimizations to provide efficient implementations of benchmark functions. It uses Zig's C ABI compatibility to create shared libraries that can be called from Python.

## Features

- **Memory Safety**: Zig's compile-time memory safety checks prevent common errors
- **Performance**: Optimized implementations with efficient algorithms
- **C ABI Compatibility**: All functions follow the standard C ABI for FFI integration
- **Cross-platform**: Builds on Linux, macOS, and Windows
- **Thread Safety**: Safe parallel processing with Zig's threading model

## Files

- `functions.zig` - Zig implementation of benchmark functions with C exports
- `build.zig` - Zig build configuration
- `build.zig.zon` - Zig package configuration
- `ffi_wrapper.py` - Python ctypes wrapper for Zig functions
- `__init__.py` - Module initialization

## Building

### Prerequisites

- Zig 0.12.0 or later
- C compiler (for linking)

### Build Commands

```bash
# Build shared library
zig build

# Or build manually
zig build-lib -dynamic -lc functions.zig  # Creates libfunctions.so/dll/dylib

# Clean build artifacts
rm -rf zig-out zig-cache
```

### Platform-specific builds

```bash
# Linux
zig build -Dtarget=x86_64-linux

# Windows
zig build -Dtarget=x86_64-windows

# macOS
zig build -Dtarget=x86_64-macos
```

## Functions

All functions follow the FFI C ABI specification:

### find_primes_ffi
```c
int* find_primes_ffi(int n, int* count);
```
Finds all prime numbers up to n using the Sieve of Eratosthenes algorithm with memory-safe implementation.

### matrix_multiply_ffi
```c
double* matrix_multiply_ffi(double* a, int rows_a, int cols_a, 
                           double* b, int rows_b, int cols_b,
                           int* result_rows, int* result_cols);
```
Multiplies two matrices using cache-friendly access patterns for optimal performance.

### sort_array_ffi
```c
int* sort_array_ffi(int* arr, int size);
```
Sorts an integer array using Zig's optimized introsort algorithm (hybrid of quicksort, heapsort, and insertion sort).

### filter_array_ffi
```c
int* filter_array_ffi(int* arr, int size, int threshold, int* result_size);
```
Filters array elements that are >= threshold with memory-safe implementation.

### parallel_compute_ffi
```c
double parallel_compute_ffi(double* data, int size, int num_threads);
```
Performs parallel computation (sum) using Zig's threading model with proper error handling.

### free_memory_ffi
```c
void free_memory_ffi(void* ptr);
```
Frees memory allocated by Zig FFI functions (simplified implementation).

## Performance Characteristics

- **Memory Safety**: Compile-time checks prevent buffer overflows and memory leaks
- **Performance**: Comparable to C with additional safety guarantees
- **Optimization**: Zig's optimizer produces efficient machine code
- **Threading**: Safe parallel processing with proper synchronization

## Usage from Python

```python
from benchmark.ffi_implementations.zig_ffi import ZigFFI

# Create FFI instance
zig_ffi = ZigFFI()

# Check if available
if zig_ffi.is_available():
    # Use FFI functions
    primes = zig_ffi.find_primes(100)
    result = zig_ffi.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    sorted_arr = zig_ffi.sort_array([3, 1, 4, 1, 5])
    filtered = zig_ffi.filter_array([1, 2, 3, 4, 5], 3)
    sum_result = zig_ffi.parallel_compute([1.0, 2.0, 3.0, 4.0], 2)
```

## Troubleshooting

### Common Issues

1. **Zig not installed**: Install Zig 0.12.0+ from https://ziglang.org/
2. **Build errors**: Ensure you have a C compiler available for linking
3. **Library not found**: Run `zig build` to create the shared library

### Build Errors

- **"zig: command not found"**: Install Zig and add it to your PATH
- **"unable to find libc"**: Install development tools for your platform
- **"build.zig not found"**: Ensure you're in the correct directory

### Runtime Errors

- **Library load failed**: Check if shared library exists and has correct permissions
- **Function not found**: Verify the shared library was built correctly
- **Memory errors**: Zig's safety features should prevent most memory issues

## Integration with Benchmark System

The Zig FFI implementation integrates seamlessly with the benchmark system:

1. **Automatic Detection**: The system automatically detects if the Zig shared library is available
2. **Error Handling**: Graceful fallback if Zig FFI is not available
3. **Performance Comparison**: Direct comparison with Pure Python implementations
4. **Memory Safety**: Zig's compile-time checks provide additional safety guarantees

## Expected Performance

Zig FFI typically provides:
- **10-40x speedup** over Pure Python for most operations
- **Memory safety** without runtime overhead
- **Predictable performance** with minimal runtime surprises
- **Good parallel performance** with proper thread management

The actual performance depends on:
- Problem size and complexity
- Zig compiler optimizations
- Target platform capabilities
- Memory access patterns

## Memory Management

Zig FFI uses a simplified memory management approach:
- **Allocation**: Uses Zig's GeneralPurposeAllocator for safety
- **Deallocation**: Simplified free_memory_ffi function
- **Safety**: Compile-time checks prevent common memory errors
- **Note**: Production implementations would need more sophisticated memory tracking