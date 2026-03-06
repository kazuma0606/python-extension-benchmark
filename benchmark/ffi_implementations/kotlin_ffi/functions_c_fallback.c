/**
 * C Fallback Implementation for Kotlin FFI
 * 
 * This provides the same functionality as the Kotlin implementation
 * but uses C for compatibility when Kotlin/Native build fails.
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

/**
 * Find all prime numbers up to n using Sieve of Eratosthenes
 */
int* find_primes_ffi(int n, int* count) {
    if (n < 2) {
        *count = 0;
        return NULL;
    }
    
    // Create sieve array
    char* sieve = (char*)malloc((n + 1) * sizeof(char));
    memset(sieve, 1, n + 1);
    sieve[0] = sieve[1] = 0;
    
    // Sieve of Eratosthenes algorithm
    int limit = (int)sqrt(n);
    for (int i = 2; i <= limit; i++) {
        if (sieve[i]) {
            for (int j = i * i; j <= n; j += i) {
                sieve[j] = 0;
            }
        }
    }
    
    // Count primes first
    int prime_count = 0;
    for (int i = 2; i <= n; i++) {
        if (sieve[i]) {
            prime_count++;
        }
    }
    
    if (prime_count == 0) {
        free(sieve);
        *count = 0;
        return NULL;
    }
    
    // Allocate result array
    int* result = (int*)malloc(prime_count * sizeof(int));
    
    // Collect primes
    int index = 0;
    for (int i = 2; i <= n; i++) {
        if (sieve[i]) {
            result[index++] = i;
        }
    }
    
    free(sieve);
    *count = prime_count;
    return result;
}

/**
 * Matrix multiplication
 */
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
    int result_size = rows_a * cols_b;
    double* result = (double*)calloc(result_size, sizeof(double));
    
    // Perform matrix multiplication with cache-friendly access pattern
    for (int i = 0; i < rows_a; i++) {
        for (int k = 0; k < cols_a; k++) {
            double aik = a[i * cols_a + k];
            for (int j = 0; j < cols_b; j++) {
                result[i * cols_b + j] += aik * b[k * cols_b + j];
            }
        }
    }
    
    return result;
}

/**
 * Sort array using quicksort
 */
static int compare_ints(const void* a, const void* b) {
    int ia = *(const int*)a;
    int ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}

int* sort_array_ffi(int* arr, int size) {
    if (size <= 0) return NULL;
    
    // Allocate result array
    int* result = (int*)malloc(size * sizeof(int));
    memcpy(result, arr, size * sizeof(int));
    
    // Sort using qsort
    qsort(result, size, sizeof(int), compare_ints);
    
    return result;
}

/**
 * Filter array elements
 */
int* filter_array_ffi(int* arr, int size, int threshold, int* result_size) {
    if (size == 0) {
        *result_size = 0;
        return NULL;
    }
    
    // First pass: count matching elements
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
    
    // Allocate result array
    int* result = (int*)malloc(count * sizeof(int));
    
    // Second pass: collect matching elements
    int index = 0;
    for (int i = 0; i < size; i++) {
        if (arr[i] >= threshold) {
            result[index++] = arr[i];
        }
    }
    
    *result_size = count;
    return result;
}

/**
 * Parallel computation (sequential implementation for simplicity)
 */
double parallel_compute_ffi(double* data, int size, int num_threads) {
    if (size == 0) return 0.0;
    
    double sum = 0.0;
    for (int i = 0; i < size; i++) {
        sum += data[i];
    }
    
    return sum;
}

/**
 * Free memory allocated by FFI functions
 */
void free_memory_ffi(void* ptr) {
    if (ptr != NULL) {
        free(ptr);
    }
}