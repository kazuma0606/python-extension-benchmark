# API Reference

This document provides comprehensive API documentation for the Multi-Language Python Extension Benchmark Framework.

## Core Classes

### BenchmarkRunner

The main class for executing benchmarks across multiple implementations.

```python
from benchmark.runner.benchmark import BenchmarkRunner

runner = BenchmarkRunner()
```

#### Methods

##### `get_all_available_implementations() -> List[str]`

Returns a list of all available implementation names.

```python
implementations = runner.get_all_available_implementations()
# Returns: ['python', 'numpy_impl', 'c_ext', 'cpp_ext', 'rust_ext', ...]
```

##### `load_implementations(implementation_names: List[str]) -> List[Implementation]`

Loads specified implementations, handling errors gracefully.

```python
implementations = runner.load_implementations(['python', 'c_ext', 'rust_ext'])
```

##### `run_scenario(scenario: Scenario, implementations: List[Implementation], warmup_runs: int = 3, measurement_runs: int = 10) -> List[BenchmarkResult]`

Runs a single scenario across multiple implementations.

```python
from benchmark.runner.scenarios import NumericScenario

scenario = NumericScenario("primes")
results = runner.run_scenario(scenario, implementations, warmup_runs=2, measurement_runs=5)
```

##### `run_comprehensive_benchmark() -> List[BenchmarkResult]`

Runs all scenarios with all available implementations.

```python
all_results = runner.run_comprehensive_benchmark()
```

### Scenario Classes

Base class for all benchmark scenarios.

#### NumericScenario

Scenarios for numeric computation benchmarks.

```python
from benchmark.runner.scenarios import NumericScenario

# Prime finding scenario
primes_scenario = NumericScenario("primes")
primes_scenario.input_data = 10000  # Find primes up to 10,000

# Matrix multiplication scenario  
matrix_scenario = NumericScenario("matrix")
matrix_scenario.input_data = (matrix_a, matrix_b)
```

#### MemoryScenario

Scenarios for memory operation benchmarks.

```python
from benchmark.runner.scenarios import MemoryScenario

# Array sorting scenario
sort_scenario = MemoryScenario("sort")
sort_scenario.input_data = [3, 1, 4, 1, 5, 9, 2, 6]

# Array filtering scenario
filter_scenario = MemoryScenario("filter")
filter_scenario.input_data = ([1, 2, 3, 4, 5], 3)  # (array, threshold)
```

#### ParallelScenario

Scenarios for parallel processing benchmarks.

```python
from benchmark.runner.scenarios import ParallelScenario

# Parallel computation with 4 threads
parallel_scenario = ParallelScenario(num_threads=4)
parallel_scenario.input_data = [1.0, 2.0, 3.0, 4.0, 5.0]
```

### BenchmarkResult

Contains the results of a single benchmark execution.

#### Properties

- `scenario_name: str` - Name of the executed scenario
- `implementation_name: str` - Name of the implementation
- `status: str` - "SUCCESS" or "ERROR"
- `execution_times: List[float]` - All measured execution times (ms)
- `memory_usage: List[float]` - Memory usage measurements (MB)
- `min_time: float` - Minimum execution time
- `median_time: float` - Median execution time
- `mean_time: float` - Mean execution time
- `std_dev: float` - Standard deviation of execution times
- `relative_score: float` - Performance relative to Python baseline
- `throughput: float` - Operations per second
- `output_value: Any` - Result produced by the implementation
- `timestamp: datetime` - When the benchmark was executed
- `environment: EnvironmentInfo` - System environment information
- `error_message: str` - Error details (if status is "ERROR")

### OutputWriter

Handles saving benchmark results to various formats.

```python
from benchmark.runner.output import OutputWriter

writer = OutputWriter(base_dir="./results")
```

#### Methods

##### `write_json(results: List[BenchmarkResult], filename: str) -> str`

Saves results in JSON format.

```python
json_path = writer.write_json(results, "benchmark_results")
```

##### `write_csv(results: List[BenchmarkResult], filename: str) -> str`

