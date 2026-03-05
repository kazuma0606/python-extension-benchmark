# Fallback Julia FFI implementation
# This is a development version - full FFI requires PackageCompiler

println("Julia FFI functions loaded (development mode)")

# Include the main functions
include("C:\Users\yoshi\py_benchmark_test\benchmark\ffi_implementations\julia_ffi\functions.jl")

# Test basic functionality
try
    count_ref = Ref{Cint}(0)
    primes_ptr = find_primes_ffi(Cint(10), pointer_from_objref(count_ref))
    println("Test: Found $(count_ref[]) primes up to 10")
catch e
    println("Test failed: $e")
end
