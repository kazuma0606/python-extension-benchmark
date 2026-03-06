#!/usr/bin/env python3
"""
FFI Benchmark Quick Start Example

This example demonstrates basic usage of the FFI benchmark system.
"""

import sys
from pathlib import Path

# Add benchmark directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.ffi_implementations.uv_checker import check_uv_environment
from benchmark.runner.ffi_benchmark_runner import FFIBenchmarkRunner


def main():
    """Quick start example"""
    
    print("FFI Benchmark Quick Start")
    print("=" * 40)
    
    # 1. Check environment
    print("1. Checking uv environment...")
    if check_uv_environment():
        print("   ✓ uv environment is ready")
    else:
        print("   ⚠ uv environment needs setup")
        print("   Please run: uv sync")
        return
    
    # 2. Initialize benchmark runner
    print("\n2. Initializing benchmark runner...")
    runner = FFIBenchmarkRunner()
    
    # 3. Check available implementations
    print("\n3. Checking available implementations...")
    runner.check_environment()
    
    # 4. Run simple benchmark
    print("\n4. Running simple FFI benchmark...")
    try:
        runner.run_ffi_comparison_benchmark(
            include_extensions=True,
            include_ffi=True,
            output_prefix="quick_start"
        )
        print("\n✓ Benchmark completed successfully!")
        print("Check the results/ directory for output files.")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        print("Please check the troubleshooting guide for help.")


if __name__ == "__main__":
    main()
