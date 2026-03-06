#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// Function to check if a number is prime
int is_prime(int n) {
    if (n < 2) return 0;
    if (n == 2) return 1;
    if (n % 2 == 0) return 0;
    
    for (int i = 3; i * i <= n; i += 2) {
        if (n % i == 0) return 0;
    }
    return 1;
}

// Find all prime numbers up to n
int* find_primes_ffi(int n, int* count) {
    if (n < 2) {
        *count = 0;
        return NULL;
    }
    
    // First pass: count primes
    int prime_count = 0;
    for (int i = 2; i <= n; i++) {
        if (is_prime(i)) {
            prime_count++;
        }
    }
    
    if (prime_count == 0) {
        *count = 0;
        return NULL;
    }
    
    // Allocate memory for primes
    int* primes = (int*)malloc(prime_count * sizeof(int));
    if (!primes) {
        *count = 0;
        return NULL;
    }
    
    // Second pass: collect primes
    int index = 0;
    for (int i = 2; i <= n; i++) {
        if (is_prime(i)) {
            primes[index++] = i;
        }
    }
    
    *count = prime_count;
    return primes;
}

// Matrix multiplication
double* matrix_multiply_ffi(double* a, int rows_a, int cols_a,
                           double* b, int rows_b, int cols_b,
                           int* result_rows, int* result_cols) {
    // Check dimensions
    if (cols_a != rows_b) {
        *result_rows = 0;
        *result_cols = 0;
        return NULL;
    }
    
    *result_rows = rows_a;
    *result_cols = cols_b;
    
    // Allocate result matrix
    double* result = (double*)malloc(rows_a * cols_b * sizeof(double));
    if (!result) {
        *result_rows = 0;
        *result_cols = 0;
        return NULL;
    }
    
    // Initialize result to zero
    memset(result, 0, rows_a * cols_b * sizeof(double));
    
    // Perform multiplication
    for (int i = 0; i < rows_a; i++) {
        for (int j = 0; j < cols_b; j++) {
            for (int k = 0; k < cols_a; k++) {
                result[i * cols_b + j] += a[i * cols_a + k] * b[k * cols_b + j];
            }
        }
    }
    
    return result;
}

// Comparison function for qsort
int compare_ints(const void* a, const void* b) {
    int ia = *(const int*)a;
    int ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}

// Sort array
int* sort_array_ffi(int* arr, int size) {
    if (size <= 0 || !arr) {
        return NULL;
    }
    
    // Allocate memory for result
    int* result = (int*)malloc(size * sizeof(int));
    if (!result) {
        return NULL;
    }
    
    // Copy array
    memcpy(result, arr, size * sizeof(int));
    
    // Sort using qsort
    qsort(result, size, sizeof(int), compare_ints);
    
    return result;
}

// Filter array (elements >= threshold)
int* filter_array_ffi(int* arr, int size, int threshold, int* result_size) {
    if (size <= 0 || !arr) {
        *result_size = 0;
        return NULL;
    }
    
    // First pass: count elements >= threshold
    int count = 0;
    for (int i = 0; i < size; i++) {
        if (arr[i] >= threshold) {
            count++;
        }
    }
    
    if (count == 0) {
        *result_size = 0;
        return NULL;
    }
    
    // Allocate memory for result
    int* result = (int*)malloc(count * sizeof(int));
    if (!result) {
        *result_size = 0;
        return NULL;
    }
    
    // Second pass: collect elements >= threshold
    int index = 0;
    for (int i = 0; i < size; i++) {
        if (arr[i] >= threshold) {
            result[index++] = arr[i];
        }
    }
    
    *result_size = count;
    return result;
}

// Parallel computation (sum of squares)
double parallel_compute_ffi(double* data, int size, int num_threads) {
    if (size <= 0 || !data) {
        return 0.0;
    }
    
    // Simple implementation without actual threading for now
    // In a real implementation, this would use OpenMP or pthreads
    double sum = 0.0;
    for (int i = 0; i < size; i++) {
        sum += data[i] * data[i];
    }
    
    return sum;
}

// Free memory allocated by FFI functions
void free_memory_ffi(void* ptr) {
    if (ptr) {
        free(ptr);
    }
}