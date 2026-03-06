# Go FFI Implementation

This directory contains the Go FFI (Foreign Function Interface) implementation for the benchmark system. It provides high-performance Go functions accessible from Python via ctypes.

## Overview

The Go FFI implementation leverages Go's excellent concurrency model with goroutines to provide parallel processing capabilities. It uses cgo to create C-compatible shared libraries that can be called from Python.

## Features

- **Goroutine-based Parallelism**: Utilizes Go's lightweight goroutines for efficient parallel processing
- **Memory Management**: Proper memory allocation and cleanup using C.malloc/C.free
- **C ABI Compatibility**: All functions follow the standard C ABI for FFI integration
- **Cross-platform**: Builds on Linux, macOS, and Windows

## Files

- `functions.go` - Go implementation of benchmark functions with cgo exports
- `go.mod` - Go module definition
- `Makefile` - Build automation for shared library generation
- `ffi_wrapper.py` - Python ctypes wrapper for Go functions
- `__init__.py` - Module initialization

## Building

### Prerequisites

- Go 1.21 or later
- GCC (for cgo compilation)
- Make (optional, for using Makefile)

### Build Commands

```bash
# Build shared library (auto-detects platform)
make

# Or build manually
go build -buildmode=c-shared -o libfunctions.so functions.go  # Linux
go build -buildmode=c-shared -o libfunctions.dll functions.go # Windows
go build -buildmode=c-shared -o libfunctions.dylib functions.go # macOS

# Clean build artifacts
make clean

# Test compilation
make test
```

### Cross-compilation

```bash
# Build for specific platforms
make linux    # Build for Linux
make windows  # Build for Windows
make darwin   # Build for macOS
```

## Functions

All functions follow the FFI C ABI specification:

### find_primes_ffi
```c
int* find_primes_ffi(int n, int* count);
```
Finds all prime numbers up to n using the Sieve of Eratosthenes algorithm.

### matrix_multiply_ffi
```c
double* matrix_multiply_ffi(double* a, int rows_a, int cols_a, 
                           double* b, int rows_b, int cols_b,
                           int* result_rows, int* result_cols);
```
Multiplies two matrices using parallel goroutines for improved performance.

### sort_array_ffi
```c
int* sort_array_ffi(int* arr, int size);
```
Sorts an integer array using Go's optimized sort algorithm.

### filter_array_ffi
```c
int* filter_array_ffi(int* arr, int size, int threshold, int* result_size);
```
Filters array elements that are >= threshold.

### parallel_compute_ffi
```c
double parallel_compute_ffi(double* data, int size, int num_threads);
```
Performs parallel computation (sum) using the specified number of goroutines.

### free_memory_ffi
```c
void free_memory_ffi(void* ptr);
```
Frees memory allocated by Go FFI functions.

## Performance Characteristics

- **Concurrency**: Excellent parallel processing with goroutines
- **Memory**: Efficient memory management with garbage collector
- **Startup**: Fast compilation and execution
- **Scalability**: Good performance scaling with multiple cores

## Usage from Python

```python
from benchmark.ffi_implementations.go_ffi import GoFFI

# Create FFI instance
go_ffi = GoFFI()

# Check if available
if go_ffi.is_available():
    # Use FFI functions
    primes = go_ffi.find_primes(100)
    result = go_ffi.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    sorted_arr = go_ffi.sort_array([3, 1, 4, 1, 5])
    filtered = go_ffi.filter_array([1, 2, 3, 4, 5], 3)
    sum_result = go_ffi.parallel_compute([1.0, 2.0, 3.0, 4.0], 2)
```

## Troubleshooting

### Common Issues

1. **Go not installed**: Install Go 1.21+ from https://golang.org/
2. **CGO disabled**: Ensure CGO is enabled (`CGO_ENABLED=1`)
3. **GCC not found**: Install GCC compiler for your platform
4. **Library not found**: Run `make` to build the shared library

### Build Errors

- **"cgo: C compiler not found"**: Install GCC or appropriate C compiler
- **"cannot find package"**: Run `go mod tidy` to update dependencies
- **Permission denied**: Ensure write permissions in the directory

### Runtime Errors

- **Library load failed**: Check if shared library exists and has correct permissions
- **Function not found**: Verify the shared library was built correctly
- **Memory errors**: Ensure proper cleanup using free_memory_ffi

## Integration with Benchmark System

The Go FFI implementation integrates seamlessly with the benchmark system:

1. **Automatic Detection**: The system automatically detects if the Go shared library is available
2. **Error Handling**: Graceful fallback if Go FFI is not available
3. **Performance Comparison**: Direct comparison with Pure Python implementations
4. **Memory Safety**: Automatic memory management through the FFI base class

## Expected Performance

Go FFI typically provides:
- **3-15x speedup** over Pure Python for most operations
- **Excellent parallel performance** due to goroutines
- **Good memory efficiency** with Go's garbage collector
- **Fast startup time** compared to JIT-compiled languages

The actual performance depends on:
- Problem size and complexity
- Number of available CPU cores
- Memory bandwidth
- Go compiler optimizations