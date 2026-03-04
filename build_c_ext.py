#!/usr/bin/env python3
"""Build script for C extensions."""

import subprocess
import sys
import os
from pathlib import Path

def build_c_extensions():
    """Build the C extension modules."""
    print("Building C extensions...")
    
    # Change to the c_ext directory
    c_ext_dir = Path("benchmark/c_ext")
    if not c_ext_dir.exists():
        print(f"Error: {c_ext_dir} directory not found")
        return False
    
    # Run setup.py build_ext --inplace
    try:
        result = subprocess.run([
            sys.executable, "setup.py", "build_ext", "--inplace"
        ], cwd=c_ext_dir, check=True, capture_output=True, text=True)
        
        print("C extensions built successfully!")
        print("Build output:")
        print(result.stdout)
        
        if result.stderr:
            print("Build warnings/errors:")
            print(result.stderr)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error building C extensions: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = build_c_extensions()
    sys.exit(0 if success else 1)