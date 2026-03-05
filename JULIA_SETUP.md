# Julia Extension Setup Guide

This guide helps you set up Julia for the benchmark system.

## Julia Installation

### Option 1: Manual Installation (Recommended)
1. Download Julia from https://julialang.org/downloads/
2. Install Julia and make sure it's added to PATH
3. Verify installation: `julia --version`

### Option 2: Using Chocolatey (Windows)
```powershell
# Install Julia
choco install julia

# Add Julia to PATH manually if needed
# Find Julia installation directory and add to PATH
```

### Option 3: Using Docker (Recommended for Development)
The Docker environment already includes Julia setup. Build and run:
```bash
docker build -t benchmark .
docker run -it benchmark
```

## Julia Package Setup

After Julia is installed, run the build script:
```bash
python build_julia_ext.py
```

This will:
1. Install PyJulia (`pip install julia`)
2. Install required Julia packages (PyCall, LinearAlgebra)
3. Configure PyCall to work with your Python installation
4. Test the Julia functions

## Manual Julia Package Installation

If the build script fails, you can install packages manually:

```julia
# Start Julia REPL
julia

# Install packages
using Pkg
Pkg.add("PyCall")
Pkg.add("LinearAlgebra")  # Usually built-in

# Configure PyCall for your Python
ENV["PYTHON"] = "/path/to/your/python"  # Use your Python path
Pkg.build("PyCall")

# Test
using PyCall
println("PyCall configured for: ", PyCall.python)
```

## Testing Julia Extension

### Test 1: Import Test
```python
from benchmark import julia_ext
print("Julia available:", julia_ext.is_available())
```

### Test 2: Function Test (if Julia is available)
```python
from benchmark import julia_ext

if julia_ext.is_available():
    # Test prime finding
    primes = julia_ext.find_primes(20)
    print("Primes up to 20:", primes)
    
    # Test matrix multiplication
    a = [[1, 2], [3, 4]]
    b = [[5, 6], [7, 8]]
    result = julia_ext.matrix_multiply(a, b)
    print("Matrix multiplication result:", result)
else:
    print("Julia extension not available")
```

### Test 3: Run Test Suite
```bash
python -m pytest tests/test_julia_extension.py -v
```

## Troubleshooting

### Julia Not Found in PATH
If Julia is installed but not found:

**Windows:**
1. Find Julia installation directory (usually `C:\Users\{username}\AppData\Local\Programs\Julia\Julia-{version}\bin`)
2. Add to PATH environment variable
3. Restart terminal/IDE

**Linux/Mac:**
1. Find Julia installation directory
2. Add to PATH in `.bashrc` or `.zshrc`:
   ```bash
   export PATH="/path/to/julia/bin:$PATH"
   ```

### PyJulia Installation Issues
```bash
# Reinstall PyJulia
pip uninstall julia
pip install julia

# Or install from source
pip install git+https://github.com/JuliaPy/pyjulia
```

### PyCall Configuration Issues
```julia
# In Julia REPL, reconfigure PyCall
using Pkg
ENV["PYTHON"] = "/path/to/python"  # Your Python executable
Pkg.build("PyCall")
```

### Docker Environment
If you're having issues with local installation, use Docker:
```bash
# Build Docker image
docker build -t benchmark .

# Run tests in Docker
docker run benchmark python -m pytest tests/test_julia_extension.py -v

# Run interactive shell
docker run -it benchmark bash
```

## Performance Notes

- Julia uses JIT compilation, so first runs may be slower
- Subsequent runs should show significant performance improvements
- Julia excels at numerical computations and should outperform Python
- Matrix operations use optimized BLAS libraries
- Parallel operations utilize Julia's threading capabilities

## Integration with Benchmark System

Once Julia is set up, it will be automatically included in benchmark runs:

```python
from benchmark.runner.benchmark import BenchmarkRunner

runner = BenchmarkRunner()
implementations = runner.load_implementations([
    "python", "numpy_impl", "c_ext", "cpp_ext", 
    "rust_ext", "julia_ext"  # Julia extension
])

results = runner.run_all_scenarios(implementations)
```

The Julia extension follows the same interface as other extensions and provides:
- `find_primes(n)` - Prime number finding
- `matrix_multiply(a, b)` - Matrix multiplication  
- `sort_array(arr)` - Array sorting
- `filter_array(arr, threshold)` - Array filtering
- `parallel_compute(data, num_threads)` - Parallel computation