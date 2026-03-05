"""
Julia Extension Property-Based Tests

**Feature: multi-language-extensions, Property 2: 数値計算の正確性**
**Validates: Requirements 1.2, 1.3**

This module contains property-based tests for Julia extension numerical computation accuracy.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import math
from typing import List

# Skip tests if Julia is not available
pytest_plugins = []

def is_prime(n: int) -> bool:
    """Helper function to check if a number is prime."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

def get_expected_primes(n: int) -> List[int]:
    """Get expected prime numbers up to n using reference implementation."""
    return [i for i in range(2, n + 1) if is_prime(i)]

def matrix_multiply_reference(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Reference implementation of matrix multiplication."""
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    
    if cols_a != rows_b:
        raise ValueError("Matrix dimensions don't match for multiplication")
    
    result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
    
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    
    return result

@pytest.mark.skipif(False, reason="Run in Docker environment")
class TestJuliaPropertyDocker:
    """Property-based tests for Julia extension - Docker environment only."""
    
    @given(n=st.integers(min_value=2, max_value=1000))
    @settings(max_examples=100, deadline=5000)
    def test_find_primes_correctness(self, n):
        """
        **Feature: multi-language-extensions, Property 2: 数値計算の正確性**
        **Validates: Requirements 1.2**
        
        Property: For any integer n >= 2, find_primes(n) returns mathematically correct prime numbers.
        """
        try:
            from benchmark import julia_ext
            
            # Skip if Julia is not available
            if not julia_ext.is_available():
                pytest.skip("Julia extension not available")
            
            # Get result from Julia implementation
            result = julia_ext.find_primes(n)
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            elif isinstance(result, list):
                result = [int(x) for x in result]
            
            # Get expected result from reference implementation
            expected = get_expected_primes(n)
            
            # Property: Result should match mathematical definition of primes
            assert result == expected, f"Julia primes for n={n}: {result}, expected: {expected}"
            
            # Property: All returned numbers should be prime
            for prime in result:
                assert is_prime(prime), f"Number {prime} is not prime"
            
            # Property: All primes up to n should be included
            for i in range(2, n + 1):
                if is_prime(i):
                    assert i in result, f"Prime {i} missing from result"
                    
        except ImportError:
            pytest.skip("Julia extension not available")
    
    @given(
        size=st.integers(min_value=1, max_value=10),
        values=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50, deadline=10000)
    def test_matrix_multiply_correctness(self, size, values):
        """
        **Feature: multi-language-extensions, Property 2: 数値計算の正確性**
        **Validates: Requirements 1.3**
        
        Property: For any valid matrices A and B, matrix_multiply(A, B) returns mathematically correct result.
        """
        try:
            from benchmark import julia_ext
            
            # Skip if Julia is not available
            if not julia_ext.is_available():
                pytest.skip("Julia extension not available")
            
            # Create square matrices for simplicity
            matrix_a = [[values + i * size + j for j in range(size)] for i in range(size)]
            matrix_b = [[values + i * size + j + size * size for j in range(size)] for i in range(size)]
            
            # Get result from Julia implementation
            result = julia_ext.matrix_multiply(matrix_a, matrix_b)
            
            # Convert numpy types to Python types if needed
            if hasattr(result, 'tolist'):
                result = result.tolist()
            elif isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'tolist'):
                result = [row.tolist() if hasattr(row, 'tolist') else [float(x) for x in row] for row in result]
            
            # Get expected result from reference implementation
            expected = matrix_multiply_reference(matrix_a, matrix_b)
            
            # Property: Result dimensions should be correct
            assert len(result) == len(expected), "Result row count mismatch"
            assert len(result[0]) == len(expected[0]), "Result column count mismatch"
            
            # Property: Result should match mathematical matrix multiplication
            for i in range(len(result)):
                for j in range(len(result[0])):
                    # Allow small floating point differences
                    assert abs(result[i][j] - expected[i][j]) < 1e-10, \
                        f"Matrix multiplication mismatch at [{i}][{j}]: {result[i][j]} != {expected[i][j]}"
                        
        except ImportError:
            pytest.skip("Julia extension not available")

# Tests that can run in any environment (with mocking)
class TestJuliaPropertyMocked:
    """Property-based tests with mocking for local development."""
    
    @given(n=st.integers(min_value=2, max_value=100))
    @settings(max_examples=20)
    def test_find_primes_property_structure(self, n):
        """
        Test the property structure without requiring Julia.
        This validates the test logic itself.
        """
        # Reference implementation test
        expected = get_expected_primes(n)
        
        # Property: All returned numbers should be prime
        for prime in expected:
            assert is_prime(prime), f"Reference implementation error: {prime} is not prime"
        
        # Property: Result should be sorted
        assert expected == sorted(expected), "Primes should be in ascending order"
        
        # Property: No duplicates
        assert len(expected) == len(set(expected)), "No duplicate primes should exist"
    
    def test_matrix_multiply_property_structure(self):
        """
        Test matrix multiplication property structure.
        """
        # Test with simple 2x2 matrices
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[5.0, 6.0], [7.0, 8.0]]
        
        expected = matrix_multiply_reference(a, b)
        
        # Expected result: [[19.0, 22.0], [43.0, 50.0]]
        assert expected == [[19.0, 22.0], [43.0, 50.0]]
        
        # Property: Result dimensions
        assert len(expected) == len(a)
        assert len(expected[0]) == len(b[0])

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
            "tests/test_julia_property.py::TestJuliaPropertyDocker",
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
        pytest.main([__file__ + "::TestJuliaPropertyMocked", "-v"])