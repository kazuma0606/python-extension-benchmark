#!/usr/bin/env python3
"""
Tests for Nim extension integration.
"""

import pytest
import sys
import os

# Add benchmark directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))

try:
    import nim_ext
    NIM_AVAILABLE = nim_ext.is_available()
except ImportError:
    NIM_AVAILABLE = False

@pytest.mark.skipif(not NIM_AVAILABLE, reason="Nim extension not available")
class TestNimExtension:
    """Test cases for Nim extension functionality."""
    
    def test_find_primes(self):
        """Test prime number generation."""
        # Test small cases
        assert nim_ext.find_primes(1) == []
        assert nim_ext.find_primes(2) == [2]
        assert nim_ext.find_primes(10) == [2, 3, 5, 7]
        assert nim_ext.find_primes(20) == [2, 3, 5, 7, 11, 13, 17, 19]
    
    def test_matrix_multiply(self):
        """Test matrix multiplication."""
        # Test 2x2 matrices
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[5.0, 6.0], [7.0, 8.0]]
        result = nim_ext.matrix_multiply(a, b)
        expected = [[19.0, 22.0], [43.0, 50.0]]
        assert result == expected
        
        # Test identity matrix
        identity = [[1.0, 0.0], [0.0, 1.0]]
        matrix = [[2.0, 3.0], [4.0, 5.0]]
        result = nim_ext.matrix_multiply(identity, matrix)
        assert result == matrix
    
    def test_sort_array(self):
        """Test array sorting."""
        # Test various cases
        assert nim_ext.sort_array([]) == []
        assert nim_ext.sort_array([1]) == [1]
        assert nim_ext.sort_array([3, 1, 4, 1, 5]) == [1, 1, 3, 4, 5]
        assert nim_ext.sort_array([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    
    def test_filter_array(self):
        """Test array filtering."""
        # Test filtering
        assert nim_ext.filter_array([], 5) == []
        assert nim_ext.filter_array([1, 2, 3, 4, 5], 3) == [3, 4, 5]
        assert nim_ext.filter_array([1, 2, 3, 4, 5], 10) == []
        assert nim_ext.filter_array([10, 5, 15, 3, 20], 8) == [10, 15, 20]
    
    def test_parallel_compute(self):
        """Test parallel computation."""
        # Test sum computation
        assert abs(nim_ext.parallel_compute([], 2) - 0.0) < 1e-10
        assert abs(nim_ext.parallel_compute([1.0], 1) - 1.0) < 1e-10
        assert abs(nim_ext.parallel_compute([1.0, 2.0, 3.0, 4.0], 2) - 10.0) < 1e-10
        assert abs(nim_ext.parallel_compute([0.5, 1.5, 2.5, 3.5], 4) - 8.0) < 1e-10
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Matrix multiplication with incompatible dimensions
        with pytest.raises(ValueError):
            nim_ext.matrix_multiply([[1.0, 2.0]], [[1.0], [2.0], [3.0]])

class TestNimExtensionFallback:
    """Test cases for Nim extension with fallback implementations."""
    
    def test_find_primes_fallback(self):
        """Test prime number generation with fallback."""
        # These should work even if Nim library is not available
        result = nim_ext.find_primes(10)
        expected = [2, 3, 5, 7]
        assert result == expected
    
    def test_matrix_multiply_fallback(self):
        """Test matrix multiplication with fallback."""
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[2.0, 0.0], [1.0, 2.0]]
        result = nim_ext.matrix_multiply(a, b)
        expected = [[4.0, 4.0], [10.0, 8.0]]
        assert result == expected
    
    def test_sort_array_fallback(self):
        """Test array sorting with fallback."""
        result = nim_ext.sort_array([3, 1, 4, 1, 5])
        expected = [1, 1, 3, 4, 5]
        assert result == expected
    
    def test_filter_array_fallback(self):
        """Test array filtering with fallback."""
        result = nim_ext.filter_array([1, 2, 3, 4, 5], 3)
        expected = [3, 4, 5]
        assert result == expected
    
    def test_parallel_compute_fallback(self):
        """Test parallel computation with fallback."""
        result = nim_ext.parallel_compute([1.0, 2.0, 3.0], 2)
        expected = 6.0
        assert abs(result - expected) < 1e-10

def test_nim_availability():
    """Test that we can detect Nim availability."""
    # This test should always pass, regardless of whether Nim is available
    available = False
    try:
        import nim_ext
        available = nim_ext.is_available()
    except ImportError:
        pass
    
    # Just verify the function works
    assert isinstance(available, bool)

def test_nim_extension_import():
    """Test that Nim extension can be imported."""
    try:
        import nim_ext
        # Should have all required functions
        assert hasattr(nim_ext, 'find_primes')
        assert hasattr(nim_ext, 'matrix_multiply')
        assert hasattr(nim_ext, 'sort_array')
        assert hasattr(nim_ext, 'filter_array')
        assert hasattr(nim_ext, 'parallel_compute')
        assert hasattr(nim_ext, 'is_available')
    except ImportError:
        pytest.fail("Could not import nim_ext module")

def test_nim_functions_signature():
    """Test that Nim extension functions have correct signatures."""
    import nim_ext
    import inspect
    
    # Test function signatures match the interface
    sig_find_primes = inspect.signature(nim_ext.find_primes)
    assert len(sig_find_primes.parameters) == 1
    
    sig_matrix_multiply = inspect.signature(nim_ext.matrix_multiply)
    assert len(sig_matrix_multiply.parameters) == 2
    
    sig_sort_array = inspect.signature(nim_ext.sort_array)
    assert len(sig_sort_array.parameters) == 1
    
    sig_filter_array = inspect.signature(nim_ext.filter_array)
    assert len(sig_filter_array.parameters) == 2
    
    sig_parallel_compute = inspect.signature(nim_ext.parallel_compute)
    assert len(sig_parallel_compute.parameters) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])