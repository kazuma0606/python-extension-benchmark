"""Property-based tests for Cython implementation function signature uniformity."""

import inspect
import pytest
from hypothesis import given, strategies as st, settings
from typing import get_type_hints

from benchmark.interface import ImplementationModule
from benchmark import python as python_impl


def test_property_13_function_signature_uniformity():
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
    
    # Try to import Cython implementation
    try:
        from benchmark import cython_ext as cython_impl
        
        cython_functions = {
            'find_primes': cython_impl.find_primes,
            'matrix_multiply': cython_impl.matrix_multiply,
            'sort_array': cython_impl.sort_array,
            'filter_array': cython_impl.filter_array,
            'parallel_compute': cython_impl.parallel_compute,
        }
        
        # Check that all required functions exist
        for func_name in reference_functions:
            assert hasattr(cython_impl, func_name), f"Cython implementation missing function: {func_name}"
        
        # Check function signatures match
        for func_name, ref_func in reference_functions.items():
            cython_func = cython_functions[func_name]
            
            # Get signatures
            ref_sig = inspect.signature(ref_func)
            cython_sig = inspect.signature(cython_func)
            
            # Compare parameter names and count
            ref_params = list(ref_sig.parameters.keys())
            cython_params = list(cython_sig.parameters.keys())
            
            assert len(ref_params) == len(cython_params), \
                f"Parameter count mismatch for {func_name}: reference={len(ref_params)}, cython={len(cython_params)}"
            
            assert ref_params == cython_params, \
                f"Parameter names mismatch for {func_name}: reference={ref_params}, cython={cython_params}"
            
            # Check return type annotations if available
            if ref_sig.return_annotation != inspect.Signature.empty:
                assert cython_sig.return_annotation == ref_sig.return_annotation or \
                       cython_sig.return_annotation == inspect.Signature.empty, \
                    f"Return type mismatch for {func_name}"
    
    except ImportError:
        # Cython extensions not compiled - this is expected in some environments
        pytest.skip("Cython extensions not available - need to be compiled first")
    except NotImplementedError:
        # Cython extensions not compiled - fallback functions raise NotImplementedError
        pytest.skip("Cython extensions not compiled - fallback functions active")


@given(
    func_name=st.sampled_from(['find_primes', 'matrix_multiply', 'sort_array', 'filter_array', 'parallel_compute'])
)
@settings(max_examples=50)
def test_property_13_interface_compliance(func_name):
    """Property test: All implementations must comply with the common interface.
    
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
    
    # Try to test Cython implementation
    try:
        from benchmark import cython_ext as cython_impl
        
        # Check function exists
        assert hasattr(cython_impl, func_name), f"Cython implementation missing function: {func_name}"
        
        cython_func = getattr(cython_impl, func_name)
        
        # Check signatures are compatible
        ref_sig = inspect.signature(ref_func)
        cython_sig = inspect.signature(cython_func)
        
        # Parameter count should match
        assert len(ref_sig.parameters) == len(cython_sig.parameters), \
            f"Parameter count mismatch for {func_name}"
        
        # Parameter names should match
        ref_param_names = list(ref_sig.parameters.keys())
        cython_param_names = list(cython_sig.parameters.keys())
        assert ref_param_names == cython_param_names, \
            f"Parameter names mismatch for {func_name}"
    
    except ImportError:
        pytest.skip("Cython extensions not available")
    except NotImplementedError:
        pytest.skip("Cython extensions not compiled")


def test_cython_module_structure():
    """Test that Cython module has the expected structure."""
    try:
        from benchmark import cython_ext
        
        # Check __all__ is defined
        assert hasattr(cython_ext, '__all__'), "Cython module should define __all__"
        
        expected_functions = [
            'find_primes',
            'matrix_multiply', 
            'sort_array',
            'filter_array',
            'parallel_compute'
        ]
        
        # Check all expected functions are in __all__
        for func_name in expected_functions:
            assert func_name in cython_ext.__all__, f"{func_name} should be in __all__"
            assert hasattr(cython_ext, func_name), f"{func_name} should be available in module"
    
    except ImportError:
        pytest.skip("Cython extensions not available")
    except NotImplementedError:
        pytest.skip("Cython extensions not compiled")