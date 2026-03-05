"""
Nim Extension Property-Based Tests

**Feature: multi-language-extensions, Property 5: フィルタ結果の正確性**
**Validates: Requirements 4.4**

This module contains property-based tests for Nim extension filter result correctness.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import math
from typing import List

# Skip tests if Nim is not available
pytest_plugins = []

def filter_array_reference(arr: List[int], threshold: int) -> List[int]:
    """Reference implementation of array filtering."""
    return [x for x in arr if x >= threshold]

def all_elements_above_threshold(arr: List[int], threshold: int) -> bool:
    """Check if all elements in array are above or equal to threshold."""
    return all(x >= threshold for x in arr)

def is_subset_of_original(filtered: List[int], original: List[int]) -> bool:
    """Check if filtered array is a subset of original array (preserving frequencies)."""
    from collections import Counter
    filtered_count = Counter(filtered)
    original_count = Counter(original)
    
    for element, count in filtered_count.items():
        if original_count[element] < count:
            return False
    return True

def preserves_order(filtered: List[int], original: List[int]) -> bool:
    """Check if filtered array preserves the relative order of elements from original."""
    if not filtered:
        return True
    
    # Find positions of filtered elements in original array
    original_positions = []
    original_index = 0
    
    for filtered_element in filtered:
        # Find next occurrence of this element in original array
        while original_index < len(original) and original[original_index] != filtered_element:
            original_index += 1
        
        if original_index >= len(original):
            return False  # Element not found in remaining original array
        
        original_positions.append(original_index)
        original_index += 1
    
    # Check if positions are in ascending order
    return all(original_positions[i] <= original_positions[i+1] for i in range(len(original_positions)-1))

@pytest.mark.skipif(False, reason="Run in Docker environment")
class TestNimPropertyDocker:
    """Property-based tests for Nim extension - Docker environment only."""
    
    @given(
        arr=st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=1000),
        threshold=st.integers(min_value=-500, max_value=500)
    )
    @settings(max_examples=100, deadline=5000)
    def test_filter_array_correctness(self, arr, threshold):
        """
        **Feature: multi-language-extensions, Property 5: フィルタ結果の正確性**
        **Validates: Requirements 4.4**
        
        Property: For any array and threshold, filter_array(arr, threshold) returns only 
        elements that are greater than or equal to the threshold.
        """
        try:
            from benchmark import nim_ext
            
            # Note: We test with fallback implementation if Nim library is not available
            # This still validates the interface and basic functionality
            
            # Get result from Nim implementation
            result = nim_ext.filter_array(arr, threshold)
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            elif isinstance(result, list):
                result = [int(x) for x in result]
            
            # Get expected result from reference implementation
            expected = filter_array_reference(arr, threshold)
            
            # Property 1: All elements in result should be >= threshold
            assert all_elements_above_threshold(result, threshold), \
                f"Nim filter result contains elements below threshold {threshold}: {result}"
            
            # Property 2: Result should be a subset of original array
            assert is_subset_of_original(result, arr), \
                f"Nim filter result is not a subset of original. Original: {arr}, Filtered: {result}"
            
            # Property 3: Result should match reference implementation
            assert result == expected, \
                f"Nim filter mismatch. Input: {arr}, Threshold: {threshold}, Got: {result}, Expected: {expected}"
            
            # Property 4: Result should preserve relative order from original
            assert preserves_order(result, arr), \
                f"Nim filter changed relative order. Original: {arr}, Filtered: {result}"
            
            # Property 5: Length should be <= original length
            assert len(result) <= len(arr), \
                f"Nim filter result longer than input. Input length: {len(arr)}, Output length: {len(result)}"
                
        except ImportError:
            pytest.skip("Nim extension not available")
    
    @given(
        arr=st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=100),
        threshold=st.integers(min_value=-50, max_value=50)
    )
    @settings(max_examples=50, deadline=5000)
    def test_filter_array_boundary_conditions(self, arr, threshold):
        """
        **Feature: multi-language-extensions, Property 5: フィルタ結果の正確性**
        **Validates: Requirements 4.4**
        
        Additional properties for filter correctness: boundary conditions and edge cases.
        """
        try:
            from benchmark import nim_ext
            
            # Note: We test with fallback implementation if Nim library is not available
            # This still validates the interface and basic functionality
            
            # Get result from Nim implementation
            result = nim_ext.filter_array(arr, threshold)
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            elif isinstance(result, list):
                result = [int(x) for x in result]
            
            # Property: If threshold is higher than max element, result should be empty
            if threshold > max(arr):
                assert result == [], \
                    f"Filter with threshold {threshold} > max({max(arr)}) should be empty, got: {result}"
            
            # Property: If threshold is lower than min element, result should equal original
            if threshold <= min(arr):
                assert len(result) == len(arr), \
                    f"Filter with threshold {threshold} <= min({min(arr)}) should preserve all elements"
            
            # Property: Elements equal to threshold should be included
            elements_equal_to_threshold = [x for x in arr if x == threshold]
            elements_equal_in_result = [x for x in result if x == threshold]
            assert len(elements_equal_in_result) == len(elements_equal_to_threshold), \
                f"Elements equal to threshold {threshold} not properly included. " \
                f"Original count: {len(elements_equal_to_threshold)}, Result count: {len(elements_equal_in_result)}"
                
        except ImportError:
            pytest.skip("Nim extension not available")

# Edge case tests
@pytest.mark.skipif(False, reason="Run in Docker environment")
class TestNimPropertyEdgeCases:
    """Property-based tests for edge cases."""
    
    def test_filter_empty_array(self):
        """Test filtering empty array."""
        try:
            from benchmark import nim_ext
            
            # Note: We test with fallback implementation if Nim library is not available
            
            result = nim_ext.filter_array([], 5)
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            
            assert result == [], f"Empty array filter failed: {result}"
            
        except ImportError:
            pytest.skip("Nim extension not available")
    
    @given(threshold=st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=20, deadline=3000)
    def test_filter_single_element(self, threshold):
        """Test filtering single element array."""
        try:
            from benchmark import nim_ext
            
            # Note: We test with fallback implementation if Nim library is not available
            
            # Test with element above threshold
            if threshold <= 42:
                result = nim_ext.filter_array([42], threshold)
                
                # Convert numpy types to Python types if needed
                if hasattr(result, 'tolist'):
                    result = result.tolist()
                elif isinstance(result, list):
                    result = [int(x) for x in result]
                
                assert result == [42], f"Single element filter failed for threshold {threshold}: {result}"
            
            # Test with element below threshold
            if threshold > 42:
                result = nim_ext.filter_array([42], threshold)
                
                # Convert numpy types to Python types if needed
                if hasattr(result, 'tolist'):
                    result = result.tolist()
                
                assert result == [], f"Single element filter should be empty for threshold {threshold}: {result}"
                
        except ImportError:
            pytest.skip("Nim extension not available")
    
    @given(
        value=st.integers(min_value=-100, max_value=100), 
        count=st.integers(min_value=2, max_value=50),
        threshold=st.integers(min_value=-150, max_value=150)
    )
    @settings(max_examples=30, deadline=3000)
    def test_filter_duplicate_elements(self, value, count, threshold):
        """Test filtering arrays with duplicate elements."""
        try:
            from benchmark import nim_ext
            
            # Note: We test with fallback implementation if Nim library is not available
            
            # Create array with all same elements
            arr = [value] * count
            result = nim_ext.filter_array(arr, threshold)
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            elif isinstance(result, list):
                result = [int(x) for x in result]
            
            # If value >= threshold, all elements should be preserved
            if value >= threshold:
                assert result == arr, f"Duplicate element filter failed for value {value}, threshold {threshold}: {result}"
                assert len(result) == count, f"Length mismatch for duplicates: {len(result)} != {count}"
            else:
                # If value < threshold, no elements should be preserved
                assert result == [], f"Duplicate element filter should be empty for value {value} < threshold {threshold}: {result}"
            
        except ImportError:
            pytest.skip("Nim extension not available")

# Tests that can run in any environment (with mocking)
class TestNimPropertyMocked:
    """Property-based tests with mocking for local development."""
    
    @given(
        arr=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=50),
        threshold=st.integers(min_value=-50, max_value=50)
    )
    @settings(max_examples=20)
    def test_filter_array_property_structure(self, arr, threshold):
        """
        Test the property structure without requiring Nim.
        This validates the test logic itself.
        """
        # Reference implementation test
        expected = filter_array_reference(arr, threshold)
        
        # Property: All elements should be >= threshold
        assert all_elements_above_threshold(expected, threshold), \
            "Reference implementation should only return elements >= threshold"
        
        # Property: Should be subset of original
        assert is_subset_of_original(expected, arr), \
            "Reference implementation should preserve element frequencies"
        
        # Property: Should preserve order
        assert preserves_order(expected, arr), \
            "Reference implementation should preserve relative order"
        
        # Property: Length should be <= original
        assert len(expected) <= len(arr), \
            "Reference implementation should not increase length"
    
    def test_helper_functions(self):
        """Test helper functions used in properties."""
        # Test all_elements_above_threshold
        assert all_elements_above_threshold([], 5)
        assert all_elements_above_threshold([5, 6, 7], 5)
        assert all_elements_above_threshold([10], 5)
        assert not all_elements_above_threshold([4, 5, 6], 5)
        assert not all_elements_above_threshold([1, 2, 3], 5)
        
        # Test is_subset_of_original
        assert is_subset_of_original([], [1, 2, 3])
        assert is_subset_of_original([1, 3], [1, 2, 3])
        assert is_subset_of_original([1, 1], [1, 1, 2, 3])
        assert not is_subset_of_original([1, 1, 1], [1, 1, 2])
        assert not is_subset_of_original([4], [1, 2, 3])
        
        # Test preserves_order
        assert preserves_order([], [1, 2, 3])
        assert preserves_order([1, 3], [1, 2, 3])
        assert preserves_order([2, 2], [1, 2, 2, 3])
        assert not preserves_order([3, 1], [1, 2, 3])

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
            "tests/test_nim_property.py::TestNimPropertyDocker",
            "tests/test_nim_property.py::TestNimPropertyEdgeCases",
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
        pytest.main([__file__ + "::TestNimPropertyMocked", "-v"])