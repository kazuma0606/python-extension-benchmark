"""
Cython FFI wrapper implementation.

This module provides a Python wrapper for Cython functions using ctypes FFI.
"""

import os
import subprocess
import sys
from ..ffi_base import FFIBase
from ..uv_checker import require_uv_environment


class CythonFFI(FFIBase):
    """Cython FFI implementation using ctypes."""
    
    def __init__(self, skip_uv_check=False):
        """Initialize Cython FFI implementation.
        
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
        super().__init__("libcythonfunctions", library_dir)
    
    def _ensure_library_built(self, library_dir: str):
        """Ensure the Cython library is built."""
        import platform
        
        # Determine expected library name
        system = platform.system().lower()
        if system == 'windows':
            lib_name = 'libcythonfunctions.dll'
        elif system == 'darwin':
            lib_name = 'libcythonfunctions.dylib'
        else:
            lib_name = 'libcythonfunctions.so'
        
        lib_path = os.path.join(library_dir, lib_name)
        
        # If library doesn't exist, try to build it
        if not os.path.exists(lib_path):
            self._build_library(library_dir, lib_name)
    
    def _build_library(self, library_dir: str, lib_name: str):
        """Build the Cython shared library."""
        try:
            # Change to library directory
            original_cwd = os.getcwd()
            os.chdir(library_dir)
            
            # Build the extension
            result = subprocess.run([
                sys.executable, 'setup.py', 'build_ext', '--inplace'
            ], capture_output=True, text=True, check=True)
            
            # Find the generated shared library and rename it
            import glob
            import platform
            
            system = platform.system().lower()
            if system == 'windows':
                pattern = '*.pyd'
            else:
                pattern = '*.so'
            
            built_files = glob.glob(pattern)
            if built_files:
                # Rename the first found file to our expected name
                os.rename(built_files[0], lib_name)
                print(f"Successfully built Cython FFI library: {lib_name}")
            else:
                print("Warning: Cython build completed but no shared library found")
                
        except subprocess.CalledProcessError as e:
            print(f"Failed to build Cython FFI library: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
        except Exception as e:
            print(f"Error building Cython FFI library: {e}")
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    def get_implementation_name(self) -> str:
        """Get the name of this FFI implementation."""
        return "Cython FFI"