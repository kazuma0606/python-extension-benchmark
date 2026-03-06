# Julia FFI implementation for C ABI compatibility
# This module provides C-compatible functions for FFI integration
# Memory for returned pointers is allocated with Libc.malloc so callers can free it.

using LinearAlgebra

# Find all prime numbers up to n using Sieve of Eratosthenes
# C signature: int* find_primes_ffi(int n, int* count)
Base.@ccallable function find_primes_ffi(n::Cint, count_ptr::Ptr{Cint})::Ptr{Cint}
    if n < 2
        unsafe_store!(count_ptr, Cint(0))
        return Ptr{Cint}(C_NULL)
    end

    # Create boolean array, true means prime
    is_prime = trues(n)
    is_prime[1] = false  # 1 is not prime

    # Sieve of Eratosthenes
    sqrt_n = Int(floor(sqrt(Float64(n))))
    for i in 2:sqrt_n
        if is_prime[i]
            is_prime[i*i:i:n] .= false
        end
    end

    # Count primes
    prime_count = count(is_prime)
    unsafe_store!(count_ptr, Cint(prime_count))

    if prime_count == 0
        return Ptr{Cint}(C_NULL)
    end

    # Allocate with Libc.malloc so memory persists after function returns
    ptr = Ptr{Cint}(Libc.malloc(prime_count * sizeof(Cint)))

    idx = 0
    for i in 1:n
        if is_prime[i]
            unsafe_store!(ptr, Cint(i), idx + 1)
            idx += 1
        end
    end

    return ptr
end

# Matrix multiplication: C = A * B
# C signature: double* matrix_multiply_ffi(double* a, int rows_a, int cols_a,
#                                         double* b, int rows_b, int cols_b,
#                                         int* result_rows, int* result_cols)
Base.@ccallable function matrix_multiply_ffi(a_ptr::Ptr{Cdouble}, rows_a::Cint, cols_a::Cint,
                                             b_ptr::Ptr{Cdouble}, rows_b::Cint, cols_b::Cint,
                                             result_rows_ptr::Ptr{Cint}, result_cols_ptr::Ptr{Cint})::Ptr{Cdouble}
    if cols_a != rows_b
        unsafe_store!(result_rows_ptr, Cint(0))
        unsafe_store!(result_cols_ptr, Cint(0))
        return Ptr{Cdouble}(C_NULL)
    end

    # Convert C pointers to Julia arrays (row-major, flattened)
    a_flat = unsafe_wrap(Array, a_ptr, Int(rows_a) * Int(cols_a); own=false)
    b_flat = unsafe_wrap(Array, b_ptr, Int(rows_b) * Int(cols_b); own=false)

    # Reshape to matrices (Julia is column-major, transpose to get row-major)
    A = reshape(a_flat, Int(cols_a), Int(rows_a))'
    B = reshape(b_flat, Int(cols_b), Int(rows_b))'

    # Use Julia's optimized matrix multiplication (BLAS)
    C = A * B

    res_rows = size(C, 1)
    res_cols = size(C, 2)
    unsafe_store!(result_rows_ptr, Cint(res_rows))
    unsafe_store!(result_cols_ptr, Cint(res_cols))

    # Allocate result with Libc.malloc (row-major order)
    ptr = Ptr{Cdouble}(Libc.malloc(res_rows * res_cols * sizeof(Cdouble)))
    for i in 1:res_rows
        for j in 1:res_cols
            unsafe_store!(ptr, C[i, j], (i-1) * res_cols + j)
        end
    end

    return ptr
end

# Sort an array of integers
# C signature: int* sort_array_ffi(int* arr, int size)
Base.@ccallable function sort_array_ffi(arr_ptr::Ptr{Cint}, size::Cint)::Ptr{Cint}
    if size <= 0
        return Ptr{Cint}(C_NULL)
    end

    arr = unsafe_wrap(Array, arr_ptr, Int(size); own=false)
    sorted = sort(arr)

    ptr = Ptr{Cint}(Libc.malloc(Int(size) * sizeof(Cint)))
    for i in 1:Int(size)
        unsafe_store!(ptr, sorted[i], i)
    end

    return ptr
end

# Filter array elements >= threshold
# C signature: int* filter_array_ffi(int* arr, int size, int threshold, int* result_size)
Base.@ccallable function filter_array_ffi(arr_ptr::Ptr{Cint}, size::Cint, threshold::Cint,
                                          result_size_ptr::Ptr{Cint})::Ptr{Cint}
    if size <= 0
        unsafe_store!(result_size_ptr, Cint(0))
        return Ptr{Cint}(C_NULL)
    end

    arr = unsafe_wrap(Array, arr_ptr, Int(size); own=false)
    filtered = arr[arr .>= threshold]
    result_size = length(filtered)
    unsafe_store!(result_size_ptr, Cint(result_size))

    if result_size == 0
        return Ptr{Cint}(C_NULL)
    end

    ptr = Ptr{Cint}(Libc.malloc(result_size * sizeof(Cint)))
    for i in 1:result_size
        unsafe_store!(ptr, filtered[i], i)
    end

    return ptr
end

# Perform parallel computation
# C signature: double parallel_compute_ffi(double* data, int size, int num_threads)
Base.@ccallable function parallel_compute_ffi(data_ptr::Ptr{Cdouble}, size::Cint, num_threads::Cint)::Cdouble
    if size <= 0
        return 0.0
    end
    data = unsafe_wrap(Array, data_ptr, Int(size); own=false)
    return sum(data)
end

# Free memory allocated by Julia FFI functions (Libc.malloc)
# C signature: void free_memory_ffi(void* ptr)
Base.@ccallable function free_memory_ffi(ptr::Ptr{Cvoid})::Cvoid
    if ptr != C_NULL
        Libc.free(ptr)
    end
    nothing
end
