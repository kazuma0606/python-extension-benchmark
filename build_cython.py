#!/usr/bin/env python3
"""Build script for Cython extensions.

This script builds the Cython extensions for the benchmark project.
Run this script from the project root directory.

Usage:
    python build_cython.py
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Build Cython extensions."""
    project_root = Path(__file__).parent
    cython_dir = project_root / "benchmark" / "cython_ext"
    setup_py = cython_dir / "setup.py"
    
    if not setup_py.exists():
        print(f"Error: setup.py not found at {setup_py}")
        sys.exit(1)
    
    print("Building Cython extensions...")
    print(f"Working directory: {project_root}")
    print(f"Setup script: {setup_py}")
    
    try:
        # Change to project root directory
        os.chdir(project_root)
        
        # Run the setup script
        cmd = [sys.executable, str(setup_py), "build_ext", "--inplace"]
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("Build successful!")
        print("Output:", result.stdout)
        
        if result.stderr:
            print("Warnings:", result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code {e.returncode}")
        print("Error output:", e.stderr)
        print("Standard output:", e.stdout)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()