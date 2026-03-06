#!/usr/bin/env python3
"""
Integration test for FFI summary generation

Tests the complete workflow from mock data to final report generation.
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.models import BenchmarkResult, EnvironmentInfo, ValidationResult
from scripts.generate_ffi_summary import load_benchmark_results, main as generate_main


def create_sample_results_file(output_path: str):
    """Create a sample results file for testing."""
    env = EnvironmentInfo(
        os="Linux",
        cpu="Intel i7-9700K",
        memory_gb=16.0,
        python_version="3.11.0",
        docker=False
    )
    
    validation = ValidationResult(
        is_valid=True,
        max_relative_error=0.001,
        mismatches=[]
    )
    
    results = []
    
    # Create comprehensive test data
    scenarios = ["find_primes", "matrix_multiply", "sort_array"]
    implementations = [
        ("python", 100.0, 5.0),
        ("c_ffi", 20.0, 2.0),
        ("cpp_ffi", 18.0, 3.0),
        ("rust_ffi", 15.0, 1.5),
        ("cython_ffi", 25.0, 4.0),
        ("julia_ffi", 30.0, 6.0),
        ("go_ffi", 35.0, 5.0),
        ("zig_ffi", 22.0, 3.0),
    ]
    
    for scenario in scenarios:
        for impl_name, base_time, std_dev in implementations:
            # Vary performance by scenario
            scenario_multiplier = {
                "find_primes": 1.0,
                "matrix_multiply": 2.0,
                "sort_array": 0.8
            }[scenario]
            
            mean_time = base_time * scenario_multiplier
            
            result = BenchmarkResult(
                scenario_name=scenario,
                implementation_name=impl_name,
                execution_times=[mean_time] * 100,
                memory_usage=[50.0] * 100,
                min_time=mean_time - std_dev,
                median_time=mean_time,
                mean_time=mean_time,
                std_dev=std_dev,
                relative_score=100.0 / mean_time if impl_name != "python" else 1.0,
                throughput=1000.0 / mean_time,
                output_value=f"result_{scenario}",
                timestamp=datetime.now(),
                environment=env,
                validation=validation,
                status="SUCCESS"
            )
            results.append(result)
    
    # Convert to JSON format
    results_data = {
        'results': [result.to_dict() for result in results],
        'metadata': {
            'generated': datetime.now().isoformat(),
            'total_results': len(results)
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2)
    
    return output_path


def test_complete_ffi_summary_workflow():
    """Test the complete FFI summary generation workflow."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample results file
        results_file = temp_path / "sample_results.json"
        create_sample_results_file(str(results_file))
        
        # Test loading results
        results = load_benchmark_results(str(results_file))
        assert len(results) > 0
        
        # Verify we have both Python and FFI results
        python_results = [r for r in results if r.implementation_name == "python"]
        ffi_results = [r for r in results if r.implementation_name.endswith("_ffi")]
        
        assert len(python_results) > 0, "Should have Python baseline results"
        assert len(ffi_results) > 0, "Should have FFI implementation results"
        
        print(f"✅ Loaded {len(results)} results ({len(python_results)} Python, {len(ffi_results)} FFI)")
        
        # Generate summary using the main generator
        from benchmark.runner.ffi_summary_generator import FFISummaryGenerator
        
        generator = FFISummaryGenerator(output_dir=str(temp_path))
        
        # Mock visualization to avoid matplotlib in test
        generator.visualizer.generate_speedup_comparison_chart = lambda x: str(temp_path / "speedup.png")
        generator.visualizer.generate_performance_distribution_chart = lambda x: str(temp_path / "distribution.png")
        generator.visualizer.generate_language_characteristics_chart = lambda x: str(temp_path / "characteristics.png")
        
        report_path = generator.generate_comprehensive_ffi_summary(results)
        
        # Verify report was created
        assert Path(report_path).exists(), f"Report should be created at {report_path}"
        
        # Read and verify report content
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify key sections exist
        required_sections = [
            "# FFI Benchmark Results Summary",
            "## Executive Summary",
            "## Performance Analysis",
            "## Language-Specific Analysis",
            "## Statistical Analysis",
            "## Technology Selection Guide",
            "## Implementation Recommendations",
            "## Detailed Results",
            "## Limitations and Considerations"
        ]
        
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"
        
        # Verify data content
        assert "find_primes" in content
        assert "matrix_multiply" in content
        assert "sort_array" in content
        
        # Verify language analysis
        assert "Rust" in content
        assert "C" in content
        assert "Julia" in content
        
        # Verify statistical content
        assert "speedup" in content.lower()
        assert "significant" in content.lower()
        
        print(f"✅ Generated comprehensive report: {len(content)} characters")
        print(f"📄 Report location: {report_path}")
        
        # Calculate and display summary statistics
        scenarios = set(r.scenario_name for r in results)
        implementations = set(r.implementation_name for r in results)
        
        print(f"📊 Report covers:")
        print(f"   • {len(scenarios)} scenarios: {', '.join(sorted(scenarios))}")
        print(f"   • {len(implementations)} implementations: {', '.join(sorted(implementations))}")
        
        return report_path


if __name__ == "__main__":
    print("🧪 Running FFI Summary Integration Test")
    print("=" * 50)
    
    try:
        report_path = test_complete_ffi_summary_workflow()
        print("\n🎉 Integration test completed successfully!")
        print(f"📋 Sample report generated at: {report_path}")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)