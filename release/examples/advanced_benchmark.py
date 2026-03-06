#!/usr/bin/env python3
"""
FFI Benchmark Advanced Example

This example demonstrates advanced usage including custom scenarios,
performance analysis, and result visualization.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add benchmark directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.runner.ffi_benchmark_runner import FFIBenchmarkRunner
from benchmark.runner.scenarios import NumericScenario, MemoryScenario
from benchmark.runner.output import OutputWriter
from benchmark.runner.visualize import Visualizer


def main():
    """Advanced benchmark example"""
    
    print("FFI Benchmark Advanced Example")
    print("=" * 50)
    
    # 1. Custom scenarios
    print("1. Creating custom scenarios...")
    
    custom_scenarios = [
        NumericScenario("primes"),
        MemoryScenario("sort")
    ]
    
    # Adjust data sizes for demonstration
    custom_scenarios[0].input_data = 1000  # Prime search up to 1000
    custom_scenarios[1].input_data = list(range(5000, 0, -1))  # Sort 5000 elements
    
    print(f"   Created {len(custom_scenarios)} custom scenarios")
    
    # 2. Run benchmark with custom scenarios
    print("\n2. Running benchmark with custom scenarios...")
    
    runner = FFIBenchmarkRunner()
    
    try:
        runner.run_ffi_comparison_benchmark(
            scenarios=custom_scenarios,
            include_extensions=True,
            include_ffi=True,
            output_prefix=f"advanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        print("   ✓ Benchmark completed")
        
    except Exception as e:
        print(f"   ❌ Benchmark failed: {e}")
        return
    
    # 3. Performance analysis
    print("\n3. Performing performance analysis...")
    
    # Load latest results
    results_dir = Path("benchmark/results/json")
    if results_dir.exists():
        json_files = list(results_dir.glob("advanced_*.json"))
        if json_files:
            latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get('results', [])
            
            # Analyze results
            analyze_performance(results)
        else:
            print("   ⚠ No result files found")
    else:
        print("   ⚠ Results directory not found")
    
    print("\n✓ Advanced example completed!")


def analyze_performance(results):
    """Analyze benchmark performance results"""
    
    print("   Performance Analysis:")
    print("   " + "-" * 30)
    
    # Group by implementation
    by_implementation = {}
    for result in results:
        impl_name = result.get('implementation_name', 'unknown')
        if impl_name not in by_implementation:
            by_implementation[impl_name] = []
        by_implementation[impl_name].append(result)
    
    # Calculate statistics
    for impl_name, impl_results in by_implementation.items():
        if impl_results:
            avg_time = sum(r.get('mean_time', 0) for r in impl_results) / len(impl_results)
            avg_throughput = sum(r.get('throughput', 0) for r in impl_results) / len(impl_results)
            
            print(f"   {impl_name}:")
            print(f"     Average time: {avg_time:.2f} ms")
            print(f"     Average throughput: {avg_throughput:.2f} ops/sec")
    
    # Find fastest implementation
    if results:
        fastest = min(results, key=lambda r: r.get('mean_time', float('inf')))
        print(f"\n   Fastest: {fastest.get('implementation_name')} "
              f"({fastest.get('mean_time', 0):.2f} ms)")


if __name__ == "__main__":
    main()
