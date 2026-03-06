# Julia build script for creating shared library
# Uses PackageCompiler.jl to create C ABI compatible shared library

using Pkg

# Install PackageCompiler if not available
try
    using PackageCompiler
catch
    println("Installing PackageCompiler.jl...")
    Pkg.add("PackageCompiler")
    using PackageCompiler
end

# Get the directory of this script
script_dir = @__DIR__

# Define source and target files
julia_file = joinpath(script_dir, "functions.jl")
output_dir = script_dir

# Determine library name based on platform
if Sys.iswindows()
    lib_name = "libjuliafunctions.dll"
elseif Sys.isapple()
    lib_name = "libjuliafunctions.dylib"
else
    lib_name = "libjuliafunctions.so"
end

lib_path = joinpath(output_dir, lib_name)

println("Building Julia FFI shared library...")
println("Source: $julia_file")
println("Target: $lib_path")

try
    # Create shared library using PackageCompiler
    # Note: This requires Julia 1.9+ for @ccallable support in PackageCompiler
    create_library(julia_file, lib_path; 
                   lib_name="juliafunctions",
                   precompile_execution_file=nothing,
                   precompile_statements_file=nothing,
                   incremental=false,
                   filter_stdlibs=true)
    
    println("Successfully built Julia FFI library: $lib_path")
    
    # Verify the library exists
    if isfile(lib_path)
        println("Library file verified: $(filesize(lib_path)) bytes")
    else
        println("Warning: Library file not found after build")
    end
    
catch e
    println("Error building Julia FFI library: $e")
    println("\nFallback: Creating a simple test library...")
    
    # Fallback: Create a minimal Julia script that can be used for testing
    # This won't be a true shared library but can be used for development
    fallback_script = """
    # Fallback Julia FFI implementation
    # This is a development version - full FFI requires PackageCompiler
    
    println("Julia FFI functions loaded (development mode)")
    
    # Include the main functions
    include("$julia_file")
    
    # Test basic functionality
    try
        count_ref = Ref{Cint}(0)
        primes_ptr = find_primes_ffi(Cint(10), pointer_from_objref(count_ref))
        println("Test: Found \$(count_ref[]) primes up to 10")
    catch e
        println("Test failed: \$e")
    end
    """
    
    fallback_path = joinpath(output_dir, "fallback_test.jl")
    open(fallback_path, "w") do f
        write(f, fallback_script)
    end
    
    println("Created fallback test script: $fallback_path")
    println("\nNote: For full FFI support, ensure you have:")
    println("  - Julia 1.9+ with PackageCompiler.jl")
    println("  - Proper C compiler toolchain")
    println("  - All required system libraries")
end

println("\nBuild process completed.")