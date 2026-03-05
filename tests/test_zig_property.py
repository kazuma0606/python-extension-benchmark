"""
Zig Extension Property-Based Tests

**Feature: multi-language-extensions, Property 4: ソート結果の正確性**
**Validates: Requirements 3.4**

This module contains property-based tests for Zig extension sort result correctness.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import math
from typing import List

# Skip tests if Zig is not available
pytest_plugins = []

def sort_array_reference(arr: List[int]) -> List[int]:
    """Reference implementation of array sorting."""
    return sorted(arr)

def is_sorted_ascending(arr: List[int]) -> bool:
    """Check if array is sorted in ascending order."""
    for i in range(1, len(arr)):
        if arr[i] < arr[i-1]:
            return False
    return True

def has_same_elements(arr1: List[int], arr2: List[int]) -> bool:
    """Check if two arrays contain the same elements (with same frequencies)."""
    from collections import Counter
    return Counter(arr1) == Counter(arr2)

@pytest.mark.skipif(False, reason="Run in Docker environment")
class TestZigPropertyDocker:
    """Property-based tests for Zig extension - Docker environment only."""
    
    @given(arr=st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=1000))
    @settings(max_examples=100, deadline=5000)
    def test_sort_array_correctness(self, arr):
        """
        **Feature: multi-language-extensions, Property 4: ソート結果の正確性**
        **Validates: Requirements 3.4**
        
        Property: For any array, sort_array(arr) returns the elements in ascending order 
        with the same elements as the original array.
        """
        try:
            from benchmark import zig_ext
            
            # Skip if Zig is not available
            if not zig_ext.is_available():
                pytest.skip("Zig extension not available")
            
            # Get result from Zig implementation
            result = zig_ext.sort_array(arr)
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            elif isinstance(result, list):
                result = [int(x) for x in result]
            
            # Get expected result from reference implementation
            expected = sort_array_reference(arr)
            
            # Property 1: Result should be sorted in ascending order
            assert is_sorted_ascending(result), f"Zig sort result is not sorted: {result}"
            
            # Property 2: Result should contain the same elements as input
            assert has_same_elements(result, arr), \
                f"Zig sort changed elements. Input: {arr}, Output: {result}"
            
            # Property 3: Result should match reference implementation
            assert result == expected, \
                f"Zig sort mismatch. Input: {arr}, Got: {result}, Expected: {expected}"
            
            # Property 4: Length should be preserved
            assert len(result) == len(arr), \
                f"Zig sort changed array length. Input length: {len(arr)}, Output length: {len(result)}"
                
        except ImportError:
            pytest.skip("Zig extension not available")
    
    @given(arr=st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=100))
    @settings(max_examples=50, deadline=5000)
    def test_sort_array_stability_properties(self, arr):
        """
        **Feature: multi-language-extensions, Property 4: ソート結果の正確性**
        **Validates: Requirements 3.4**
        
        Additional properties for sort correctness: idempotence and boundary conditions.
        """
        try:
            from benchmark import zig_ext
            
            # Skip if Zig is not available
            if not zig_ext.is_available():
                pytest.skip("Zig extension not available")
            
            # Get result from Zig implementation
            result = zig_ext.sort_array(arr)
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            elif isinstance(result, list):
                result = [int(x) for x in result]
            
            # Property: Sorting an already sorted array should be idempotent
            result_twice = zig_ext.sort_array(result)
            if hasattr(result_twice, 'tolist'):
                result_twice = result_twice.tolist()
            elif isinstance(result_twice, list):
                result_twice = [int(x) for x in result_twice]
            
            assert result == result_twice, \
                f"Zig sort is not idempotent. First sort: {result}, Second sort: {result_twice}"
            
            # Property: Minimum element should be first (if array is non-empty)
            if result:
                assert result[0] == min(arr), \
                    f"Minimum element not first. Array: {arr}, Sorted: {result}, Min: {min(arr)}"
            
            # Property: Maximum element should be last (if array is non-empty)
            if result:
                assert result[-1] == max(arr), \
                    f"Maximum element not last. Array: {arr}, Sorted: {result}, Max: {max(arr)}"
                
        except ImportError:
            pytest.skip("Zig extension not available")

# Edge case tests
@pytest.mark.skipif(False, reason="Run in Docker environment")
class TestZigPropertyEdgeCases:
    """Property-based tests for edge cases."""
    
    def test_sort_empty_array(self):
        """Test sorting empty array."""
        try:
            from benchmark import zig_ext
            
            if not zig_ext.is_available():
                pytest.skip("Zig extension not available")
            
            result = zig_ext.sort_array([])
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            
            assert result == [], f"Empty array sort failed: {result}"
            
        except ImportError:
            pytest.skip("Zig extension not available")
    
    def test_sort_single_element(self):
        """Test sorting single element array."""
        try:
            from benchmark import zig_ext
            
            if not zig_ext.is_available():
                pytest.skip("Zig extension not available")
            
            test_cases = [[42], [0], [-1], [1000], [-1000]]
            
            for arr in test_cases:
                result = zig_ext.sort_array(arr)
                
                # Convert numpy types to Python types if needed
                if hasattr(result, 'tolist'):
                    result = result.tolist()
                elif isinstance(result, list):
                    result = [int(x) for x in result]
                
                assert result == arr, f"Single element sort failed for {arr}: {result}"
                
        except ImportError:
            pytest.skip("Zig extension not available")
    
    @given(value=st.integers(min_value=-1000, max_value=1000), 
           count=st.integers(min_value=2, max_value=100))
    @settings(max_examples=20, deadline=3000)
    def test_sort_duplicate_elements(self, value, count):
        """Test sorting arrays with duplicate elements."""
        try:
            from benchmark import zig_ext
            
            if not zig_ext.is_available():
                pytest.skip("Zig extension not available")
            
            # Create array with all same elements
            arr = [value] * count
            result = zig_ext.sort_array(arr)
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            elif isinstance(result, list):
                result = [int(x) for x in result]
            
            # All elements should remain the same
            assert result == arr, f"Duplicate element sort failed for {arr}: {result}"
            assert len(result) == count, f"Length changed for duplicates: {len(result)} != {count}"
            
        except ImportError:
            pytest.skip("Zig extension not available")

# Tests that can run in any environment (with mocking)
class TestZigPropertyMocked:
    """Property-based tests with mocking for local development."""
    
    @given(arr=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=50))
    @settings(max_examples=20)
    def test_sort_array_property_structure(self, arr):
        """
        Test the property structure without requiring Zig.
        This validates the test logic itself.
        """
        # Reference implementation test
        expected = sort_array_reference(arr)
        
        # Property: Result should be sorted
        assert is_sorted_ascending(expected), "Reference implementation should produce sorted result"
        
        # Property: Same elements
        assert has_same_elements(expected, arr), "Reference implementation should preserve elements"
        
        # Property: Length preservation
        assert len(expected) == len(arr), "Reference implementation should preserve length"
    
    def test_helper_functions(self):
        """Test helper functions used in properties."""
        # Test is_sorted_ascending
        assert is_sorted_ascending([])
        assert is_sorted_ascending([1])
        assert is_sorted_ascending([1, 2, 3])
        assert is_sorted_ascending([1, 1, 1])
        assert not is_sorted_ascending([3, 2, 1])
        assert not is_sorted_ascending([1, 3, 2])
        
        # Test has_same_elements
        assert has_same_elements([], [])
        assert has_same_elements([1, 2, 3], [3, 1, 2])
        assert has_same_elements([1, 1, 2], [2, 1, 1])
        assert not has_same_elements([1, 2], [1, 2, 3])
        assert not has_same_elements([1, 1], [1, 2])

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
            "tests/test_zig_property.py::TestZigPropertyDocker",
            "tests/test_zig_property.py::TestZigPropertyEdgeCases",
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
        pytest.main([__file__ + "::TestZigPropertyMocked", "-v"])