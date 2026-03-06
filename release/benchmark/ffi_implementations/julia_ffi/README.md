# Julia FFI Implementation

This directory contains the Julia FFI implementation for the benchmark system, providing high-performance numerical computing functions accessible via Python's ctypes FFI.

## Overview

The Julia FFI implementation leverages Julia's strengths in numerical computing and JIT compilation while maintaining C ABI compatibility through `@ccallable` functions. This approach allows Python to call optimized Julia functions directly via shared libraries.

## Features

- **@ccallable Functions**: C ABI compatibility for seamless FFI integration
- **BLAS Integration**: Leverages optimized linear algebra libraries
- **JIT Compilation**: Julia's just-in-time compilation for optimal performance
- **Vectorized Operations**: Takes advantage of Julia's broadcasting and vectorization
- **Memory Management**: Automatic garbage collection with FFI considerations

## Requirements

- **Julia**: Julia 1.9+ (for @ccallable support in PackageCompiler)
- **PackageCompiler.jl**: For creating shared libraries
- **LinearAlgebra**: For optimized matrix operations (standard library)
- **uv environment**: Active uv virtual environment

### Installing Julia

#### Windows
```bash
# Download from https://julialang.org/downloads/
# Or use winget
winget install julia -s msstore
```

#### macOS (with Homebrew)
```bash
brew install julia
```

#### Ubuntu/Debian
```bash
# Download from https://julialang.org/downloads/
# Or use snap
sudo snap install julia --classic
```

## Building

### Automatic Build
```bash
julia build.jl
```

### Manual Build (Alternative)
```julia
# In Julia REPL
using Pkg
Pkg.add("PackageCompiler")
using PackageCompiler

# Create shared library
create_library("functions.jl", "libjuliafunctions"; 
               lib_name="juliafunctions")
```

### Development Mode
If PackageCompiler is not available, the system will fall back to a development mode that can still be used for testing and development.

## Functions

All functions follow the unified C ABI specification with Julia optimizations:

### find_primes_ffi
```julia
function find_primes_ffi(n::Cint, count_ptr::Ptr{Cint})::Ptr{Cint}
```
- **Purpose**: Find all prime numbers up to n using vectorized Sieve of Eratosthenes
- **Algorithm**: Vectorized sieve with Julia's broadcasting
- **Performance**: O(n log log n) with vectorized operations

### matrix_multiply_ffi
```julia
function matrix_multiply_ffi(a_ptr, rows_a, cols_a, b_ptr, rows_b, cols_b, 
                            result_rows_ptr, result_cols_ptr)::Ptr{Cdouble}
```
- **Purpose**: Matrix multiplication using BLAS
- **Algorithm**: Leverages Julia's optimized linear algebra (BLAS/LAPACK)
- **Performance**: O(n³) with highly optimized BLAS routines

