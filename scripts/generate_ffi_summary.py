#!/usr/bin/env python3
"""
Generate FFI Summary Report Script

Command-line interface for generating comprehensive FFI benchmark summary reports.
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add benchmark directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.models import BenchmarkResult
from benchmark.runner.ffi_summary_generator import FFISummaryGenerator


def load_benchmark_results(results_path: str) -> list:
    """Load benchmark results from JSON file.
    
    Args:
        results_path: Path to JSON results file
        
    Returns:
        List of BenchmarkResult objects
    """
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both direct results list and wrapped format
    if isinstance(data, dict) and 'results' in data:
        results_data = data['results']
    elif isinstance(data, list):
        results_data = data
    else:
        raise ValueError("Invalid results file format")
    
    # Convert to BenchmarkResult objects
    results = []
    for result_dict in results_data:
        try:
            result = BenchmarkResult.from_dict(result_dict)
            results.append(result)
        except Exception as e:
            print(f"Warning: Failed to parse result: {e}")
            continue
    
    return results


def find_latest_results_file(results_dir: str = "benchmark/results/json") -> str:
    """Find the most recent FFI benchmark results file.
    
    Args:
        results_dir: Directory containing results files
        
    Returns:
        Path to most recent results file
    """
    results_path = Path(results_dir)
    
    if not results_path.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")
    
    # Look for FFI benchmark files
    ffi_files = list(results_path.glob("*ffi_benchmark*.json"))
    
    if not ffi_files:
        # Fall back to any JSON files
        ffi_files = list(results_path.glob("*.json"))
    
    if not ffi_files:
        raise FileNotFoundError(f"No benchmark results files found in {results_dir}")
    
    # Sort by modification time and return the most recent
    latest_file = max(ffi_files, key=lambda f: f.stat().st_mtime)
    return str(latest_file)


def main():
    """Main entry point for FFI summary generation."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive FFI benchmark summary report"
    )
    
    parser.add_argument(
        "--results-file",
        help="Path to benchmark results JSON file (auto-detects latest if not specified)"
    )
    
    parser.add_argument(
        "--output-file",
        default="benchmark_results_summary_FFI.md",
        help="Output filename for the summary report (default: benchmark_results_summary_FFI.md)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="docs",
        help="Output directory for the report (default: docs)"
    )
    
    parser.add_argument(
        "--results-dir",
        default="benchmark/results/json",
        help="Directory to search for results files (default: benchmark/results/json)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        # Determine results file
        if args.results_file:
            results_file = args.results_file
            if args.verbose:
                print(f"Using specified results file: {results_file}")
        else:
            results_file = find_latest_results_file(args.results_dir)
            if args.verbose:
                print(f"Auto-detected latest results file: {results_file}")
        
        # Load results
        print(f"📂 Loading benchmark results from: {results_file}")
        results = load_benchmark_results(results_file)
        
        if not results:
            print("❌ No valid benchmark results found in file")
            return 1
        
        print(f"✅ Loaded {len(results)} benchmark results")
        
        # Check for FFI results (including extension implementations)
        ffi_results = [r for r in results if (
            r.implementation_name.endswith('_ffi') or 
            r.implementation_name.endswith('_ext') or
            r.implementation_name == 'numpy_impl'
        ) and r.implementation_name != 'python']
        python_results = [r for r in results if r.implementation_name == 'python']
        
        if not ffi_results:
            print("⚠️  Warning: No FFI results found in data")
        else:
            print(f"🔧 Found {len(ffi_results)} FFI results")
        
        if not python_results:
            print("⚠️  Warning: No Pure Python baseline results found")
        else:
            print(f"🐍 Found {len(python_results)} Pure Python baseline results")
        
        # Generate summary
        generator = FFISummaryGenerator(output_dir=args.output_dir)
        
        print("\n🚀 Generating comprehensive FFI summary report...")
        report_path = generator.generate_comprehensive_ffi_summary(
            results=results,
            filename=args.output_file
        )
        
        print(f"\n🎉 FFI summary report generated successfully!")
        print(f"📄 Report location: {report_path}")
        
        # Print summary statistics
        total_scenarios = len(set(r.scenario_name for r in results))
        total_implementations = len(set(r.implementation_name for r in results))
        successful_results = len([r for r in results if r.status == "SUCCESS"])
        
        print(f"\n📊 Report Statistics:")
        print(f"   • Total scenarios: {total_scenarios}")
        print(f"   • Total implementations: {total_implementations}")
        print(f"   • Successful runs: {successful_results}/{len(results)}")
        
        if ffi_results and python_results:
            # Calculate quick performance summary
            ffi_scenarios = set(r.scenario_name for r in ffi_results if r.status == "SUCCESS")
            python_scenarios = {r.scenario_name: r for r in python_results if r.status == "SUCCESS"}
            
            speedups = []
            for ffi_result in ffi_results:
                if (ffi_result.status == "SUCCESS" and 
                    ffi_result.scenario_name in python_scenarios and
                    ffi_result.implementation_name != 'python'):
                    python_time = python_scenarios[ffi_result.scenario_name].mean_time
                    if python_time > 0:
                        speedup = python_time / ffi_result.mean_time
                        speedups.append(speedup)
            
            if speedups:
                avg_speedup = sum(speedups) / len(speedups)
                max_speedup = max(speedups)
                print(f"   • Average FFI speedup: {avg_speedup:.1f}x")
                print(f"   • Maximum FFI speedup: {max_speedup:.1f}x")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())