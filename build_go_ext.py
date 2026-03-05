#!/usr/bin/env python3
"""
Build script for Go extension

This script builds the Go shared library for the Python benchmark system.
It handles cross-platform compilation and automatic dependency resolution.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


def check_go_installation():
    """Check if Go is installed and accessible"""
    try:
        result = subprocess.run(['go', 'version'], capture_output=True, text=True, check=True)
        print(f"✓ Go found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Go not found. Please install Go 1.21 or later.")
        print("  Download from: https://golang.org/dl/")
        return False


def check_c_compiler():
    """Check if C compiler is available"""
    compilers = ['gcc', 'clang', 'cc']
    for compiler in compilers:
        try:
            result = subprocess.run([compiler, '--version'], capture_output=True, text=True, check=True)
            print(f"✓ C compiler found: {compiler}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("✗ No C compiler found. Please install gcc or clang.")
    return False


def get_library_name():
    """Get the appropriate library name for the current platform"""
    system = platform.system().lower()
    if system == 'windows':
        return 'libgofunctions.dll'
    elif system == 'darwin':
        return 'libgofunctions.dylib'
    else:  # Linux and others
        return 'libgofunctions.so'


def build_go_extension():
    """Build the Go shared library"""
    go_ext_dir = Path('benchmark/go_ext')
    
    if not go_ext_dir.exists():
        print(f"✗ Go extension directory not found: {go_ext_dir}")
        return False
    
    print(f"Building Go extension in {go_ext_dir}")
    
    # Change to Go extension directory
    original_cwd = os.getcwd()
    os.chdir(go_ext_dir)
    
    try:
        # Initialize Go module if needed
        if not Path('go.mod').exists():
            print("Initializing Go module...")
            subprocess.run(['go', 'mod', 'init', 'gofunctions'], check=True)
        
        # Tidy dependencies
        print("Updating Go dependencies...")
        subprocess.run(['go', 'mod', 'tidy'], check=True)
        
        # Build shared library
        lib_name = get_library_name()
        print(f"Building shared library: {lib_name}")
        
        build_cmd = [
            'go', 'build',
            '-buildmode=c-shared',
            '-o', lib_name,
            'functions.go'
        ]
        
        result = subprocess.run(build_cmd, capture_output=True, text=True, check=True)
        
        # Check if library was created
        if Path(lib_name).exists():
            print(f"✓ Go shared library built successfully: {lib_name}")
            
            # Also check for header file
            header_name = lib_name.replace('.so', '.h').replace('.dylib', '.h').replace('.dll', '.h')
            if Path(header_name).exists():
                print(f"✓ C header file generated: {header_name}")
            
            return True
        else:
            print(f"✗ Shared library not found after build: {lib_name}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Go build failed:")
        print(f"  Command: {' '.join(e.cmd)}")
        print(f"  Return code: {e.returncode}")
        if e.stdout:
            print(f"  Stdout: {e.stdout}")
        if e.stderr:
            print(f"  Stderr: {e.stderr}")
        return False
    
    finally:
        os.chdir(original_cwd)


def test_go_extension():
    """Test the built Go extension"""
    try:
        # Try to import the Go extension
        sys.path.insert(0, 'benchmark')
        from go_ext import find_primes, matrix_multiply, sort_array, filter_array, parallel_compute
        
        print("Testing Go extension functions...")
        
        # Test find_primes
        primes = find_primes(20)
        expected_primes = [2, 3, 5, 7, 11, 13, 17, 19]
        if primes == expected_primes:
            print("✓ find_primes test passed")
        else:
            print(f"✗ find_primes test failed: got {primes}, expected {expected_primes}")
            return False
        
        # Test matrix_multiply
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        result = matrix_multiply(a, b)
        expected = [[19, 22], [43, 50]]
        if result == expected:
            print("✓ matrix_multiply test passed")
        else:
            print(f"✗ matrix_multiply test failed: got {result}, expected {expected}")
            return False
        
        # Test sort_array
        arr = [3, 1, 4, 1, 5, 9]
        sorted_arr = sort_array(arr)
        expected_sorted = [1, 1, 3, 4, 5, 9]
        if sorted_arr == expected_sorted:
            print("✓ sort_array test passed")
        else:
            print(f"✗ sort_array test failed: got {sorted_arr}, expected {expected_sorted}")
            return False
        
        # Test filter_array
        arr = [1, 5, 3, 8, 2]
        filtered = filter_array(arr, 4)
        expected_filtered = [5, 8]
        if filtered == expected_filtered:
            print("✓ filter_array test passed")
        else:
            print(f"✗ filter_array test failed: got {filtered}, expected {expected_filtered}")
            return False
        
        # Test parallel_compute
        data = [1.0, 2.0, 3.0, 4.0]
        total = parallel_compute(data, 2)
        expected_total = 10.0
        if abs(total - expected_total) < 1e-10:
            print("✓ parallel_compute test passed")
        else:
            print(f"✗ parallel_compute test failed: got {total}, expected {expected_total}")
            return False
        
        print("✓ All Go extension tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Go extension test failed: {e}")
        return False


def clean_build_artifacts():
    """Clean build artifacts"""
    go_ext_dir = Path('benchmark/go_ext')
    if not go_ext_dir.exists():
        return
    
    artifacts = ['*.so', '*.dylib', '*.dll', '*.h']
    for pattern in artifacts:
        for file in go_ext_dir.glob(pattern):
            try:
                file.unlink()
                print(f"Removed: {file}")
            except OSError as e:
                print(f"Warning: Could not remove {file}: {e}")


def main():
    """Main build function"""
    print("=" * 60)
    print("Building Go Extension for Python Benchmark System")
    print("=" * 60)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'clean':
            print("Cleaning build artifacts...")
            clean_build_artifacts()
            return
        elif sys.argv[1] == 'test':
            print("Testing Go extension...")
            if test_go_extension():
                sys.exit(0)
            else:
                sys.exit(1)
        elif sys.argv[1] == '--help':
            print("Usage: python build_go_ext.py [clean|test|--help]")
            print("  clean: Remove build artifacts")
            print("  test:  Test the built extension")
            print("  --help: Show this help message")
            return
    
    # Check prerequisites
    print("Checking prerequisites...")
    if not check_go_installation():
        sys.exit(1)
    
    if not check_c_compiler():
        sys.exit(1)
    
    # Build extension
    print("\nBuilding Go extension...")
    if not build_go_extension():
        print("\n✗ Go extension build failed!")
        sys.exit(1)
    
    # Test extension
    print("\nTesting Go extension...")
    if not test_go_extension():
        print("\n✗ Go extension tests failed!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Go extension built and tested successfully!")
    print("=" * 60)
    
    # Show usage information
    print("\nUsage:")
    print("  from benchmark.go_ext import find_primes, matrix_multiply")
    print("  primes = find_primes(100)")
    print("  result = matrix_multiply([[1, 2], [3, 4]], [[5, 6], [7, 8]])")


if __name__ == '__main__':
    main()