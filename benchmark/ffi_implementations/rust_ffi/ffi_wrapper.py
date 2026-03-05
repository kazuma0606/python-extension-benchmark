"""
Rust FFI wrapper implementation.

This module provides a Python wrapper for Rust functions using ctypes FFI.
"""

import os
import subprocess
import sys
import platform
from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class RustFFI(FFIBase):
    """Rust FFI implementation using ctypes."""
    
    def __init__(self, skip_uv_check=False):
        """Initialize Rust FFI implementation.
        
        Args:
            skip_uv_check: If True, skip uv environment check (for testing)
        """
        # Ensure uv environment is active (unless skipped for testing)
        if not skip_uv_check and not os.environ.get('PYTEST_CURRENT_TEST'):
            require_uv_environment()
        
        # Get the directory where this file is located
        library_dir = os.path.dirname(__file__)
        
        # Try to build the library if it doesn't exist
        self._ensure_library_built(library_dir)
        
        # Initialize with library name (without extension) and directory
        super().__init__("librustfunctions", library_dir)
    
    def _ensure_library_built(self, library_dir: str):
        """Ensure the Rust library is built."""
        # Determine expected library name
        system = platform.system().lower()
        if system == 'windows':
            lib_name = 'librustfunctions.dll'
        elif system == 'darwin':
            lib_name = 'librustfunctions.dylib'
        else:
            lib_name = 'librustfunctions.so'
        
        lib_path = os.path.join(library_dir, lib_name)
        
        # If library doesn't exist, try to build it
        if not os.path.exists(lib_path):
            self._build_library(library_dir, lib_name)
    
    def _build_library(self, library_dir: str, lib_name: str):
        """Build the Rust shared library."""
        try:
            # Check if Cargo is available
            result = subprocess.run(['cargo', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("Warning: Cargo not found. Rust FFI will be unavailable.")
                return
            
            # Change to library directory
            original_cwd = os.getcwd()
            os.chdir(library_dir)
            
            # Build the library in release mode
            result = subprocess.run([
                'cargo', 'build', '--release'
            ], capture_output=True, text=True, check=True)
            
            # Find the generated shared library and copy it
            target_dir = os.path.join(library_dir, 'target', 'release')
            
            # Look for the library in the target directory
            import glob
            system = platform.system().lower()
            
            if system == 'windows':
                pattern = os.path.join(target_dir, '*.dll')
            elif system == 'darwin':
                pattern = os.path.join(target_dir, '*.dylib')
            else:
                pattern = os.path.join(target_dir, '*.so')
            
            built_files = glob.glob(pattern)
            
            # Also check for the specific library name
            if not built_files:
                if system == 'windows':
                    specific_file = os.path.join(target_dir, 'rust_ffi_functions.dll')
                elif system == 'darwin':
                    specific_file = os.path.join(target_dir, 'librustrfunctions.dylib')
                else:
                    specific_file = os.path.join(target_dir, 'librustrfunctions.so')
                
                if os.path.exists(specific_file):
                    built_files = [specific_file]
            
            if built_files:
                # Copy the first found file to our expected location
                import shutil
                shutil.copy2(built_files[0], lib_name)
                print(f"Successfully built Rust FFI library: {lib_name}")
            else:
                print("Warning: Rust build completed but no shared library found")
                
        except subprocess.CalledProcessError as e:
            print(f"Failed to build Rust FFI library: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
        except Exception as e:
            print(f"Error building Rust FFI library: {e}")
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        return "Rust FFI"