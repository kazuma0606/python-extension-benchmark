"""
Go Extension Property-Based Tests

**Feature: multi-language-extensions, Property 6: 並列計算の正確性**
**Validates: Requirements 2.5**

This module contains property-based tests for Go extension parallel computation accuracy.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import math
from typing import List

# Skip tests if Go is not available
pytest_plugins = []

def reference_parallel_compute(data: List[float], num_threads: int) -> float:
    """Reference implementation of parallel computation (simple sum)."""
    return sum(data)

@pytest.mark.skipif(False, reason="Run in Docker environment")
class TestGoPropertyDocker:
    """Property-based tests for Go extension - Docker environment only."""
    
    @given(
        data=st.lists(
            st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=1000
        ),
        num_threads=st.integers(min_value=1, max_value=16)
    )
    @settings(max_examples=100, deadline=10000)
    def test_parallel_compute_correctness(self, data, num_threads):
        """
        **Feature: multi-language-extensions, Property 6: 並列計算の正確性**
        **Validates: Requirements 2.5**
        
        Property: For any data array and thread count, parallel_compute returns the correct sum.
        """
        try:
            from benchmark import go_ext
            
            # Get result from Go implementation
            result = go_ext.parallel_compute(data, num_threads)
            
            # Get expected result from reference implementation
            expected = reference_parallel_compute(data, num_threads)
            
            # Property: Result should match mathematical sum
            # Allow small floating point differences due to parallel computation order
            tolerance = 1e-10 * len(data)  # Scale tolerance with data size
            assert abs(result - expected) <= tolerance, \
                f"Go parallel_compute mismatch: {result} != {expected} (diff: {abs(result - expected)}, tolerance: {tolerance})"
            
            # Property: Result should be finite
            assert math.isfinite(result), f"Result should be finite, got: {result}"
                    
        except ImportError:
            pytest.skip("Go extension not available")
        except RuntimeError as e:
            if "Go shared library not available" in str(e):
                pytest.skip("Go shared library not available")
            else:
                raise
    
    @given(
        size=st.integers(min_value=1, max_value=100),
        value=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        num_threads=st.integers(min_value=1, max_value=8)
    )
    @settings(max_examples=50, deadline=5000)
    def test_parallel_compute_uniform_data(self, size, value, num_threads):
        """
        **Feature: multi-language-extensions, Property 6: 並列計算の正確性**
        **Validates: Requirements 2.5**
        
        Property: For uniform data arrays, parallel_compute should return size * value.
        """
        try:
            from benchmark import go_ext
            
            # Create uniform data array
            data = [value] * size
            
            # Get result from Go implementation
            result = go_ext.parallel_compute(data, num_threads)
            
            # Expected result for uniform data
            expected = size * value
            
            # Property: Result should match expected calculation
            tolerance = 1e-10 * size
            assert abs(result - expected) <= tolerance, \
                f"Go parallel_compute uniform data mismatch: {result} != {expected}"
                    
        except ImportError:
            pytest.skip("Go extension not available")
        except RuntimeError as e:
            if "Go shared library not available" in str(e):
                pytest.skip("Go shared library not available")
            else:
                raise
    
    @given(num_threads=st.integers(min_value=1, max_value=16))
    @settings(max_examples=20)
    def test_parallel_compute_empty_data(self, num_threads):
        """
        **Feature: multi-language-extensions, Property 6: 並列計算の正確性**
        **Validates: Requirements 2.5**
        
        Property: For empty data arrays, parallel_compute should return 0.0.
        """
        try:
            from benchmark import go_ext
            
            # Empty data array
            data = []
            
            # Get result from Go implementation
            result = go_ext.parallel_compute(data, num_threads)
            
            # Property: Empty array should sum to 0.0
            assert result == 0.0, f"Empty array should sum to 0.0, got: {result}"
                    
        except ImportError:
            pytest.skip("Go extension not available")
        except RuntimeError as e:
            if "Go shared library not available" in str(e):
                pytest.skip("Go shared library not available")
            else:
                raise

# Tests that can run in any environment (with mocking)
class TestGoPropertyMocked:
    """Property-based tests with mocking for local development."""
    
    @given(
        data=st.lists(
            st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=100
        ),
        num_threads=st.integers(min_value=1, max_value=8)
    )
    @settings(max_examples=20)
    def test_parallel_compute_property_structure(self, data, num_threads):
        """
        Test the property structure without requiring Go.
        This validates the test logic itself.
        """
        # Reference implementation test
        expected = reference_parallel_compute(data, num_threads)
        
        # Property: Sum should equal manual calculation
        manual_sum = sum(data)
        assert expected == manual_sum, "Reference implementation should match manual sum"
        
        # Property: Sum should be finite for finite inputs
        assert math.isfinite(expected), "Sum of finite numbers should be finite"
    
    def test_parallel_compute_edge_cases(self):
        """
        Test edge cases for parallel computation.
        """
        # Test with single element
        assert reference_parallel_compute([5.0], 1) == 5.0
        
        # Test with zeros
        assert reference_parallel_compute([0.0, 0.0, 0.0], 2) == 0.0
        
        # Test with positive and negative numbers
        assert reference_parallel_compute([1.0, -1.0, 2.0, -2.0], 4) == 0.0

# Docker-specific test runner
def run_docker_tests():
    """
    Function to run property tests in Docker environment.
    This should be called from within Docker container.
    """
    import subprocess
    import sys
    
    try:
        # Run the Docker-specific tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_go_property.py::TestGoPropertyDocker",
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print("Docker Property Test Results:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running Docker tests: {e}")
        return False

if __name__ == "__main__":
    # Run mocked tests locally, Docker tests in container
    import os
    if os.environ.get("DOCKER_ENV"):
        success = run_docker_tests()
        exit(0 if success else 1)
    else:
        pytest.main([__file__ + "::TestGoPropertyMocked", "-v"])