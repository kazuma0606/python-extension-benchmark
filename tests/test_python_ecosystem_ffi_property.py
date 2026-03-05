"""
Property-based tests for Python ecosystem FFI implementations (NumPy, Cython, Rust).

**Feature: ffi-benchmark-extensions, Property 2: 共有ライブラリの自動検出**
**Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
**Validates: Requirements 4.2, 5.2, 6.2**
"""

import pytest
import sys
import os
from hypothesis import given, strategies as st, assume, settings
from typing import List
import ctypes

# Add benchmark directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))

from benchmark.ffi_implementations.numpy_ffi import NumPyFFI
from benchmark.ffi_implementations.cython_ffi import CythonFFI
from benchmark.ffi_implementations.rust_ffi import RustFFI
from benchmark.python.numeric import find_primes as py_find_primes, matrix_multiply as py_matrix_multiply
from benchmark.python.memory import sort_array as py_sort_array, filter_array as py_filter_array
from benchmark.python.parallel import parallel_compute as py_parallel_compute


class TestSharedLibraryAutoDetection:
    """Property-based tests for shared library auto-detection."""
    
    def test_numpy_ffi_library_auto_detection(self):
        """
        **Feature: ffi-benchmark-extensions, Property 2: 共有ライブラリの自動検出**
        
        NumPy FFI implementation should automatically detect and load its shared library.
        **Validates: Requirements 4.2**
        """
        numpy_ffi = NumPyFFI(skip_uv_check=True)
        
        # Check that the library was detected and loaded (or build attempted)
        # Even if build fails, the auto-detection mechanism should work
        assert hasattr(numpy_ffi, 'lib'), "NumPy FFI should have lib attribute"
        assert hasattr(numpy_ffi, 'library_name'), "NumPy FFI should have library_name attribute"
        assert numpy_ffi.library_name == "libnumpyfunctions", "Correct library name should be set"
        
        # If available, should have proper function signatures
        if numpy_ffi.is_available():
            assert hasattr(numpy_ffi.lib, 'find_primes_ffi'), "Should have find_primes_ffi function"
            assert hasattr(numpy_ffi.lib, 'matrix_multiply_ffi'), "Should have matrix_multiply_ffi function"
            assert hasattr(numpy_ffi.lib, 'sort_array_ffi'), "Should have sort_array_ffi function"
            assert hasattr(numpy_ffi.lib, 'filter_array_ffi'), "Should have filter_array_ffi function"
            assert hasattr(numpy_ffi.lib, 'parallel_compute_ffi'), "Should have parallel_compute_ffi function"
            assert hasattr(numpy_ffi.lib, 'free_memory_ffi'), "Should have free_memory_ffi function"
    
    def test_cython_ffi_library_auto_detection(self):
        """
        **Feature: ffi-benchmark-extensions, Property 2: 共有ライブラリの自動検出**
        
        Cython FFI implementation should automatically detect and load its shared library.
        **Validates: Requirements 5.2**
        """
        cython_ffi = CythonFFI(skip_uv_check=True)
        
        # Check that the library was detected and loaded (or build attempted)
        assert hasattr(cython_ffi, 'lib'), "Cython FFI should have lib attribute"
        assert hasattr(cython_ffi, 'library_name'), "Cython FFI should have library_name attribute"
        assert cython_ffi.library_name == "libcythonfunctions", "Correct library name should be set"
        
        # If available, should have proper function signatures
        if cython_ffi.is_available():
            assert hasattr(cython_ffi.lib, 'find_primes_ffi'), "Should have find_primes_ffi function"
            assert hasattr(cython_ffi.lib, 'matrix_multiply_ffi'), "Should have matrix_multiply_ffi function"
            assert hasattr(cython_ffi.lib, 'sort_array_ffi'), "Should have sort_array_ffi function"
            assert hasattr(cython_ffi.lib, 'filter_array_ffi'), "Should have filter_array_ffi function"
            assert hasattr(cython_ffi.lib, 'parallel_compute_ffi'), "Should have parallel_compute_ffi function"
            assert hasattr(cython_ffi.lib, 'free_memory_ffi'), "Should have free_memory_ffi function"
    
    def test_rust_ffi_library_auto_detection(self):
        """
        **Feature: ffi-benchmark-extensions, Property 2: 共有ライブラリの自動検出**
        
        Rust FFI implementation should automatically detect and load its shared library.
        **Validates: Requirements 6.2**
        """
        rust_ffi = RustFFI(skip_uv_check=True)
        
        # Check that the library was detected and loaded (or build attempted)
        assert hasattr(rust_ffi, 'lib'), "Rust FFI should have lib attribute"
        assert hasattr(rust_ffi, 'library_name'), "Rust FFI should have library_name attribute"
        assert rust_ffi.library_name == "librustfunctions", "Correct library name should be set"
        
        # If available, should have proper function signatures
        if rust_ffi.is_available():
            assert hasattr(rust_ffi.lib, 'find_primes_ffi'), "Should have find_primes_ffi function"
            assert hasattr(rust_ffi.lib, 'matrix_multiply_ffi'), "Should have matrix_multiply_ffi function"
            assert hasattr(rust_ffi.lib, 'sort_array_ffi'), "Should have sort_array_ffi function"
            assert hasattr(rust_ffi.lib, 'filter_array_ffi'), "Should have filter_array_ffi function"
            assert hasattr(rust_ffi.lib, 'parallel_compute_ffi'), "Should have parallel_compute_ffi function"
            assert hasattr(rust_ffi.lib, 'free_memory_ffi'), "Should have free_memory_ffi function"


