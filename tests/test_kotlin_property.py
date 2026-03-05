"""
Kotlin Extension Property-Based Tests

**Feature: multi-language-extensions, Property 1: 関数シグネチャの統一性**
**Validates: Requirements 5.1**

This module contains property-based tests for Kotlin extension function signature uniformity.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import inspect
from typing import List, get_type_hints, get_origin, get_args
import sys
import os

# Add the benchmark directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'benchmark'))

# Skip tests if Kotlin is not available
pytest_plugins = []

def get_function_signature_info(func):
    """Extract signature information from a function."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    # Filter out 'self' parameter for protocol methods
    parameters = {
        name: {
            'annotation': param.annotation,
            'type_hint': type_hints.get(name, param.annotation)
        }
        for name, param in sig.parameters.items()
        if name != 'self'
    }
    
    return {
        'name': func.__name__,
        'parameters': parameters,
        'return_annotation': sig.return_annotation,
        'return_type_hint': type_hints.get('return', sig.return_annotation)
    }

def signatures_match(sig1, sig2):
    """Check if two function signatures match."""
    # Check function name
    if sig1['name'] != sig2['name']:
        return False, f"Function names differ: {sig1['name']} vs {sig2['name']}"
    
    # Check parameter count
    if len(sig1['parameters']) != len(sig2['parameters']):
        return False, f"Parameter count differs: {len(sig1['parameters'])} vs {len(sig2['parameters'])}"
    
    # Check each parameter
    for (name1, param1), (name2, param2) in zip(sig1['parameters'].items(), sig2['parameters'].items()):
        if name1 != name2:
            return False, f"Parameter names differ: {name1} vs {name2}"
        
        # Compare type hints (more reliable than annotations)
        type1 = param1['type_hint']
        type2 = param2['type_hint']
        
        if not types_equivalent(type1, type2):
            return False, f"Parameter {name1} types differ: {type1} vs {type2}"
    
    # Check return type
    if not types_equivalent(sig1['return_type_hint'], sig2['return_type_hint']):
        return False, f"Return types differ: {sig1['return_type_hint']} vs {sig2['return_type_hint']}"
    
    return True, "Signatures match"

def types_equivalent(type1, type2):
    """Check if two types are equivalent, handling generic types."""
    # Handle exact matches
    if type1 == type2:
        return True
    
    # Handle List[T] types
    if get_origin(type1) is list and get_origin(type2) is list:
        args1 = get_args(type1)
        args2 = get_args(type2)
        if len(args1) == len(args2):
            return all(types_equivalent(a1, a2) for a1, a2 in zip(args1, args2))
    
    # Handle nested List[List[T]] types
    if (get_origin(type1) is list and get_origin(type2) is list and 
        len(get_args(type1)) == 1 and len(get_args(type2)) == 1):
        inner1 = get_args(type1)[0]
        inner2 = get_args(type2)[0]
        if (get_origin(inner1) is list and get_origin(inner2) is list):
            return types_equivalent(inner1, inner2)
    
    # Handle basic type equivalence
    if str(type1) == str(type2):
        return True
    
    return False

