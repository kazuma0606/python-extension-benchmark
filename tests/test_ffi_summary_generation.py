#!/usr/bin/env python3
"""
Test FFI Summary Generation

Unit tests for FFI summary generation functionality.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.models import BenchmarkResult, EnvironmentInfo, ValidationResult
from benchmark.runner.ffi_summary_generator import FFISummaryGenerator
from benchmark.runner.ffi_visualizer import FFIVisualizer
from benchmark.runner.ffi_statistical_analyzer import FFIStatisticalAnalyzer
from benchmark.runner.ffi_technology_advisor import FFITechnologyAdvisor


class TestFFISummaryGeneration:
    """Test FFI summary generation functionality."""
    
    def create_mock_results(self) -> list:
        """Create mock benchmark results for testing."""
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
        
        # Pure Python baseline
        results.append(BenchmarkResult(
            scenario_name="find_primes",
            implementation_name="python",
            execution_times=[100.0] * 100,  # 100ms baseline
            memory_usage=[50.0] * 100,
            min_time=95.0,
            median_time=100.0,
            mean_time=100.0,
            std_dev=5.0,
            relative_score=1.0,
            throughput=10.0,
            output_value=[2, 3, 5, 7, 11],
            timestamp=datetime.now(),
            environment=env,
            validation=validation,
            status="SUCCESS"
        ))
        
        # FFI implementations with different performance characteristics
        ffi_implementations = [
            ("c_ffi", 20.0, 5.0),      # 5x speedup, consistent
            ("cpp_ffi", 18.0, 3.0),    # 5.5x speedup, very consistent
            ("rust_ffi", 15.0, 2.0),   # 6.7x speedup, extremely consistent
            ("cython_ffi", 25.0, 8.0), # 4x speedup, less consistent
            ("julia_ffi", 30.0, 10.0), # 3.3x speedup, variable
        ]
        
        for impl_name, mean_time, std_dev in ffi_implementations:
            results.append(BenchmarkResult(
                scenario_name="find_primes",
                implementation_name=impl_name,
                execution_times=[mean_time] * 100,
                memory_usage=[30.0] * 100,
                min_time=mean_time - std_dev,
                median_time=mean_time,
                mean_time=mean_time,
                std_dev=std_dev,
                relative_score=100.0 / mean_time,  # Relative to Python
                throughput=1000.0 / mean_time,
                output_value=[2, 3, 5, 7, 11],
                timestamp=datetime.now(),
                environment=env,
                validation=validation,
                status="SUCCESS"
            ))
        
        # Add another scenario
        for impl_name, base_time, base_std in [("python", 200.0, 10.0)] + ffi_implementations:
            mean_time = base_time * 2 if impl_name == "python" else base_time * 1.5
            std_dev = base_std * 1.5
            
            results.append(BenchmarkResult(
                scenario_name="matrix_multiply",
                implementation_name=impl_name,
                execution_times=[mean_time] * 100,
                memory_usage=[80.0] * 100,
                min_time=mean_time - std_dev,
                median_time=mean_time,
                mean_time=mean_time,
                std_dev=std_dev,
                relative_score=200.0 / mean_time if impl_name != "python" else 1.0,
                throughput=2000.0 / mean_time,
                output_value=[[1, 2], [3, 4]],
                timestamp=datetime.now(),
                environment=env,
                validation=validation,
                status="SUCCESS"
            ))
        
        return results
    
    def test_ffi_summary_generator_initialization(self):
        """Test FFI summary generator initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = FFISummaryGenerator(output_dir=temp_dir)
            
            assert generator.output_dir == Path(temp_dir)
            assert isinstance(generator.visualizer, FFIVisualizer)
            assert isinstance(generator.statistical_analyzer, FFIStatisticalAnalyzer)
            assert isinstance(generator.technology_advisor, FFITechnologyAdvisor)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_comprehensive_summary_generation(self, mock_close, mock_savefig):
        """Test comprehensive FFI summary generation."""
        results = self.create_mock_results()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            generator = FFISummaryGenerator(output_dir=temp_dir)
            
            # Mock visualization methods to avoid matplotlib issues in tests
            generator.visualizer.generate_speedup_comparison_chart = Mock(return_value=f"{temp_dir}/speedup.png")
            generator.visualizer.generate_performance_distribution_chart = Mock(return_value=f"{temp_dir}/distribution.png")
            generator.visualizer.generate_language_characteristics_chart = Mock(return_value=f"{temp_dir}/characteristics.png")
            
            report_path = generator.generate_comprehensive_ffi_summary(results)
            
            # Verify report was created
            assert Path(report_path).exists()
            
            # Read and verify report content
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for key sections
            assert "# FFI Benchmark Results Summary" in content
            assert "## Executive Summary" in content
            assert "## Performance Analysis" in content
            assert "## Language-Specific Analysis" in content
            assert "## Statistical Analysis" in content
            assert "## Technology Selection Guide" in content
            assert "## Implementation Recommendations" in content
            
            # Check for specific data
            assert "find_primes" in content
            assert "matrix_multiply" in content
            assert "C" in content  # Language names, not implementation names
            assert "Rust" in content
            
            # Verify visualization methods were called
            generator.visualizer.generate_speedup_comparison_chart.assert_called_once()
            generator.visualizer.generate_performance_distribution_chart.assert_called_once()
            generator.visualizer.generate_language_characteristics_chart.assert_called_once()
    
    def test_statistical_analysis_integration(self):
        """Test statistical analysis integration."""
        results = self.create_mock_results()
        
        analyzer = FFIStatisticalAnalyzer()
        report = analyzer.analyze_ffi_performance(results)
        
        # Verify statistical report structure
        assert report.total_comparisons > 0
        assert len(report.languages_analyzed) > 0
        assert len(report.scenarios_analyzed) > 0
        assert report.overall_speedup_stats is not None
        assert len(report.significance_tests) > 0
        assert report.outlier_analysis is not None
        
        # Verify language comparisons
        assert "C" in report.language_comparisons
        assert "Rust" in report.language_comparisons
        
        # Verify scenario comparisons
        assert "find_primes" in report.scenario_comparisons
        assert "matrix_multiply" in report.scenario_comparisons
    
    def test_technology_advisor_integration(self):
        """Test technology advisor integration."""
        results = self.create_mock_results()
        
        advisor = FFITechnologyAdvisor()
        matrix = advisor.generate_technology_matrix(results)
        
        # Verify technology matrix structure
        assert matrix.timestamp is not None
        assert len(matrix.technology_profiles) > 0
        assert len(matrix.use_case_recommendations) > 0
        assert len(matrix.performance_ranking) > 0
        assert len(matrix.ease_of_use_ranking) > 0
        assert len(matrix.reliability_ranking) > 0
        
        # Verify technology profiles
        assert "C" in matrix.technology_profiles
        assert "Rust" in matrix.technology_profiles
        
        # Verify use case recommendations exist
        from benchmark.runner.ffi_technology_advisor import UseCase
        assert UseCase.PROTOTYPING in matrix.use_case_recommendations
        assert UseCase.PRODUCTION_PERFORMANCE in matrix.use_case_recommendations
    
    def test_error_handling_with_insufficient_data(self):
        """Test error handling with insufficient data."""
        # Create minimal results (no FFI implementations)
        env = EnvironmentInfo("Linux", "CPU", 16.0, "3.11.0", False)
        results = [BenchmarkResult(
            scenario_name="test",
            implementation_name="python",
            execution_times=[100.0],
            memory_usage=[50.0],
            min_time=100.0,
            median_time=100.0,
            mean_time=100.0,
            std_dev=0.0,
            relative_score=1.0,
            throughput=10.0,
            output_value=None,
            timestamp=datetime.now(),
            environment=env,
            status="SUCCESS"
        )]
        
        analyzer = FFIStatisticalAnalyzer()
        
        # Should raise ValueError for insufficient data
        with pytest.raises(ValueError):
            analyzer.analyze_ffi_performance(results)
    
    def test_performance_categorization(self):
        """Test performance categorization logic."""
        generator = FFISummaryGenerator()
        
        # Test performance insight generation
        assert "Exceptional" in generator._get_performance_insight(15.0)
        assert "Excellent" in generator._get_performance_insight(7.0)
        assert "Good" in generator._get_performance_insight(3.0)
        assert "Moderate" in generator._get_performance_insight(1.5)
        
        # Test consistency rating
        assert generator._rate_consistency_simple(0.05) == "Excellent"
        assert generator._rate_consistency_simple(0.15) == "Good"
        assert generator._rate_consistency_simple(0.25) == "Fair"
        assert generator._rate_consistency_simple(0.5) == "Poor"
    
    def test_ffi_implementation_detection(self):
        """Test FFI implementation detection."""
        generator = FFISummaryGenerator()
        
        assert generator._is_ffi_implementation("c_ffi")
        assert generator._is_ffi_implementation("rust_ffi")
        assert generator._is_ffi_implementation("julia_ffi")
        assert not generator._is_ffi_implementation("python")
        assert not generator._is_ffi_implementation("numpy_impl")
        assert not generator._is_ffi_implementation("c_ext")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])