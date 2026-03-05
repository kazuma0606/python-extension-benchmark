#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// Simple C implementations for testing Julia FFI interface
// These are fallback implementations when Julia compilation is not available

int* find_primes_ffi(int n, int* count) {
    if (n < 2) {
        *count = 0;
        return NULL;
    }
    
    // Simple sieve implementation
    char* is_prime = (char*)calloc(n + 1, sizeof(char));
    for (int i = 2; i <= n; i++) is_prime[i] = 1;
    
    for (int i = 2; i * i <= n; i++) {
        if (is_prime[i]) {
            for (int j = i * i; j <= n; j += i) {
                is_prime[j] = 0;
            }
        }
    }
    
    // Count primes
    int prime_count = 0;
    for (int i = 2; i <= n; i++) {
        if (is_prime[i]) prime_count++;
    }
    
    *count = prime_count;
    if (prime_count == 0) {
        free(is_prime);
        return NULL;
    }
    
    // Collect primes
    int* primes = (int*)malloc(prime_count * sizeof(int));
    int idx = 0;
    for (int i = 2; i <= n; i++) {
        if (is_prime[i]) {
            primes[idx++] = i;
        }
    }
    
    free(is_prime);
    return primes;
}

double* matrix_multiply_ffi(double* a, int rows_a, int cols_a,
                           double* b, int rows_b, int cols_b,
                           int* result_rows, int* result_cols) {
    if (cols_a != rows_b) {
        *result_rows = 0;
        *result_cols = 0;
        return NULL;
    }
    
    *result_rows = rows_a;
    *result_cols = cols_b;
    
    double* c = (double*)calloc(rows_a * cols_b, sizeof(double));
    
    for (int i = 0; i < rows_a; i++) {
        for (int j = 0; j < cols_b; j++) {
            for (int k = 0; k < cols_a; k++) {
                c[i * cols_b + j] += a[i * cols_a + k] * b[k * cols_b + j];
            }
        }
    }
    
    return c;
}

int* sort_array_ffi(int* arr, int size) {
    if (size <= 0) return NULL;
    
    int* result = (int*)malloc(size * sizeof(int));
    for (int i = 0; i < size; i++) {
        result[i] = arr[i];
    }
    
    // Simple quicksort
    // (Implementation omitted for brevity - would use qsort)
    for (int i = 0; i < size - 1; i++) {
        for (int j = 0; j < size - i - 1; j++) {
            if (result[j] > result[j + 1]) {
                int temp = result[j];
                result[j] = result[j + 1];
                result[j + 1] = temp;
            }
        }
    }
    
    return result;
}

int* filter_array_ffi(int* arr, int size, int threshold, int* result_size) {
    if (size <= 0) {
        *result_size = 0;
        return NULL;
    }
    
    // Count elements >= threshold
    int count = 0;
    for (int i = 0; i < size; i++) {
        if (arr[i] >= threshold) count++;
    }
    
    *result_size = count;
    if (count == 0) return NULL;
    
    int* result = (int*)malloc(count * sizeof(int));
    int idx = 0;
    for (int i = 0; i < size; i++) {
        if (arr[i] >= threshold) {
            result[idx++] = arr[i];
        }
    }
    
    return result;
}

double parallel_compute_ffi(double* data, int size, int num_threads) {
    if (size <= 0) return 0.0;
    
    double sum = 0.0;
    for (int i = 0; i < size; i++) {
        sum += data[i];
    }
    
    return sum;
}

void free_memory_ffi(void* ptr) {
    if (ptr) free(ptr);
}
