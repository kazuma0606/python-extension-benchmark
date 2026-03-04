#!/usr/bin/env python3
"""Build script for C++ extensions using pybind11."""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_cpp_extensions():
    """Build C++ extensions using setup.py."""
    cpp_ext_dir = Path("benchmark/cpp_ext")
    
    if not cpp_ext_dir.exists():
        print(f"Error: {cpp_ext_dir} directory not found")
        return False
    
    print("Building C++ extensions...")
    
    # Change to cpp_ext directory
    original_dir = os.getcwd()
    os.chdir(cpp_ext_dir)
    
    try:
        # Build extensions in place
        result = subprocess.run([
            sys.executable, "setup.py", "build_ext", "--inplace"
        ], check=True, capture_output=True, text=True)
        
        print("C++ extensions built successfully!")
        print("Output:", result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error building C++ extensions: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return False
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
        
    finally:
        # Return to original directory
        os.chdir(original_dir)

def clean_build():
    """Clean build artifacts."""
    cpp_ext_dir = Path("benchmark/cpp_ext")
    
    # Remove build directory
    build_dir = cpp_ext_dir / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("Removed build directory")
    
    # Remove .so/.pyd files
    for ext in ["*.so", "*.pyd"]:
        for file in cpp_ext_dir.glob(ext):
            file.unlink()
            print(f"Removed {file}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_build()
    else:
        success = build_cpp_extensions()
        if not success:
            sys.exit(1)