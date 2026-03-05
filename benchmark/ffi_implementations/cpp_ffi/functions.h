#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#ifdef __cplusplus
extern "C" {
#endif

// Find all prime numbers up to n
int* find_primes_ffi(int n, int* count);

// Matrix multiplication
double* matrix_multiply_ffi(double* a, int rows_a, int cols_a,
                           double* b, int rows_b, int cols_b,
                           int* result_rows, int* result_cols);

// Sort array
int* sort_array_ffi(int* arr, int size);

// Filter array (elements >= threshold)
int* filter_array_ffi(int* arr, int size, int threshold, int* result_size);

// Parallel computation (sum of squares)
double parallel_compute_ffi(double* data, int size, int num_threads);

// Free memory allocated by FFI functions
void free_memory_ffi(void* ptr);

#ifdef __cplusplus
}
#endif

#endif // FUNCTIONS_H