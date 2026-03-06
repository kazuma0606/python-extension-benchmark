# Rust FFI Implementation

This directory contains the Rust FFI implementation for the benchmark system.

## Overview

The Rust FFI implementation provides high-performance Rust code compiled to a shared library that can be accessed via Python's ctypes FFI interface. This approach leverages Rust's memory safety and performance characteristics.

## Files

- `src/lib.rs` - Rust implementation of benchmark functions
- `Cargo.toml` - Rust project configuration and dependencies
- `ffi_wrapper.py` - Python ctypes wrapper for the shared library
- `__init__.py` - Module initialization

## Building

The shared library is built automatically when the RustFFI class is first instantiated. You can also build it manually:

```bash
cd benchmark/ffi_implementations/rust_ffi
cargo build --release
```

## Requirements

- Rust toolchain (rustc, cargo)
- A C linker (usually available with system compiler)

## Implementation Details

### Rust Optimizations

The Rust implementation uses several optimization techniques:

1. **Release Profile**: Compiled with maximum optimizations (`opt-level = 3`)
2. **LTO**: Link-time optimization enabled for better performance
3. **Memory Safety**: Rust's ownership system prevents memory errors
4. **Zero-Cost Abstractions**: High-level code compiles to efficient machine code

### FFI Interface

All functions follow the standard C ABI interface using `extern "C"`:

- `find_primes_ffi(int n, int* count) -> int*`
- `matrix_multiply_ffi(double* a, int rows_a, int cols_a, double* b, int rows_b, int cols_b, int* result_rows, int* result_cols) -> double*`
- `sort_array_ffi(int* arr, int size) -> int*`
- `filter_array_ffi(int* arr, int size, int threshold, int* result_size) -> int*`
- `parallel_compute_ffi(double* data, int size, int num_threads) -> double`
- `free_memory_ffi(void* ptr) -> void`

### Safety Considerations

The Rust implementation uses `unsafe` blocks for FFI interop but maintains safety through:

1. **Null Pointer Checks**: All pointers are validated before use
2. **Bounds Checking**: Array access is bounds-checked using slices
3. **Memory Management**: Proper allocation and deallocation patterns
4. **Error Handling**: Graceful handling of invalid inputs

### Performance Characteristics

Rust FFI typically provides:
- 10-40x speedup over Pure Python
- Memory safety without garbage collection overhead
- Excellent optimization by LLVM backend
- Efficient handling of numerical computations

## Usage

```python
from benchmark.ffi_implementations.rust_ffi import RustFFI

# Create FFI instance
rust_ffi = RustFFI()

# Use the functions
primes = rust_ffi.find_primes(100)
result = rust_ffi.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
```

## Troubleshooting

### Build Issues

1. **Missing Rust**: Install from https://rustup.rs/
2. **Linker Issues**: Ensure you have a C linker installed
3. **Permission Issues**: Make sure you have write permissions in the directory
4. **Target Issues**: The build system will automatically detect your platform

### Runtime Issues

1. **Library Not Found**: The build process may have failed
2. **Symbol Errors**: Check that all functions are properly exported with `#[no_mangle]`
3. **Memory Errors**: Rust's safety should prevent most memory issues
4. **Performance**: Ensure you're using the release build for benchmarking

### Platform-Specific Notes

- **Windows**: Requires MSVC or MinGW toolchain
- **macOS**: Requires Xcode command line tools
- **Linux**: Requires gcc or clang