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
        
        # Build the extension using maturin build instead of develop
        result = subprocess.run([
            sys.executable, "-m", "maturin", "build", "--release", "--out", "dist"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Build failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
        
        # Install the built wheel
        dist_dir = Path("dist")
        if dist_dir.exists():
            wheel_files = list(dist_dir.glob("*.whl"))
            if wheel_files:
                wheel_file = wheel_files[0]  # Use the first wheel file
                install_result = subprocess.run([
                    sys.executable, "-m", "pip", "install", str(wheel_file), "--force-reinstall"
                ], capture_output=True, text=True)
                
                if install_result.returncode == 0:
                    print("✓ Rust extension built and installed successfully")
                    return True
                else:
                    print(f"✗ Installation failed:")
                    print(f"stdout: {install_result.stdout}")
                    print(f"stderr: {install_result.stderr}")
                    return False
            else:
                print("✗ No wheel file found in dist directory")
                return False
        else:
            print("✗ Dist directory not created")
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