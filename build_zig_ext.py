#!/usr/bin/env python3
"""
Build script for Zig extension module.
Compiles Zig code to a shared library for Python integration.
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def check_zig_installation():
    """Check if Zig is installed and accessible."""
    try:
        result = subprocess.run(['zig', 'version'], 
                              capture_output=True, text=True, check=True)
        print(f"Found Zig version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Zig is not installed or not in PATH")
        print("Please install Zig from https://ziglang.org/download/")
        return False

def get_library_name():
    """Get the appropriate library name for the current platform."""
    system = platform.system().lower()
    if system == "linux":
        return "libzigfunctions.so"
    elif system == "darwin":  # macOS
        return "libzigfunctions.dylib"
    elif system == "windows":
        return "zigfunctions.dll"
    else:
        # Default to Linux naming
        return "libzigfunctions.so"

def build_zig_extension():
    """Build the Zig extension."""
    print("Building Zig extension...")
    
    # Check Zig installation
    if not check_zig_installation():
        return False
    
    # Get paths
    script_dir = Path(__file__).parent
    zig_dir = script_dir / "benchmark" / "zig_ext"
    
    if not zig_dir.exists():
        print(f"Error: Zig extension directory not found: {zig_dir}")
        return False
    
    # Change to Zig directory
    original_cwd = os.getcwd()
    os.chdir(zig_dir)
    
    try:
        # Clean previous builds
        for pattern in ["*.dll", "*.so", "*.dylib", "*.lib", "*.pdb"]:
            for file in Path(".").glob(pattern):
                if file.name.startswith("functions") or file.name.startswith("libzigfunctions"):
                    file.unlink()
        
        # Build the shared library directly
        print("Compiling Zig shared library...")
        build_cmd = [
            'zig', 'build-lib', 'functions.zig',
            '-dynamic',
            '-lc',
            '-O', 'ReleaseFast'
        ]
        
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True)
        print("Zig compilation successful!")
        
        # Find the built library and rename it appropriately
        expected_lib_name = get_library_name()
        
        # Look for the generated library file
        built_libs = list(Path(".").glob("functions.*"))
        built_libs.extend(list(Path(".").glob("libfunctions.*")))
        
        if not built_libs:
            print(f"Error: No library files found after build")
            return False
        
        # Find the shared library (not .lib or .pdb files)
        shared_lib = None
        for lib in built_libs:
            if lib.suffix in ['.dll', '.so', '.dylib']:
                shared_lib = lib
                break
        
        if not shared_lib:
            print(f"Error: No shared library found in: {[str(lib) for lib in built_libs]}")
            return False
        
        # Rename to expected name if different
        target_lib = Path(expected_lib_name)
        if shared_lib.name != expected_lib_name:
            print(f"Renaming {shared_lib.name} to {expected_lib_name}")
            shared_lib.rename(target_lib)
        else:
            target_lib = shared_lib
        
        # Verify the library exists
        if target_lib.exists():
            print(f"Successfully built Zig extension: {target_lib}")
            return True
        else:
            print("Error: Failed to create library file")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Zig build failed with return code {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error during build: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def test_zig_extension():
    """Test the built Zig extension."""
    print("\nTesting Zig extension...")
    
    try:
        # Add the benchmark directory to Python path
        script_dir = Path(__file__).parent
        benchmark_dir = script_dir / "benchmark"
        sys.path.insert(0, str(benchmark_dir))
        
        # Import and test the extension
        import zig_ext
        
        if not zig_ext.is_available():
            print("Error: Zig extension is not available after build")
            return False
        
        # Test basic functionality
        print("Testing find_primes(10)...")
        primes = zig_ext.find_primes(10)
        expected_primes = [2, 3, 5, 7]
        if primes == expected_primes:
            print(f"✓ find_primes test passed: {primes}")
        else:
            print(f"✗ find_primes test failed: got {primes}, expected {expected_primes}")
            return False
        
        print("Testing sort_array([3, 1, 4, 1, 5])...")
        sorted_arr = zig_ext.sort_array([3, 1, 4, 1, 5])
        expected_sorted = [1, 1, 3, 4, 5]
        if sorted_arr == expected_sorted:
            print(f"✓ sort_array test passed: {sorted_arr}")
        else:
            print(f"✗ sort_array test failed: got {sorted_arr}, expected {expected_sorted}")
            return False
        
        print("Testing parallel_compute([1.0, 2.0, 3.0, 4.0], 2)...")
        result = zig_ext.parallel_compute([1.0, 2.0, 3.0, 4.0], 2)
        expected_sum = 10.0
        if abs(result - expected_sum) < 1e-10:
            print(f"✓ parallel_compute test passed: {result}")
        else:
            print(f"✗ parallel_compute test failed: got {result}, expected {expected_sum}")
            return False
        
        print("All Zig extension tests passed!")
        return True
        
    except ImportError as e:
        print(f"Error importing Zig extension: {e}")
        return False
    except Exception as e:
        print(f"Error testing Zig extension: {e}")
        return False

def main():
    """Main build function."""
    print("=" * 50)
    print("Building Zig Extension for Python Benchmark")
    print("=" * 50)
    
    # Build the extension
    if not build_zig_extension():
        print("\n❌ Zig extension build failed!")
        sys.exit(1)
    
    # Test the extension
    if not test_zig_extension():
        print("\n❌ Zig extension tests failed!")
        sys.exit(1)
    
    print("\n✅ Zig extension built and tested successfully!")
    print("\nThe Zig extension is now ready for benchmarking.")

if __name__ == "__main__":
    main()