Saves results in CSV format.

```python
csv_path = writer.write_csv(results, "benchmark_results")
```

### Visualizer

Generates graphs and visualizations from benchmark results.

```python
from benchmark.runner.visualize import Visualizer

visualizer = Visualizer(base_dir="./results/graphs")
```

#### Methods

##### `plot_execution_time(results: List[BenchmarkResult], filename: str) -> str`

Creates execution time comparison graph.

```python
graph_path = visualizer.plot_execution_time(results, "execution_time_comparison")
```

##### `plot_memory_usage(results: List[BenchmarkResult], filename: str) -> str`

Creates memory usage comparison graph.

```python
graph_path = visualizer.plot_memory_usage(results, "memory_usage_comparison")
```

##### `plot_scalability(results: List[BenchmarkResult], filename: str) -> str`

Creates parallel scalability graph.

```python
graph_path = visualizer.plot_scalability(parallel_results, "scalability_analysis")
```

### OutputValidator

Validates that different implementations produce identical results.

```python
from benchmark.runner.validator import OutputValidator

# Validate outputs from multiple implementations
outputs = {
    'python': [2, 3, 5, 7, 11],
    'c_ext': [2, 3, 5, 7, 11],
    'rust_ext': [2, 3, 5, 7, 11]
}

validation = OutputValidator.validate(outputs, tolerance=1e-6)
print(f"Valid: {validation.is_valid}")
print(f"Max error: {validation.max_relative_error}")
```

## Implementation Interface

All language implementations must provide these functions:

### Required Functions

#### `find_primes(n: int) -> List[int]`

Find all prime numbers up to n using the Sieve of Eratosthenes.

```python
def find_primes(n: int) -> List[int]:
    """Find all prime numbers up to n."""
    # Implementation here
    return primes_list
```

#### `matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]`

Multiply two matrices.

```python
def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Multiply two matrices."""
    # Implementation here
    return result_matrix
```

#### `sort_array(arr: List[int]) -> List[int]`

Sort an array of integers.

```python
def sort_array(arr: List[int]) -> List[int]:
    """Sort an array of integers."""
    # Implementation here
    return sorted_array
```

#### `filter_array(arr: List[int], threshold: int) -> List[int]`

Filter array elements greater than or equal to threshold.

```python
def filter_array(arr: List[int], threshold: int) -> List[int]:
    """Filter array elements >= threshold."""
    # Implementation here
    return filtered_array
```

#### `parallel_compute(data: List[float], num_threads: int) -> float`

Compute sum of array elements using parallel processing.

```python
def parallel_compute(data: List[float], num_threads: int) -> float:
    """Compute sum using parallel processing."""
    # Implementation here
    return total_sum
```

## Error Handling

### ErrorHandler

Manages errors during benchmark execution.

```python
from benchmark.runner.error_handler import ErrorHandler

error_handler = ErrorHandler()
```

#### Methods

##### `handle_import_error(implementation_name: str, error: Exception) -> ErrorLog`

Records import errors for implementations.

##### `handle_execution_error(implementation_name: str, scenario_name: str, error: Exception) -> ErrorLog`

Records execution errors during benchmarks.

##### `has_errors() -> bool`

Returns True if any errors have been recorded.

##### `get_implementation_statistics() -> Dict[str, Dict[str, int]]`

Returns error statistics by implementation.

## Configuration

### Environment Variables

Control benchmark behavior with environment variables:

- `OMP_NUM_THREADS` - OpenMP thread limit
- `NUMBA_NUM_THREADS` - Numba thread limit  
- `MKL_NUM_THREADS` - Intel MKL thread limit
- `JULIA_NUM_THREADS` - Julia thread limit

### Default Settings

```python
# Default benchmark settings
WARMUP_RUNS = 3
MEASUREMENT_RUNS = 10
TIMEOUT_SECONDS = 300
MEMORY_LIMIT_MB = 4096
```

## Usage Examples

### Basic Benchmark

