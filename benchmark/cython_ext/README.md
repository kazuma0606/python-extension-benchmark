# Cython Implementation

This directory contains the Cython implementation of the benchmark functions.

## Files

- `numeric.pyx` - Cython implementation of numeric computation functions (find_primes, matrix_multiply)
- `memory.pyx` - Cython implementation of memory operation functions (sort_array, filter_array)
- `parallel.pyx` - Cython implementation of parallel computation functions (parallel_compute)
- `setup.py` - Build configuration for Cython extensions
- `__init__.py` - Module initialization and function exports

## Building the Extensions

### Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install cython setuptools numpy
```

### Build Commands

From the project root directory, run:

```bash
# Option 1: Use the build script
python build_cython.py

# Option 2: Build directly
python benchmark/cython_ext/setup.py build_ext --inplace
```

### Build Requirements

- **Cython**: For compiling .pyx files to C
- **setuptools**: For building extensions
- **numpy**: For array operations and includes
- **C compiler**: 
  - Windows: Microsoft Visual C++ or MinGW
  - Linux/macOS: GCC or Clang
- **OpenMP**: For parallel processing support (optional but recommended)

## Implementation Details

### Optimizations

The Cython implementations include several performance optimizations:

1. **Type annotations**: All variables use Cython's static typing
2. **Bounds checking disabled**: `@cython.boundscheck(False)`
3. **Wraparound disabled**: `@cython.wraparound(False)`
4. **C-level loops**: Direct C loops for better performance
5. **Memory management**: Manual memory allocation for arrays
6. **OpenMP parallelization**: Using `prange` for parallel loops

### Function Signatures

All functions maintain the same signatures as the Python reference implementation:

- `find_primes(n: int) -> List[int]`
- `matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]`
- `sort_array(arr: List[int]) -> List[int]`
- `filter_array(arr: List[int], threshold: int) -> List[int]`
- `parallel_compute(data: List[float], num_threads: int) -> float`

## Troubleshooting

### Build Errors

1. **Missing compiler**: Install a C compiler for your platform
2. **OpenMP not found**: Install OpenMP or remove OpenMP flags from setup.py
3. **Cython not found**: Install Cython with `pip install cython`
4. **NumPy headers not found**: Make sure NumPy is installed

### Runtime Errors

1. **ImportError**: Extensions not built - run the build command
2. **NotImplementedError**: Fallback functions active - build the extensions

### Performance Notes

- The Cython implementations should be significantly faster than Pure Python
- Parallel processing performance depends on OpenMP availability
- Memory operations benefit most from C-level optimizations