### sort_array_ffi
```julia
function sort_array_ffi(arr_ptr::Ptr{Cint}, size::Cint)::Ptr{Cint}
```
- **Purpose**: Sort integer array using Julia's optimized sorting
- **Algorithm**: Timsort (Julia's default, highly optimized)
- **Performance**: O(n log n) with excellent real-world performance

### filter_array_ffi
```julia
function filter_array_ffi(arr_ptr, size, threshold, result_size_ptr)::Ptr{Cint}
```
- **Purpose**: Filter array elements using vectorized operations
- **Algorithm**: Broadcasting-based filtering
- **Performance**: O(n) with vectorized operations

### parallel_compute_ffi
```julia
function parallel_compute_ffi(data_ptr::Ptr{Cdouble}, size::Cint, num_threads::Cint)::Cdouble
```
- **Purpose**: Parallel sum computation
- **Algorithm**: Julia's optimized sum (may use SIMD and threading)
- **Performance**: O(n/p) with automatic optimization

## Usage

```python
from benchmark.ffi_implementations.julia_ffi import JuliaFFI

# Initialize Julia FFI
julia_ffi = JuliaFFI()

# Check availability
if julia_ffi.is_available():
    # Use Julia functions
    primes = julia_ffi.find_primes(100)
    result = julia_ffi.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
    sorted_arr = julia_ffi.sort_array([3, 1, 4, 1, 5])
    filtered = julia_ffi.filter_array([1, 2, 3, 4, 5], 3)
    sum_result = julia_ffi.parallel_compute([1.0, 2.0, 3.0, 4.0], 2)
```

## Performance Characteristics

### Expected Performance vs Pure Python
- **Prime Finding**: 30-100x faster (vectorized sieve + JIT)
- **Matrix Multiplication**: 50-200x faster (BLAS integration)
- **Array Sorting**: 20-60x faster (optimized Timsort)
- **Array Filtering**: 15-50x faster (vectorized broadcasting)
- **Parallel Computation**: 10-40x faster (optimized sum + SIMD)

### Julia Advantages
- **JIT Compilation**: Runtime optimization for specific data types and sizes
- **BLAS Integration**: Automatic use of optimized linear algebra libraries
- **Vectorization**: Automatic SIMD optimization for array operations
- **Type Specialization**: Compile-time optimization for specific type combinations
- **Memory Layout**: Efficient memory access patterns

## Memory Management

The Julia FFI implementation uses Julia's garbage collector:

1. **Allocation**: Functions allocate result arrays using Julia's memory management
2. **Tracking**: Pointers are returned for C compatibility
3. **Cleanup**: Memory is managed by Julia's garbage collector
4. **Limitation**: Direct deallocation from C pointers is not supported

**Note**: Julia's garbage collector handles memory management automatically, but this can complicate FFI memory management. The FFI base class provides automatic cleanup where possible.

## Troubleshooting

### Common Issues

1. **Julia not found**
   ```
   Error: julia command not found
   ```
   **Solution**: Install Julia and ensure it's in your PATH

2. **PackageCompiler not available**
   ```
   Error building Julia FFI library: PackageCompiler not found
   ```
   **Solution**: Install PackageCompiler.jl: `julia -e 'using Pkg; Pkg.add("PackageCompiler")'`

3. **Library not found**
   ```
   OSError: cannot load library 'libjuliafunctions.dll'
   ```
   **Solution**: Run `julia build.jl` to build the shared library

4. **@ccallable not supported**
   ```
   Error: @ccallable requires Julia 1.9+
   ```
   **Solution**: Upgrade to Julia 1.9 or later

### Development Mode
If the shared library cannot be built, the system falls back to development mode:

```julia
# Test Julia functions directly
julia> include("functions.jl")
julia> count_ref = Ref{Cint}(0)
julia> primes_ptr = find_primes_ffi(Cint(10), pointer_from_objref(count_ref))
```

### Verify Julia Installation
```bash
julia --version
julia -e 'using Pkg; Pkg.status()'
julia -e 'using LinearAlgebra; println("BLAS: ", BLAS.vendor())'
```

## Integration with Benchmark System

The Julia FFI implementation integrates seamlessly with the benchmark system:

1. **Automatic Detection**: The system automatically detects and loads the Julia library
2. **Error Handling**: Graceful fallback if Julia is not available
3. **Performance Comparison**: Direct comparison with Pure Python implementations
4. **Result Validation**: Automatic verification of numerical correctness

## Julia-Specific Benefits

Julia's advantages for numerical computing in FFI context:

- **Multiple Dispatch**: Compile-time optimization for different argument types
- **LLVM Backend**: Modern compiler optimizations and code generation
- **Interoperability**: Easy integration with C, Fortran, and Python libraries
- **Scientific Ecosystem**: Rich ecosystem of numerical and scientific packages
- **Performance**: Near-C performance with high-level syntax

## Limitations

1. **Startup Time**: Julia has a longer startup time due to JIT compilation
2. **Memory Management**: Limited control over garbage collection from FFI
3. **Library Size**: Shared libraries can be large due to Julia runtime inclusion
4. **Compilation Complexity**: PackageCompiler setup can be complex

## Future Improvements

1. **Static Compilation**: Use Julia's static compilation features for smaller libraries
2. **Precompilation**: Pre-compile functions for faster startup
3. **Memory Pools**: Implement custom memory management for FFI
4. **Error Handling**: Improve error propagation from Julia to Python

This implementation demonstrates how Julia's numerical computing strengths and JIT compilation can be leveraged in Python applications through FFI, providing significant performance improvements for scientific computations.