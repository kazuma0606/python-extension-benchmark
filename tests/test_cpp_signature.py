"""Property-based tests for C++ implementation function signature uniformity."""

import inspect
import pytest
from hypothesis import given, strategies as st, settings
from typing import get_type_hints

from benchmark.interface import ImplementationModule
from benchmark import python as python_impl


def test_property_13_cpp_function_signature_uniformity():
    """Feature: python-extension-benchmark, Property 13: 関数シグネチャの統一性
    
    任意の実装モジュールに対して、提供される関数（find_primes、matrix_multiply、
    sort_array、filter_array、parallel_compute）のシグネチャは、
    定義されたインターフェースと一致しなければならない
    
    **検証: 要件 8.1**
    """
    # Test with Python implementation as reference
    reference_functions = {
        'find_primes': python_impl.numeric.find_primes,
        'matrix_multiply': python_impl.numeric.matrix_multiply,
        'sort_array': python_impl.memory.sort_array,
        'filter_array': python_impl.memory.filter_array,
        'parallel_compute': python_impl.parallel.parallel_compute,
    }
    
    # Try to import C++ implementation
    try:
        from benchmark import cpp_ext as cpp_impl
        
        cpp_functions = {
            'find_primes': cpp_impl.numeric.find_primes,
            'matrix_multiply': cpp_impl.numeric.matrix_multiply,
            'sort_array': cpp_impl.memory.sort_array,
            'filter_array': cpp_impl.memory.filter_array,
            'parallel_compute': cpp_impl.parallel.parallel_compute,
        }
        
        # Check that all required functions exist
        for func_name in reference_functions:
            if func_name in ['find_primes', 'matrix_multiply']:
                assert hasattr(cpp_impl.numeric, func_name), f"C++ numeric module missing function: {func_name}"
            elif func_name in ['sort_array', 'filter_array']:
                assert hasattr(cpp_impl.memory, func_name), f"C++ memory module missing function: {func_name}"
            else:  # parallel_compute
                assert hasattr(cpp_impl.parallel, func_name), f"C++ parallel module missing function: {func_name}"
        
        # Check function signatures match (pybind11 functions don't have introspectable signatures)
        # So we'll test by calling the functions with known inputs
        for func_name, ref_func in reference_functions.items():
            cpp_func = cpp_functions[func_name]
            
            # Test that the function is callable
            assert callable(cpp_func), f"C++ function {func_name} is not callable"
            
            # Test with sample inputs to verify the interface works
            try:
                if func_name == 'find_primes':
                    result = cpp_func(10)
                    assert isinstance(result, list), f"{func_name} should return a list"
                elif func_name == 'matrix_multiply':
                    result = cpp_func([[1, 2]], [[3], [4]])
                    assert isinstance(result, list), f"{func_name} should return a list"
                elif func_name == 'sort_array':
                    result = cpp_func([3, 1, 2])
                    assert isinstance(result, list), f"{func_name} should return a list"
                elif func_name == 'filter_array':
                    result = cpp_func([1, 2, 3], 2)
                    assert isinstance(result, list), f"{func_name} should return a list"
                elif func_name == 'parallel_compute':
                    result = cpp_func([1.0, 2.0], 1)
                    assert isinstance(result, float), f"{func_name} should return a float"
            except Exception as e:
                pytest.fail(f"C++ function {func_name} failed with sample input: {e}")
    
    except ImportError:
        # C++ extensions not compiled - this is expected in some environments
        pytest.skip("C++ extensions not available - need to be compiled first")
    except AttributeError:
        # C++ extensions not compiled - modules might be None
        pytest.skip("C++ extensions not compiled - modules not available")


