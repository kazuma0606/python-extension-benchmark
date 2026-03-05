/*!
Rust FFI implementation of benchmark functions.

This module provides high-performance Rust implementations that are compiled
to a shared library for FFI access via ctypes.
*/

use std::ptr;
use std::slice;
use libc::{c_int, c_double, c_void, malloc, free};

/// Find all prime numbers up to n using Sieve of Eratosthenes
/// 
/// # Safety
/// This function allocates memory that must be freed by the caller using free_memory_ffi
#[no_mangle]
pub unsafe extern "C" fn find_primes_ffi(n: c_int, count: *mut c_int) -> *mut c_int {
    if n < 2 {
        *count = 0;
        return ptr::null_mut();
    }
    
    let n = n as usize;
    
    // Sieve of Eratosthenes
    let mut is_prime = vec![true; n + 1];
    is_prime[0] = false;
    is_prime[1] = false;
    
    let sqrt_n = (n as f64).sqrt() as usize + 1;
    for i in 2..sqrt_n {
        if is_prime[i] {
            let mut j = i * i;
            while j <= n {
                is_prime[j] = false;
                j += i;
            }
        }
    }
    
    // Count primes
    let prime_count = is_prime.iter().filter(|&&x| x).count();
    
    if prime_count == 0 {
        *count = 0;
        return ptr::null_mut();
    }
    
    // Allocate result array
    let result = malloc(prime_count * std::mem::size_of::<c_int>()) as *mut c_int;
    if result.is_null() {
        *count = 0;
        return ptr::null_mut();
    }
    
    // Fill result array
    let mut idx = 0;
    for (i, &prime) in is_prime.iter().enumerate() {
        if prime {
            *result.add(idx) = i as c_int;
            idx += 1;
        }
    }
    
    *count = prime_count as c_int;
    result
}

/// Multiply two matrices
/// 
/// # Safety
/// This function allocates memory that must be freed by the caller using free_memory_ffi
#[no_mangle]
pub unsafe extern "C" fn matrix_multiply_ffi(
    a: *const c_double, rows_a: c_int, cols_a: c_int,
    b: *const c_double, rows_b: c_int, cols_b: c_int,
    result_rows: *mut c_int, result_cols: *mut c_int
) -> *mut c_double {
    if cols_a != rows_b {
        *result_rows = 0;
        *result_cols = 0;
        return ptr::null_mut();
    }
    
    let rows_a = rows_a as usize;
    let cols_a = cols_a as usize;
    let rows_b = rows_b as usize;
    let cols_b = cols_b as usize;
    
    *result_rows = rows_a as c_int;
    *result_cols = cols_b as c_int;
    
    let result_size = rows_a * cols_b;
    let result = malloc(result_size * std::mem::size_of::<c_double>()) as *mut c_double;
    if result.is_null() {
        *result_rows = 0;
        *result_cols = 0;
        return ptr::null_mut();
    }
    
    // Initialize result to zero
    for i in 0..result_size {
        *result.add(i) = 0.0;
    }
    
    // Convert raw pointers to slices for safe access
    let a_slice = slice::from_raw_parts(a, rows_a * cols_a);
    let b_slice = slice::from_raw_parts(b, rows_b * cols_b);
    
    // Perform matrix multiplication
    for i in 0..rows_a {
        for k in 0..cols_a {
            let a_ik = a_slice[i * cols_a + k];
            for j in 0..cols_b {
                let idx = i * cols_b + j;
                *result.add(idx) += a_ik * b_slice[k * cols_b + j];
            }
        }
    }
    
    result
}

/// Sort an array of integers using quicksort
/// 
/// # Safety
/// This function allocates memory that must be freed by the caller using free_memory_ffi
#[no_mangle]
pub unsafe extern "C" fn sort_array_ffi(arr: *const c_int, size: c_int) -> *mut c_int {
    if size <= 0 {
        return ptr::null_mut();
    }
    
    let size = size as usize;
    
    // Allocate result array
    let result = malloc(size * std::mem::size_of::<c_int>()) as *mut c_int;
    if result.is_null() {
        return ptr::null_mut();
    }
    
    // Copy input array to result
    let arr_slice = slice::from_raw_parts(arr, size);
    for i in 0..size {
        *result.add(i) = arr_slice[i];
    }
    
    // Sort using Rust's optimized sort
    let result_slice = slice::from_raw_parts_mut(result, size);
    result_slice.sort_unstable();
    
    result
}

/// Filter array elements >= threshold
/// 
/// # Safety
/// This function allocates memory that must be freed by the caller using free_memory_ffi
#[no_mangle]
pub unsafe extern "C" fn filter_array_ffi(
    arr: *const c_int, size: c_int, threshold: c_int, result_size: *mut c_int
) -> *mut c_int {
    if size <= 0 {
        *result_size = 0;
        return ptr::null_mut();
    }
    
    let size = size as usize;
    let arr_slice = slice::from_raw_parts(arr, size);
    
    // Count elements >= threshold
    let count = arr_slice.iter().filter(|&&x| x >= threshold).count();
    
    if count == 0 {
        *result_size = 0;
        return ptr::null_mut();
    }
    
    // Allocate result array
    let result = malloc(count * std::mem::size_of::<c_int>()) as *mut c_int;
    if result.is_null() {
        *result_size = 0;
        return ptr::null_mut();
    }
    
    // Fill result array
    let mut idx = 0;
    for &value in arr_slice {
        if value >= threshold {
            *result.add(idx) = value;
            idx += 1;
        }
    }
    
    *result_size = count as c_int;
    result
}

/// Perform parallel computation (sum) on data
#[no_mangle]
pub unsafe extern "C" fn parallel_compute_ffi(
    data: *const c_double, size: c_int, _num_threads: c_int
) -> c_double {
    if size <= 0 {
        return 0.0;
    }
    
    let size = size as usize;
    let data_slice = slice::from_raw_parts(data, size);
    
    // Use Rust's iterator for efficient summation
    // Note: For true parallelism, we could use rayon crate, but keeping dependencies minimal
    data_slice.iter().sum()
}

/// Free memory allocated by FFI functions
/// 
/// # Safety
/// The pointer must have been allocated by one of the FFI functions in this module
#[no_mangle]
pub unsafe extern "C" fn free_memory_ffi(ptr: *mut c_void) {
    if !ptr.is_null() {
        free(ptr);
    }
}