# Go Extension for Python Benchmark System

This directory contains the Go implementation of benchmark functions using cgo and shared libraries.

## Overview

The Go extension provides high-performance implementations of:
- **find_primes**: Prime number generation using Sieve of Eratosthenes
- **matrix_multiply**: Parallel matrix multiplication using goroutines
- **sort_array**: Array sorting using Go's standard library
- **filter_array**: Array filtering with slice operations
- **parallel_compute**: Parallel sum computation using goroutines and channels

## Architecture

### Integration Method
- **Technology**: cgo + shared library
- **Interface**: C ABI compatible functions
- **Python Integration**: ctypes for calling shared library functions

### Performance Features
- **Concurrency**: Utilizes goroutines for parallel processing
- **Memory Management**: Efficient slice operations and memory reuse
- **Standard Library**: Leverages Go's optimized standard library functions
- **CPU Utilization**: Automatically scales to available CPU cores

## Building

### Prerequisites
- Go 1.21 or later
- C compiler (gcc/clang)
- Make (optional, for using Makefile)

### Build Commands

Using Makefile (recommended):
```bash
make all          # Build shared library
make test         # Test compilation
make clean        # Clean build artifacts
make rebuild      # Clean and rebuild
```

Manual build:
```bash
go build -buildmode=c-shared -o libgofunctions.so functions.go
```

### Build Outputs
- `libgofunctions.so` (Linux)
- `libgofunctions.dylib` (macOS)  
- `libgofunctions.dll` (Windows)
- `libgofunctions.h` (C header file)

## Usage

The Go extension is automatically loaded by the Python benchmark system:

```python
from benchmark.go_ext import find_primes, matrix_multiply, sort_array, filter_array, parallel_compute

# Find primes up to 1000
primes = find_primes(1000)

# Multiply two matrices
result = matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])

# Sort an array
sorted_arr = sort_array([3, 1, 4, 1, 5, 9])

# Filter array (keep elements >= threshold)
filtered = filter_array([1, 5, 3, 8, 2], 4)  # Returns [5, 8]

# Parallel computation with 4 goroutines
total = parallel_compute([1.0, 2.0, 3.0, 4.0], 4)
```

## Performance Characteristics

### Expected Performance Profile
- **Numerical Computation**: Good performance with parallel algorithms
- **Matrix Operations**: Excellent scalability with goroutines
- **Memory Operations**: Efficient slice operations
- **Parallel Processing**: Outstanding concurrent performance

### Optimization Features
- Automatic CPU core detection and utilization
- Work-stealing scheduler for load balancing
- Efficient memory allocation patterns
- Zero-copy operations where possible

## Error Handling

The Go extension includes robust error handling:
- Input validation for matrix dimensions
- Memory allocation checks
- Graceful degradation on resource constraints
- Detailed error reporting through Python interface

## Troubleshooting

### Common Issues

1. **Library not found**
   - Ensure the shared library is built: `make all`
   - Check file permissions and path

2. **Build failures**
   - Verify Go installation: `go version`
   - Check C compiler availability: `gcc --version`
   - Update Go modules: `go mod tidy`

3. **Runtime errors**
   - Check input data types and ranges
   - Verify matrix dimensions for multiplication
   - Ensure sufficient memory for large datasets

### Debug Mode
Set environment variable for verbose output:
```bash
export CGO_ENABLED=1
export GODEBUG=cgocheck=1
```

## Technical Details

### Memory Management
- Uses unsafe.Pointer for C interoperability
- Efficient slice operations without copying
- Automatic garbage collection for Go objects
- Manual memory management for C interface

### Concurrency Model
- Goroutines for lightweight threading
- Channels for communication between goroutines
- Work distribution based on available CPU cores
- Synchronization using sync.WaitGroup

### C Interface
All exported functions follow C calling conventions:
- `find_primes(n int, result *int, count *int)`
- `matrix_multiply(a *double, rows_a, cols_a int, b *double, rows_b, cols_b int, result *double)`
- `sort_array(arr *int, length int)`
- `filter_array(arr *int, length int, threshold int, result *int, count *int)`
- `parallel_compute(data *double, length int, num_threads int) double`