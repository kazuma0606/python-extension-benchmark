# Python Extension Benchmark Framework

A comprehensive benchmarking framework for comparing performance across multiple Python extension implementations (Pure Python, NumPy, C, C++, Cython, Rust) using identical algorithms and statistical analysis.

## 🎯 Project Overview

This project provides quantitative performance comparisons between different Python extension technologies by implementing identical computational tasks in multiple languages and measuring their execution time, memory usage, and parallel processing capabilities.

### Key Features

- **Multi-language implementations**: Pure Python, NumPy, C, C++, Cython, Rust
- **Comprehensive scenarios**: Numeric computation, memory operations, parallel processing
- **Statistical rigor**: 100 measurement runs with warmup cycles and statistical analysis
- **Output validation**: Ensures all implementations produce identical results
- **Multiple output formats**: JSON, CSV, and visual graphs
- **Docker environment**: Reproducible benchmarking environment
- **Automated testing**: Property-based testing with Hypothesis

### Supported Languages & Technologies

| Language/Tool | Binding Method | Memory Safety | Learning Curve | Primary Use Case |
|---------------|----------------|---------------|----------------|------------------|
| Pure Python | Native | High (GC) | Low | Baseline reference |
| NumPy | Native | High | Low | Vectorized operations |
| C | Python C API | Low | High | Maximum performance |
| C++ | pybind11 | Low-Medium | High | Existing C++ codebases |
| Cython | Cython compiler | Medium | Medium | Gradual optimization |
| Rust | PyO3 | Highest | Medium-High | Safe high performance |

## 📁 Project Structure

```
benchmark/
├── python/              # Pure Python implementations (baseline)
│   ├── numeric.py       # Prime finding, matrix multiplication
│   ├── memory.py        # Array sorting, filtering
│   └── parallel.py      # Multi-threaded computation
├── numpy_impl/          # NumPy vectorized implementations
│   ├── numeric.py       # Vectorized operations
│   ├── memory.py        # NumPy array operations
│   └── parallel.py      # NumPy parallel processing
├── c_ext/               # C extension implementations
│   ├── setup.py         # Build configuration
│   ├── numeric.c        # C numeric algorithms
│   ├── memory.c         # C memory operations
│   └── parallel.c       # C parallel processing (pthreads)
├── cpp_ext/             # C++ (pybind11) implementations
│   ├── CMakeLists.txt   # CMake build configuration
│   ├── numeric.cpp      # C++ numeric algorithms
│   ├── memory.cpp       # C++ memory operations (std::sort)
│   └── parallel.cpp     # C++ parallel processing (std::thread)
├── cython_ext/          # Cython implementations
│   ├── setup.py         # Cython build configuration
│   ├── numeric.pyx      # Cython numeric algorithms
│   ├── memory.pyx       # Cython memory operations
│   └── parallel.pyx     # Cython parallel processing (prange)
├── rust_ext/            # Rust (PyO3) implementations
│   ├── Cargo.toml       # Rust build configuration
│   └── src/             # Rust source files
│       ├── lib.rs       # Main library
│       ├── numeric.rs   # Rust numeric algorithms
│       ├── memory.rs    # Rust memory operations
│       └── parallel.rs  # Rust parallel processing (rayon)
├── runner/              # Benchmark execution framework
│   ├── benchmark.py     # Main benchmark runner
│   ├── scenarios.py     # Scenario definitions
│   ├── statistics.py    # Statistical calculations
│   ├── output.py        # Result output (JSON/CSV)
│   ├── visualize.py     # Graph generation
│   ├── validator.py     # Output validation
│   └── error_handler.py # Error handling
├── results/             # Benchmark results
│   ├── json/            # JSON format results
│   ├── csv/             # CSV format results
│   └── graphs/          # Generated graphs (PNG)
├── tests/               # Test suite
│   ├── test_*.py        # Unit and integration tests
│   └── conftest.py      # Pytest configuration
├── docs/                # Documentation
└── docker/              # Docker environment
    ├── Dockerfile
    └── docker-compose.yml
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ 
- Docker and Docker Compose (recommended)
- C/C++ compiler (gcc/clang)
- Rust toolchain (for Rust extensions)
- CMake (for C++ extensions)

### Installation

#### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd python-extension-benchmark

# Build and run with Docker
docker-compose up benchmark

# Run tests
docker-compose up test
```

#### Option 2: Local Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Build all extensions
python build_c_ext.py
python build_cpp_ext.py
python build_cython.py
python build_rust_ext.py

# Run tests to verify installation
pytest tests/ -v
```

### Running Benchmarks

#### Full Benchmark Suite

```python
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import get_all_scenarios

# Initialize runner
runner = BenchmarkRunner()

# Run all scenarios with all available implementations
results = runner.run_all_scenarios()

# Results are automatically saved to benchmark/results/
print("Benchmark completed! Check benchmark/results/ for output files.")
```

#### Individual Scenarios

```python
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import NumericScenario, MemoryScenario, ParallelScenario

runner = BenchmarkRunner()

# Run specific scenario
numeric_results = runner.run_scenario(
    NumericScenario(),
    implementations=['python', 'numpy', 'c_ext', 'rust_ext']
)
```

#### Command Line Usage

```bash
# Run demo with error handling
python demo_error_handling.py

