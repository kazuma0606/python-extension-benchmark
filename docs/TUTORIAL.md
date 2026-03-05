# Multi-Language Extension Benchmark Tutorial

This tutorial will guide you through using the Multi-Language Python Extension Benchmark Framework to compare performance across 12 different language implementations.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Understanding Results](#understanding-results)
4. [Advanced Usage](#advanced-usage)
5. [Adding New Implementations](#adding-new-implementations)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### Installation

#### Option 1: Docker (Recommended)

The easiest way to get started is using Docker, which includes all 12 language environments:

```bash
# Clone the repository
git clone <repository-url>
cd python-extension-benchmark

# Build and run with Docker
docker-compose up benchmark

# Run in interactive mode
docker-compose run --rm benchmark bash
```

#### Option 2: Local Installation

For local installation, you'll need to install each language toolchain separately:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Build available extensions (some may fail if toolchains are missing)
python scripts/build/build_c_ext.py
python scripts/build/build_cpp_ext.py
python scripts/build/build_rust_ext.py
# ... continue with other languages as available
```

### Verify Installation

Check which implementations are available:

```python
from benchmark.runner.benchmark import BenchmarkRunner

runner = BenchmarkRunner()
available = runner.get_all_available_implementations()
print(f"Available implementations: {available}")

# Load and test implementations
implementations = runner.load_implementations(available)
print(f"Successfully loaded: {[impl.name for impl in implementations]}")
```

## Basic Usage

### Running Your First Benchmark

Let's start with a simple benchmark comparing prime number finding across different implementations:

```python
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import NumericScenario

# Initialize the benchmark runner
runner = BenchmarkRunner()

# Create a prime finding scenario
scenario = NumericScenario("primes")
scenario.input_data = 1000  # Find primes up to 1000

# Load some implementations to compare
implementations = runner.load_implementations([
    'python',      # Pure Python baseline
    'numpy_impl',  # NumPy implementation
    'c_ext',       # C extension
    'rust_ext'     # Rust extension
])

# Run the benchmark
results = runner.run_scenario(
    scenario, 
    implementations,
    warmup_runs=2,      # 2 warmup runs
    measurement_runs=5  # 5 measurement runs
)

# Display results
print("\nBenchmark Results:")
print("-" * 50)
for result in results:
    if result.status == "SUCCESS":
        print(f"{result.implementation_name:12}: {result.mean_time:8.2f}ms "
              f"(relative: {result.relative_score:.2f}x)")
    else:
        print(f"{result.implementation_name:12}: ERROR - {result.error_message}")
```

### Running Multiple Scenarios

Compare implementations across different types of computations:

```python
from benchmark.runner.scenarios import NumericScenario, MemoryScenario, ParallelScenario

# Define multiple scenarios
scenarios = [
    NumericScenario("primes"),    # Prime finding
    NumericScenario("matrix"),    # Matrix multiplication
    MemoryScenario("sort"),       # Array sorting
    ParallelScenario(4)           # Parallel computation with 4 threads
]

# Set appropriate input data for each scenario
scenarios[0].input_data = 1000  # Primes up to 1000
scenarios[1].input_data = (
    [[1.0, 2.0], [3.0, 4.0]],    # 2x2 matrices for quick testing
    [[5.0, 6.0], [7.0, 8.0]]
)
scenarios[2].input_data = list(range(1000, 0, -1))  # 1000 integers to sort
scenarios[3].input_data = [float(i) for i in range(1000)]  # 1000 floats to sum

# Load implementations
implementations = runner.load_implementations(['python', 'c_ext', 'rust_ext'])

# Run all scenarios
all_results = []
for scenario in scenarios:
    print(f"\nRunning scenario: {scenario.name}")
    results = runner.run_scenario(scenario, implementations, warmup_runs=1, measurement_runs=3)
    all_results.extend(results)
    
    # Show quick results
    for result in results:
        if result.status == "SUCCESS":
            print(f"  {result.implementation_name}: {result.mean_time:.2f}ms")
```

### Saving and Visualizing Results

Save your benchmark results and create visualizations:

```python
from benchmark.runner.output import OutputWriter
from benchmark.runner.visualize import Visualizer

# Save results in multiple formats
writer = OutputWriter(base_dir="./my_results")

# JSON format (complete data)
json_path = writer.write_json(all_results, "my_benchmark_results")
print(f"JSON results saved to: {json_path}")

# CSV format (tabular data)
csv_path = writer.write_csv(all_results, "my_benchmark_results")
print(f"CSV results saved to: {csv_path}")

# Create visualizations
visualizer = Visualizer(base_dir="./my_results/graphs")

# Execution time comparison
exec_graph = visualizer.plot_execution_time(all_results, "execution_time_comparison")
print(f"Execution time graph: {exec_graph}")

# Memory usage comparison
memory_graph = visualizer.plot_memory_usage(all_results, "memory_usage_comparison")
print(f"Memory usage graph: {memory_graph}")

# Parallel scalability (if you have parallel results)
parallel_results = [r for r in all_results if hasattr(r, 'thread_count')]
if parallel_results:
    scalability_graph = visualizer.plot_scalability(parallel_results, "scalability_analysis")
    print(f"Scalability graph: {scalability_graph}")
```

## Understanding Results

### Key Metrics Explained

#### Execution Time Metrics

- **min_time**: Fastest execution time (best case performance)
- **median_time**: Middle value when all times are sorted (typical performance)
- **mean_time**: Average execution time (overall performance)
- **std_dev**: Standard deviation (consistency indicator)

```python
# Analyzing execution time consistency
for result in results:
    if result.status == "SUCCESS":
        consistency = result.std_dev / result.mean_time * 100
        print(f"{result.implementation_name}: {result.mean_time:.2f}ms ± {consistency:.1f}%")
```

#### Relative Performance

The `relative_score` shows performance relative to the Python baseline:

- `1.0` = Same speed as Python
- `0.5` = 2x faster than Python  
- `0.1` = 10x faster than Python
- `2.0` = 2x slower than Python

```python
# Find the fastest implementation
successful_results = [r for r in results if r.status == "SUCCESS"]
if successful_results:
    fastest = min(successful_results, key=lambda r: r.relative_score)
    print(f"Fastest implementation: {fastest.implementation_name} "
          f"({1/fastest.relative_score:.1f}x faster than Python)")
```

#### Memory Usage

Memory metrics help identify memory-efficient implementations:

```python
# Compare memory usage
for result in successful_results:
    avg_memory = sum(result.memory_usage) / len(result.memory_usage)
    peak_memory = max(result.memory_usage)
    print(f"{result.implementation_name}: avg={avg_memory:.1f}MB, peak={peak_memory:.1f}MB")
```

### Output Validation

The framework automatically validates that all implementations produce identical results:

```python
from benchmark.runner.validator import OutputValidator

# Group results by scenario
by_scenario = {}
for result in successful_results:
    scenario = result.scenario_name
    if scenario not in by_scenario:
        by_scenario[scenario] = {}
    by_scenario[scenario][result.implementation_name] = result.output_value

# Validate each scenario
for scenario_name, outputs in by_scenario.items():
    if len(outputs) > 1:  # Need at least 2 implementations to compare
        validation = OutputValidator.validate(outputs, tolerance=1e-6)
        
        if validation.is_valid:
            print(f"✓ {scenario_name}: All outputs match")
        else:
            print(f"⚠ {scenario_name}: Output mismatch detected!")
            print(f"  Max relative error: {validation.max_relative_error:.2e}")
            print(f"  Mismatched implementations: {validation.mismatches}")
```

## Advanced Usage

### Comprehensive Benchmarking

Run all available scenarios with all available implementations:

```python
# Run comprehensive benchmark (this may take several minutes)
print("Running comprehensive benchmark...")
comprehensive_results = runner.run_comprehensive_benchmark()

print(f"Completed {len(comprehensive_results)} benchmark runs")

# Analyze results by implementation
by_implementation = {}
for result in comprehensive_results:
    impl = result.implementation_name
    if impl not in by_implementation:
        by_implementation[impl] = {'success': 0, 'error': 0, 'total_time': 0}
    
    if result.status == "SUCCESS":
        by_implementation[impl]['success'] += 1
        by_implementation[impl]['total_time'] += result.mean_time
    else:
        by_implementation[impl]['error'] += 1

# Print implementation summary
print("\nImplementation Summary:")
print("-" * 60)
for impl, stats in by_implementation.items():
    total = stats['success'] + stats['error']
    success_rate = stats['success'] / total * 100 if total > 0 else 0
    avg_time = stats['total_time'] / stats['success'] if stats['success'] > 0 else 0
    
    print(f"{impl:15}: {stats['success']:2d}/{total:2d} success ({success_rate:5.1f}%) "
          f"avg: {avg_time:8.2f}ms")
```

### Custom Scenarios

Create your own benchmark scenarios:

```python
from benchmark.runner.scenarios import Scenario

class FibonacciScenario(Scenario):
    def __init__(self, n):
        super().__init__(f"fibonacci_{n}", f"Fibonacci({n})")
        self.n = n
    
    def execute(self, implementation):
        # Assume implementations have a fibonacci function
        return implementation.fibonacci(self.n)

# Use custom scenario
fibonacci_scenario = FibonacciScenario(30)
implementations = runner.load_implementations(['python', 'c_ext'])

# You would need to add fibonacci functions to your implementations
# results = runner.run_scenario(fibonacci_scenario, implementations)
```

### Performance Analysis

Analyze performance characteristics across different data sizes:

```python
import matplotlib.pyplot as plt

# Test performance scaling
data_sizes = [100, 500, 1000, 5000, 10000]
implementations_to_test = ['python', 'c_ext', 'rust_ext']

scaling_results = {}
for impl_name in implementations_to_test:
    scaling_results[impl_name] = []
    
    impl = runner.load_implementations([impl_name])
    if impl:
        for size in data_sizes:
            scenario = NumericScenario("primes")
            scenario.input_data = size
            
            results = runner.run_scenario(scenario, impl, warmup_runs=1, measurement_runs=3)
            if results and results[0].status == "SUCCESS":
                scaling_results[impl_name].append(results[0].mean_time)
            else:
                scaling_results[impl_name].append(None)

# Plot scaling results
plt.figure(figsize=(10, 6))
for impl_name, times in scaling_results.items():
    valid_sizes = []
    valid_times = []
    for size, time in zip(data_sizes, times):
        if time is not None:
            valid_sizes.append(size)
            valid_times.append(time)
    
    if valid_times:
        plt.plot(valid_sizes, valid_times, marker='o', label=impl_name)

plt.xlabel('Input Size')
plt.ylabel('Execution Time (ms)')
plt.title('Performance Scaling Comparison')
plt.legend()
plt.grid(True)
plt.show()
```

### Error Handling and Debugging

Handle errors gracefully and debug issues:

```python
# Enable detailed error reporting
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with error handling
try:
    results = runner.run_scenario(scenario, implementations)
    
    # Check for errors
    error_results = [r for r in results if r.status == "ERROR"]
    if error_results:
        print("Errors encountered:")
        for result in error_results:
            print(f"  {result.implementation_name}: {result.error_message}")
    
    # Check error handler for more details
    if runner.error_handler.has_errors():
        error_stats = runner.error_handler.get_implementation_statistics()
        print("\nError Statistics:")
        for impl, stats in error_stats.items():
            print(f"  {impl}: {stats}")

except Exception as e:
    print(f"Benchmark failed: {e}")
    import traceback
    traceback.print_exc()
```

## Adding New Implementations

### Implementation Structure

Each implementation must provide the five required functions:

```python
# Example: benchmark/my_lang_ext/__init__.py

def find_primes(n: int) -> list:
    """Find all prime numbers up to n using Sieve of Eratosthenes."""
    # Your implementation here
    pass

def matrix_multiply(a: list, b: list) -> list:
    """Multiply two matrices."""
    # Your implementation here
    pass

def sort_array(arr: list) -> list:
    """Sort an array of integers."""
    # Your implementation here
    pass

def filter_array(arr: list, threshold: int) -> list:
    """Filter array elements >= threshold."""
    # Your implementation here
    pass

def parallel_compute(data: list, num_threads: int) -> float:
    """Compute sum using parallel processing."""
    # Your implementation here
    pass
```

### Adding to the Framework

1. Create implementation directory: `benchmark/my_lang_ext/`
2. Implement required functions in `__init__.py`
3. Add build script if needed: `scripts/build/build_my_lang_ext.py`
4. Update tests to include your implementation
5. Test your implementation:

```python
# Test your new implementation
runner = BenchmarkRunner()
my_impl = runner.load_implementations(['my_lang_ext'])

if my_impl:
    scenario = NumericScenario("primes")
    scenario.input_data = 100
    results = runner.run_scenario(scenario, my_impl)
    
    if results[0].status == "SUCCESS":
        print(f"Success! Result: {results[0].output_value}")
    else:
        print(f"Error: {results[0].error_message}")
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```
Error: No module named 'benchmark.some_ext'
```

**Solution**: Check that the implementation is properly installed and built.

```python
# Check available implementations
runner = BenchmarkRunner()
available = runner.get_all_available_implementations()
print(f"Available: {available}")

# Try loading individually
for impl_name in available:
    try:
        impl = runner.load_implementations([impl_name])
        print(f"✓ {impl_name}: OK")
    except Exception as e:
        print(f"✗ {impl_name}: {e}")
```

#### 2. Build Failures

```
Error: Extension build failed
```

**Solution**: Check that required compilers and dependencies are installed.

```bash
# For C/C++ extensions
gcc --version
g++ --version

# For Rust extensions  
rustc --version

# For specific languages, check their installation
julia --version
go version
zig version
```

#### 3. Inconsistent Results

```
Warning: Output validation failed
```

**Solution**: Check for floating-point precision issues or algorithm differences.

```python
# Increase validation tolerance
validation = OutputValidator.validate(outputs, tolerance=1e-4)  # Less strict

# Debug output differences
for impl, output in outputs.items():
    print(f"{impl}: {output[:10]}...")  # Show first 10 elements
```

#### 4. Performance Issues

```
Benchmark taking too long
```

**Solution**: Reduce data sizes or increase timeouts.

```python
# Use smaller data sizes for testing
scenario.input_data = 100  # Instead of 10000

# Increase timeout
results = runner.run_scenario(scenario, implementations, timeout=600)  # 10 minutes
```

### Getting Help

1. Check the logs for detailed error messages
2. Run individual implementations to isolate issues
3. Use smaller data sizes for debugging
4. Check the `docs/` directory for additional documentation
5. Review test files for usage examples

### Performance Tips

1. **Use warmup runs** to account for JIT compilation and caching
2. **Take multiple measurements** for statistical significance  
3. **Control the environment** (CPU affinity, thread limits)
4. **Validate results** to ensure correctness
5. **Monitor resource usage** to avoid system limits

```python
# Optimal benchmark settings
results = runner.run_scenario(
    scenario,
    implementations,
    warmup_runs=3,      # Allow JIT warmup
    measurement_runs=10, # Good statistical sample
    timeout=300         # 5 minute timeout
)
```

This tutorial should get you started with the Multi-Language Python Extension Benchmark Framework. Experiment with different scenarios and implementations to understand the performance characteristics of various language extensions!