@pytest.mark.skipif(False, reason="Run in Docker environment")
class TestKotlinPropertyDocker:
    """Property-based tests for Kotlin extension - Docker environment only."""
    
    def test_function_signature_uniformity(self):
        """
        **Feature: multi-language-extensions, Property 1: 関数シグネチャの統一性**
        **Validates: Requirements 5.1**
        
        Property: All Kotlin extension functions should have signatures that match the unified interface.
        """
        try:
            from benchmark import kotlin_ext
            from benchmark.interface import ImplementationModule
            
            # Get the expected signatures from the interface protocol
            interface_functions = {
                'find_primes': ImplementationModule.find_primes,
                'matrix_multiply': ImplementationModule.matrix_multiply,
                'sort_array': ImplementationModule.sort_array,
                'filter_array': ImplementationModule.filter_array,
                'parallel_compute': ImplementationModule.parallel_compute
            }
            
            # Get the actual functions from Kotlin extension
            kotlin_functions = {
                'find_primes': kotlin_ext.find_primes,
                'matrix_multiply': kotlin_ext.matrix_multiply,
                'sort_array': kotlin_ext.sort_array,
                'filter_array': kotlin_ext.filter_array,
                'parallel_compute': kotlin_ext.parallel_compute
            }
            
            # Check each function signature
            for func_name in interface_functions:
                interface_func = interface_functions[func_name]
                kotlin_func = kotlin_functions[func_name]
                
                # Get signature information
                interface_sig = get_function_signature_info(interface_func)
                kotlin_sig = get_function_signature_info(kotlin_func)
                
                # Property: Signatures should match
                match, reason = signatures_match(interface_sig, kotlin_sig)
                assert match, f"Kotlin {func_name} signature mismatch: {reason}"
                
                # Property: Function should be callable
                assert callable(kotlin_func), f"Kotlin {func_name} should be callable"
                
                # Property: Function should have proper docstring
                assert kotlin_func.__doc__ is not None, f"Kotlin {func_name} should have docstring"
                
        except ImportError:
            pytest.skip("Kotlin extension not available")
    
    @given(
        n=st.integers(min_value=2, max_value=100)
    )
    @settings(max_examples=10, deadline=3000)
    def test_find_primes_signature_compliance(self, n):
        """
        **Feature: multi-language-extensions, Property 1: 関数シグネチャの統一性**
        **Validates: Requirements 5.1**
        
        Property: find_primes function should accept int and return List[int].
        """
        try:
            from benchmark import kotlin_ext
            
            # Property: Function should accept integer input
            result = kotlin_ext.find_primes(n)
            
            # Property: Function should return a list
            assert isinstance(result, list), f"find_primes should return list, got {type(result)}"
            
            # Property: All elements should be integers
            for item in result:
                assert isinstance(item, int), f"find_primes should return List[int], found {type(item)}"
                
        except ImportError:
            pytest.skip("Kotlin extension not available")
    
    @given(
        size=st.integers(min_value=1, max_value=5),
        value=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=10, deadline=5000)
    def test_matrix_multiply_signature_compliance(self, size, value):
        """
        **Feature: multi-language-extensions, Property 1: 関数シグネチャの統一性**
        **Validates: Requirements 5.1**
        
        Property: matrix_multiply function should accept List[List[float]] and return List[List[float]].
        """
        try:
            from benchmark import kotlin_ext
            
            # Create test matrices
            matrix_a = [[value + i + j for j in range(size)] for i in range(size)]
            matrix_b = [[value + i + j + size*size for j in range(size)] for i in range(size)]
            
            # Property: Function should accept List[List[float]] inputs
            result = kotlin_ext.matrix_multiply(matrix_a, matrix_b)
            
            # Property: Function should return a list
            assert isinstance(result, list), f"matrix_multiply should return list, got {type(result)}"
            
            # Property: Result should be List[List[float]]
            for row in result:
                assert isinstance(row, list), f"matrix_multiply should return List[List[float]], found row type {type(row)}"
                for item in row:
                    assert isinstance(item, (int, float)), f"matrix_multiply should return List[List[float]], found item type {type(item)}"
                    
        except ImportError:
            pytest.skip("Kotlin extension not available")
    
    @given(
        arr=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=50)
    )
    @settings(max_examples=10, deadline=3000)
    def test_sort_array_signature_compliance(self, arr):
        """
        **Feature: multi-language-extensions, Property 1: 関数シグネチャの統一性**
        **Validates: Requirements 5.1**
        
        Property: sort_array function should accept List[int] and return List[int].
        """
        try:
            from benchmark import kotlin_ext
            
            # Property: Function should accept List[int] input
            result = kotlin_ext.sort_array(arr)
            
            # Property: Function should return a list
            assert isinstance(result, list), f"sort_array should return list, got {type(result)}"
            
            # Property: All elements should be integers
            for item in result:
                assert isinstance(item, int), f"sort_array should return List[int], found {type(item)}"
                
        except ImportError:
            pytest.skip("Kotlin extension not available")
    
    @given(
        arr=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=50),
        threshold=st.integers(min_value=-50, max_value=50)
    )
    @settings(max_examples=10, deadline=3000)
    def test_filter_array_signature_compliance(self, arr, threshold):
        """
        **Feature: multi-language-extensions, Property 1: 関数シグネチャの統一性**
        **Validates: Requirements 5.1**
        
        Property: filter_array function should accept List[int] and int, return List[int].
        """
        try:
            from benchmark import kotlin_ext
            
            # Property: Function should accept List[int] and int inputs
            result = kotlin_ext.filter_array(arr, threshold)
            
            # Property: Function should return a list
            assert isinstance(result, list), f"filter_array should return list, got {type(result)}"
            
            # Property: All elements should be integers
            for item in result:
                assert isinstance(item, int), f"filter_array should return List[int], found {type(item)}"
                
        except ImportError:
            pytest.skip("Kotlin extension not available")
    
    @given(
        data=st.lists(st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False), min_size=0, max_size=50),
        num_threads=st.integers(min_value=1, max_value=8)
    )
    @settings(max_examples=10, deadline=3000)
    def test_parallel_compute_signature_compliance(self, data, num_threads):
        """
        **Feature: multi-language-extensions, Property 1: 関数シグネチャの統一性**
        **Validates: Requirements 5.1**
        
        Property: parallel_compute function should accept List[float] and int, return float.
        """
        try:
            from benchmark import kotlin_ext
            
            # Property: Function should accept List[float] and int inputs
            result = kotlin_ext.parallel_compute(data, num_threads)
            
            # Property: Function should return a float
            assert isinstance(result, (int, float)), f"parallel_compute should return float, got {type(result)}"
            
            # Convert to float for consistency
            result_float = float(result)
            assert isinstance(result_float, float), f"parallel_compute result should be convertible to float"
                
        except ImportError:
            pytest.skip("Kotlin extension not available")

