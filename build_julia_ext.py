#!/usr/bin/env python3
"""
Julia Extension Build Script

This script sets up the Julia environment and installs necessary packages
for the Python-Julia integration in the benchmark system.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_julia_installation():
    """Check if Julia is installed and accessible."""
    try:
        result = subprocess.run(['julia', '--version'], 
                              capture_output=True, text=True, check=True)
        logger.info(f"Julia found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Julia not found. Please install Julia first.")
        return False

def install_julia_packages():
    """Install required Julia packages for Python integration."""
    packages = [
        'PyCall',
        'LinearAlgebra',  # Usually built-in, but ensure it's available
    ]
    
    julia_commands = []
    
    # Add package installation commands
    for package in packages:
        julia_commands.append(f'using Pkg; Pkg.add("{package}")')
    
    # Precompile packages
    julia_commands.append('using Pkg; Pkg.precompile()')
    
    # Test PyCall installation
    julia_commands.append('using PyCall; println("PyCall successfully loaded")')
    
    for cmd in julia_commands:
        try:
            logger.info(f"Running Julia command: {cmd}")
            result = subprocess.run(['julia', '-e', cmd], 
                                  capture_output=True, text=True, check=True)
            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run Julia command: {cmd}")
            logger.error(f"Error: {e.stderr}")
            return False
    
    return True

def install_pyjulia():
    """Install PyJulia for Python-Julia integration."""
    try:
        logger.info("Installing PyJulia...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'julia'], 
                      check=True)
        logger.info("PyJulia installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install PyJulia: {e}")
        return False

def setup_julia_python_integration():
    """Set up Julia-Python integration."""
    try:
        logger.info("Setting up Julia-Python integration...")
        
        # Import julia and set up PyCall
        import julia
        j = julia.Julia(compiled_modules=False)
        
        # Configure PyCall to use the current Python
        python_exe = sys.executable
        julia_cmd = f'''
        using Pkg
        ENV["PYTHON"] = "{python_exe}"
        Pkg.build("PyCall")
        using PyCall
        println("PyCall configured for Python: ", PyCall.python)
        '''
        
        result = subprocess.run(['julia', '-e', julia_cmd], 
                              capture_output=True, text=True, check=True)
        logger.info(f"PyCall configuration: {result.stdout.strip()}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to set up Julia-Python integration: {e}")
        return False

def test_julia_functions():
    """Test that Julia functions can be loaded and executed."""
    try:
        logger.info("Testing Julia functions...")
        
        # Check if functions.jl exists
        julia_ext_dir = Path(__file__).parent / 'benchmark' / 'julia_ext'
        functions_file = julia_ext_dir / 'functions.jl'
        
        if not functions_file.exists():
            logger.error(f"Julia functions file not found: {functions_file}")
            return False
        
        # Test loading and running a simple function
        test_cmd = f'''
        include("{functions_file}")
        result = find_primes_jl(10)
        println("Prime test result: ", result)
        '''
        
        result = subprocess.run(['julia', '-e', test_cmd], 
                              capture_output=True, text=True, check=True)
        logger.info(f"Function test: {result.stdout.strip()}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to test Julia functions: {e}")
        return False

def main():
    """Main build process."""
    logger.info("Starting Julia extension build process...")
    
    # Step 1: Check Julia installation
    if not check_julia_installation():
        logger.error("Julia installation check failed")
        return False
    
    # Step 2: Install PyJulia
    if not install_pyjulia():
        logger.error("PyJulia installation failed")
        return False
    
    # Step 3: Install Julia packages
    if not install_julia_packages():
        logger.error("Julia package installation failed")
        return False
    
    # Step 4: Set up integration
    if not setup_julia_python_integration():
        logger.error("Julia-Python integration setup failed")
        return False
    
    # Step 5: Test functions
    if not test_julia_functions():
        logger.error("Julia function testing failed")
        return False
    
    logger.info("Julia extension build completed successfully!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)