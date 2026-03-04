"""Test to verify project setup is correct."""

import pytest
from pathlib import Path


def test_project_structure():
    """Verify that the project directory structure exists."""
    benchmark_dir = Path("benchmark")
    
    # Check main directories exist
    assert (benchmark_dir / "python").exists()
    assert (benchmark_dir / "numpy_impl").exists()
    assert (benchmark_dir / "c_ext").exists()
    assert (benchmark_dir / "cpp_ext").exists()
    assert (benchmark_dir / "cython_ext").exists()
    assert (benchmark_dir / "rust_ext").exists()
    assert (benchmark_dir / "runner").exists()
    assert (benchmark_dir / "results").exists()
    
    # Check results subdirectories
    assert (benchmark_dir / "results" / "json").exists()
    assert (benchmark_dir / "results" / "csv").exists()
    assert (benchmark_dir / "results" / "graphs").exists()


def test_interface_module_exists():
    """Verify that the interface module exists and can be imported."""
    from benchmark import interface
    
    # Check that the protocol is defined
    assert hasattr(interface, "ImplementationModule")


def test_pytest_configuration():
    """Verify pytest is configured correctly."""
    import pytest
    
    # Check that pytest is available
    assert pytest.__version__ is not None


def test_hypothesis_configuration():
    """Verify Hypothesis is configured correctly."""
    from hypothesis import settings
    
    # Check that the benchmark profile is loaded
    current_settings = settings()
    assert current_settings.max_examples >= 100
