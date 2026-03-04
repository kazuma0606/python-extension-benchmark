#!/usr/bin/env python3
"""Build script for Rust extension using PyO3."""

import subprocess
import sys
import os
from pathlib import Path


def build_rust_extension():
    """Build the Rust extension using maturin."""
    rust_dir = Path("benchmark/rust_ext")
    
    if not rust_dir.exists():
        print(f"Error: Rust directory {rust_dir} does not exist")
        return False
    
    # Change to the Rust directory
    original_dir = os.getcwd()
    os.chdir(rust_dir)
    
    try:
        print("Building Rust extension with maturin...")
        
        # Install maturin if not available
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "maturin"], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("Warning: Could not install maturin")
        
        # Build the extension
        result = subprocess.run([
            sys.executable, "-m", "maturin", "develop", "--release"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Rust extension built successfully")
            return True
        else:
            print(f"✗ Build failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("Error: maturin not found. Please install it with: pip install maturin")
        return False
    except Exception as e:
        print(f"Error building Rust extension: {e}")
        return False
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    success = build_rust_extension()
    sys.exit(0 if success else 1)