# Tests that can run in any environment (with mocking)
class TestKotlinPropertyMocked:
    """Property-based tests with mocking for local development."""
    
    def test_signature_analysis_helpers(self):
        """Test the signature analysis helper functions."""
        # Test function signature extraction
        def sample_func(x: int, y: List[float]) -> List[int]:
            return []
        
        sig_info = get_function_signature_info(sample_func)
        
        assert sig_info['name'] == 'sample_func'
        assert 'x' in sig_info['parameters']
        assert 'y' in sig_info['parameters']
        assert sig_info['parameters']['x']['type_hint'] == int
        
        # Test type equivalence
        assert types_equivalent(int, int)
        assert types_equivalent(List[int], List[int])
        assert types_equivalent(List[List[float]], List[List[float]])
        assert not types_equivalent(int, float)
        assert not types_equivalent(List[int], List[float])
    
    def test_interface_protocol_structure(self):
        """Test that the interface protocol has the expected structure."""
        from benchmark.interface import ImplementationModule
        
        # Check that all expected methods exist
        expected_methods = ['find_primes', 'matrix_multiply', 'sort_array', 'filter_array', 'parallel_compute']
        
        for method_name in expected_methods:
            assert hasattr(ImplementationModule, method_name), f"Interface missing method: {method_name}"
            
            method = getattr(ImplementationModule, method_name)
            sig_info = get_function_signature_info(method)
            
            # Each method should have proper signature structure
            assert sig_info['name'] == method_name
            assert isinstance(sig_info['parameters'], dict)
            assert sig_info['return_type_hint'] is not None

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
            "tests/test_kotlin_property.py::TestKotlinPropertyDocker",
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
        pytest.main([__file__ + "::TestKotlinPropertyMocked", "-v"])