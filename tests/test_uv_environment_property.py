"""
UV Environment Property-Based Tests

**Feature: ffi-benchmark-extensions, Property 10: uv環境の確認**
**Validates: Requirements 1.2**

This module contains property-based tests for uv environment validation functionality.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import patch, MagicMock

from benchmark.ffi_implementations.uv_checker import UVEnvironmentChecker, check_uv_environment


class TestUVEnvironmentProperty:
    """Property-based tests for uv environment checking."""
    
    @given(
        virtual_env_path=st.one_of(
            st.none(),
            st.text(
                alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\x00'),
                min_size=1, 
                max_size=50
            ).filter(lambda x: '/' in x or '\\' in x),
            st.just("/path/to/.venv"),
            st.just("C:\\path\\to\\.venv"),
            st.just("/some/other/env")
        )
    )
    @settings(max_examples=50, deadline=5000)
    def test_uv_environment_detection_property(self, virtual_env_path):
        """
        **Feature: ffi-benchmark-extensions, Property 10: uv環境の確認**
        **Validates: Requirements 1.2**
        
        Property: For any virtual environment path, uv detection should correctly identify uv environments.
        """
        # Mock both environment variables and file system to control test conditions
        env_dict = {'VIRTUAL_ENV': virtual_env_path} if virtual_env_path else {}
        
        with patch.dict(os.environ, env_dict, clear=True):
            checker = UVEnvironmentChecker()
            
            # Mock file system operations to prevent real uv.lock detection
            with patch.object(checker, '_find_uv_lock') as mock_uv_lock:
                mock_uv_lock.return_value = None  # No uv.lock found
                
                # Property: Detection should be consistent
                result1 = checker.is_uv_environment_active()
                result2 = checker.is_uv_environment_active()
                assert result1 == result2, "uv environment detection should be consistent"
                
                # Property: If VIRTUAL_ENV is None, should return False
                if virtual_env_path is None:
                    assert not result1, "No VIRTUAL_ENV should result in False"
                
                # Property: If path ends with .venv, should return True (typical uv pattern)
                if virtual_env_path and virtual_env_path.endswith('.venv'):
                    assert result1, f"Path ending with .venv should be detected as uv environment: {virtual_env_path}"
                
                # Property: Detection result should be boolean
                assert isinstance(result1, bool), "Detection result should be boolean"
    
    @given(
        has_uv_lock=st.booleans(),
        has_pyproject=st.booleans(),
        has_virtual_env=st.booleans()
    )
    @settings(max_examples=30, deadline=5000)
    def test_environment_validation_property(self, has_uv_lock, has_pyproject, has_virtual_env):
        """
        **Feature: ffi-benchmark-extensions, Property 10: uv環境の確認**
        **Validates: Requirements 1.2**
        
        Property: Environment validation should correctly assess completeness based on available components.
        """
        checker = UVEnvironmentChecker()
        
        # Mock the file system checks
        with patch.object(checker, '_find_uv_lock') as mock_uv_lock, \
             patch.object(checker, '_find_pyproject_toml') as mock_pyproject, \
             patch.object(checker, 'is_uv_environment_active') as mock_uv_active, \
             patch.object(checker, 'get_uv_version') as mock_uv_version, \
             patch.object(checker, 'check_required_packages') as mock_packages:
            
            # Setup mocks based on test parameters
            mock_uv_lock.return_value = Path('/fake/uv.lock') if has_uv_lock else None
            mock_pyproject.return_value = Path('/fake/pyproject.toml') if has_pyproject else None
            mock_uv_active.return_value = has_virtual_env
            mock_uv_version.return_value = "0.1.0" if has_virtual_env else None
            mock_packages.return_value = {'ctypes': True, 'numpy': True, 'pytest': True, 'hypothesis': True}
            
            is_valid, issues = checker.validate_environment()
            
            # Property: Validation result should be boolean
            assert isinstance(is_valid, bool), "Validation result should be boolean"
            
            # Property: Issues should be a list
            assert isinstance(issues, list), "Issues should be a list"
            
            # Property: If environment is valid, issues list should be empty
            if is_valid:
                assert len(issues) == 0, "Valid environment should have no issues"
            
            # Property: If environment is invalid, issues list should not be empty
            if not is_valid:
                assert len(issues) > 0, "Invalid environment should have issues"
            
            # Property: If no uv environment is active, should be invalid
            if not has_virtual_env:
                assert not is_valid, "No active uv environment should result in invalid state"
                assert any("uv virtual environment is not active" in issue for issue in issues), \
                    "Should report inactive uv environment"
    
    @given(
        package_availability=st.dictionaries(
            st.sampled_from(['ctypes', 'numpy', 'pytest', 'hypothesis']),
            st.booleans(),
            min_size=1,
            max_size=4
        )
    )
    @settings(max_examples=20, deadline=3000)
    def test_package_checking_property(self, package_availability):
        """
        **Feature: ffi-benchmark-extensions, Property 10: uv環境の確認**
        **Validates: Requirements 1.2**
        
        Property: Package checking should correctly report availability for all tested packages.
        """
        checker = UVEnvironmentChecker()
        
        # Mock package imports, but don't mock ctypes since it's handled specially
        original_import = __builtins__['__import__']
        
        def mock_import(name, *args, **kwargs):
            if name == 'ctypes':
                # Always allow ctypes import (it's built-in)
                return original_import(name, *args, **kwargs)
            elif name in package_availability and package_availability[name]:
                return MagicMock()  # Successful import
            else:
                raise ImportError(f"No module named '{name}'")
        
        with patch('builtins.__import__', side_effect=mock_import):
            # ctypes is built-in and should always be available regardless of mocking
            result = checker.check_required_packages()
            
            # Property: Result should be a dictionary
            assert isinstance(result, dict), "Package check result should be dictionary"
            
            # Property: All checked packages should be in result
            expected_packages = {'ctypes', 'numpy', 'pytest', 'hypothesis'}
            for package in expected_packages:
                assert package in result, f"Package {package} should be in result"
            
            # Property: Result values should be boolean
            for package, available in result.items():
                assert isinstance(available, bool), f"Availability for {package} should be boolean"
            
            # Property: ctypes should always be available (built-in module)
            assert result['ctypes'], "ctypes should always be available (built-in)"
            
            # Property: Mocked availability should match result (for non-built-in packages)
            for package, expected_available in package_availability.items():
                if package != 'ctypes':  # Skip ctypes as it's always available
                    assert result[package] == expected_available, \
                        f"Package {package} availability mismatch: expected {expected_available}, got {result[package]}"
    
    @given(
        env_vars=st.dictionaries(
            st.sampled_from(['VIRTUAL_ENV', 'PATH', 'PYTHONPATH']),
            st.text(
                alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\x00'),
                min_size=0, 
                max_size=50
            ),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=20, deadline=3000)
    def test_environment_info_property(self, env_vars):
        """
        **Feature: ffi-benchmark-extensions, Property 10: uv環境の確認**
        **Validates: Requirements 1.2**
        
        Property: Environment info should always return complete information dictionary.
        """
        with patch.dict(os.environ, env_vars, clear=True):
            # Restore VIRTUAL_ENV if it was in the original environment and not overridden
            if 'VIRTUAL_ENV' not in env_vars:
                # Don't set VIRTUAL_ENV, let it be "Not set"
                pass
            
            checker = UVEnvironmentChecker()
            
            # Mock file system operations
            with patch.object(checker, '_find_uv_lock') as mock_uv_lock, \
                 patch.object(checker, '_find_pyproject_toml') as mock_pyproject:
                
                mock_uv_lock.return_value = None
                mock_pyproject.return_value = None
                
                info = checker.get_environment_info()
                
                # Property: Result should be a dictionary
                assert isinstance(info, dict), "Environment info should be dictionary"
                
                # Property: Required keys should be present
                required_keys = {
                    'virtual_env', 'python_executable', 'python_version', 
                    'platform', 'cwd', 'uv_lock_found', 'pyproject_toml'
                }
                for key in required_keys:
                    assert key in info, f"Required key {key} should be in environment info"
                
                # Property: All values should be strings
                for key, value in info.items():
                    assert isinstance(value, str), f"Value for {key} should be string, got {type(value)}"
                
                # Property: VIRTUAL_ENV should match environment variable or be "Not set"
                if 'VIRTUAL_ENV' in env_vars:
                    expected_venv = env_vars['VIRTUAL_ENV'] if env_vars['VIRTUAL_ENV'] else 'Not set'
                else:
                    expected_venv = 'Not set'
                
                assert info['virtual_env'] == expected_venv, \
                    f"VIRTUAL_ENV mismatch: expected '{expected_venv}', got '{info['virtual_env']}'"
    
    def test_setup_instructions_property(self):
        """
        **Feature: ffi-benchmark-extensions, Property 10: uv環境の確認**
        **Validates: Requirements 1.2**
        
        Property: Setup instructions should always be comprehensive and non-empty.
        """
        checker = UVEnvironmentChecker()
        instructions = checker.get_setup_instructions()
        
        # Property: Instructions should be a list
        assert isinstance(instructions, list), "Setup instructions should be a list"
        
        # Property: Instructions should not be empty
        assert len(instructions) > 0, "Setup instructions should not be empty"
        
        # Property: All instructions should be strings
        for instruction in instructions:
            assert isinstance(instruction, str), "Each instruction should be a string"
        
        # Property: Instructions should contain key setup steps
        instruction_text = ' '.join(instructions).lower()
        key_terms = ['uv', 'install', 'sync', 'activate', 'environment']
        for term in key_terms:
            assert term in instruction_text, f"Instructions should mention '{term}'"
    
    @given(
        mock_uv_available=st.booleans(),
        mock_env_active=st.booleans()
    )
    @settings(max_examples=10, deadline=2000)
    def test_check_uv_environment_function_property(self, mock_uv_available, mock_env_active):
        """
        **Feature: ffi-benchmark-extensions, Property 10: uv環境の確認**
        **Validates: Requirements 1.2**
        
        Property: check_uv_environment function should return boolean and handle all environment states.
        """
        with patch('benchmark.ffi_implementations.uv_checker.UVEnvironmentChecker') as mock_checker_class:
            mock_checker = MagicMock()
            mock_checker_class.return_value = mock_checker
            
            # Setup mock behavior
            if mock_uv_available and mock_env_active:
                mock_checker.validate_environment.return_value = (True, [])
            else:
                issues = []
                if not mock_env_active:
                    issues.append("uv virtual environment is not active")
                if not mock_uv_available:
                    issues.append("uv is not installed")
                mock_checker.validate_environment.return_value = (False, issues)
            
            mock_checker.print_setup_instructions.return_value = None
            
            # Suppress print output for testing
            with patch('builtins.print'):
                result = check_uv_environment()
            
            # Property: Result should be boolean
            assert isinstance(result, bool), "check_uv_environment should return boolean"
            
            # Property: Should return True only when environment is fully valid
            expected_result = mock_uv_available and mock_env_active
            assert result == expected_result, \
                f"Expected {expected_result} for uv_available={mock_uv_available}, env_active={mock_env_active}"
            
            # Property: validate_environment should be called
            mock_checker.validate_environment.assert_called_once()


class TestUVEnvironmentIntegration:
    """Integration tests for uv environment checking."""
    
    def test_real_environment_detection(self):
        """
        Test with the actual current environment.
        This is not a property test but validates real-world behavior.
        """
        checker = UVEnvironmentChecker()
        
        # Should not raise exceptions
        is_active = checker.is_uv_environment_active()
        assert isinstance(is_active, bool)
        
        env_info = checker.get_environment_info()
        assert isinstance(env_info, dict)
        assert 'virtual_env' in env_info
        
        package_status = checker.check_required_packages()
        assert isinstance(package_status, dict)
        assert 'ctypes' in package_status
        
        is_valid, issues = checker.validate_environment()
        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)
    
    def test_uv_checker_module_import(self):
        """
        Test that the uv_checker module can be imported and used.
        """
        # Should be able to import without errors
        from benchmark.ffi_implementations.uv_checker import (
            UVEnvironmentChecker, 
            check_uv_environment, 
            require_uv_environment
        )
        
        # Should be able to create instances
        checker = UVEnvironmentChecker()
        assert checker is not None
        
        # Functions should be callable
        assert callable(check_uv_environment)
        assert callable(require_uv_environment)


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])