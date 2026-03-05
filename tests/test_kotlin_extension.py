"""
Tests for Kotlin/Native extension functionality
"""

import pytest
import sys
import os

# Add the benchmark directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))

try:
    import kotlin_ext
    KOTLIN_AVAILABLE = kotlin_ext.is_available()
except ImportError:
    KOTLIN_AVAILABLE = False
    kotlin_ext = None

class TestKotlinExtension:
    """Test cases for Kotlin/Native extension"""
    
    def test_kotlin_import(self):
        """Test that Kotlin extension can be imported"""
        assert kotlin_ext is not None, "Kotlin extension should be importable"
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_find_primes_basic(self):
        """Test basic prime finding functionality"""
        primes = kotlin_ext.find_primes(10)
        expected = [2, 3, 5, 7]
        assert primes == expected, f"Expected {expected}, got {primes}"
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_find_primes_edge_cases(self):
        """Test edge cases for prime finding"""
        # Test n < 2
        assert kotlin_ext.find_primes(1) == []
        assert kotlin_ext.find_primes(0) == []
        
        # Test n = 2
        assert kotlin_ext.find_primes(2) == [2]
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_matrix_multiply_basic(self):
        """Test basic matrix multiplication"""
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[2.0, 0.0], [1.0, 2.0]]
        result = kotlin_ext.matrix_multiply(a, b)
        expected = [[4.0, 4.0], [10.0, 8.0]]
        
        assert len(result) == len(expected)
        for i in range(len(result)):
            for j in range(len(result[i])):
                assert abs(result[i][j] - expected[i][j]) < 1e-10
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_matrix_multiply_edge_cases(self):
        """Test edge cases for matrix multiplication"""
        # Empty matrices
        assert kotlin_ext.matrix_multiply([], []) == []
        
        # Incompatible dimensions should raise ValueError
        a = [[1.0, 2.0]]  # 1x2
        b = [[1.0], [2.0], [3.0]]  # 3x1
        with pytest.raises(ValueError):
            kotlin_ext.matrix_multiply(a, b)
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_sort_array_basic(self):
        """Test basic array sorting"""
        arr = [3, 1, 4, 1, 5, 9, 2, 6]
        result = kotlin_ext.sort_array(arr)
        expected = [1, 1, 2, 3, 4, 5, 6, 9]
        assert result == expected
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_sort_array_edge_cases(self):
        """Test edge cases for array sorting"""
        # Empty array
        assert kotlin_ext.sort_array([]) == []
        
        # Single element
        assert kotlin_ext.sort_array([42]) == [42]
        
        # Already sorted
        assert kotlin_ext.sort_array([1, 2, 3]) == [1, 2, 3]
        
        # Reverse sorted
        assert kotlin_ext.sort_array([3, 2, 1]) == [1, 2, 3]
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_filter_array_basic(self):
        """Test basic array filtering"""
        arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = kotlin_ext.filter_array(arr, 5)
        expected = [5, 6, 7, 8, 9, 10]
        assert result == expected
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_filter_array_edge_cases(self):
        """Test edge cases for array filtering"""
        # Empty array
        assert kotlin_ext.filter_array([], 5) == []
        
        # No elements pass threshold
        assert kotlin_ext.filter_array([1, 2, 3], 10) == []
        
        # All elements pass threshold
        arr = [5, 6, 7, 8]
        assert kotlin_ext.filter_array(arr, 5) == arr
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_parallel_compute_basic(self):
        """Test basic parallel computation"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = kotlin_ext.parallel_compute(data, 2)
        expected = sum(data)
        assert abs(result - expected) < 1e-10
    
    @pytest.mark.skipif(not KOTLIN_AVAILABLE, reason="Kotlin extension not available")
    def test_parallel_compute_edge_cases(self):
        """Test edge cases for parallel computation"""
        # Empty data
        assert kotlin_ext.parallel_compute([], 2) == 0.0
        
        # Single element
        assert kotlin_ext.parallel_compute([42.0], 1) == 42.0
        
        # Single thread
        data = [1.0, 2.0, 3.0]
        result = kotlin_ext.parallel_compute(data, 1)
        assert abs(result - 6.0) < 1e-10

class TestKotlinFallback:
    """Test fallback behavior when Kotlin extension is not available"""
    
    def test_fallback_behavior(self):
        """Test that functions work with Python fallback when Kotlin is unavailable"""
        if KOTLIN_AVAILABLE:
            pytest.skip("Kotlin extension is available, cannot test fallback")
        
        # These should use Python fallbacks and not raise exceptions
        primes = kotlin_ext.find_primes(10)
        assert isinstance(primes, list)
        
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[2.0, 0.0], [1.0, 2.0]]
        result = kotlin_ext.matrix_multiply(a, b)
        assert isinstance(result, list)
        
        sorted_arr = kotlin_ext.sort_array([3, 1, 4])
        assert isinstance(sorted_arr, list)
        
        filtered = kotlin_ext.filter_array([1, 2, 3, 4, 5], 3)
        assert isinstance(filtered, list)
        
        sum_result = kotlin_ext.parallel_compute([1.0, 2.0, 3.0], 2)
        assert isinstance(sum_result, float)

if __name__ == "__main__":
    pytest.main([__file__])