# Rust Extension Implementation

This directory contains the Rust implementation of the benchmark functions using PyO3.

## Functions Implemented

- `find_primes(n)` - Find all prime numbers up to n using Sieve of Eratosthenes
- `matrix_multiply(a, b)` - Multiply two matrices
- `sort_array(arr)` - Sort an array of integers
- `filter_array(arr, threshold)` - Filter array elements >= threshold
- `parallel_compute(data, num_threads)` - Perform parallel computation using rayon

## Building

To build the Rust extension:

```bash
# From the project root
python build_rust_ext.py

# Or manually from this directory
python -m maturin develop --release
```

## Dependencies

- Rust (with cargo)
- PyO3 0.20
- rayon 1.8 (for parallel processing)
- maturin (for building)

## Usage

```python
import benchmark.rust_ext as rust

# Find primes up to 100
primes = rust.find_primes(100)

# Matrix multiplication
result = rust.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])

# Sort array
sorted_arr = rust.sort_array([3, 1, 4, 1, 5])

# Filter array
filtered = rust.filter_array([1, 2, 3, 4, 5], 3)

# Parallel computation
sum_result = rust.parallel_compute([1.0, 2.0, 3.0, 4.0], 2)
```

## Performance

The Rust implementation leverages:
- Native Rust performance for computational tasks
- Rayon for efficient parallel processing
- Zero-copy data transfer where possible with PyO3
- Optimized algorithms (e.g., unstable sort for better performance)