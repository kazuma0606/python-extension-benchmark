#!/usr/bin/env python3
"""
Julia Property-Based Test Runner for Docker Environment

This script builds the Docker image and runs Julia property-based tests
to validate numerical computation accuracy.
"""

import subprocess
import sys
import os
import time

def build_docker_image():
    """Build the Docker image with Julia extension."""
    print("🐳 Building Docker image with Julia extension...")
    
    try:
        # Change to project root directory
        os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        result = subprocess.run([
            "docker", "build", "-t", "benchmark", "."
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ Docker image built successfully")
            return True
        else:
            print("❌ Docker build failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Docker build timed out")
        return False
    except Exception as e:
        print(f"❌ Docker build error: {e}")
        return False

def run_julia_property_tests():
    """Run Julia property-based tests in Docker container."""
    print("🧪 Running Julia property-based tests in Docker...")
    
    try:
        # Run the property tests in Docker
        docker_cmd = [
            "docker", "run", "--rm",
            "-e", "DOCKER_ENV=1",
            "benchmark",
            "python", "-m", "pytest", 
            "tests/test_julia_property.py::TestJuliaPropertyDocker",
            "-v", "--tb=short", "-x"
        ]
        
        print(f"Running command: {' '.join(docker_cmd)}")
        
        result = subprocess.run(docker_cmd, timeout=300)
        
        if result.returncode == 0:
            print("✅ Julia property tests passed!")
            return True
        else:
            print("❌ Julia property tests failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Property tests timed out")
        return False
    except Exception as e:
        print(f"❌ Property test error: {e}")
        return False

def run_julia_function_verification():
    """Verify Julia functions work correctly in Docker."""
    print("🔍 Verifying Julia functions in Docker...")
    
    try:
        docker_cmd = [
            "docker", "run", "--rm",
            "benchmark",
            "julia", "test_julia_functions.jl"
        ]
        
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Julia functions verified:")
            print(result.stdout)
            return True
        else:
            print("❌ Julia function verification failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Julia verification error: {e}")
        return False

def run_julia_extension_test():
    """Test Julia extension availability in Docker."""
    print("🔧 Testing Julia extension in Docker...")
    
    try:
        docker_cmd = [
            "docker", "run", "--rm",
            "benchmark",
            "python", "-c", 
            "from benchmark import julia_ext; print('Julia available:', julia_ext.is_available())"
        ]
        
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=60)
        
        print("Julia extension test output:")
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        return "Julia available: True" in result.stdout
        
    except Exception as e:
        print(f"❌ Julia extension test error: {e}")
        return False

def main():
    """Main execution flow."""
    print("Julia Property-Based Test Runner")
    print("=" * 50)
    
    # Step 1: Build Docker image
    if not build_docker_image():
        print("❌ Failed to build Docker image")
        return False
    
    # Step 2: Verify Julia functions work
    if not run_julia_function_verification():
        print("❌ Julia functions not working properly")
        return False
    
    # Step 3: Test Julia extension
    if not run_julia_extension_test():
        print("⚠️  Julia extension may have issues, but continuing...")
    
    # Step 4: Run property-based tests
    if not run_julia_property_tests():
        print("❌ Property-based tests failed")
        return False
    
    print("\n🎉 All Julia property tests completed successfully!")
    print("✅ Property 2 (数値計算の正確性) validated")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)