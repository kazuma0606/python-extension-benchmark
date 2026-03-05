#include <iostream>
#include <vector>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <cstdlib>

extern "C" {

// Function to check if a number is prime
bool is_prime(int n) {
    if (n < 2) return false;
    if (n == 2) return true;
    if (n % 2 == 0) return false;
    
    for (int i = 3; i * i <= n; i += 2) {
        if (n % i == 0) return false;
    }
    return true;
}

// Find all prime numbers up to n
int* find_primes_ffi(int n, int* count) {
    if (n < 2) {
        *count = 0;
        return nullptr;
    }
    
    // Use C++ vector for convenience, then convert to C array
    std::vector<int> primes;
    
    for (int i = 2; i <= n; i++) {
        if (is_prime(i)) {
            primes.push_back(i);
        }
    }
    
    if (primes.empty()) {
        *count = 0;
        return nullptr;
    }
    
    // Allocate C array and copy data
    int* result = static_cast<int*>(std::malloc(primes.size() * sizeof(int)));
    if (!result) {
        *count = 0;
        return nullptr;
    }
    
    std::copy(primes.begin(), primes.end(), result);
    *count = static_cast<int>(primes.size());
    
    return result;
}

// Matrix multiplication using C++ features
double* matrix_multiply_ffi(double* a, int rows_a, int cols_a,
                           double* b, int rows_b, int cols_b,
                           int* result_rows, int* result_cols) {
    // Check dimensions
    if (cols_a != rows_b) {
        *result_rows = 0;
        *result_cols = 0;
        return nullptr;
    }
    
    *result_rows = rows_a;
    *result_cols = cols_b;
    
    // Allocate result matrix
    double* result = static_cast<double*>(std::malloc(rows_a * cols_b * sizeof(double)));
    if (!result) {
        *result_rows = 0;
        *result_cols = 0;
        return nullptr;
    }
    
    // Initialize result to zero
    std::memset(result, 0, rows_a * cols_b * sizeof(double));
    
    // Perform multiplication with C++ style loops
    for (int i = 0; i < rows_a; ++i) {
        for (int j = 0; j < cols_b; ++j) {
            for (int k = 0; k < cols_a; ++k) {
                result[i * cols_b + j] += a[i * cols_a + k] * b[k * cols_b + j];
            }
        }
    }
    
    return result;
}

// Sort array using C++ STL
int* sort_array_ffi(int* arr, int size) {
    if (size <= 0 || !arr) {
        return nullptr;
    }
    
    // Allocate memory for result
    int* result = static_cast<int*>(std::malloc(size * sizeof(int)));
    if (!result) {
        return nullptr;
    }
    
    // Copy array and sort using STL
    std::copy(arr, arr + size, result);
    std::sort(result, result + size);
    
    return result;
}

// Filter array using C++ features
int* filter_array_ffi(int* arr, int size, int threshold, int* result_size) {
    if (size <= 0 || !arr) {
        *result_size = 0;
        return nullptr;
    }
    
    // Use vector to collect filtered elements
    std::vector<int> filtered;
    
    for (int i = 0; i < size; ++i) {
        if (arr[i] >= threshold) {
            filtered.push_back(arr[i]);
        }
    }
    
    if (filtered.empty()) {
        *result_size = 0;
        return nullptr;
    }
    
    // Allocate C array and copy data
    int* result = static_cast<int*>(std::malloc(filtered.size() * sizeof(int)));
    if (!result) {
        *result_size = 0;
        return nullptr;
    }
    
    std::copy(filtered.begin(), filtered.end(), result);
    *result_size = static_cast<int>(filtered.size());
    
    return result;
}

// Parallel computation using C++ features
double parallel_compute_ffi(double* data, int size, int num_threads) {
    if (size <= 0 || !data) {
        return 0.0;
    }
    
    // Simple implementation without actual threading for now
    // In a real implementation, this would use std::thread or OpenMP
    double sum = 0.0;
    
    for (int i = 0; i < size; ++i) {
        sum += data[i] * data[i];
    }
    
    return sum;
}

// Free memory allocated by FFI functions
void free_memory_ffi(void* ptr) {
    if (ptr) {
        std::free(ptr);
    }
}

} // extern "C"