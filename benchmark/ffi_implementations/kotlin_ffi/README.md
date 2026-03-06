# Kotlin FFI Implementation

This directory contains the Kotlin FFI (Foreign Function Interface) implementation for the benchmark system. It provides high-performance Kotlin/Native functions accessible from Python via ctypes.

## Overview

The Kotlin FFI implementation leverages Kotlin/Native's ability to compile to native code and create C-compatible shared libraries. It uses Kotlin's modern language features while maintaining C ABI compatibility for FFI integration.

## Features

- **Native Performance**: Compiled to native machine code for optimal performance
- **Memory Management**: Efficient memory allocation with native heap management
- **C ABI Compatibility**: All functions follow the standard C ABI for FFI integration
- **Cross-platform**: Builds on Linux, macOS, and Windows
- **Modern Language**: Leverages Kotlin's expressive syntax and safety features

## Files

- `functions.kt` - Kotlin/Native implementation of benchmark functions with C exports
- `build.gradle.kts` - Gradle build configuration for Kotlin/Native
- `gradle.properties` - Gradle properties for optimization
- `settings.gradle.kts` - Gradle settings
- `ffi_wrapper.py` - Python ctypes wrapper for Kotlin functions
- `__init__.py` - Module initialization

## Building

### Prerequisites

- JDK 8 or later
- Gradle 7.0 or later (or use Gradle wrapper)
- Kotlin/Native toolchain (automatically downloaded by Gradle)

### Build Commands

```bash
# Build shared library using Gradle wrapper (recommended)
./gradlew build

# Or using system Gradle
gradle build

# Clean build artifacts
./gradlew clean

# Build only the shared library
./gradlew linkReleaseSharedNative

# Copy library to current directory
./gradlew copySharedLib
```

### Platform-specific builds

The build system automatically detects the platform and builds the appropriate shared library:
- **Linux**: `liblibfunctions.so`
- **Windows**: `liblibfunctions.dll`
- **macOS**: `liblibfunctions.dylib`

## Functions

All functions follow the FFI C ABI specification:

### find_primes_ffi
```c
int* find_primes_ffi(int n, int* count);
```
Finds all prime numbers up to n using the Sieve of Eratosthenes algorithm with efficient memory management.

### matrix_multiply_ffi
```c
double* matrix_multiply_ffi(double* a, int rows_a, int cols_a, 
                           double* b, int rows_b, int cols_b,
                           int* result_rows, int* result_cols);
```
Multiplies two matrices using cache-friendly algorithms with proper memory allocation.

### sort_array_ffi
```c
int* sort_array_ffi(int* arr, int size);
```
Sorts an integer array using Kotlin's optimized introsort algorithm.

### filter_array_ffi
```c
int* filter_array_ffi(int* arr, int size, int threshold, int* result_size);
```
Filters array elements that are >= threshold with efficient two-pass algorithm.

### parallel_compute_ffi
```c
double parallel_compute_ffi(double* data, int size, int num_threads);
```
Performs parallel computation (sum) using divide-and-conquer approach for efficient processing.

### free_memory_ffi
```c
void free_memory_ffi(void* ptr);
```
Frees memory allocated by Kotlin FFI functions using native heap management.

## Performance Characteristics

- **Native Speed**: Compiled to optimized native machine code
- **Memory Efficiency**: Direct memory management without garbage collection overhead
- **Algorithm Optimization**: Uses efficient algorithms with good cache locality
- **Parallelism**: Divide-and-conquer approach for scalable parallel processing

## Usage from Python

```python
from benchmark.ffi_implementations.kotlin_ffi import KotlinFFI

# Create FFI instance
kotlin_ffi = KotlinFFI()

# Check if available
if kotlin_ffi.is_available():
    # Use FFI functions
    primes = kotlin_ffi.find_primes(100)
    result = kotlin_ffi.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    sorted_arr = kotlin_ffi.sort_array([3, 1, 4, 1, 5])
    filtered = kotlin_ffi.filter_array([1, 2, 3, 4, 5], 3)
    sum_result = kotlin_ffi.parallel_compute([1.0, 2.0, 3.0, 4.0], 2)
```

## Troubleshooting

### Common Issues

1. **JDK not installed**: Install JDK 8+ from https://adoptium.net/
2. **Gradle not found**: Use the Gradle wrapper (`./gradlew`) or install Gradle
3. **Library not found**: Run `./gradlew build` to create the shared library

### Build Errors

- **"JAVA_HOME not set"**: Set JAVA_HOME environment variable to JDK installation
- **"Gradle daemon stopped"**: Increase heap size in gradle.properties
- **"Kotlin/Native not found"**: Gradle will automatically download the toolchain

### Runtime Errors

- **Library load failed**: Check if shared library exists and has correct permissions
- **Function not found**: Verify the shared library was built correctly
- **Memory errors**: Ensure proper cleanup using free_memory_ffi

## Integration with Benchmark System

The Kotlin FFI implementation integrates seamlessly with the benchmark system:

1. **Automatic Detection**: The system automatically detects if the Kotlin shared library is available
2. **Error Handling**: Graceful fallback if Kotlin FFI is not available
3. **Performance Comparison**: Direct comparison with Pure Python implementations
4. **Memory Safety**: Native heap management with explicit cleanup

## Expected Performance

Kotlin FFI typically provides:
- **2-10x speedup** over Pure Python for most operations
- **Consistent performance** with native code compilation
- **Good memory efficiency** with direct memory management
- **Moderate parallel performance** with divide-and-conquer algorithms

The actual performance depends on:
- Problem size and complexity
- Kotlin/Native compiler optimizations
- Target platform capabilities
- JIT warmup effects (minimal for native code)

## Memory Management

Kotlin FFI uses native heap management:
- **Allocation**: Uses nativeHeap.allocArray for FFI return values
- **Deallocation**: Manual cleanup via free_memory_ffi function
- **Safety**: Explicit memory management without garbage collection
- **Efficiency**: Direct memory allocation suitable for FFI integration

## Development Notes

- **Kotlin/Native Limitations**: Some Kotlin features are not available in Native context
- **C Interop**: Uses kotlinx.cinterop for C ABI compatibility
- **Performance**: Optimized for native execution without JVM overhead
- **Debugging**: Use native debugging tools for troubleshooting