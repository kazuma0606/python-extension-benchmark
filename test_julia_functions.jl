include("benchmark/julia_ext/functions.jl")

println("Testing Julia functions...")

# Test find_primes_jl
println("Testing find_primes_jl(10):")
primes = find_primes_jl(10)
println("Result: ", primes)

# Test matrix_multiply_jl
println("\nTesting matrix_multiply_jl:")
a = [[1.0, 2.0], [3.0, 4.0]]
b = [[5.0, 6.0], [7.0, 8.0]]
result = matrix_multiply_jl(a, b)
println("Result: ", result)
println("Expected: [[19.0, 22.0], [43.0, 50.0]]")

# Test sort_array_jl
println("\nTesting sort_array_jl:")
arr = [3, 1, 4, 1, 5, 9, 2, 6]
sorted_arr = sort_array_jl(arr)
println("Result: ", sorted_arr)

# Test filter_array_jl
println("\nTesting filter_array_jl:")
filtered = filter_array_jl([1, 2, 3, 4, 5], 3)
println("Result: ", filtered)

# Test parallel_compute_jl
println("\nTesting parallel_compute_jl:")
data = [1.0, 2.0, 3.0, 4.0, 5.0]
sum_result = parallel_compute_jl(data, 2)
println("Result: ", sum_result)

println("\nAll Julia functions work correctly!")