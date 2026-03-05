# Julia implementations of benchmark functions
# Optimized for performance using Julia's strengths

using LinearAlgebra
using Base.Threads

"""
Find all prime numbers up to n using Sieve of Eratosthenes.
Uses vectorized operations for efficiency.
"""
function find_primes_jl(n::Int)
    if n < 2
        return Int[]
    end
    
    # Create boolean array, true means prime
    is_prime = trues(n)
    is_prime[1] = false  # 1 is not prime
    
    # Sieve of Eratosthenes with vectorized operations
    for i in 2:Int(floor(sqrt(n)))
        if is_prime[i]
            # Mark multiples as composite using vectorized assignment
            is_prime[i*i:i:n] .= false
        end
    end
    
    # Return indices where is_prime is true
    return findall(is_prime)
end

"""
Multiply two matrices using Julia's optimized linear algebra.
Leverages BLAS for high performance.
"""
function matrix_multiply_jl(a, b)
    # PyJulia already converts Python lists to Julia matrices
    # But they might be in column-major format, so we need to handle this
    
    # If inputs are already matrices, use them directly
    if isa(a, Matrix) && isa(b, Matrix)
        # PyJulia converts [[1,2],[3,4]] to column-major format
        # We need to transpose to get the correct row-major interpretation
        A = a'  # Transpose to get correct orientation
        B = b'  # Transpose to get correct orientation
        
        # Use Julia's optimized matrix multiplication (BLAS)
        C = A * B
        
        # Convert back to nested arrays for Python compatibility
        result = []
        for i in 1:size(C, 1)
            row = []
            for j in 1:size(C, 2)
                push!(row, C[i, j])
            end
            push!(result, row)
        end
        
        return result
    else
        # Fallback for other input types
        rows_a, cols_a = length(a), length(a[1])
        rows_b, cols_b = length(b), length(b[1])
        
        # Create Julia matrices
        A = zeros(Float64, rows_a, cols_a)
        B = zeros(Float64, rows_b, cols_b)
        
        # Fill matrices
        for i in 1:rows_a
            for j in 1:cols_a
                A[i, j] = Float64(a[i][j])
            end
        end
        
        for i in 1:rows_b
            for j in 1:cols_b
                B[i, j] = Float64(b[i][j])
            end
        end
        
        # Use Julia's optimized matrix multiplication (BLAS)
        C = A * B
        
        # Convert back to nested arrays for Python compatibility
        result = []
        for i in 1:size(C, 1)
            row = []
            for j in 1:size(C, 2)
                push!(row, C[i, j])
            end
            push!(result, row)
        end
        
        return result
    end
end

"""
Sort array using Julia's efficient sorting algorithms.
Julia's sort is typically very fast.
"""
function sort_array_jl(arr)
    # Convert to Julia array and sort
    julia_arr = Vector{Int}(arr)
    return sort(julia_arr)
end

"""
Filter array elements above threshold using vectorized operations.
Takes advantage of Julia's broadcasting.
"""
function filter_array_jl(arr, threshold)
    # Convert to Julia array
    julia_arr = Vector{Int}(arr)
    
    # Use vectorized filtering (broadcasting)
    return julia_arr[julia_arr .>= threshold]
end

"""
Compute sum of data using Julia's multithreading.
Utilizes @threads macro for parallel computation.
"""
function parallel_compute_jl(data, num_threads)
    # Convert to Julia array
    julia_data = Vector{Float64}(data)
    n = length(julia_data)
    
    if n == 0
        return 0.0
    end
    
    # Set number of threads (if possible)
    # Note: Julia thread count is typically set at startup
    
    # Parallel sum using @threads
    chunk_size = max(1, n ÷ nthreads())
    partial_sums = zeros(Float64, nthreads())
    
    @threads for tid in 1:nthreads()
        start_idx = (tid - 1) * chunk_size + 1
        end_idx = min(tid * chunk_size, n)
        
        if start_idx <= n
            local_sum = 0.0
            for i in start_idx:end_idx
                local_sum += julia_data[i]
            end
            partial_sums[tid] = local_sum
        end
    end
    
    return sum(partial_sums)
end

# Alternative simpler parallel sum using built-in functions
function parallel_compute_simple_jl(data, num_threads)
    julia_data = Vector{Float64}(data)
    return sum(julia_data)  # Julia's sum is already optimized and may use parallelism
end