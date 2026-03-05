"""
Property-based tests for C and C++ FFI implementations.

**Feature: ffi-benchmark-extensions, Property 1: FFI関数の数学的正確性**
**Feature: ffi-benchmark-extensions, Property 8: メモリ安全性**
**Validates: Requirements 2.2, 3.2**
"""

import pytest
import sys
import os
from hypothesis import given, strategies as st, assume, settings
from typing import List

# Add benchmark directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))

from benchmark.ffi_implementations.c_ffi import CFFI
from benchmark.ffi_implementations.cpp_ffi import CppFFI
from benchmark.python.numeric import find_primes as py_find_primes, matrix_multiply as py_matrix_multiply
from benchmark.python.memory import sort_array as py_sort_array, filter_array as py_filter_array


class TestCFFIProperties:
    """Property-based tests for C FFI implementation."""
    
    @given(n=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=100)
    def test_c_find_primes_mathematical_correctness(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 1: FFI関数の数学的正確性**
        
        For any integer n, C FFI find_primes should return mathematically correct primes.
        **Validates: Requirements 2.2**
        """
        c_ffi = CFFI(skip_uv_check=True)
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        # Get results from both implementations
        c_result = c_ffi.find_primes(n)
        py_result = py_find_primes(n)
        
        # Results should be identical
        assert c_result == py_result, f"C FFI primes mismatch for n={n}: C={c_result}, Python={py_result}"
        
        # Additional mathematical correctness checks
        for prime in c_result:
            assert prime >= 2, f"Invalid prime {prime} < 2"
            assert prime <= n, f"Prime {prime} > limit {n}"
            
            # Check primality (for small primes to avoid timeout)
            if prime <= 100:
                is_prime = True
                for i in range(2, int(prime**0.5) + 1):
                    if prime % i == 0:
                        is_prime = False
                        break
                assert is_prime, f"{prime} is not actually prime"
    
    @given(arr=st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_c_sort_array_mathematical_correctness(self, arr):
        """
        **Feature: ffi-benchmark-extensions, Property 1: FFI関数の数学的正確性**
        
        For any array, C FFI sort should produce a correctly sorted array.
        **Validates: Requirements 2.2**
        """
        c_ffi = CFFI(skip_uv_check=True)
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        c_result = c_ffi.sort_array(arr)
        py_result = py_sort_array(arr)
        
        # Results should be identical
        assert c_result == py_result, f"Sort mismatch for {arr}: C={c_result}, Python={py_result}"
        
        # Additional correctness checks
        if c_result:
            # Check that result is actually sorted
            for i in range(len(c_result) - 1):
                assert c_result[i] <= c_result[i + 1], f"Result not sorted at index {i}: {c_result}"
            
            # Check that all elements are preserved
            assert sorted(arr) == c_result, "Elements not preserved during sort"
    
    @given(
        arr=st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=100),
        threshold=st.integers(min_value=-1000, max_value=1000)
    )
    @settings(max_examples=100)
    def test_c_filter_array_mathematical_correctness(self, arr, threshold):
        """
        **Feature: ffi-benchmark-extensions, Property 1: FFI関数の数学的正確性**
        
        For any array and threshold, C FFI filter should correctly filter elements >= threshold.
        **Validates: Requirements 2.2**
        """
        c_ffi = CFFI(skip_uv_check=True)
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        c_result = c_ffi.filter_array(arr, threshold)
        py_result = py_filter_array(arr, threshold)
        
        # Results should be identical
        assert c_result == py_result, f"Filter mismatch for {arr}, threshold={threshold}: C={c_result}, Python={py_result}"
        
        # Additional correctness checks
        for element in c_result:
            assert element >= threshold, f"Element {element} < threshold {threshold} in result"
            assert element in arr, f"Element {element} not in original array {arr}"
        
        # Check that no valid elements are missing
        expected_count = sum(1 for x in arr if x >= threshold)
        assert len(c_result) == expected_count, f"Wrong number of filtered elements"
    
    @given(n=st.integers(min_value=0, max_value=100))
    @settings(max_examples=50)
    def test_c_memory_safety_repeated_operations(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 8: メモリ安全性**
        
        For any number of repeated operations, C FFI should not leak memory or crash.
        **Validates: Requirements 2.2**
        """
        c_ffi = CFFI(skip_uv_check=True)
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        # Perform multiple operations to test memory safety
        for _ in range(10):  # Repeat operations multiple times
            # Test find_primes
            primes = c_ffi.find_primes(n)
            assert isinstance(primes, list)
            
            # Test sort_array
            test_arr = list(range(n, 0, -1))  # Reverse order
            sorted_arr = c_ffi.sort_array(test_arr)
            assert isinstance(sorted_arr, list)
            
            # Test filter_array
            filtered = c_ffi.filter_array(test_arr, n // 2 if n > 0 else 0)
            assert isinstance(filtered, list)
            
            # Test parallel_compute
            data = [float(i) for i in range(min(n, 10))]
            result = c_ffi.parallel_compute(data, 1)
            assert isinstance(result, float)


class TestCppFFIProperties:
    """Property-based tests for C++ FFI implementation."""
    
    @given(n=st.integers(min_value=0, max_value=1000))
    @settings(max_examples=100)
    def test_cpp_find_primes_mathematical_correctness(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 1: FFI関数の数学的正確性**
        
        For any integer n, C++ FFI find_primes should return mathematically correct primes.
        **Validates: Requirements 3.2**
        """
        cpp_ffi = CppFFI(skip_uv_check=True)
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI not available")
        
        # Get results from both implementations
        cpp_result = cpp_ffi.find_primes(n)
        py_result = py_find_primes(n)
        
        # Results should be identical
        assert cpp_result == py_result, f"C++ FFI primes mismatch for n={n}: C++={cpp_result}, Python={py_result}"
        
        # Additional mathematical correctness checks
        for prime in cpp_result:
            assert prime >= 2, f"Invalid prime {prime} < 2"
            assert prime <= n, f"Prime {prime} > limit {n}"
    
    @given(arr=st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_cpp_sort_array_mathematical_correctness(self, arr):
        """
        **Feature: ffi-benchmark-extensions, Property 1: FFI関数の数学的正確性**
        
        For any array, C++ FFI sort should produce a correctly sorted array.
        **Validates: Requirements 3.2**
        """
        cpp_ffi = CppFFI(skip_uv_check=True)
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI not available")
        
        cpp_result = cpp_ffi.sort_array(arr)
        py_result = py_sort_array(arr)
        
        # Results should be identical
        assert cpp_result == py_result, f"Sort mismatch for {arr}: C++={cpp_result}, Python={py_result}"
        
        # Additional correctness checks
        if cpp_result:
            # Check that result is actually sorted
            for i in range(len(cpp_result) - 1):
                assert cpp_result[i] <= cpp_result[i + 1], f"Result not sorted at index {i}: {cpp_result}"
    
    @given(n=st.integers(min_value=0, max_value=100))
    @settings(max_examples=50)
    def test_cpp_memory_safety_repeated_operations(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 8: メモリ安全性**
        
        For any number of repeated operations, C++ FFI should not leak memory or crash.
        **Validates: Requirements 3.2**
        """
        cpp_ffi = CppFFI(skip_uv_check=True)
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI not available")
        
        # Perform multiple operations to test memory safety
        for _ in range(10):  # Repeat operations multiple times
            # Test find_primes
            primes = cpp_ffi.find_primes(n)
            assert isinstance(primes, list)
            
            # Test sort_array
            test_arr = list(range(n, 0, -1))  # Reverse order
            sorted_arr = cpp_ffi.sort_array(test_arr)
            assert isinstance(sorted_arr, list)


class TestCVsCppFFIConsistency:
    """Property-based tests for C vs C++ FFI consistency."""
    
    @given(n=st.integers(min_value=0, max_value=500))
    @settings(max_examples=50)
    def test_c_vs_cpp_find_primes_consistency(self, n):
        """
        **Feature: ffi-benchmark-extensions, Property 1: FFI関数の数学的正確性**
        
        For any integer n, C and C++ FFI should produce identical prime results.
        **Validates: Requirements 2.2, 3.2**
        """
        c_ffi = CFFI(skip_uv_check=True)
        cpp_ffi = CppFFI(skip_uv_check=True)
        
        if not (c_ffi.is_available() and cpp_ffi.is_available()):
            pytest.skip("Both C and C++ FFI must be available")
        
        c_result = c_ffi.find_primes(n)
        cpp_result = cpp_ffi.find_primes(n)
        
        assert c_result == cpp_result, f"C vs C++ primes mismatch for n={n}: C={c_result}, C++={cpp_result}"
    
    @given(arr=st.lists(st.integers(min_value=-1000, max_value=1000), min_size=0, max_size=50))
    @settings(max_examples=50)
    def test_c_vs_cpp_sort_array_consistency(self, arr):
        """
        **Feature: ffi-benchmark-extensions, Property 1: FFI関数の数学的正確性**
        
        For any array, C and C++ FFI should produce identical sort results.
        **Validates: Requirements 2.2, 3.2**
        """
        c_ffi = CFFI(skip_uv_check=True)
        cpp_ffi = CppFFI(skip_uv_check=True)
        
        if not (c_ffi.is_available() and cpp_ffi.is_available()):
            pytest.skip("Both C and C++ FFI must be available")
        
        c_result = c_ffi.sort_array(arr)
        cpp_result = cpp_ffi.sort_array(arr)
        
        assert c_result == cpp_result, f"C vs C++ sort mismatch for {arr}: C={c_result}, C++={cpp_result}"
    
    @given(
        arr=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=50),
        threshold=st.integers(min_value=-100, max_value=100)
    )
    @settings(max_examples=50)
    def test_c_vs_cpp_filter_array_consistency(self, arr, threshold):
        """
        **Feature: ffi-benchmark-extensions, Property 1: FFI関数の数学的正確性**
        
        For any array and threshold, C and C++ FFI should produce identical filter results.
        **Validates: Requirements 2.2, 3.2**
        """
        c_ffi = CFFI(skip_uv_check=True)
        cpp_ffi = CppFFI(skip_uv_check=True)
        
        if not (c_ffi.is_available() and cpp_ffi.is_available()):
            pytest.skip("Both C and C++ FFI must be available")
        
        c_result = c_ffi.filter_array(arr, threshold)
        cpp_result = cpp_ffi.filter_array(arr, threshold)
        
        assert c_result == cpp_result, f"C vs C++ filter mismatch for {arr}, threshold={threshold}: C={c_result}, C++={cpp_result}"


if __name__ == "__main__":
    pytest.main([__file__])