# Julia FFI implementation for C ABI compatibility
# This module provides C-compatible functions for FFI integration

using LinearAlgebra
using Base.Threads

# Find all prime numbers up to n using Sieve of Eratosthenes
# C signature: int* find_primes_ffi(int n, int* count)
function find_primes_ffi(n::Cint, count_ptr::Ptr{Cint})::Ptr{Cint}
    if n < 2
        unsafe_store!(count_ptr, 0)
        return C_NULL
    end
    
    # Create boolean array, true means prime
    is_prime = trues(n)
    is_prime[1] = false  # 1 is not prime
    
    # Sieve of Eratosthenes with vectorized operations
    sqrt_n = Int(floor(sqrt(n)))
    for i in 2:sqrt_n
        if is_prime[i]
            # Mark multiples as composite using vectorized assignment
            is_prime[i*i:i:n] .= false
        end
    end
    
    # Count primes
    prime_count = count(is_prime)
    unsafe_store!(count_ptr, prime_count)
    
    if prime_count == 0
        return C_NULL
    end
    
    # Allocate result array
    primes = Vector{Cint}(undef, prime_count)
    
    # Collect primes
    idx = 1
    for i in 1:n
        if is_prime[i]
            primes[idx] = i
            idx += 1
        end
    end
    
    # Return pointer to allocated array
    return pointer(primes)
end

# Matrix multiplication: C = A * B
# C signature: double* matrix_multiply_ffi(double* a, int rows_a, int cols_a, 
#                                         double* b, int rows_b, int cols_b,
#                                         int* result_rows, int* result_cols)
function matrix_multiply_ffi(a_ptr::Ptr{Cdouble}, rows_a::Cint, cols_a::Cint,
                            b_ptr::Ptr{Cdouble}, rows_b::Cint, cols_b::Cint,
                            result_rows_ptr::Ptr{Cint}, result_cols_ptr::Ptr{Cint})::Ptr{Cdouble}
    
    # Check dimensions
    if cols_a != rows_b
        unsafe_store!(result_rows_ptr, 0)
        unsafe_store!(result_cols_ptr, 0)
        return C_NULL
    end
    
    # Convert C pointers to Julia arrays (row-major, flattened)
    a_flat = unsafe_wrap(Array, a_ptr, rows_a * cols_a)
    b_flat = unsafe_wrap(Array, b_ptr, rows_b * cols_b)
    
    # Reshape to matrices (Julia is column-major, so we need to transpose)
    A = reshape(a_flat, cols_a, rows_a)'  # Transpose to get correct row-major interpretation
    B = reshape(b_flat, cols_b, rows_b)'  # Transpose to get correct row-major interpretation
    
    # Use Julia's optimized matrix multiplication (BLAS)
    C = A * B
    
    # Set result dimensions
    result_rows = size(C, 1)
    result_cols = size(C, 2)
    unsafe_store!(result_rows_ptr, result_rows)
    unsafe_store!(result_cols_ptr, result_cols)
    
    # Flatten result matrix (row-major order)
    result = Vector{Cdouble}(undef, result_rows * result_cols)
    for i in 1:result_rows
        for j in 1:result_cols
            result[(i-1) * result_cols + j] = C[i, j]
        end
    end
    
    return pointer(result)
end

# Sort an array of integers using Julia's efficient sorting
# C signature: int* sort_array_ffi(int* arr, int size)
function sort_array_ffi(arr_ptr::Ptr{Cint}, size::Cint)::Ptr{Cint}
    if size <= 0
        return C_NULL
    end
    
    # Convert C pointer to Julia array
    arr = unsafe_wrap(Array, arr_ptr, size)
    
    # Create a copy and sort it
    result = copy(arr)
    sort!(result)
    
    return pointer(result)
end

