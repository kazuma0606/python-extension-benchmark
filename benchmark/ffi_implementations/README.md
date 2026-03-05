# FFI Implementations

This directory contains Foreign Function Interface (FFI) implementations for various programming languages, allowing performance comparison between Pure Python and FFI approaches.

## Directory Structure

```
ffi_implementations/
├── c_ffi/              # C FFI implementation
├── cpp_ffi/            # C++ FFI implementation  
├── numpy_ffi/          # NumPy FFI implementation
├── cython_ffi/         # Cython FFI implementation
├── rust_ffi/           # Rust FFI implementation
├── fortran_ffi/        # Fortran FFI implementation
├── julia_ffi/          # Julia FFI implementation
├── go_ffi/             # Go FFI implementation
├── zig_ffi/            # Zig FFI implementation
├── nim_ffi/            # Nim FFI implementation
├── kotlin_ffi/         # Kotlin FFI implementation
├── build_template.sh   # Unix build script template
├── build_template.bat  # Windows build script template
└── README.md           # This file
```

## Prerequisites

### uv Environment

**IMPORTANT**: All FFI implementations must be built and run within a uv virtual environment.

```bash
# Activate uv environment
uv sync
source .venv/bin/activate  # On Unix
# or
.venv\Scripts\activate     # On Windows
```

### Language Dependencies

Each FFI implementation requires its respective language toolchain:

- **C**: gcc or clang
- **C++**: g++ or clang++
- **NumPy**: Cython compiler
- **Cython**: Cython compiler
- **Rust**: Cargo (Rust toolchain)
- **Fortran**: gfortran
- **Julia**: Julia with PackageCompiler.jl
- **Go**: Go toolchain with cgo
- **Zig**: Zig compiler
- **Nim**: Nim compiler
- **Kotlin**: Kotlin/Native

## Common Interface

All FFI implementations provide the same function signatures:

```c
// C ABI compatible functions
int* find_primes_ffi(int n, int* count);
double* matrix_multiply_ffi(double* a, int rows_a, int cols_a, 
                           double* b, int rows_b, int cols_b,
                           int* result_rows, int* result_cols);
int* sort_array_ffi(int* arr, int size);
int* filter_array_ffi(int* arr, int size, int threshold, int* result_size);
double parallel_compute_ffi(double* data, int size, int num_threads);
void free_memory_ffi(void* ptr);
```

## Building FFI Implementations

Each language directory contains:
- Source code files
- Language-specific build script (based on templates)
- Python wrapper using ctypes
- README with specific instructions

### General Build Process

1. Navigate to the language directory
2. Ensure uv environment is active
3. Run the build script
4. Verify shared library creation

```bash
cd benchmark/ffi_implementations/c_ffi
./build.sh  # or build.bat on Windows
```

## Usage

```python
from benchmark.ffi_implementations import c_ffi

# Create FFI instance
ffi_impl = c_ffi.CFFI()

# Use same interface as Pure Python
primes = ffi_impl.find_primes(1000)
result = ffi_impl.matrix_multiply(matrix_a, matrix_b)
```

## Performance Comparison

FFI implementations are designed to be compared against Pure Python:

- **Pure Python**: Baseline implementation
- **FFI**: Language-specific optimized implementation via ctypes

Expected performance improvements:
- C/C++: 10-50x faster
- Rust: 10-40x faster  
- Fortran: 10-50x faster (scientific computing)
- Julia: 5-30x faster (JIT optimized)
- Others: 2-25x faster (varies by language)

## Error Handling

FFI implementations include robust error handling:
- Library loading failures are gracefully handled
- Missing implementations are skipped
- Memory management is automated
- Detailed error reporting for debugging

## Contributing

When adding new FFI implementations:

1. Follow the common C ABI interface
2. Use the build script templates
3. Implement proper memory management
4. Add comprehensive error handling
5. Include language-specific documentation
6. Test with the unified benchmark system