```python
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import NumericScenario

# Initialize
runner = BenchmarkRunner()
scenario = NumericScenario("primes")
scenario.input_data = 1000

# Load implementations
implementations = runner.load_implementations(['python', 'c_ext', 'rust_ext'])

# Run benchmark
results = runner.run_scenario(scenario, implementations)

# Print results
for result in results:
    if result.status == "SUCCESS":
        print(f"{result.implementation_name}: {result.mean_time:.2f}ms")
```

### Comprehensive Analysis

```python
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.output import OutputWriter
from benchmark.runner.visualize import Visualizer

# Run comprehensive benchmark
runner = BenchmarkRunner()
results = runner.run_comprehensive_benchmark()

# Save results
writer = OutputWriter()
json_path = writer.write_json(results, "comprehensive_benchmark")
csv_path = writer.write_csv(results, "comprehensive_benchmark")

# Generate visualizations
visualizer = Visualizer()
exec_graph = visualizer.plot_execution_time(results, "execution_time")
memory_graph = visualizer.plot_memory_usage(results, "memory_usage")

print(f"Results saved: {json_path}, {csv_path}")
print(f"Graphs saved: {exec_graph}, {memory_graph}")
```

### Custom Scenario

```python
from benchmark.runner.scenarios import Scenario
from benchmark.runner.benchmark import BenchmarkRunner

class CustomScenario(Scenario):
    def __init__(self):
        super().__init__("custom_computation", "Custom Computation")
        self.input_data = {"param1": 100, "param2": 200}
    
    def execute(self, implementation):
        # Custom execution logic
        return implementation.custom_function(
            self.input_data["param1"], 
            self.input_data["param2"]
        )

# Use custom scenario
runner = BenchmarkRunner()
custom_scenario = CustomScenario()
implementations = runner.load_implementations(['python'])
results = runner.run_scenario(custom_scenario, implementations)
```

## Testing

### Property-Based Testing

The framework includes property-based tests using Hypothesis:

```python
from hypothesis import given, strategies as st
import pytest

@given(st.integers(min_value=2, max_value=1000))
def test_find_primes_property(n):
    """Property: All returned numbers should be prime."""
    from benchmark.python.numeric import find_primes
    
    primes = find_primes(n)
    
    for p in primes:
        assert is_prime(p), f"{p} is not prime"
        assert p <= n, f"{p} exceeds limit {n}"
```

### Integration Testing

```python
def test_multi_language_consistency():
    """Test that all implementations produce identical results."""
    from benchmark.runner.benchmark import BenchmarkRunner
    from benchmark.runner.scenarios import NumericScenario
    from benchmark.runner.validator import OutputValidator
    
    runner = BenchmarkRunner()
    scenario = NumericScenario("primes")
    scenario.input_data = 100
    
    implementations = runner.load_implementations(['python', 'c_ext', 'rust_ext'])
    results = runner.run_scenario(scenario, implementations)
    
    outputs = {r.implementation_name: r.output_value for r in results if r.status == "SUCCESS"}
    validation = OutputValidator.validate(outputs)
    
    assert validation.is_valid, f"Outputs don't match: {validation.mismatches}"
```

## Performance Optimization

### Best Practices

1. **Warmup Runs**: Always use warmup runs to account for JIT compilation and caching
2. **Multiple Measurements**: Take multiple measurements for statistical significance
3. **Resource Limits**: Set appropriate CPU and memory limits for consistent results
4. **Environment Control**: Use consistent environment variables across runs
5. **Validation**: Always validate that implementations produce correct results

### Troubleshooting

#### Common Issues

1. **Import Errors**: Check that all required dependencies are installed
2. **Build Failures**: Verify compiler toolchains are properly configured
3. **Memory Issues**: Reduce data sizes or increase memory limits
4. **Timeout Errors**: Increase timeout values for slow implementations
5. **Inconsistent Results**: Check for non-deterministic algorithms or race conditions

#### Debug Mode

Enable debug logging for detailed execution information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

runner = BenchmarkRunner()
# Detailed logs will be printed during execution
```