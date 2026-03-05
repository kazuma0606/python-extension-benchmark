# Zig Extension for Python Benchmark

This directory contains the Zig implementation of benchmark functions for the Python extension performance comparison project.

## Overview

The Zig extension provides high-performance implementations of computational functions using Zig's memory-safe systems programming capabilities. Zig offers C-like performance with compile-time safety guarantees and zero-cost abstractions.

## Features

- **Memory Safety**: Zig's compile-time safety checks prevent buffer overflows and memory leaks
- **High Performance**: Compiled to native code with aggressive optimizations
- **C ABI Compatibility**: Seamless integration with Python via ctypes
- **Thread Safety**: Safe parallel computation using Zig's threading primitives

## Functions Implemented

### Numerical Computation
- `find_primes(n)`: Sieve of Eratosthenes with memory-safe implementation
- `matrix_multiply(a, b)`: Cache-friendly matrix multiplication

### Memory Operations  
- `sort_array(arr)`: Introsort algorithm (hybrid quicksort/heapsort/insertion sort)
- `filter_array(arr, threshold)`: Memory-safe element filtering

### Parallel Processing
- `parallel_compute(data, num_threads)`: Multi-threaded sum computation with work stealing

## Building

### Prerequisites

1. **Zig Compiler**: Install Zig 0.11+ from [ziglang.org](https://ziglang.org/download/)
2. **Python Development Headers**: Usually included with Python installation

### Build Process

```bash
# From the project root directory
python build_zig_ext.py
```

The build script will:
1. Check for Zig installation
2. Compile the Zig source to a shared library
3. Copy the library to the appropriate location
4. Run basic functionality tests

### Manual Build

If you prefer to build manually:

```bash
cd benchmark/zig_ext
zig build -Doptimize=ReleaseFast
cp zig-out/lib/libzigfunctions.* ./
```

## Architecture

### Memory Management
- Uses Zig's GeneralPurposeAllocator for safe memory allocation
- Automatic cleanup with defer statements
- Bounds checking on all array operations

### Threading Model
- Spawns worker threads for parallel computation
- Graceful fallback to single-threaded execution on errors
- Work distribution with load balancing

### Error Handling
- Compile-time error prevention where possible
- Runtime error handling with graceful degradation
- Detailed error reporting through Python exceptions

## Performance Characteristics

### Expected Performance Profile
- **Numerical Computation**: Excellent (C-like performance)
- **Memory Operations**: Excellent (optimized algorithms + safety)
- **Parallel Processing**: Very Good (efficient threading)
- **Memory Usage**: Low (manual memory management)

### Optimization Features
- Release mode compilation with aggressive optimizations
- Cache-friendly memory access patterns
- Minimal runtime overhead
- Zero-cost abstractions

## Integration with Python

The Zig extension integrates with Python through:

1. **C ABI**: Functions exported with C calling convention
2. **ctypes**: Python's foreign function interface
3. **Type Safety**: Careful type conversion between Python and Zig
4. **Error Propagation**: Zig errors converted to Python exceptions

## Troubleshooting

### Common Issues

1. **Zig Not Found**
   ```
   Error: Zig is not installed or not in PATH
   ```
   Solution: Install Zig and ensure it's in your PATH

2. **Library Not Found**
   ```
   Zig shared library not found
   ```
   Solution: Run the build script or check library permissions

3. **Compilation Errors**
   - Check Zig version compatibility (0.11+ required)
   - Ensure all source files are present
   - Check for syntax errors in functions.zig

### Debug Build

For debugging, build with debug information:

```bash
cd benchmark/zig_ext
zig build -Doptimize=Debug
```

## Testing

The extension includes comprehensive tests:

- **Unit Tests**: Individual function validation
- **Integration Tests**: Python-Zig interface testing  
- **Performance Tests**: Benchmark validation
- **Memory Tests**: Leak detection and bounds checking

Run tests with:
```bash
python -m pytest tests/test_zig_extension.py -v
```

## Contributing

When modifying the Zig extension:

1. Maintain C ABI compatibility
2. Follow Zig naming conventions
3. Add appropriate error handling
4. Update tests for new functionality
5. Document performance implications

## License

This Zig extension is part of the Python Extension Benchmark project and follows the same licensing terms.