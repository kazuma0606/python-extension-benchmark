"""
uv environment checker for FFI benchmark system.

This module provides functionality to verify that the system is running
within a proper uv virtual environment before executing FFI benchmarks.
"""

import os
import sys
import subprocess
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UVEnvironmentChecker:
    """Checks and validates uv virtual environment setup."""
    
    def __init__(self):
        self.virtual_env = os.environ.get('VIRTUAL_ENV')
        self.python_executable = sys.executable
        
    def is_uv_environment_active(self) -> bool:
        """Check if a uv virtual environment is currently active.
        
        Returns:
            True if uv environment is active, False otherwise
        """
        if not self.virtual_env:
            return False
        
        # Check if the virtual environment path contains .venv (typical uv pattern)
        venv_path = Path(self.virtual_env)
        if venv_path.name == '.venv':
            return True
        
        # Additional check: see if uv.lock exists in parent directories
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            if (parent / 'uv.lock').exists():
                return True
        
        return False
    
    def get_environment_info(self) -> Dict[str, str]:
        """Get detailed information about the current environment.
        
        Returns:
            Dictionary containing environment information
        """
        info = {
            'virtual_env': self.virtual_env or 'Not set',
            'python_executable': self.python_executable,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'platform': sys.platform,
            'cwd': str(Path.cwd())
        }
        
        # Check for uv.lock
        uv_lock_path = self._find_uv_lock()
        info['uv_lock_found'] = str(uv_lock_path) if uv_lock_path else 'Not found'
        
        # Check for pyproject.toml
        pyproject_path = self._find_pyproject_toml()
        info['pyproject_toml'] = str(pyproject_path) if pyproject_path else 'Not found'
        
        return info
    
    def _find_uv_lock(self) -> Optional[Path]:
        """Find uv.lock file in current or parent directories."""
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            uv_lock = parent / 'uv.lock'
            if uv_lock.exists():
                return uv_lock
        return None
    
    def _find_pyproject_toml(self) -> Optional[Path]:
        """Find pyproject.toml file in current or parent directories."""
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            pyproject = parent / 'pyproject.toml'
            if pyproject.exists():
                return pyproject
        return None
    
    def check_required_packages(self) -> Dict[str, bool]:
        """Check if required packages are installed.
        
        Returns:
            Dictionary mapping package names to availability status
        """
        required_packages = [
            'ctypes',  # Built-in, should always be available
            'numpy',
            'pytest',
            'hypothesis'  # For property-based testing
        ]
        
        package_status = {}
        
        for package in required_packages:
            try:
                if package == 'ctypes':
                    import ctypes
                    package_status[package] = True
                else:
                    __import__(package)
                    package_status[package] = True
            except ImportError:
                package_status[package] = False
        
        return package_status
    
    def get_uv_version(self) -> Optional[str]:
        """Get the version of uv if available.
        
        Returns:
            uv version string or None if not available
        """
        try:
            result = subprocess.run(['uv', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    def validate_environment(self) -> Tuple[bool, List[str]]:
        """Validate the complete environment setup.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if we're in a virtual environment (either uv or regular venv)
        in_venv = (hasattr(sys, 'real_prefix') or 
                   (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
        
        if not in_venv:
            issues.append("No virtual environment detected (uv or venv)")
        
        # Check if uv is installed (optional if we're in a working venv)
        uv_version = self.get_uv_version()
        if not uv_version and not in_venv:
            issues.append("uv is not installed or not in PATH")
        
        # Check required packages
        package_status = self.check_required_packages()
        missing_packages = [pkg for pkg, available in package_status.items() if not available]
        if missing_packages:
            issues.append(f"Missing required packages: {', '.join(missing_packages)}")
        
        # Check for project files (optional if we're in a working environment)
        if not self._find_uv_lock() and not in_venv:
            issues.append("uv.lock file not found in project directory")
        
        return len(issues) == 0, issues
    
    def print_environment_status(self):
        """Print detailed environment status to console."""
        print("=" * 60)
        print("UV ENVIRONMENT STATUS")
        print("=" * 60)
        
        # Basic environment info
        env_info = self.get_environment_info()
        for key, value in env_info.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        print()
        
        # uv version
        uv_version = self.get_uv_version()
        print(f"UV Version: {uv_version or 'Not available'}")
        
        print()
        
        # Package status
        print("Required Packages:")
        package_status = self.check_required_packages()
        for package, available in package_status.items():
            status = "✓ Available" if available else "✗ Missing"
            print(f"  {package}: {status}")
        
        print()
        
        # Overall validation
        is_valid, issues = self.validate_environment()
        if is_valid:
            print("✓ Environment validation: PASSED")
        else:
            print("✗ Environment validation: FAILED")
            print("\nIssues found:")
            for issue in issues:
                print(f"  - {issue}")
        
        print("=" * 60)
    
    def get_setup_instructions(self) -> List[str]:
        """Get setup instructions for uv environment.
        
        Returns:
            List of setup instruction strings
        """
        instructions = [
            "To set up the uv environment for FFI benchmarks:",
            "",
            "1. Install uv (if not already installed):",
            "   curl -LsSf https://astral.sh/uv/install.sh | sh",
            "   # or on Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"",
            "",
            "2. Navigate to the project directory:",
            "   cd /path/to/py_benchmark_test",
            "",
            "3. Create and activate uv environment:",
            "   uv sync",
            "   source .venv/bin/activate  # On Unix/macOS",
            "   # or",
            "   .venv\\Scripts\\activate     # On Windows",
            "",
            "4. Verify the environment:",
            "   python -c \"from benchmark.ffi_implementations.uv_checker import UVEnvironmentChecker; UVEnvironmentChecker().print_environment_status()\"",
            "",
            "5. Install additional dependencies if needed:",
            "   uv add numpy pytest hypothesis",
            "",
            "For more information, see: https://docs.astral.sh/uv/"
        ]
        
        return instructions
    
    def print_setup_instructions(self):
        """Print setup instructions to console."""
        instructions = self.get_setup_instructions()
        for instruction in instructions:
            print(instruction)


def check_uv_environment() -> bool:
    """Convenience function to check uv environment.
    
    Returns:
        True if environment is properly set up, False otherwise
    """
    checker = UVEnvironmentChecker()
    is_valid, issues = checker.validate_environment()
    
    if not is_valid:
        # Check if we're in any virtual environment as a fallback
        in_venv = (hasattr(sys, 'real_prefix') or 
                   (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
        
        if in_venv:
            # If we're in a virtual environment, only check for critical issues
            critical_issues = [issue for issue in issues 
                             if "Missing required packages" in issue]
            
            if not critical_issues:
                # We're in a working virtual environment, that's good enough
                return True
        
        print("\n" + "!" * 60)
        print("WARNING: UV ENVIRONMENT ISSUES DETECTED")
        print("!" * 60)
        
        for issue in issues:
            print(f"  ✗ {issue}")
        
        print("\nSetup instructions:")
        print("-" * 40)
        checker.print_setup_instructions()
        print("!" * 60)
        
        return False
    
    return True


def require_uv_environment():
    """Decorator/function to require uv environment.
    
    Raises:
        RuntimeError: If uv environment is not properly set up
    """
    if not check_uv_environment():
        raise RuntimeError(
            "uv virtual environment is required but not properly set up. "
            "Please follow the setup instructions above."
        )


if __name__ == "__main__":
    # Command-line interface for environment checking
    checker = UVEnvironmentChecker()
    checker.print_environment_status()
    
    if not checker.validate_environment()[0]:
        print("\nSetup Instructions:")
        print("-" * 40)
        checker.print_setup_instructions()