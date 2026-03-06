module JuliaFFI

using LinearAlgebra

Base.@ccallable function find_primes_ffi(n::Cint, count_ptr::Ptr{Cint})::Ptr{Cint}
    if n < 2
        unsafe_store!(count_ptr, Cint(0))
        return Ptr{Cint}(C_NULL)
    end
    is_prime = trues(Int(n))
    is_prime[1] = false
    sqrt_n = Int(floor(sqrt(Float64(n))))
    for i in 2:sqrt_n
        if is_prime[i]
            is_prime[i*i:i:Int(n)] .= false
        end
    end
    prime_count = count(is_prime)
    unsafe_store!(count_ptr, Cint(prime_count))
    if prime_count == 0
        return Ptr{Cint}(C_NULL)
    end
    ptr = Ptr{Cint}(Libc.malloc(prime_count * sizeof(Cint)))
    idx = 0
    for i in 1:Int(n)
        if is_prime[i]
            idx += 1
            unsafe_store!(ptr, Cint(i), idx)
        end
    end
    return ptr
end

Base.@ccallable function matrix_multiply_ffi(a_ptr::Ptr{Cdouble}, rows_a::Cint, cols_a::Cint,
                                             b_ptr::Ptr{Cdouble}, rows_b::Cint, cols_b::Cint,
                                             result_rows_ptr::Ptr{Cint}, result_cols_ptr::Ptr{Cint})::Ptr{Cdouble}
    if cols_a != rows_b
        unsafe_store!(result_rows_ptr, Cint(0))
        unsafe_store!(result_cols_ptr, Cint(0))
        return Ptr{Cdouble}(C_NULL)
    end
    a_flat = unsafe_wrap(Array, a_ptr, Int(rows_a)*Int(cols_a); own=false)
    b_flat = unsafe_wrap(Array, b_ptr, Int(rows_b)*Int(cols_b); own=false)
    A = reshape(a_flat, Int(cols_a), Int(rows_a))'
    B = reshape(b_flat, Int(cols_b), Int(rows_b))'
    C = A * B
    res_rows, res_cols = size(C)
    unsafe_store!(result_rows_ptr, Cint(res_rows))
    unsafe_store!(result_cols_ptr, Cint(res_cols))
    ptr = Ptr{Cdouble}(Libc.malloc(res_rows * res_cols * sizeof(Cdouble)))
    for i in 1:res_rows, j in 1:res_cols
        unsafe_store!(ptr, C[i,j], (i-1)*res_cols + j)
    end
    return ptr
end

Base.@ccallable function sort_array_ffi(arr_ptr::Ptr{Cint}, size::Cint)::Ptr{Cint}
    if size <= 0; return Ptr{Cint}(C_NULL); end
    arr = unsafe_wrap(Array, arr_ptr, Int(size); own=false)
    sorted = sort(arr)
    ptr = Ptr{Cint}(Libc.malloc(Int(size) * sizeof(Cint)))
    for i in 1:Int(size); unsafe_store!(ptr, sorted[i], i); end
    return ptr
end

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
    if result_size == 0; return Ptr{Cint}(C_NULL); end
    ptr = Ptr{Cint}(Libc.malloc(result_size * sizeof(Cint)))
    for i in 1:result_size; unsafe_store!(ptr, filtered[i], i); end
    return ptr
end

Base.@ccallable function parallel_compute_ffi(data_ptr::Ptr{Cdouble}, size::Cint, num_threads::Cint)::Cdouble
    if size <= 0; return 0.0; end
    data = unsafe_wrap(Array, data_ptr, Int(size); own=false)
    return sum(data)
end

Base.@ccallable function free_memory_ffi(ptr::Ptr{Cvoid})::Cvoid
    if ptr != C_NULL; Libc.free(ptr); end
    nothing
end

end # module JuliaFFI
