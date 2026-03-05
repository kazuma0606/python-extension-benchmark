#!/usr/bin/env python3
"""
Validation script for Julia extension structure
"""

import os
import sys
from pathlib import Path

def validate_julia_extension():
    """Validate that Julia extension files are properly structured."""
    
    julia_ext_dir = Path('benchmark/julia_ext')
    
    # Check if directory exists
    if not julia_ext_dir.exists():
        print("❌ Julia extension directory not found")
        return False
    
    # Check required files
    required_files = [
        '__init__.py',
        'functions.jl',
        'setup.py',
        'README.md'
    ]
    
    missing_files = []
    for file in required_files:
        file_path = julia_ext_dir / file
        if not file_path.exists():
            missing_files.append(file)
        else:
            print(f"✅ {file} exists")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    # Check build script
    build_script = Path('build_julia_ext.py')
    if build_script.exists():
        print("✅ build_julia_ext.py exists")
    else:
        print("❌ build_julia_ext.py not found")
        return False
    
    # Validate Python module structure
    try:
        init_file = julia_ext_dir / '__init__.py'
        with open(init_file, 'r') as f:
            content = f.read()
            
        # Check for required functions
        required_functions = [
            'find_primes',
            'matrix_multiply', 
            'sort_array',
            'filter_array',
            'parallel_compute'
        ]
        
        for func in required_functions:
            if f'def {func}(' in content:
                print(f"✅ Function {func} defined")
            else:
                print(f"❌ Function {func} missing")
                return False
                
    except Exception as e:
        print(f"❌ Error reading __init__.py: {e}")
        return False
    
    # Validate Julia functions file
    try:
        functions_file = julia_ext_dir / 'functions.jl'
        with open(functions_file, 'r') as f:
            content = f.read()
            
        # Check for Julia function implementations
        julia_functions = [
            'find_primes_jl',
            'matrix_multiply_jl',
            'sort_array_jl', 
            'filter_array_jl',
            'parallel_compute_jl'
        ]
        
        for func in julia_functions:
            if f'function {func}(' in content:
                print(f"✅ Julia function {func} defined")
            else:
                print(f"❌ Julia function {func} missing")
                return False
                
    except Exception as e:
        print(f"❌ Error reading functions.jl: {e}")
        return False
    
    print("✅ Julia extension validation passed!")
    return True

if __name__ == '__main__':
    success = validate_julia_extension()
    sys.exit(0 if success else 1)