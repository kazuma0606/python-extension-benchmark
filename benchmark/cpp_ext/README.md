# C++ Extension Implementation

This directory contains the C++ implementation of the benchmark functions using pybind11.

## Files

- `numeric.cpp` - Numeric computation functions (find_primes, matrix_multiply)
- `memory.cpp` - Memory operation functions (sort_array, filter_array)
- `parallel.cpp` - Parallel processing functions (parallel_compute)
- `setup.py` - Python setup script for building the extensions
- `CMakeLists.txt` - CMake configuration (alternative build method)

## Building

### Method 1: Using setup.py (Recommended)

```bash
cd benchmark/cpp_ext
python setup.py build_ext --inplace
```

### Method 2: Using the build script

From the project root:

```bash
python build_cpp_ext.py
```

### Method 3: Using CMake (Advanced)

```bash
cd benchmark/cpp_ext
mkdir build
cd build
cmake ..
make
```

## Requirements

- Python 3.6+
- pybind11 >= 2.10.0
- C++17 compatible compiler
- CMake 3.12+ (for CMake build method)

## Usage

After building, the extensions can be imported:

```python
from benchmark.cpp_ext import numeric, memory, parallel

# Numeric functions
primes = numeric.find_primes(100)
result = numeric.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])

# Memory functions
sorted_arr = memory.sort_array([3, 1, 4, 1, 5])
filtered = memory.filter_array([1, 2, 3, 4, 5], 3)

# Parallel functions
sum_result = parallel.parallel_compute([1.0, 2.0, 3.0, 4.0], 2)
```

## Implementation Details

- **find_primes**: Uses Sieve of Eratosthenes algorithm with std::vector<bool>
- **matrix_multiply**: Standard O(n³) matrix multiplication with bounds checking
- **sort_array**: Uses std::sort (typically introsort - hybrid algorithm)
- **filter_array**: Linear scan with std::vector reserve optimization
- **parallel_compute**: Uses std::async with std::launch::async for true parallelism

## Performance Notes

- All functions use modern C++ features (C++17)
- Memory operations use RAII and smart memory management
- Parallel computation uses std::future for thread management
- Optimized compilation flags are enabled (-O2 on Windows, -O3 on Unix)