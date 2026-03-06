"""
Property-based tests for FFI benchmark integration.

**Feature: ffi-benchmark-extensions, Property 9: 結果ファイル生成**
**Validates: Requirements 15.1**

Tests that the integrated FFI benchmark system generates appropriate
result files when benchmarks are completed.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume
from typing import List, Dict, Any

# Import benchmark components
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.output import OutputWriter
from benchmark.runner.scenarios import NumericScenario, MemoryScenario
from benchmark.models import BenchmarkResult, EnvironmentInfo, Implementation, Scenario
from benchmark.ffi_implementations.uv_checker import UVEnvironmentChecker


class MockImplementation:
    """Mock implementation for testing."""
    
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
    
    def find_primes(self, n: int) -> List[int]:
        if self.should_fail:
            raise RuntimeError("Mock implementation failure")
        # Simple sieve implementation for testing
        if n < 2:
            return []
        sieve = [True] * (n + 1)
        sieve[0] = sieve[1] = False
        for i in range(2, int(n**0.5) + 1):
            if sieve[i]:
                for j in range(i*i, n + 1, i):
                    sieve[j] = False
        return [i for i in range(2, n + 1) if sieve[i]]
    
    def matrix_multiply(self, a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
        if self.should_fail:
            raise RuntimeError("Mock implementation failure")
        rows_a, cols_a = len(a), len(a[0])
        rows_b, cols_b = len(b), len(b[0])
        if cols_a != rows_b:
            raise ValueError("Matrix dimensions incompatible")
        
        result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
        for i in range(rows_a):
            for j in range(cols_b):
                for k in range(cols_a):
                    result[i][j] += a[i][k] * b[k][j]
        return result
    
    def sort_array(self, arr: List[int]) -> List[int]:
        if self.should_fail:
            raise RuntimeError("Mock implementation failure")
        return sorted(arr)
    
    def filter_array(self, arr: List[int], threshold: int) -> List[int]:
        if self.should_fail:
            raise RuntimeError("Mock implementation failure")
        return [x for x in arr if x >= threshold]
    
    def parallel_compute(self, data: List[float], num_threads: int) -> float:
        if self.should_fail:
            raise RuntimeError("Mock implementation failure")
        return sum(data)


def create_mock_benchmark_result(
    scenario_name: str,
    implementation_name: str,
    success: bool = True,
    execution_time: float = 10.0
) -> BenchmarkResult:
    """Create a mock benchmark result for testing."""
    env = EnvironmentInfo(
        os="Linux",
        cpu="Test CPU",
        memory_gb=16.0,
        python_version="3.11.0",
        docker=False
    )
    
    if success:
        return BenchmarkResult(
            scenario_name=scenario_name,
            implementation_name=implementation_name,
            execution_times=[execution_time] * 10,
            memory_usage=[100.0] * 10,
            min_time=execution_time * 0.9,
            median_time=execution_time,
            mean_time=execution_time,
            std_dev=execution_time * 0.1,
            relative_score=1.0,
            throughput=1000.0 / execution_time,
            output_value=[2, 3, 5, 7] if "prime" in scenario_name.lower() else [[1.0, 2.0], [3.0, 4.0]],
            timestamp=datetime.now(),
            environment=env,
            status="SUCCESS"
        )
    else:
        return BenchmarkResult(
            scenario_name=scenario_name,
            implementation_name=implementation_name,
            execution_times=[],
            memory_usage=[],
            min_time=0.0,
            median_time=0.0,
            mean_time=0.0,
            std_dev=0.0,
            relative_score=0.0,
            throughput=0.0,
            output_value=None,
            timestamp=datetime.now(),
            environment=env,
            status="ERROR",
            error_message="Mock implementation failure"
        )


# Hypothesis strategies for generating test data
@st.composite
def benchmark_results_strategy(draw):
    """Generate a list of benchmark results for testing."""
    # Generate scenario names
    scenarios = draw(st.lists(
        st.sampled_from(["Numeric: Prime Search", "Numeric: Matrix Multiplication", 
                        "Memory: Array Sort", "Memory: Array Filter"]),
        min_size=1, max_size=4, unique=True
    ))
    
    # Generate implementation names (mix of extension and FFI)
    extension_impls = ["python", "numpy_impl", "c_ext", "cpp_ext"]
    ffi_impls = ["c_ffi", "cpp_ffi", "numpy_ffi", "rust_ffi"]
    
    implementations = draw(st.lists(
        st.sampled_from(extension_impls + ffi_impls),
        min_size=2, max_size=6, unique=True
    ))
    
    # Ensure we have at least one python implementation for baseline
    if "python" not in implementations:
        implementations = ["python"] + implementations
    
    results = []
    for scenario in scenarios:
        for impl in implementations:
            # Most results should be successful
            success = draw(st.booleans().filter(lambda x: x or len([r for r in results if r.status == "SUCCESS"]) > 0))
            execution_time = draw(st.floats(min_value=1.0, max_value=1000.0))
            
            result = create_mock_benchmark_result(scenario, impl, success, execution_time)
            results.append(result)
    
    return results


class TestFFIBenchmarkIntegrationProperty:
    """Property-based tests for FFI benchmark integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_writer = OutputWriter(str(self.temp_dir))
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @given(benchmark_results_strategy())
    @settings(max_examples=20, deadline=30000)
    def test_result_file_generation_property(self, results: List[BenchmarkResult]):
        """
        **Feature: ffi-benchmark-extensions, Property 9: 結果ファイル生成**
        **Validates: Requirements 15.1**
        
        Property: For any valid benchmark results, the output system generates
        appropriate result files in the expected formats and locations.
        """
        assume(len(results) > 0)
        assume(any(r.status == "SUCCESS" for r in results))
        
        # Test standard JSON output
        json_path = self.output_writer.write_json(results, "test_benchmark")
        json_file = Path(json_path)
        
        assert json_file.exists(), "JSON result file should be generated"
        assert json_file.suffix == ".json", "JSON file should have .json extension"
        assert json_file.stat().st_size > 0, "JSON file should not be empty"
        
        # Test standard CSV output
        csv_path = self.output_writer.write_csv(results, "test_benchmark")
        csv_file = Path(csv_path)
        
        assert csv_file.exists(), "CSV result file should be generated"
        assert csv_file.suffix == ".csv", "CSV file should have .csv extension"
        assert csv_file.stat().st_size > 0, "CSV file should not be empty"
        
        # Test comprehensive report
        comprehensive_path = self.output_writer.write_comprehensive_report(results, "test_benchmark")
        comprehensive_file = Path(comprehensive_path)
        
        assert comprehensive_file.exists(), "Comprehensive report should be generated"
        assert comprehensive_file.suffix == ".json", "Comprehensive report should be JSON"
        assert comprehensive_file.stat().st_size > 0, "Comprehensive report should not be empty"
        
        # If FFI implementations are present, test FFI-specific outputs
        has_ffi = any(r.implementation_name.endswith('_ffi') for r in results)
        if has_ffi:
            ffi_json_path = self.output_writer.write_ffi_comparison_report(results, "test_benchmark")
            ffi_json_file = Path(ffi_json_path)
            
            assert ffi_json_file.exists(), "FFI comparison report should be generated"
            assert ffi_json_file.suffix == ".json", "FFI comparison should be JSON"
            assert ffi_json_file.stat().st_size > 0, "FFI comparison should not be empty"
            
            ffi_csv_path = self.output_writer.write_ffi_csv_comparison(results, "test_benchmark")
            ffi_csv_file = Path(ffi_csv_path)
            
            assert ffi_csv_file.exists(), "FFI CSV comparison should be generated"
            assert ffi_csv_file.suffix == ".csv", "FFI CSV should have .csv extension"
            assert ffi_csv_file.stat().st_size > 0, "FFI CSV should not be empty"
    
    @given(benchmark_results_strategy())
    @settings(max_examples=15, deadline=30000)
    def test_result_file_content_validity_property(self, results: List[BenchmarkResult]):
        """
        Property: Generated result files contain valid, parseable content
        that accurately represents the benchmark results.
        """
        assume(len(results) > 0)
        
        # Generate files
        json_path = self.output_writer.write_json(results, "test_content")
        csv_path = self.output_writer.write_csv(results, "test_content")
        
        # Test JSON content validity
        import json
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        assert 'results' in json_data, "JSON should contain results section"
        assert 'summary' in json_data, "JSON should contain summary section"
        assert len(json_data['results']) == len(results), "JSON should contain all results"
        
        # Test CSV content validity
        import csv as csv_module
        with open(csv_path, 'r') as f:
            csv_reader = csv_module.DictReader(f)
            csv_rows = list(csv_reader)
        
        assert len(csv_rows) == len(results), "CSV should contain all results"
        
        # Verify required columns exist
        required_columns = [
            'scenario_name', 'implementation_name', 'mean_time',
            'status', 'timestamp'
        ]
        
        if csv_rows:
            for col in required_columns:
                assert col in csv_rows[0], f"CSV should contain {col} column"
    
    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5, unique=True))
    @settings(max_examples=10, deadline=15000)
    def test_file_naming_consistency_property(self, filenames: List[str]):
        """
        Property: File naming is consistent and predictable across different
        output formats for the same benchmark run.
        """
        # Create minimal results for testing
        results = [create_mock_benchmark_result("Test Scenario", "python", True, 10.0)]
        
        for filename in filenames:
            # Clean filename for filesystem compatibility
            clean_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
            if not clean_filename:
                clean_filename = "test"
            
            json_path = self.output_writer.write_json(results, clean_filename)
            csv_path = self.output_writer.write_csv(results, clean_filename)
            
            json_file = Path(json_path)
            csv_file = Path(csv_path)
            
            # Files should exist
            assert json_file.exists(), f"JSON file should exist for filename: {clean_filename}"
            assert csv_file.exists(), f"CSV file should exist for filename: {clean_filename}"
            
            # Files should have consistent base names
            assert json_file.stem == f"{clean_filename}", "JSON file should have correct base name"
            assert csv_file.stem == f"{clean_filename}", "CSV file should have correct base name"
            
            # Files should be in correct directories
            assert json_file.parent.name == "json", "JSON file should be in json directory"
            assert csv_file.parent.name == "csv", "CSV file should be in csv directory"
    
    def test_ffi_comparison_report_structure_property(self):
        """
        Property: FFI comparison reports have the expected structure and
        contain appropriate comparison data when FFI implementations are present.
        """
        # Create results with both extension and FFI implementations
        results = [
            create_mock_benchmark_result("Numeric: Prime Search", "python", True, 100.0),
            create_mock_benchmark_result("Numeric: Prime Search", "c_ffi", True, 10.0),
            create_mock_benchmark_result("Numeric: Prime Search", "rust_ffi", True, 8.0),
            create_mock_benchmark_result("Memory: Array Sort", "python", True, 200.0),
            create_mock_benchmark_result("Memory: Array Sort", "c_ffi", True, 20.0),
        ]
        
        ffi_json_path = self.output_writer.write_ffi_comparison_report(results, "test_ffi")
        
        # Load and verify structure
        import json
        with open(ffi_json_path, 'r') as f:
            ffi_data = json.load(f)
        
        # Check required top-level sections
        required_sections = [
            'metadata', 'scenario_comparisons', 'overall_statistics',
            'performance_rankings', 'language_effectiveness'
        ]
        
        for section in required_sections:
            assert section in ffi_data, f"FFI report should contain {section} section"
        
        # Check scenario comparisons structure
        scenario_comparisons = ffi_data['scenario_comparisons']
        assert len(scenario_comparisons) > 0, "Should have scenario comparisons"
        
        for scenario_name, comparison in scenario_comparisons.items():
            assert 'pure_python' in comparison, "Should have pure_python section"
            assert 'ffi_implementations' in comparison, "Should have ffi_implementations section"
            assert 'speedup_analysis' in comparison, "Should have speedup_analysis section"
        
        # Check that speedup ratios are calculated
        for scenario_name, comparison in scenario_comparisons.items():
            if comparison['ffi_implementations']:
                for impl_name, impl_data in comparison['ffi_implementations'].items():
                    assert 'speedup_ratio' in impl_data, "Should have speedup ratio"
                    assert impl_data['speedup_ratio'] > 0, "Speedup ratio should be positive"
    
    def test_error_handling_in_result_generation_property(self):
        """
        Property: Result file generation handles error cases gracefully
        and produces valid output even when some benchmark results contain errors.
        """
        # Create mixed results (some successful, some failed)
        results = [
            create_mock_benchmark_result("Test Scenario 1", "python", True, 50.0),
            create_mock_benchmark_result("Test Scenario 1", "c_ffi", False, 0.0),  # Failed
            create_mock_benchmark_result("Test Scenario 2", "python", True, 75.0),
            create_mock_benchmark_result("Test Scenario 2", "rust_ffi", True, 15.0),
        ]
        
        # Should not raise exceptions
        json_path = self.output_writer.write_json(results, "test_errors")
        csv_path = self.output_writer.write_csv(results, "test_errors")
        comprehensive_path = self.output_writer.write_comprehensive_report(results, "test_errors")
        
        # Files should be generated
        assert Path(json_path).exists(), "JSON should be generated despite errors"
        assert Path(csv_path).exists(), "CSV should be generated despite errors"
        assert Path(comprehensive_path).exists(), "Comprehensive report should be generated despite errors"
        
        # Content should be valid
        import json
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        assert len(json_data['results']) == len(results), "All results should be included"
        
        # Failed results should be marked appropriately
        failed_results = [r for r in json_data['results'] if r['status'] == 'ERROR']
        assert len(failed_results) == 1, "Should have one failed result"
        assert failed_results[0]['error_message'] is not None, "Failed result should have error message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])