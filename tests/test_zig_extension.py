#!/usr/bin/env python3
"""
Tests for Zig extension integration.
"""

import pytest
import sys
import os

# Add benchmark directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))

try:
    import zig_ext
    ZIG_AVAILABLE = zig_ext.is_available()
except ImportError:
    ZIG_AVAILABLE = False

@pytest.mark.skipif(not ZIG_AVAILABLE, reason="Zig extension not available")
class TestZigExtension:
    """Test cases for Zig extension functionality."""
    
    def test_find_primes(self):
        """Test prime number generation."""
        # Test small cases
        assert zig_ext.find_primes(1) == []
        assert zig_ext.find_primes(2) == [2]
        assert zig_ext.find_primes(10) == [2, 3, 5, 7]
        assert zig_ext.find_primes(20) == [2, 3, 5, 7, 11, 13, 17, 19]
    
    def test_matrix_multiply(self):
        """Test matrix multiplication."""
        # Test 2x2 matrices
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        result = zig_ext.matrix_multiply(a, b)
        expected = [[19, 22], [43, 50]]
        assert result == expected
        
        # Test identity matrix
        identity = [[1, 0], [0, 1]]
        matrix = [[2, 3], [4, 5]]
        result = zig_ext.matrix_multiply(identity, matrix)
        assert result == matrix
    
    def test_sort_array(self):
        """Test array sorting."""
        # Test various cases
        assert zig_ext.sort_array([]) == []
        assert zig_ext.sort_array([1]) == [1]
        assert zig_ext.sort_array([3, 1, 4, 1, 5]) == [1, 1, 3, 4, 5]
        assert zig_ext.sort_array([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    
    def test_filter_array(self):
        """Test array filtering."""
        # Test filtering
        assert zig_ext.filter_array([], 5) == []
        assert zig_ext.filter_array([1, 2, 3, 4, 5], 3) == [3, 4, 5]
        assert zig_ext.filter_array([1, 2, 3, 4, 5], 10) == []
        assert zig_ext.filter_array([10, 5, 15, 3, 20], 8) == [10, 15, 20]
    
    def test_parallel_compute(self):
        """Test parallel computation."""
        # Test sum computation
        assert abs(zig_ext.parallel_compute([], 2) - 0.0) < 1e-10
        assert abs(zig_ext.parallel_compute([1.0], 1) - 1.0) < 1e-10
        assert abs(zig_ext.parallel_compute([1.0, 2.0, 3.0, 4.0], 2) - 10.0) < 1e-10
        assert abs(zig_ext.parallel_compute([0.5, 1.5, 2.5, 3.5], 4) - 8.0) < 1e-10
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Matrix multiplication with incompatible dimensions
        with pytest.raises(ValueError):
            zig_ext.matrix_multiply([[1, 2]], [[1], [2], [3]])

def test_zig_availability():
    """Test that we can detect Zig availability."""
    # This test should always pass, regardless of whether Zig is available
    available = False
    try:
        import zig_ext
        available = zig_ext.is_available()
    except ImportError:
        pass
    
    # Just verify the function works
    assert isinstance(available, bool)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])