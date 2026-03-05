# Nim Extension for Python Benchmark

This directory contains the Nim implementation of benchmark functions.

## Overview

The Nim extension provides high-performance implementations of:
- `find_primes`: Prime number generation using Sieve of Eratosthenes
- `matrix_multiply`: Optimized matrix multiplication
- `sort_array`: Fast array sorting using Nim's built-in algorithms
- `filter_array`: Efficient array filtering
- `parallel_compute`: Parallel computation using thread pools

## Dependencies

- Nim 2.0+
- nimpy package
- Python 3.8+

## Building

The extension is built automatically by the `build_nim_ext.py` script:

```bash
python build_nim_ext.py
```

## Performance Characteristics

- **Numerical computation**: High performance with efficient algorithms
- **Memory operations**: Excellent performance with memory safety
- **Parallel processing**: Good scalability with thread pools
- **Integration**: Seamless Python integration via nimpy

## Technical Details

- Uses Nim's ARC garbage collector for optimal performance
- Compiled with speed optimizations (`--opt:speed`)
- Thread-safe implementations for parallel operations
- Efficient memory layout for cache-friendly operations

## Troubleshooting

1. **Import Error**: Ensure nimpy is installed (`nimble install nimpy`)
2. **Compilation Error**: Check Nim installation and version
3. **Runtime Error**: Verify shared library was created successfully

## Files

- `functions.nim`: Main Nim implementation
- `__init__.py`: Python integration layer
- `nim.cfg`: Nim compiler configuration
- `README.md`: This documentation
