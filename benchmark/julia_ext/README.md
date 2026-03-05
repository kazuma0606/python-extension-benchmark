# Julia Extension for Python Benchmark

This module provides Julia implementations of benchmark functions, leveraging Julia's high-performance numerical computing capabilities.

## Features

- **High-performance numerical computing**: Uses Julia's optimized mathematical operations
- **Vectorized operations**: Leverages Julia's broadcasting and vectorization
- **Multithreading support**: Utilizes Julia's `@threads` macro for parallel computation
- **BLAS integration**: Matrix operations use optimized BLAS routines
- **Memory efficient**: Julia's efficient memory management

## Requirements

- Julia 1.6+ 
- PyJulia (`pip install julia`)
- Julia packages: PyCall, LinearAlgebra

## Installation

1. Install Julia from https://julialang.org/
2. Install PyJulia: `pip install julia`
3. Run the build script: `python build_julia_ext.py`

## Functions

### `find_primes(n: int) -> List[int]`
Finds all prime numbers up to n using the Sieve of Eratosthenes with vectorized operations.

### `matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]`
Multiplies two matrices using Julia's optimized linear algebra (BLAS).

### `sort_array(arr: List[int]) -> List[int]`
Sorts an array using Julia's efficient sorting algorithms.

### `filter_array(arr: List[int], threshold: int) -> List[int]`
Filters array elements above threshold using vectorized operations.

### `parallel_compute(data: List[float], num_threads: int) -> float`
Computes sum of data using Julia's multithreading capabilities.

## Performance Characteristics

- **Numerical computation**: Excellent (comparable to Fortran/C)
- **Matrix operations**: Excellent (BLAS-optimized)
- **Memory operations**: Good (efficient algorithms)
- **Parallel processing**: Good (thread-based parallelism)

## Usage Example

```python
from benchmark.julia_ext import find_primes, matrix_multiply

# Find primes up to 1000
primes = find_primes(1000)

# Multiply two matrices
a = [[1, 2], [3, 4]]
b = [[5, 6], [7, 8]]
result = matrix_multiply(a, b)
```

## Error Handling

The module includes comprehensive error handling:
- Graceful fallback when Julia is not available
- Detailed error messages for debugging
- Runtime availability checking with `is_available()`

## Integration with Benchmark System

This extension integrates seamlessly with the existing benchmark system:
- Follows the same interface as other extensions
- Supports the same benchmark scenarios
- Provides consistent error handling and reporting