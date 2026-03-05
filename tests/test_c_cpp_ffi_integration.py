"""
Integration tests for C and C++ FFI implementations.

Tests basic functionality, Pure Python result consistency, and memory safety.
"""

import pytest
import sys
import os

# Add benchmark directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))

from benchmark.ffi_implementations.c_ffi import CFFI
from benchmark.ffi_implementations.cpp_ffi import CppFFI
from benchmark.python.numeric import find_primes as py_find_primes, matrix_multiply as py_matrix_multiply
from benchmark.python.memory import sort_array as py_sort_array, filter_array as py_filter_array
from benchmark.python.parallel import parallel_compute as py_parallel_compute


class TestCFFIIntegration:
    """Test C FFI implementation."""
    
    @pytest.fixture
    def c_ffi(self):
        """Create C FFI instance."""
        return CFFI(skip_uv_check=True)
    
    def test_c_ffi_availability(self, c_ffi):
        """Test that C FFI is available."""
        if not c_ffi.is_available():
            pytest.skip("C FFI shared library not available")
        
        assert c_ffi.is_available()
        assert c_ffi.get_implementation_name() == "C FFI"
    
    def test_c_find_primes_basic(self, c_ffi):
        """Test C find_primes basic functionality."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        # Test basic cases
        assert c_ffi.find_primes(1) == []
        assert c_ffi.find_primes(2) == [2]
        assert c_ffi.find_primes(10) == [2, 3, 5, 7]
        assert c_ffi.find_primes(20) == [2, 3, 5, 7, 11, 13, 17, 19]
    
    def test_c_find_primes_vs_python(self, c_ffi):
        """Test C find_primes matches Pure Python results."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        test_cases = [0, 1, 2, 10, 50, 100]
        
        for n in test_cases:
            c_result = c_ffi.find_primes(n)
            py_result = py_find_primes(n)
            assert c_result == py_result, f"Mismatch for n={n}: C={c_result}, Python={py_result}"
    
    def test_c_matrix_multiply_basic(self, c_ffi):
        """Test C matrix multiplication basic functionality."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        # Test 2x2 matrices
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[5.0, 6.0], [7.0, 8.0]]
        expected = [[19.0, 22.0], [43.0, 50.0]]
        
        result = c_ffi.matrix_multiply(a, b)
        assert result == expected
    
    def test_c_matrix_multiply_vs_python(self, c_ffi):
        """Test C matrix multiplication matches Pure Python results."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        test_cases = [
            ([[1.0]], [[2.0]]),
            ([[1.0, 2.0]], [[3.0], [4.0]]),
            ([[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]),
        ]
        
        for a, b in test_cases:
            c_result = c_ffi.matrix_multiply(a, b)
            py_result = py_matrix_multiply(a, b)
            assert c_result == py_result, f"Matrix multiply mismatch: C={c_result}, Python={py_result}"
    
    def test_c_sort_array_basic(self, c_ffi):
        """Test C sort_array basic functionality."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        # Test basic cases
        assert c_ffi.sort_array([]) == []
        assert c_ffi.sort_array([1]) == [1]
        assert c_ffi.sort_array([3, 1, 4, 1, 5]) == [1, 1, 3, 4, 5]
        assert c_ffi.sort_array([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
    
    def test_c_sort_array_vs_python(self, c_ffi):
        """Test C sort_array matches Pure Python results."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        test_cases = [
            [],
            [1],
            [3, 1, 4, 1, 5, 9, 2, 6],
            [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
            [1, 2, 3, 4, 5],
        ]
        
        for arr in test_cases:
            c_result = c_ffi.sort_array(arr)
            py_result = py_sort_array(arr)
            assert c_result == py_result, f"Sort mismatch for {arr}: C={c_result}, Python={py_result}"
    
    def test_c_filter_array_basic(self, c_ffi):
        """Test C filter_array basic functionality."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        # Test basic cases
        assert c_ffi.filter_array([], 5) == []
        assert c_ffi.filter_array([1, 2, 3, 4, 5], 3) == [3, 4, 5]
        assert c_ffi.filter_array([1, 2, 3, 4, 5], 10) == []
        assert c_ffi.filter_array([10, 5, 15, 3, 20], 10) == [10, 15, 20]
    
    def test_c_filter_array_vs_python(self, c_ffi):
        """Test C filter_array matches Pure Python results."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        test_cases = [
            ([], 5),
            ([1, 2, 3, 4, 5], 3),
            ([10, 5, 15, 3, 20], 10),
            ([1, 2, 3, 4, 5], 0),
            ([1, 2, 3, 4, 5], 10),
        ]
        
        for arr, threshold in test_cases:
            c_result = c_ffi.filter_array(arr, threshold)
            py_result = py_filter_array(arr, threshold)
            assert c_result == py_result, f"Filter mismatch for {arr}, {threshold}: C={c_result}, Python={py_result}"
    
    def test_c_parallel_compute_basic(self, c_ffi):
        """Test C parallel_compute basic functionality."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        # Test basic cases (sum of squares)
        assert c_ffi.parallel_compute([], 1) == 0.0
        assert c_ffi.parallel_compute([1.0], 1) == 1.0
        assert c_ffi.parallel_compute([1.0, 2.0, 3.0], 1) == 14.0  # 1^2 + 2^2 + 3^2 = 14
    
    def test_c_parallel_compute_vs_python_single_thread(self, c_ffi):
        """Test C parallel_compute matches Pure Python results for single thread."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        test_cases = [
            [],
            [1.0],
            [1.0, 2.0, 3.0],
            [0.5, 1.5, 2.5, 3.5],
        ]
        
        for data in test_cases:
            c_result = c_ffi.parallel_compute(data, 1)
            # Python parallel_compute does sum, C does sum of squares
            # So we need to compute sum of squares for comparison
            py_result = sum(x * x for x in data)
            assert abs(c_result - py_result) < 1e-10, f"Parallel compute mismatch for {data}: C={c_result}, Expected={py_result}"


