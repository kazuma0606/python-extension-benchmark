"""
Tests for Julia extension
"""

import pytest
import sys
from unittest.mock import Mock, patch

def test_julia_extension_import():
    """Test that Julia extension can be imported."""
    try:
        from benchmark import julia_ext
        assert hasattr(julia_ext, 'find_primes')
        assert hasattr(julia_ext, 'matrix_multiply')
        assert hasattr(julia_ext, 'sort_array')
        assert hasattr(julia_ext, 'filter_array')
        assert hasattr(julia_ext, 'parallel_compute')
        assert hasattr(julia_ext, 'is_available')
    except ImportError as e:
        pytest.skip(f"Julia extension not available: {e}")

def test_julia_extension_availability():
    """Test Julia extension availability check."""
    try:
        from benchmark import julia_ext
        # Should not raise an exception
        available = julia_ext.is_available()
        assert isinstance(available, bool)
    except ImportError:
        pytest.skip("Julia extension not available")

@patch('benchmark.julia_ext._julia_available', False)
def test_julia_extension_unavailable():
    """Test Julia extension behavior when Julia is not available."""
    try:
        from benchmark import julia_ext
        
        # Should return False when Julia is not available
        assert julia_ext.is_available() == False
        
        # Functions should raise RuntimeError when Julia is not available
        with pytest.raises(RuntimeError, match="Julia extension not available"):
            julia_ext.find_primes(10)
            
        with pytest.raises(RuntimeError, match="Julia extension not available"):
            julia_ext.matrix_multiply([[1, 2]], [[3], [4]])
            
        with pytest.raises(RuntimeError, match="Julia extension not available"):
            julia_ext.sort_array([3, 1, 2])
            
        with pytest.raises(RuntimeError, match="Julia extension not available"):
            julia_ext.filter_array([1, 2, 3], 2)
            
        with pytest.raises(RuntimeError, match="Julia extension not available"):
            julia_ext.parallel_compute([1.0, 2.0, 3.0], 2)
            
    except ImportError:
        pytest.skip("Julia extension not available")

def test_julia_functions_signature():
    """Test that Julia functions have correct signatures."""
    try:
        from benchmark import julia_ext
        import inspect
        
        # Check function signatures
        sig_find_primes = inspect.signature(julia_ext.find_primes)
        assert len(sig_find_primes.parameters) == 1
        
        sig_matrix_multiply = inspect.signature(julia_ext.matrix_multiply)
        assert len(sig_matrix_multiply.parameters) == 2
        
        sig_sort_array = inspect.signature(julia_ext.sort_array)
        assert len(sig_sort_array.parameters) == 1
        
        sig_filter_array = inspect.signature(julia_ext.filter_array)
        assert len(sig_filter_array.parameters) == 2
        
        sig_parallel_compute = inspect.signature(julia_ext.parallel_compute)
        assert len(sig_parallel_compute.parameters) == 2
        
    except ImportError:
        pytest.skip("Julia extension not available")

@pytest.mark.skipif(sys.platform == "win32", reason="Julia may not be available on Windows CI")
def test_julia_extension_integration():
    """Integration test for Julia extension with mock Julia."""
    try:
        # Mock Julia to avoid dependency issues in testing
        with patch('benchmark.julia_ext.Main') as mock_main:
            # Mock Julia function returns
            mock_main.find_primes_jl.return_value = [2, 3, 5, 7]
            mock_main.matrix_multiply_jl.return_value = [[19, 22], [43, 50]]
            mock_main.sort_array_jl.return_value = [1, 2, 3]
            mock_main.filter_array_jl.return_value = [2, 3]
            mock_main.parallel_compute_jl.return_value = 6.0
            
            with patch('benchmark.julia_ext._julia_available', True):
                from benchmark import julia_ext
                
                # Test functions with mocked Julia
                result = julia_ext.find_primes(10)
                assert result == [2, 3, 5, 7]
                
                result = julia_ext.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
                assert result == [[19, 22], [43, 50]]
                
                result = julia_ext.sort_array([3, 1, 2])
                assert result == [1, 2, 3]
                
                result = julia_ext.filter_array([1, 2, 3], 2)
                assert result == [2, 3]
                
                result = julia_ext.parallel_compute([1.0, 2.0, 3.0], 2)
                assert result == 6.0
                
    except ImportError:
        pytest.skip("Julia extension not available")