# Kotlin/Native Extension for Python Benchmark

This directory contains the Kotlin/Native implementation of benchmark functions for the Python extension benchmark system.

## Overview

The Kotlin/Native extension provides high-performance implementations of:
- **find_primes**: Prime number generation using Sieve of Eratosthenes
- **matrix_multiply**: Optimized matrix multiplication
- **sort_array**: Efficient array sorting using Kotlin's standard library
- **filter_array**: Functional-style array filtering
- **parallel_compute**: Concurrent computation using Kotlin coroutines

## Architecture

### Technology Stack
- **Kotlin/Native**: 1.9.21+
- **Gradle**: 8.5+ (build system)
- **C ABI**: For Python integration via ctypes
- **Coroutines**: For concurrent processing

### Integration Method
The Kotlin/Native code is compiled to a shared library (.so/.dll/.dylib) that exposes C-compatible functions. Python integration is achieved through:
1. Kotlin/Native compilation to native shared library
2. C ABI function exports with `@CName` annotations
3. Python ctypes interface for function calls

## Files

- `functions.kt` - Kotlin/Native implementation of benchmark functions
- `build.gradle.kts` - Gradle build configuration
- `settings.gradle.kts` - Gradle project settings
- `gradle.properties` - Build optimization settings
- `__init__.py` - Python integration layer
- `README.md` - This documentation

## Building

### Prerequisites
1. **Kotlin/Native**: Install via SDKMAN or download from JetBrains
2. **Gradle**: 8.5+ (wrapper will be created automatically)
3. **C compiler**: GCC/Clang (for native compilation)

### Build Commands

```bash
# Using the build script (recommended)
python scripts/build/build_kotlin_ext.py

# Or manually with Gradle
cd benchmark/kotlin_ext
./gradlew build

# Clean build
./gradlew clean build
```

### Build Output
The build process creates:
- `libkotlinfunctions.so` (Linux)
- `libkotlinfunctions.dylib` (macOS)
- `kotlinfunctions.dll` (Windows)

## Performance Characteristics

### Expected Performance
- **Numerical computation**: Good performance with JIT optimizations
- **Matrix operations**: Efficient with cache-friendly algorithms
- **Memory operations**: Standard library optimizations
- **Parallel processing**: Coroutine-based concurrency

### Optimization Features
- Kotlin/Native compiler optimizations (`-opt` flag)
- Fast memory allocator (mimalloc)
- Cache-friendly matrix multiplication
- Efficient sieve algorithms
- Functional programming optimizations

## Usage

```python
import benchmark.kotlin_ext as kotlin_ext

# Check availability
if kotlin_ext.is_available():
    # Use Kotlin implementations
    primes = kotlin_ext.find_primes(100)
    result = kotlin_ext.matrix_multiply(a, b)
    sorted_arr = kotlin_ext.sort_array([3, 1, 4, 1, 5])
    filtered = kotlin_ext.filter_array([1, 2, 3, 4, 5], 3)
    sum_result = kotlin_ext.parallel_compute([1.0, 2.0, 3.0], 2)
else:
    print("Kotlin/Native extension not available")
```

## Error Handling

The extension includes comprehensive error handling:
- **Library loading**: Graceful fallback to Python implementations
- **Function calls**: Exception catching with fallback
- **Memory management**: Automatic cleanup via Kotlin/Native GC
- **Build errors**: Detailed error reporting

## Troubleshooting

### Common Issues

1. **Library not found**
   ```
   Warning: Kotlin/Native shared library not found
   ```
   - Solution: Run the build script or check Kotlin/Native installation

2. **Build failures**
   ```
   Build failed: Could not resolve dependencies
   ```
   - Solution: Check internet connection and Gradle cache

3. **Function not found**
   ```
   Function 'find_primes' not found - check export names
   ```
   - Solution: Verify `@CName` annotations in Kotlin code

### Debug Steps

1. **Check Kotlin installation**:
   ```bash
   kotlin -version
   ```

2. **Verify Gradle**:
   ```bash
   cd benchmark/kotlin_ext
   ./gradlew --version
   ```

3. **Manual build with verbose output**:
   ```bash
   ./gradlew build --info --stacktrace
   ```

4. **Check library symbols** (Linux/macOS):
   ```bash
   nm -D libkotlinfunctions.so | grep find_primes
   ```

## Development

### Adding New Functions

1. **Implement in Kotlin**:
   ```kotlin
   @CName("new_function")
   fun newFunction(param: Int): Int {
       // Implementation
   }
   ```

2. **Add Python binding**:
   ```python
   def new_function(param: int) -> int:
       # ctypes setup and call
   ```

3. **Update build configuration** if needed

### Performance Tuning

- Use `@OptIn(ExperimentalUnsignedTypes::class)` for unsigned arithmetic
- Leverage `inline` functions for small operations
- Consider `@ThreadLocal` for thread-safe globals
- Profile with Kotlin/Native profiler tools

## Integration with Benchmark System

The Kotlin extension integrates seamlessly with the benchmark system:
- Automatic discovery by the benchmark runner
- Consistent interface with other language extensions
- Error isolation (failures don't affect other extensions)
- Performance metrics collection

## Limitations

1. **Coroutines**: Limited in C ABI context, using sequential simulation
2. **Memory model**: Experimental features may have stability issues
3. **Build time**: Kotlin/Native compilation can be slow
4. **Platform support**: Limited to supported Kotlin/Native targets

## Future Improvements

- Native coroutine integration when C ABI supports it
- SIMD optimizations for numerical computations
- Memory pool optimizations
- Advanced parallel algorithms
- Integration with Kotlin Multiplatform libraries