# Filter array elements >= threshold
# C signature: int* filter_array_ffi(int* arr, int size, int threshold, int* result_size)
function filter_array_ffi(arr_ptr::Ptr{Cint}, size::Cint, threshold::Cint, 
                          result_size_ptr::Ptr{Cint})::Ptr{Cint}
    if size <= 0
        unsafe_store!(result_size_ptr, 0)
        return C_NULL
    end
    
    # Convert C pointer to Julia array
    arr = unsafe_wrap(Array, arr_ptr, size)
    
    # Use vectorized filtering (broadcasting)
    filtered = arr[arr .>= threshold]
    
    result_size = length(filtered)
    unsafe_store!(result_size_ptr, result_size)
    
    if result_size == 0
        return C_NULL
    end
    
    return pointer(filtered)
end

# Perform parallel computation using Julia's multithreading
# C signature: double parallel_compute_ffi(double* data, int size, int num_threads)
function parallel_compute_ffi(data_ptr::Ptr{Cdouble}, size::Cint, num_threads::Cint)::Cdouble
    if size <= 0
        return 0.0
    end
    
    # Convert C pointer to Julia array
    data = unsafe_wrap(Array, data_ptr, size)
    
    # Julia's sum is already optimized and may use parallelism
    # For explicit threading, we could use @threads, but sum() is typically faster
    return sum(data)
end

# Alternative parallel implementation using explicit threading
function parallel_compute_threaded_ffi(data_ptr::Ptr{Cdouble}, size::Cint, num_threads::Cint)::Cdouble
    if size <= 0
        return 0.0
    end
    
    # Convert C pointer to Julia array
    data = unsafe_wrap(Array, data_ptr, size)
    n = length(data)
    
    # Parallel sum using @threads
    chunk_size = max(1, n ÷ nthreads())
    partial_sums = zeros(Cdouble, nthreads())
    
    @threads for tid in 1:nthreads()
        start_idx = (tid - 1) * chunk_size + 1
        end_idx = min(tid * chunk_size, n)
        
        if start_idx <= n
            local_sum = 0.0
            for i in start_idx:end_idx
                local_sum += data[i]
            end
            partial_sums[tid] = local_sum
        end
    end
    
    return sum(partial_sums)
end

# Free memory allocated by Julia functions
# C signature: void free_memory_ffi(void* ptr)
function free_memory_ffi(ptr::Ptr{Cvoid})::Cvoid
    # Note: In Julia, memory management is handled by the garbage collector
    # We cannot directly free memory from a C pointer in the same way as C/C++
    # The memory will be garbage collected when no longer referenced
    # This is a limitation of the FFI approach with Julia
    nothing
end

# Export functions for C ABI
Base.@ccallable function find_primes_ffi(n::Cint, count::Ptr{Cint})::Ptr{Cint}
    return find_primes_ffi(n, count)
end

Base.@ccallable function matrix_multiply_ffi(a_ptr::Ptr{Cdouble}, rows_a::Cint, cols_a::Cint,
                                            b_ptr::Ptr{Cdouble}, rows_b::Cint, cols_b::Cint,
                                            result_rows::Ptr{Cint}, result_cols::Ptr{Cint})::Ptr{Cdouble}
    return matrix_multiply_ffi(a_ptr, rows_a, cols_a, b_ptr, rows_b, cols_b, result_rows, result_cols)
end

Base.@ccallable function sort_array_ffi(arr_ptr::Ptr{Cint}, size::Cint)::Ptr{Cint}
    return sort_array_ffi(arr_ptr, size)
end

Base.@ccallable function filter_array_ffi(arr_ptr::Ptr{Cint}, size::Cint, threshold::Cint, 
                                          result_size::Ptr{Cint})::Ptr{Cint}
    return filter_array_ffi(arr_ptr, size, threshold, result_size)
end

Base.@ccallable function parallel_compute_ffi(data_ptr::Ptr{Cdouble}, size::Cint, num_threads::Cint)::Cdouble
    return parallel_compute_ffi(data_ptr, size, num_threads)
end

Base.@ccallable function free_memory_ffi(ptr::Ptr{Cvoid})::Cvoid
    return free_memory_ffi(ptr)
end