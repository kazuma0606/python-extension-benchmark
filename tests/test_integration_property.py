"""
Integration Property-Based Tests

**Feature: multi-language-extensions, Property 7: ベンチマーク実行の完全性**
**Feature: multi-language-extensions, Property 8: エラー時の継続実行**
**Validates: Requirements 6.1, 9.1**

This module contains property-based tests for integration scenarios:
- Property 7: Benchmark execution completeness across all available implementations
- Property 8: Error recovery and continuation when implementations fail
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import tempfile
import os
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import get_all_scenarios, get_default_implementations, NumericScenario
from benchmark.models import BenchmarkResult, Implementation, EnvironmentInfo
from benchmark.runner.error_handler import ErrorHandler
from datetime import datetime


class TestIntegrationProperties:
    """Integration property-based tests for multi-language extensions."""
    
    @given(
        available_implementations=st.lists(
            st.sampled_from(get_default_implementations()),
            min_size=1,
            max_size=12,
            unique=True
        )
    )
    @settings(max_examples=50, deadline=10000)
    def test_benchmark_execution_completeness_property(self, available_implementations):
        """
        **Feature: multi-language-extensions, Property 7: ベンチマーク実行の完全性**
        **Validates: Requirements 6.1**
        
        Property: For all available language implementations, benchmark scenarios are executed 
        and results are recorded.
        """
        # Create a mock runner with controlled available implementations
        runner = BenchmarkRunner()
        
        # Mock the get_all_available_implementations to return our test set
        with patch.object(runner, 'get_all_available_implementations', return_value=available_implementations):
            # Mock load_implementations to return mock implementations
            mock_implementations = []
            for impl_name in available_implementations:
                mock_module = Mock()
                # Mock the required functions with simple implementations
                mock_module.find_primes = Mock(return_value=[2, 3, 5, 7])
                mock_module.matrix_multiply = Mock(return_value=[[1.0, 2.0], [3.0, 4.0]])
                mock_module.sort_array = Mock(return_value=[1, 2, 3, 4, 5])
                mock_module.filter_array = Mock(return_value=[3, 4, 5])
                mock_module.parallel_compute = Mock(return_value=15.0)
                
                mock_impl = Implementation(
                    name=impl_name,
                    module=mock_module,
                    language=impl_name.replace('_ext', '').replace('_impl', '').title()
                )
                mock_implementations.append(mock_impl)
            
            with patch.object(runner, 'load_implementations', return_value=mock_implementations):
                # Use a lightweight scenario for testing
                test_scenario = NumericScenario("primes")
                test_scenario.input_data = 10  # Small input for fast execution
                
                # Execute benchmark
                results = runner.run_scenario(test_scenario, mock_implementations, warmup_runs=1, measurement_runs=3)
                
                # Property 7: All available implementations should have results recorded
                result_impl_names = {result.implementation_name for result in results}
                available_impl_names = set(available_implementations)
                
                assert result_impl_names == available_impl_names, \
                    f"Missing results for implementations: {available_impl_names - result_impl_names}"
                
                # Property 7: Each result should have the required fields
                for result in results:
                    assert result.scenario_name == test_scenario.name
                    assert result.implementation_name in available_implementations
                    assert isinstance(result.execution_times, list)
                    assert len(result.execution_times) > 0
                    assert result.status in ["SUCCESS", "ERROR"]
                    assert result.timestamp is not None
                    
                # Property 7: All successful results should have valid performance metrics
                successful_results = [r for r in results if r.status == "SUCCESS"]
                for result in successful_results:
                    assert result.min_time >= 0
                    assert result.mean_time >= 0
                    assert result.median_time >= 0
                    assert result.throughput >= 0
                    assert result.relative_score >= 0
    
    @given(
        total_implementations=st.lists(
            st.sampled_from(get_default_implementations()),
            min_size=3,
            max_size=8,
            unique=True
        ),
        failing_count=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=30, deadline=15000)
    def test_error_continuation_property(self, total_implementations, failing_count):
        """
        **Feature: multi-language-extensions, Property 8: エラー時の継続実行**
        **Validates: Requirements 9.1, 9.2, 9.3**
        
        Property: When any language implementation fails, other implementations continue to execute.
        """
        assume(failing_count < len(total_implementations))  # Ensure some implementations succeed
        
        runner = BenchmarkRunner()
        
        # Select which implementations will fail
        failing_implementations = total_implementations[:failing_count]
        working_implementations = total_implementations[failing_count:]
        
        # Create mock implementations
        mock_implementations = []
        
        # Create failing implementations
        for impl_name in failing_implementations:
            mock_module = Mock()
            # Make these implementations raise exceptions
            mock_module.find_primes = Mock(side_effect=RuntimeError(f"Simulated error in {impl_name}"))
            mock_module.matrix_multiply = Mock(side_effect=ImportError(f"Module not found for {impl_name}"))
            
            mock_impl = Implementation(
                name=impl_name,
                module=mock_module,
                language=impl_name.replace('_ext', '').replace('_impl', '').title()
            )
            mock_implementations.append(mock_impl)
        
        # Create working implementations
        for impl_name in working_implementations:
            mock_module = Mock()
            # Mock successful functions
            mock_module.find_primes = Mock(return_value=[2, 3, 5, 7])
            mock_module.matrix_multiply = Mock(return_value=[[1.0, 2.0], [3.0, 4.0]])
            
            mock_impl = Implementation(
                name=impl_name,
                module=mock_module,
                language=impl_name.replace('_ext', '').replace('_impl', '').title()
            )
            mock_implementations.append(mock_impl)
        
        # Use a lightweight scenario
        test_scenario = NumericScenario("primes")
        test_scenario.input_data = 10
        
        # Execute benchmark with mixed success/failure implementations
        results = runner.run_scenario(test_scenario, mock_implementations, warmup_runs=1, measurement_runs=2)
        
        # Property 8: All implementations should have results (success or error)
        assert len(results) == len(total_implementations), \
            f"Expected {len(total_implementations)} results, got {len(results)}"
        
        # Property 8: Failed implementations should have ERROR status
        error_results = [r for r in results if r.status == "ERROR"]
        success_results = [r for r in results if r.status == "SUCCESS"]
        
        assert len(error_results) == len(failing_implementations), \
            f"Expected {len(failing_implementations)} error results, got {len(error_results)}"
        
        # Property 8: Working implementations should have SUCCESS status
        assert len(success_results) == len(working_implementations), \
            f"Expected {len(working_implementations)} success results, got {len(success_results)}"
        
        # Property 8: Error results should contain error information
        for error_result in error_results:
            assert error_result.implementation_name in failing_implementations
            assert error_result.error_message is not None
            assert len(error_result.error_message) > 0
            
        # Property 8: Success results should have valid data
        for success_result in success_results:
            assert success_result.implementation_name in working_implementations
            assert len(success_result.execution_times) > 0
            assert success_result.output_value is not None
            
        # Property 8: Error handler should record errors
        assert runner.error_handler.has_errors(), "Error handler should record execution errors"
        
        error_stats = runner.error_handler.get_implementation_statistics()
        assert len(error_stats) >= len(failing_implementations), \
            "Error statistics should include all failing implementations"
    
    @given(
        scenario_count=st.integers(min_value=1, max_value=5),
        implementation_count=st.integers(min_value=2, max_value=6)
    )
    @settings(max_examples=20, deadline=20000)
    def test_comprehensive_benchmark_completeness_property(self, scenario_count, implementation_count):
        """
        **Feature: multi-language-extensions, Property 7: ベンチマーク実行の完全性**
        **Validates: Requirements 6.1**
        
        Property: For comprehensive benchmarks with multiple scenarios and implementations,
        all combinations are executed and results are complete.
        """
        runner = BenchmarkRunner()
        
        # Create test implementations
        available_implementations = get_default_implementations()[:implementation_count]
        
        # Create mock implementations
        mock_implementations = []
        for impl_name in available_implementations:
            mock_module = Mock()
            mock_module.find_primes = Mock(return_value=[2, 3, 5])
            mock_module.matrix_multiply = Mock(return_value=[[1.0]])
            mock_module.sort_array = Mock(return_value=[1, 2, 3])
            mock_module.filter_array = Mock(return_value=[2, 3])
            mock_module.parallel_compute = Mock(return_value=6.0)
            
            mock_impl = Implementation(
                name=impl_name,
                module=mock_module,
                language=impl_name.replace('_ext', '').replace('_impl', '').title()
            )
            mock_implementations.append(mock_impl)
        
        # Create test scenarios
        test_scenarios = []
        scenario_types = ["primes", "matrix"][:scenario_count]
        
        for scenario_type in scenario_types:
            scenario = NumericScenario(scenario_type)
            if scenario_type == "primes":
                scenario.input_data = 10
            else:  # matrix
                scenario.input_data = ([[1.0]], [[2.0]])
            test_scenarios.append(scenario)
        
        # Execute all scenarios
        all_results = []
        for scenario in test_scenarios:
            results = runner.run_scenario(scenario, mock_implementations, warmup_runs=1, measurement_runs=2)
            all_results.extend(results)
        
        # Property 7: Total results should equal scenarios × implementations
        expected_result_count = len(test_scenarios) * len(mock_implementations)
        assert len(all_results) == expected_result_count, \
            f"Expected {expected_result_count} results, got {len(all_results)}"
        
        # Property 7: Each scenario-implementation combination should have a result
        scenario_impl_combinations = set()
        for result in all_results:
            combination = (result.scenario_name, result.implementation_name)
            scenario_impl_combinations.add(combination)
        
        expected_combinations = set()
        for scenario in test_scenarios:
            for impl in mock_implementations:
                expected_combinations.add((scenario.name, impl.name))
        
        assert scenario_impl_combinations == expected_combinations, \
            f"Missing combinations: {expected_combinations - scenario_impl_combinations}"
        
        # Property 7: All results should have consistent structure
        for result in all_results:
            assert hasattr(result, 'scenario_name')
            assert hasattr(result, 'implementation_name')
            assert hasattr(result, 'status')
            assert hasattr(result, 'timestamp')
            assert hasattr(result, 'execution_times')
            assert result.status in ["SUCCESS", "ERROR"]
    
    def test_error_handler_isolation_property(self):
        """
        **Feature: multi-language-extensions, Property 8: エラー時の継続実行**
        **Validates: Requirements 9.1**
        
        Property: Error handler properly isolates failures and maintains error logs.
        """
        error_handler = ErrorHandler()
        
        # Simulate various types of errors
        import_error = ImportError("Module not found")
        runtime_error = RuntimeError("Execution failed")
        
        # Handle import error
        import_log = error_handler.handle_import_error("test_impl_1", import_error)
        
        # Handle execution error
        exec_log = error_handler.handle_execution_error("test_impl_2", "test_scenario", runtime_error)
        
        # Property 8: Error handler should record all errors
        assert error_handler.has_errors()
        assert len(error_handler.error_logs) == 2
        
        # Property 8: Error logs should contain proper information
        assert import_log.implementation_name == "test_impl_1"
        assert import_log.error_type == "ImportError"
        assert "Module not found" in import_log.error_message
        
        assert exec_log.implementation_name == "test_impl_2"
        assert exec_log.scenario_name == "test_scenario"
        assert exec_log.error_type == "RuntimeError"
        assert "Execution failed" in exec_log.error_message
        
        # Property 8: Statistics should be accurate
        stats = error_handler.get_implementation_statistics()
        assert "test_impl_1" in stats
        assert "test_impl_2" in stats
        assert stats["test_impl_1"]["import_errors"] == 1
        assert stats["test_impl_2"]["execution_errors"] == 1


# Lightweight test runner for CI/CD environments
class TestIntegrationPropertiesLightweight:
    """Lightweight integration property tests for CI/CD environments."""
    
    def test_benchmark_completeness_minimal(self):
        """Minimal test for benchmark completeness property."""
        runner = BenchmarkRunner()
        
        # Test with just Python implementation (always available)
        mock_module = Mock()
        mock_module.find_primes = Mock(return_value=[2, 3, 5])
        
        mock_impl = Implementation(
            name="python",
            module=mock_module,
            language="Python"
        )
        
        scenario = NumericScenario("primes")
        scenario.input_data = 5
        
        results = runner.run_scenario(scenario, [mock_impl], warmup_runs=1, measurement_runs=1)
        
        # Property 7: Result should be generated
        assert len(results) == 1
        assert results[0].implementation_name == "python"
        assert results[0].status == "SUCCESS"
    
    def test_error_continuation_minimal(self):
        """Minimal test for error continuation property."""
        runner = BenchmarkRunner()
        
        # Create one failing and one working implementation
        failing_module = Mock()
        failing_module.find_primes = Mock(side_effect=RuntimeError("Test error"))
        
        working_module = Mock()
        working_module.find_primes = Mock(return_value=[2, 3])
        
        failing_impl = Implementation(name="failing", module=failing_module, language="Test")
        working_impl = Implementation(name="working", module=working_module, language="Test")
        
        scenario = NumericScenario("primes")
        scenario.input_data = 5
        
        results = runner.run_scenario(scenario, [failing_impl, working_impl], warmup_runs=1, measurement_runs=1)
        
        # Property 8: Both implementations should have results
        assert len(results) == 2
        
        error_result = next(r for r in results if r.implementation_name == "failing")
        success_result = next(r for r in results if r.implementation_name == "working")
        
        assert error_result.status == "ERROR"
        assert success_result.status == "SUCCESS"


if __name__ == "__main__":
    # Run lightweight tests for local development
    pytest.main([__file__ + "::TestIntegrationPropertiesLightweight", "-v"])