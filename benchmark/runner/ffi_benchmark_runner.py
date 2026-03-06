#!/usr/bin/env python3
"""
FFI Benchmark Runner

Comprehensive benchmark runner that supports both extension and FFI implementations,
with uv environment checking and enhanced result output.
"""

import sys
import argparse
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.output import OutputWriter
from benchmark.runner.scenarios import (
    get_all_scenarios, 
    get_default_implementations,
    get_extension_implementations,
    get_ffi_implementations
)
from benchmark.ffi_implementations.uv_checker import UVEnvironmentChecker, check_uv_environment


class FFIBenchmarkRunner:
    """Enhanced benchmark runner with FFI support."""
    
    def __init__(self):
        self.runner = BenchmarkRunner()
        self.output_writer = OutputWriter()
        self.uv_checker = UVEnvironmentChecker()
    
    def run_ffi_comparison_benchmark(
        self,
        scenarios: Optional[List] = None,
        include_extensions: bool = True,
        include_ffi: bool = True,
        output_prefix: str = "ffi_benchmark"
    ) -> None:
        """Run comprehensive FFI vs Extension comparison benchmark.
        
        Args:
            scenarios: List of scenarios to run (None for all)
            include_extensions: Include extension implementations
            include_ffi: Include FFI implementations
            output_prefix: Prefix for output files
        """
        print("=" * 80)
        print("FFI BENCHMARK RUNNER")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Check uv environment if FFI implementations are requested
        if include_ffi:
            print("🔍 Checking uv environment for FFI implementations...")
            env_ok = check_uv_environment()
            if not env_ok:
                print("⚠️  Warning: uv environment issues detected.")
                print("   FFI implementations may not work correctly.")
                
                response = input("\nContinue anyway? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("Benchmark cancelled.")
                    return
            else:
                print("✓ uv environment validation passed.")
            print()
        
        # Determine implementations to run
        implementations = []
        
        if include_extensions:
            implementations.extend(get_extension_implementations())
            print(f"✓ Including {len(get_extension_implementations())} extension implementations")
        
        if include_ffi:
            ffi_impls = get_ffi_implementations()
            implementations.extend(ffi_impls)
            print(f"✓ Including {len(ffi_impls)} FFI implementations")
        
        if not implementations:
            print("❌ No implementations selected. Aborting.")
            return
        
        print(f"\nTotal implementations to test: {len(implementations)}")
        print(f"Implementations: {', '.join(implementations[:5])}{'...' if len(implementations) > 5 else ''}")
        print()
        
        # Run benchmark
        print("🚀 Starting comprehensive benchmark...")
        results = self.runner.run_comprehensive_benchmark(
            scenarios=scenarios,
            implementation_filter=implementations,
            check_uv_env=False  # Already checked above
        )
        
        if not results:
            print("❌ No results generated. Benchmark failed.")
            return
        
        # Generate outputs
        print("\n📊 Generating output files...")
        
        # Standard outputs
        json_path = self.output_writer.write_json(results, f"{output_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        csv_path = self.output_writer.write_csv(results, f"{output_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # FFI-specific outputs
        if include_ffi:
            ffi_json_path = self.output_writer.write_ffi_comparison_report(
                results, f"{output_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            ffi_csv_path = self.output_writer.write_ffi_csv_comparison(
                results, f"{output_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            print(f"✓ FFI comparison report: {ffi_json_path}")
            print(f"✓ FFI comparison CSV: {ffi_csv_path}")
        
        # Comprehensive report
        comprehensive_path = self.output_writer.write_comprehensive_report(
            results, f"{output_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        print(f"✓ Standard JSON: {json_path}")
        print(f"✓ Standard CSV: {csv_path}")
        print(f"✓ Comprehensive report: {comprehensive_path}")
        
        # Print summary
        self._print_final_summary(results, include_ffi)
        
        print("\n🎉 Benchmark completed successfully!")
        print("=" * 80)
    
    def _print_final_summary(self, results, include_ffi: bool):
        """Print final benchmark summary."""
        print("\n" + "=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        
        total_results = len(results)
        successful_results = len([r for r in results if r.status == "SUCCESS"])
        failed_results = total_results - successful_results
        
        print(f"Total benchmark runs: {total_results}")
        print(f"Successful runs: {successful_results}")
        print(f"Failed runs: {failed_results}")
        
        if include_ffi and successful_results > 0:
            # Calculate FFI vs Pure Python statistics
            python_results = [r for r in results if r.implementation_name == "python" and r.status == "SUCCESS"]
            ffi_results = [r for r in results if r.implementation_name.endswith("_ffi") and r.status == "SUCCESS"]
            
            if python_results and ffi_results:
                print(f"\nFFI Performance Summary:")
                print(f"Pure Python scenarios: {len(python_results)}")
                print(f"FFI scenarios completed: {len(ffi_results)}")
                
                # Calculate average speedup
                speedups = []
                for ffi_result in ffi_results:
                    python_result = next((r for r in python_results if r.scenario_name == ffi_result.scenario_name), None)
                    if python_result and python_result.mean_time > 0:
                        speedup = python_result.mean_time / ffi_result.mean_time
                        speedups.append(speedup)
                
                if speedups:
                    avg_speedup = sum(speedups) / len(speedups)
                    max_speedup = max(speedups)
                    min_speedup = min(speedups)
                    
                    print(f"Average FFI speedup: {avg_speedup:.2f}x")
                    print(f"Maximum FFI speedup: {max_speedup:.2f}x")
                    print(f"Minimum FFI speedup: {min_speedup:.2f}x")
        
        print("=" * 60)
    
    def check_environment(self):
        """Check and display environment status."""
        print("=" * 60)
        print("ENVIRONMENT CHECK")
        print("=" * 60)
        
        self.uv_checker.print_environment_status()
        
        # Check available implementations
        available_extensions = []
        available_ffi = []
        
        all_available = self.runner.get_all_available_implementations()
        
        for impl in all_available:
            if impl.endswith('_ffi'):
                available_ffi.append(impl)
            else:
                available_extensions.append(impl)
        
        print(f"\nAvailable Extension Implementations ({len(available_extensions)}):")
        for impl in available_extensions:
            print(f"  ✓ {impl}")
        
        print(f"\nAvailable FFI Implementations ({len(available_ffi)}):")
        for impl in available_ffi:
            print(f"  ✓ {impl}")
        
        if not available_ffi:
            print("  ⚠️  No FFI implementations available")
            print("     Make sure shared libraries are built and uv environment is active")
        
        print("=" * 60)


def main():
    """Main entry point for FFI benchmark runner."""
    parser = argparse.ArgumentParser(
        description="FFI Benchmark Runner - Compare extension and FFI implementations"
    )
    
    parser.add_argument(
        "--mode", 
        choices=["all", "extensions", "ffi", "check"],
        default="all",
        help="Benchmark mode (default: all)"
    )
    
    parser.add_argument(
        "--output-prefix",
        default="ffi_benchmark",
        help="Prefix for output files (default: ffi_benchmark)"
    )
    
    parser.add_argument(
        "--scenarios",
        nargs="*",
        help="Specific scenarios to run (default: all)"
    )
    
    args = parser.parse_args()
    
    runner = FFIBenchmarkRunner()
    
    if args.mode == "check":
        runner.check_environment()
        return
    
    # Determine what to include
    include_extensions = args.mode in ["all", "extensions"]
    include_ffi = args.mode in ["all", "ffi"]
    
    # Get scenarios
    scenarios = None
    if args.scenarios:
        all_scenarios = get_all_scenarios()
        scenario_map = {s.name: s for s in all_scenarios}
        scenarios = [scenario_map[name] for name in args.scenarios if name in scenario_map]
        
        if not scenarios:
            print(f"❌ No valid scenarios found. Available: {list(scenario_map.keys())}")
            return
    
    # Run benchmark
    runner.run_ffi_comparison_benchmark(
        scenarios=scenarios,
        include_extensions=include_extensions,
        include_ffi=include_ffi,
        output_prefix=args.output_prefix
    )


if __name__ == "__main__":
    main()