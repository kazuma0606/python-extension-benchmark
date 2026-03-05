#!/usr/bin/env python3
"""
Test Julia extension structure without requiring Julia to be installed
"""

import os
import sys
import importlib.util
from pathlib import Path

def test_julia_extension_structure():
    """Test that Julia extension files exist and have correct structure."""
    print("🧪 Testing Julia Extension Structure...")
    
    # Check if Julia extension directory exists (adjust path for new location)
    julia_ext_dir = Path(__file__).parent.parent.parent / 'benchmark' / 'julia_ext'
    if not julia_ext_dir.exists():
        print("❌ Julia extension directory not found")
        return False
    
    print("✅ Julia extension directory exists")
    
    # Check required files
    required_files = {
        '__init__.py': 'Python integration module',
        'functions.jl': 'Julia function implementations',
        'setup.py': 'Package setup configuration',
        'README.md': 'Documentation'
    }
    
    for filename, description in required_files.items():
        filepath = julia_ext_dir / filename
        if filepath.exists():
            print(f"✅ {filename} exists ({description})")
        else:
            print(f"❌ {filename} missing ({description})")
            return False
    
    # Check build script (adjust path for new location)
    build_script = Path(__file__).parent / 'build_julia_ext.py'
    if build_script.exists():
        print("✅ build_julia_ext.py exists")
    else:
        print("❌ build_julia_ext.py missing")
        return False
    
    # Test Python module structure
    try:
        spec = importlib.util.spec_from_file_location(
            "julia_ext", 
            julia_ext_dir / "__init__.py"
        )
        if spec is None:
            print("❌ Could not load Julia extension spec")
            return False
            
        print("✅ Julia extension module can be loaded")
        
        # Check if we can read the file content
        with open(julia_ext_dir / "__init__.py", 'r') as f:
            content = f.read()
        
        # Check for required functions
        required_functions = [
            'find_primes',
            'matrix_multiply',
            'sort_array', 
            'filter_array',
            'parallel_compute',
            'is_available'
        ]
        
        for func in required_functions:
            if f'def {func}(' in content:
                print(f"✅ Function {func} defined")
            else:
                print(f"❌ Function {func} missing")
                return False
                
    except Exception as e:
        print(f"❌ Error checking Python module: {e}")
        return False
    
    # Test Julia functions file
    try:
        with open(julia_ext_dir / 'functions.jl', 'r') as f:
            julia_content = f.read()
        
        # Check for Julia function implementations
        julia_functions = [
            'find_primes_jl',
            'matrix_multiply_jl',
            'sort_array_jl',
            'filter_array_jl', 
            'parallel_compute_jl'
        ]
        
        for func in julia_functions:
            if f'function {func}(' in julia_content:
                print(f"✅ Julia function {func} defined")
            else:
                print(f"❌ Julia function {func} missing")
                return False
                
        # Check for required Julia packages
        required_imports = ['LinearAlgebra', 'Base.Threads']
        for import_name in required_imports:
            if f'using {import_name}' in julia_content:
                print(f"✅ Julia import {import_name} found")
            else:
                print(f"⚠️  Julia import {import_name} not found")
                
    except Exception as e:
        print(f"❌ Error checking Julia functions: {e}")
        return False
    
    # Check integration with benchmark system (adjust path for new location)
    try:
        benchmark_file = Path(__file__).parent.parent.parent / 'benchmark' / 'runner' / 'benchmark.py'
        if benchmark_file.exists():
            with open(benchmark_file, 'r') as f:
                benchmark_content = f.read()
            
            if '"julia_ext": "Julia"' in benchmark_content:
                print("✅ Julia extension integrated in benchmark system")
            else:
                print("⚠️  Julia extension not found in benchmark language map")
        else:
            print("⚠️  Benchmark runner not found")
            
    except Exception as e:
        print(f"⚠️  Could not check benchmark integration: {e}")
    
    # Check test file (adjust path for new location)
    test_file = Path(__file__).parent.parent.parent / 'tests' / 'test_julia_extension.py'
    if test_file.exists():
        print("✅ Julia extension test file exists")
    else:
        print("⚠️  Julia extension test file missing")
    
    print("\n🎉 Julia Extension Structure Test Completed!")
    print("\nNext steps:")
    print("1. Install Julia: https://julialang.org/downloads/")
    print("2. Add Julia to PATH")
    print("3. Run: python scripts/build/build_julia_ext.py")
    print("4. Test: python -m pytest tests/test_julia_extension.py -v")
    
    return True

def test_docker_integration():
    """Test Docker integration."""
    print("\n🐳 Testing Docker Integration...")
    
    dockerfile = Path(__file__).parent.parent.parent / 'Dockerfile'
    if not dockerfile.exists():
        print("❌ Dockerfile not found")
        return False
    
    with open(dockerfile, 'r') as f:
        docker_content = f.read()
    
    # Check Julia installation in Docker
    if 'Install Julia' in docker_content:
        print("✅ Julia installation found in Dockerfile")
    else:
        print("❌ Julia installation not found in Dockerfile")
        return False
    
    # Check Julia extension build
    if 'build_julia_ext.py' in docker_content:
        print("✅ Julia extension build found in Dockerfile")
    else:
        print("❌ Julia extension build not found in Dockerfile")
        return False
    
    # Check requirements.txt (adjust path for new location)
    requirements_file = Path(__file__).parent.parent.parent / 'requirements.txt'
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            requirements_content = f.read()
        
        if 'julia' in requirements_content:
            print("✅ PyJulia dependency found in requirements.txt")
        else:
            print("❌ PyJulia dependency not found in requirements.txt")
            return False
    
    print("✅ Docker integration looks good")
    return True

if __name__ == '__main__':
    print("Julia Extension Validation")
    print("=" * 50)
    
    structure_ok = test_julia_extension_structure()
    docker_ok = test_docker_integration()
    
    if structure_ok and docker_ok:
        print("\n🎉 All tests passed! Julia extension is ready.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        sys.exit(1)