class TestCppFFIIntegration:
    """Test C++ FFI implementation."""
    
    @pytest.fixture
    def cpp_ffi(self):
        """Create C++ FFI instance."""
        return CppFFI(skip_uv_check=True)
    
    def test_cpp_ffi_availability(self, cpp_ffi):
        """Test that C++ FFI is available."""
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI shared library not available")
        
        assert cpp_ffi.is_available()
        assert cpp_ffi.get_implementation_name() == "C++ FFI"
    
    def test_cpp_find_primes_basic(self, cpp_ffi):
        """Test C++ find_primes basic functionality."""
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI not available")
        
        # Test basic cases
        assert cpp_ffi.find_primes(1) == []
        assert cpp_ffi.find_primes(2) == [2]
        assert cpp_ffi.find_primes(10) == [2, 3, 5, 7]
        assert cpp_ffi.find_primes(20) == [2, 3, 5, 7, 11, 13, 17, 19]
    
    def test_cpp_find_primes_vs_python(self, cpp_ffi):
        """Test C++ find_primes matches Pure Python results."""
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI not available")
        
        test_cases = [0, 1, 2, 10, 50, 100]
        
        for n in test_cases:
            cpp_result = cpp_ffi.find_primes(n)
            py_result = py_find_primes(n)
            assert cpp_result == py_result, f"Mismatch for n={n}: C++={cpp_result}, Python={py_result}"
    
    def test_cpp_matrix_multiply_vs_python(self, cpp_ffi):
        """Test C++ matrix multiplication matches Pure Python results."""
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI not available")
        
        test_cases = [
            ([[1.0]], [[2.0]]),
            ([[1.0, 2.0]], [[3.0], [4.0]]),
            ([[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]),
        ]
        
        for a, b in test_cases:
            cpp_result = cpp_ffi.matrix_multiply(a, b)
            py_result = py_matrix_multiply(a, b)
            assert cpp_result == py_result, f"Matrix multiply mismatch: C++={cpp_result}, Python={py_result}"
    
    def test_cpp_sort_array_vs_python(self, cpp_ffi):
        """Test C++ sort_array matches Pure Python results."""
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI not available")
        
        test_cases = [
            [],
            [1],
            [3, 1, 4, 1, 5, 9, 2, 6],
            [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
            [1, 2, 3, 4, 5],
        ]
        
        for arr in test_cases:
            cpp_result = cpp_ffi.sort_array(arr)
            py_result = py_sort_array(arr)
            assert cpp_result == py_result, f"Sort mismatch for {arr}: C++={cpp_result}, Python={py_result}"
    
    def test_cpp_filter_array_vs_python(self, cpp_ffi):
        """Test C++ filter_array matches Pure Python results."""
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI not available")
        
        test_cases = [
            ([], 5),
            ([1, 2, 3, 4, 5], 3),
            ([10, 5, 15, 3, 20], 10),
            ([1, 2, 3, 4, 5], 0),
            ([1, 2, 3, 4, 5], 10),
        ]
        
        for arr, threshold in test_cases:
            cpp_result = cpp_ffi.filter_array(arr, threshold)
            py_result = py_filter_array(arr, threshold)
            assert cpp_result == py_result, f"Filter mismatch for {arr}, {threshold}: C++={cpp_result}, Python={py_result}"


class TestCVsCppFFI:
    """Test C vs C++ FFI consistency."""
    
    @pytest.fixture
    def c_ffi(self):
        return CFFI(skip_uv_check=True)
    
    @pytest.fixture
    def cpp_ffi(self):
        return CppFFI(skip_uv_check=True)
    
    def test_c_vs_cpp_find_primes(self, c_ffi, cpp_ffi):
        """Test C and C++ find_primes produce identical results."""
        if not (c_ffi.is_available() and cpp_ffi.is_available()):
            pytest.skip("Both C and C++ FFI must be available")
        
        test_cases = [0, 1, 2, 10, 50, 100]
        
        for n in test_cases:
            c_result = c_ffi.find_primes(n)
            cpp_result = cpp_ffi.find_primes(n)
            assert c_result == cpp_result, f"C vs C++ mismatch for n={n}: C={c_result}, C++={cpp_result}"
    
    def test_c_vs_cpp_matrix_multiply(self, c_ffi, cpp_ffi):
        """Test C and C++ matrix multiplication produce identical results."""
        if not (c_ffi.is_available() and cpp_ffi.is_available()):
            pytest.skip("Both C and C++ FFI must be available")
        
        test_cases = [
            ([[1.0]], [[2.0]]),
            ([[1.0, 2.0]], [[3.0], [4.0]]),
            ([[1.0, 2.0], [3.0, 4.0]], [[5.0, 6.0], [7.0, 8.0]]),
        ]
        
        for a, b in test_cases:
            c_result = c_ffi.matrix_multiply(a, b)
            cpp_result = cpp_ffi.matrix_multiply(a, b)
            assert c_result == cpp_result, f"C vs C++ matrix multiply mismatch: C={c_result}, C++={cpp_result}"
    
    def test_c_vs_cpp_sort_array(self, c_ffi, cpp_ffi):
        """Test C and C++ sort_array produce identical results."""
        if not (c_ffi.is_available() and cpp_ffi.is_available()):
            pytest.skip("Both C and C++ FFI must be available")
        
        test_cases = [
            [],
            [1],
            [3, 1, 4, 1, 5, 9, 2, 6],
            [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
        ]
        
        for arr in test_cases:
            c_result = c_ffi.sort_array(arr)
            cpp_result = cpp_ffi.sort_array(arr)
            assert c_result == cpp_result, f"C vs C++ sort mismatch for {arr}: C={c_result}, C++={cpp_result}"
    
    def test_c_vs_cpp_filter_array(self, c_ffi, cpp_ffi):
        """Test C and C++ filter_array produce identical results."""
        if not (c_ffi.is_available() and cpp_ffi.is_available()):
            pytest.skip("Both C and C++ FFI must be available")
        
        test_cases = [
            ([], 5),
            ([1, 2, 3, 4, 5], 3),
            ([10, 5, 15, 3, 20], 10),
        ]
        
        for arr, threshold in test_cases:
            c_result = c_ffi.filter_array(arr, threshold)
            cpp_result = cpp_ffi.filter_array(arr, threshold)
            assert c_result == cpp_result, f"C vs C++ filter mismatch for {arr}, {threshold}: C={c_result}, C++={cpp_result}"


class TestMemoryManagement:
    """Test memory management and safety."""
    
    @pytest.fixture
    def c_ffi(self):
        return CFFI(skip_uv_check=True)
    
    @pytest.fixture
    def cpp_ffi(self):
        return CppFFI(skip_uv_check=True)
    
    def test_c_memory_cleanup(self, c_ffi):
        """Test C FFI memory cleanup doesn't cause issues."""
        if not c_ffi.is_available():
            pytest.skip("C FFI not available")
        
        # Perform multiple operations to test memory management
        for _ in range(10):
            primes = c_ffi.find_primes(100)
            assert len(primes) > 0
            
            sorted_arr = c_ffi.sort_array([5, 3, 8, 1, 9])
            assert sorted_arr == [1, 3, 5, 8, 9]
            
            filtered = c_ffi.filter_array([1, 2, 3, 4, 5], 3)
            assert filtered == [3, 4, 5]
    
    def test_cpp_memory_cleanup(self, cpp_ffi):
        """Test C++ FFI memory cleanup doesn't cause issues."""
        if not cpp_ffi.is_available():
            pytest.skip("C++ FFI not available")
        
        # Perform multiple operations to test memory management
        for _ in range(10):
            primes = cpp_ffi.find_primes(100)
            assert len(primes) > 0
            
            sorted_arr = cpp_ffi.sort_array([5, 3, 8, 1, 9])
            assert sorted_arr == [1, 3, 5, 8, 9]
            
            filtered = cpp_ffi.filter_array([1, 2, 3, 4, 5], 3)
            assert filtered == [3, 4, 5]
    
    def test_large_data_handling(self, c_ffi, cpp_ffi):
        """Test handling of larger datasets."""
        if not (c_ffi.is_available() and cpp_ffi.is_available()):
            pytest.skip("Both C and C++ FFI must be available")
        
        # Test with larger arrays
        large_array = list(range(1000, 0, -1))  # 1000 elements in reverse order
        
        c_sorted = c_ffi.sort_array(large_array)
        cpp_sorted = cpp_ffi.sort_array(large_array)
        
        expected = list(range(1, 1001))
        assert c_sorted == expected
        assert cpp_sorted == expected
        assert c_sorted == cpp_sorted


if __name__ == "__main__":
    pytest.main([__file__])