# Run specific tests
pytest tests/test_scenarios.py -v
pytest tests/test_end_to_end_integration.py -v
```

## 📊 Benchmark Scenarios

### 1. Numeric Computation Scenario
- **Prime Finding**: Sieve of Eratosthenes algorithm for finding all primes up to N
- **Matrix Multiplication**: Standard matrix multiplication algorithm
- **Focus**: Pure CPU computation speed differences

### 2. Memory Operations Scenario  
- **Array Sorting**: Sorting 10 million integers
- **Array Filtering**: Filtering arrays based on threshold values
- **Focus**: Memory management efficiency and allocation costs

### 3. Parallel Processing Scenario
- **Multi-threaded Computation**: Distributed calculation across multiple threads
- **Thread Scaling**: Tests with 1, 2, 4, 8, 16 threads
- **Focus**: GIL impact and parallel processing capabilities

## 📈 Understanding Benchmark Results

### Output Files

Results are saved in three formats:

1. **JSON** (`results/json/`): Complete structured data including all measurements
2. **CSV** (`results/csv/`): Tabular data suitable for spreadsheet analysis  
3. **Graphs** (`results/graphs/`): Visual comparisons in PNG format

### Key Metrics

#### Execution Time
- **Relative Score**: Pure Python = 1.0, lower is faster
- **Statistical Measures**: Min, median, mean, standard deviation
- **Example**: If C extension shows 0.1, it's 10x faster than Pure Python

#### Memory Usage
- **Peak Memory**: Maximum memory used during execution (MB)
- **Average Memory**: Mean memory usage throughout execution (MB)

#### Parallel Processing
- **Throughput**: Operations per second (ops/sec)
- **Scalability**: Speedup ratio compared to single-threaded execution
- **Efficiency**: How well the implementation utilizes additional threads

### Interpreting Results

#### Performance Expectations

**Typical Performance Rankings** (fastest to slowest):
1. **C/C++**: 10-100x faster than Python for CPU-intensive tasks
2. **Rust**: Similar to C/C++, with memory safety guarantees
3. **Cython**: 5-50x faster, depends on optimization level
4. **NumPy**: 5-20x faster for vectorizable operations
5. **Pure Python**: Baseline (1.0x)

#### When to Use Each Implementation

**Choose C/C++** when:
- Maximum performance is critical
- You have existing C/C++ code to integrate
- Memory usage must be minimized

**Choose Rust** when:
- You need C-level performance with memory safety
- Long-term maintainability is important
- You're comfortable with Rust's learning curve

**Choose Cython** when:
- You want to gradually optimize Python code
- You need a balance of performance and development speed
- You're working with existing Python codebases

**Choose NumPy** when:
- Your algorithms can be vectorized
- You're working with numerical data
- You want good performance with minimal code changes

#### Red Flags in Results

- **Inconsistent output values**: Check validation warnings in results
- **Unexpected memory usage**: May indicate memory leaks or inefficient algorithms
- **Poor parallel scaling**: Suggests GIL limitations or synchronization issues
- **High standard deviation**: Indicates unstable performance, may need more measurements

### Sample Result Interpretation

```json
{
  "scenario": "numeric_computation",
  "implementation": "rust_ext",
  "min_time": 45.2,
  "mean_time": 47.8,
  "relative_score": 0.048,
  "memory_peak_mb": 12.3,
  "validation": {"is_valid": true, "max_relative_error": 0.0}
}
```

**Interpretation**: 
- Rust implementation is ~21x faster than Python (1/0.048)
- Consistent performance (low variation between min/mean)
- Low memory usage (12.3 MB)
- Produces correct results (validation passed)

## 🔧 Development

### Adding New Implementations

1. Create implementation directory following the pattern
2. Implement required functions with identical signatures:
   - `find_primes(n: int) -> List[int]`
   - `matrix_multiply(a, b) -> List[List[float]]`
   - `sort_array(arr: List[int]) -> List[int]`
   - `filter_array(arr: List[int], threshold: int) -> List[int]`
   - `parallel_compute(data: List[float], num_threads: int) -> float`

3. Add build script if needed
4. Update tests to include new implementation

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_scenarios.py -v          # Scenario tests
pytest tests/test_validator.py -v          # Validation tests  
pytest tests/test_end_to_end_integration.py -v  # Integration tests

# Run with coverage
pytest tests/ --cov=benchmark --cov-report=html
```

### Property-Based Testing

The project uses Hypothesis for property-based testing to ensure correctness across many input variations:

```bash
# Run property-based tests
pytest tests/ -k "property" -v

# Run with more examples
pytest tests/ -k "property" --hypothesis-max-examples=1000 -v
```

## 🐳 Docker Environment

### Services

- **benchmark**: Full development environment (4 CPU, 8GB RAM)
- **benchmark-limited**: Resource-constrained testing (2 CPU, 4GB RAM)  
- **test**: Automated testing environment

### Usage

```bash
# Interactive development
docker-compose run --rm benchmark

# Run with resource limits
docker-compose run --rm benchmark-limited

# Automated testing
docker-compose up test
```

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker usage instructions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Submit a pull request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings for public functions
- Maintain test coverage above 80%

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

This project was inspired by the need for quantitative performance comparisons between Python extension technologies. Special thanks to the maintainers of:

- [pybind11](https://github.com/pybind/pybind11) for C++ bindings
- [PyO3](https://github.com/PyO3/pyo3) for Rust bindings  
- [Cython](https://cython.org/) for Python-to-C compilation
- [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check existing documentation in the `docs/` directory
- Review test files for usage examples

---

**Note**: This framework is designed for educational and research purposes. Benchmark results may vary based on hardware, operating system, and specific use cases. Always validate performance claims with your own testing in production-like environments.