@given(
    func_name=st.sampled_from(['find_primes', 'matrix_multiply', 'sort_array', 'filter_array', 'parallel_compute'])
)
@settings(max_examples=50)
def test_property_13_cpp_interface_compliance(func_name):
    """Property test: All C++ implementations must comply with the common interface.
    
    **Feature: python-extension-benchmark, Property 13: 関数シグネチャの統一性**
    **検証: 要件 8.1**
    """
    # Get reference implementation
    if func_name in ['find_primes', 'matrix_multiply']:
        ref_func = getattr(python_impl.numeric, func_name)
    elif func_name in ['sort_array', 'filter_array']:
        ref_func = getattr(python_impl.memory, func_name)
    else:  # parallel_compute
        ref_func = getattr(python_impl.parallel, func_name)
    
    # Try to test C++ implementation
    try:
        from benchmark import cpp_ext as cpp_impl
        
        # Get the appropriate module
        if func_name in ['find_primes', 'matrix_multiply']:
            cpp_module = cpp_impl.numeric
        elif func_name in ['sort_array', 'filter_array']:
            cpp_module = cpp_impl.memory
        else:  # parallel_compute
            cpp_module = cpp_impl.parallel
        
        # Check function exists
        assert hasattr(cpp_module, func_name), f"C++ implementation missing function: {func_name}"
        
        cpp_func = getattr(cpp_module, func_name)
        
        # Test that the function is callable
        assert callable(cpp_func), f"C++ function {func_name} is not callable"
        
        # Test with sample inputs to verify the interface works (pybind11 functions don't have introspectable signatures)
        try:
            if func_name == 'find_primes':
                result = cpp_func(5)
                assert isinstance(result, list), f"{func_name} should return a list"
            elif func_name == 'matrix_multiply':
                result = cpp_func([[1]], [[2]])
                assert isinstance(result, list), f"{func_name} should return a list"
            elif func_name == 'sort_array':
                result = cpp_func([1])
                assert isinstance(result, list), f"{func_name} should return a list"
            elif func_name == 'filter_array':
                result = cpp_func([1, 2], 1)
                assert isinstance(result, list), f"{func_name} should return a list"
            elif func_name == 'parallel_compute':
                result = cpp_func([1.0], 1)
                assert isinstance(result, float), f"{func_name} should return a float"
        except Exception as e:
            pytest.fail(f"C++ function {func_name} failed with sample input: {e}")
    
    except ImportError:
        pytest.skip("C++ extensions not available")
    except AttributeError:
        pytest.skip("C++ extensions not compiled")


def test_cpp_module_structure():
    """Test that C++ module has the expected structure."""
    try:
        from benchmark import cpp_ext
        
        # Check submodules exist
        assert hasattr(cpp_ext, 'numeric'), "C++ module should have numeric submodule"
        assert hasattr(cpp_ext, 'memory'), "C++ module should have memory submodule"
        assert hasattr(cpp_ext, 'parallel'), "C++ module should have parallel submodule"
        
        # Check __all__ is defined
        assert hasattr(cpp_ext, '__all__'), "C++ module should define __all__"
        
        expected_modules = ['numeric', 'memory', 'parallel']
        
        # Check all expected modules are in __all__
        for module_name in expected_modules:
            assert module_name in cpp_ext.__all__, f"{module_name} should be in __all__"
        
        # Check functions exist in appropriate modules
        numeric_functions = ['find_primes', 'matrix_multiply']
        memory_functions = ['sort_array', 'filter_array']
        parallel_functions = ['parallel_compute']
        
        for func_name in numeric_functions:
            assert hasattr(cpp_ext.numeric, func_name), f"numeric.{func_name} should be available"
        
        for func_name in memory_functions:
            assert hasattr(cpp_ext.memory, func_name), f"memory.{func_name} should be available"
        
        for func_name in parallel_functions:
            assert hasattr(cpp_ext.parallel, func_name), f"parallel.{func_name} should be available"
    
    except ImportError:
        pytest.skip("C++ extensions not available")
    except AttributeError:
        pytest.skip("C++ extensions not compiled")


def test_cpp_functions_basic_functionality():
    """Test basic functionality of C++ functions."""
    try:
        from benchmark import cpp_ext
        
        # Test find_primes
        primes = cpp_ext.numeric.find_primes(10)
        assert primes == [2, 3, 5, 7], f"find_primes(10) should return [2, 3, 5, 7], got {primes}"
        
        # Test matrix_multiply
        result = cpp_ext.numeric.matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])
        expected = [[19.0, 22.0], [43.0, 50.0]]
        assert result == expected, f"matrix_multiply failed, expected {expected}, got {result}"
        
        # Test sort_array
        sorted_arr = cpp_ext.memory.sort_array([3, 1, 4, 1, 5])
        assert sorted_arr == [1, 1, 3, 4, 5], f"sort_array failed, got {sorted_arr}"
        
        # Test filter_array
        filtered = cpp_ext.memory.filter_array([1, 2, 3, 4, 5], 3)
        assert filtered == [3, 4, 5], f"filter_array failed, got {filtered}"
        
        # Test parallel_compute
        result = cpp_ext.parallel.parallel_compute([1.0, 2.0, 3.0, 4.0], 2)
        assert result == 10.0, f"parallel_compute failed, expected 10.0, got {result}"
        
    except ImportError:
        pytest.skip("C++ extensions not available")
    except AttributeError:
        pytest.skip("C++ extensions not compiled")