class TestTypeSafeFFICalls:
    """Property-based tests for type-safe FFI calls."""
    
    @given(n=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=50)
    def test_numpy_ffi_type_safe_calls(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        For any valid input, NumPy FFI calls should succeed with correct types.
        **Validates: Requirements 4.2**
        """
        numpy_ffi = NumPyFFI(skip_uv_check=True)
        if not numpy_ffi.is_available():
            pytest.skip("NumPy FFI not available")
        
        # Test find_primes with valid input
        result = numpy_ffi.find_primes(n)
        assert isinstance(result, list), "find_primes should return a list"
        assert all(isinstance(x, int) for x in result), "All primes should be integers"
        
        # Test with small arrays to avoid timeout
        if n <= 10:
            test_arr = list(range(n))
            
            # Test sort_array
            sorted_result = numpy_ffi.sort_array(test_arr)
            assert isinstance(sorted_result, list), "sort_array should return a list"
            assert all(isinstance(x, int) for x in sorted_result), "All sorted elements should be integers"
            
            # Test filter_array
            filtered_result = numpy_ffi.filter_array(test_arr, n // 2 if n > 0 else 0)
            assert isinstance(filtered_result, list), "filter_array should return a list"
            assert all(isinstance(x, int) for x in filtered_result), "All filtered elements should be integers"
            
            # Test parallel_compute
            data = [float(i) for i in range(n)]
            compute_result = numpy_ffi.parallel_compute(data, 1)
            assert isinstance(compute_result, float), "parallel_compute should return a float"
    
    @given(n=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=50)
    def test_cython_ffi_type_safe_calls(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        For any valid input, Cython FFI calls should succeed with correct types.
        **Validates: Requirements 5.2**
        """
        cython_ffi = CythonFFI(skip_uv_check=True)
        if not cython_ffi.is_available():
            pytest.skip("Cython FFI not available")
        
        # Test find_primes with valid input
        result = cython_ffi.find_primes(n)
        assert isinstance(result, list), "find_primes should return a list"
        assert all(isinstance(x, int) for x in result), "All primes should be integers"
        
        # Test with small arrays to avoid timeout
        if n <= 10:
            test_arr = list(range(n))
            
            # Test sort_array
            sorted_result = cython_ffi.sort_array(test_arr)
            assert isinstance(sorted_result, list), "sort_array should return a list"
            assert all(isinstance(x, int) for x in sorted_result), "All sorted elements should be integers"
            
            # Test filter_array
            filtered_result = cython_ffi.filter_array(test_arr, n // 2 if n > 0 else 0)
            assert isinstance(filtered_result, list), "filter_array should return a list"
            assert all(isinstance(x, int) for x in filtered_result), "All filtered elements should be integers"
    
    @given(n=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=50)
    def test_rust_ffi_type_safe_calls(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        For any valid input, Rust FFI calls should succeed with correct types.
        **Validates: Requirements 6.2**
        """
        rust_ffi = RustFFI(skip_uv_check=True)
        if not rust_ffi.is_available():
            pytest.skip("Rust FFI not available")
        
        # Test find_primes with valid input
        result = rust_ffi.find_primes(n)
        assert isinstance(result, list), "find_primes should return a list"
        assert all(isinstance(x, int) for x in result), "All primes should be integers"
        
        # Test with small arrays to avoid timeout
        if n <= 10:
            test_arr = list(range(n))
            
            # Test sort_array
            sorted_result = rust_ffi.sort_array(test_arr)
            assert isinstance(sorted_result, list), "sort_array should return a list"
            assert all(isinstance(x, int) for x in sorted_result), "All sorted elements should be integers"
            
            # Test filter_array
            filtered_result = rust_ffi.filter_array(test_arr, n // 2 if n > 0 else 0)
            assert isinstance(filtered_result, list), "filter_array should return a list"
            assert all(isinstance(x, int) for x in filtered_result), "All filtered elements should be integers"
    
    def test_invalid_type_handling_numpy_ffi(self):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        NumPy FFI should handle invalid types gracefully.
        **Validates: Requirements 4.2**
        """
        numpy_ffi = NumPyFFI(skip_uv_check=True)
        if not numpy_ffi.is_available():
            pytest.skip("NumPy FFI not available")
        
        # Test with invalid types - should raise appropriate exceptions
        with pytest.raises((TypeError, ValueError, AttributeError, ctypes.ArgumentError)):
            numpy_ffi.find_primes("invalid")
        
        with pytest.raises((TypeError, ValueError, AttributeError, ctypes.ArgumentError)):
            numpy_ffi.sort_array("not a list")
        
        with pytest.raises((TypeError, ValueError, AttributeError, ctypes.ArgumentError)):
            numpy_ffi.filter_array([1, 2, 3], "not an int")
    
    def test_invalid_type_handling_cython_ffi(self):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        Cython FFI should handle invalid types gracefully.
        **Validates: Requirements 5.2**
        """
        cython_ffi = CythonFFI(skip_uv_check=True)
        if not cython_ffi.is_available():
            pytest.skip("Cython FFI not available")
        
        # Test with invalid types - should raise appropriate exceptions
        with pytest.raises((TypeError, ValueError, AttributeError, ctypes.ArgumentError)):
            cython_ffi.find_primes("invalid")
        
        with pytest.raises((TypeError, ValueError, AttributeError, ctypes.ArgumentError)):
            cython_ffi.sort_array("not a list")
        
        with pytest.raises((TypeError, ValueError, AttributeError, ctypes.ArgumentError)):
            cython_ffi.filter_array([1, 2, 3], "not an int")
    
    def test_invalid_type_handling_rust_ffi(self):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        Rust FFI should handle invalid types gracefully.
        **Validates: Requirements 6.2**
        """
        rust_ffi = RustFFI(skip_uv_check=True)
        if not rust_ffi.is_available():
            pytest.skip("Rust FFI not available")
        
        # Test with invalid types - should raise appropriate exceptions
        with pytest.raises((TypeError, ValueError, AttributeError, ctypes.ArgumentError)):
            rust_ffi.find_primes("invalid")
        
        with pytest.raises((TypeError, ValueError, AttributeError, ctypes.ArgumentError)):
            rust_ffi.sort_array("not a list")
        
        with pytest.raises((TypeError, ValueError, AttributeError, ctypes.ArgumentError)):
            rust_ffi.filter_array([1, 2, 3], "not an int")


class TestPythonEcosystemFFIConsistency:
    """Property-based tests for consistency between Python ecosystem FFI implementations."""
    
    @given(n=st.integers(min_value=0, max_value=500))
    @settings(max_examples=30)
    def test_numpy_vs_cython_ffi_consistency(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        For any integer n, NumPy and Cython FFI should produce identical results.
        **Validates: Requirements 4.2, 5.2**
        """
        numpy_ffi = NumPyFFI(skip_uv_check=True)
        cython_ffi = CythonFFI(skip_uv_check=True)
        
        if not (numpy_ffi.is_available() and cython_ffi.is_available()):
            pytest.skip("Both NumPy and Cython FFI must be available")
        
        numpy_result = numpy_ffi.find_primes(n)
        cython_result = cython_ffi.find_primes(n)
        
        assert numpy_result == cython_result, f"NumPy vs Cython primes mismatch for n={n}: NumPy={numpy_result}, Cython={cython_result}"
    
    @given(n=st.integers(min_value=0, max_value=500))
    @settings(max_examples=30)
    def test_cython_vs_rust_ffi_consistency(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        For any integer n, Cython and Rust FFI should produce identical results.
        **Validates: Requirements 5.2, 6.2**
        """
        cython_ffi = CythonFFI(skip_uv_check=True)
        rust_ffi = RustFFI(skip_uv_check=True)
        
        if not (cython_ffi.is_available() and rust_ffi.is_available()):
            pytest.skip("Both Cython and Rust FFI must be available")
        
        cython_result = cython_ffi.find_primes(n)
        rust_result = rust_ffi.find_primes(n)
        
        assert cython_result == rust_result, f"Cython vs Rust primes mismatch for n={n}: Cython={cython_result}, Rust={rust_result}"
    
    @given(arr=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=50))
    @settings(max_examples=30)
    def test_all_python_ecosystem_ffi_sort_consistency(self, arr):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        For any array, all Python ecosystem FFI implementations should produce identical sort results.
        **Validates: Requirements 4.2, 5.2, 6.2**
        """
        numpy_ffi = NumPyFFI(skip_uv_check=True)
        cython_ffi = CythonFFI(skip_uv_check=True)
        rust_ffi = RustFFI(skip_uv_check=True)
        
        available_ffis = []
        results = []
        
        if numpy_ffi.is_available():
            available_ffis.append("NumPy")
            results.append(numpy_ffi.sort_array(arr))
        
        if cython_ffi.is_available():
            available_ffis.append("Cython")
            results.append(cython_ffi.sort_array(arr))
        
        if rust_ffi.is_available():
            available_ffis.append("Rust")
            results.append(rust_ffi.sort_array(arr))
        
        if len(available_ffis) < 2:
            pytest.skip("At least two FFI implementations must be available")
        
        # All results should be identical
        for i in range(1, len(results)):
            assert results[0] == results[i], f"Sort mismatch between {available_ffis[0]} and {available_ffis[i]} for {arr}: {results[0]} vs {results[i]}"
    
    @given(
        arr=st.lists(st.integers(min_value=-50, max_value=50), min_size=0, max_size=30),
        threshold=st.integers(min_value=-50, max_value=50)
    )
    @settings(max_examples=30)
    def test_all_python_ecosystem_ffi_filter_consistency(self, arr, threshold):
        """
        **Feature: ffi-benchmark-extensions, Property 3: 型安全なFFI呼び出し**
        
        For any array and threshold, all Python ecosystem FFI implementations should produce identical filter results.
        **Validates: Requirements 4.2, 5.2, 6.2**
        """
        numpy_ffi = NumPyFFI(skip_uv_check=True)
        cython_ffi = CythonFFI(skip_uv_check=True)
        rust_ffi = RustFFI(skip_uv_check=True)
        
        available_ffis = []
        results = []
        
        if numpy_ffi.is_available():
            available_ffis.append("NumPy")
            results.append(numpy_ffi.filter_array(arr, threshold))
        
        if cython_ffi.is_available():
            available_ffis.append("Cython")
            results.append(cython_ffi.filter_array(arr, threshold))
        
        if rust_ffi.is_available():
            available_ffis.append("Rust")
            results.append(rust_ffi.filter_array(arr, threshold))
        
        if len(available_ffis) < 2:
            pytest.skip("At least two FFI implementations must be available")
        
        # All results should be identical
        for i in range(1, len(results)):
            assert results[0] == results[i], f"Filter mismatch between {available_ffis[0]} and {available_ffis[i]} for {arr}, threshold={threshold}: {results[0]} vs {results[i]}"


if __name__ == "__main__":
    pytest.main([__file__])