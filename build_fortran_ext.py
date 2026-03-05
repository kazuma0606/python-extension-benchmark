#!/usr/bin/env python3
"""Build script for Fortran extension using f2py."""

import subprocess
import sys
import os
from pathlib import Path


def build_fortran_extension():
    """Build the Fortran extension using f2py."""
    fortran_dir = Path("benchmark/fortran_ext")
    
    if not fortran_dir.exists():
        print(f"Error: Fortran directory {fortran_dir} does not exist")
        return False
    
    # Change to the Fortran directory
    original_dir = os.getcwd()
    os.chdir(fortran_dir)
    
    try:
        print("Building Fortran extension with f2py...")
        
        # Build using setup.py
        result = subprocess.run([
            sys.executable, "setup.py", "build_ext", "--inplace"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Fortran extension built successfully")
            
            # List generated files
            so_files = list(Path(".").glob("*.so"))
            if so_files:
                print(f"Generated files: {[str(f) for f in so_files]}")
            else:
                print("Warning: No .so files found")
            
            return True
        else:
            print(f"✗ Build failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("Error: f2py not found. Please ensure NumPy is installed.")
        return False
    except Exception as e:
        print(f"Error building Fortran extension: {e}")
        return False
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    success = build_fortran_extension()
    sys.exit(0 if success else 1)