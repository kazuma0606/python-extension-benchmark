use pyo3::prelude::*;

/// Find all prime numbers up to n using Sieve of Eratosthenes.
#[pyfunction]
pub fn find_primes(n: i32) -> PyResult<Vec<i32>> {
    if n < 2 {
        return Ok(vec![]);
    }
    
    let n_usize = n as usize;
    let mut is_prime = vec![true; n_usize + 1];
    is_prime[0] = false;
    if n_usize >= 1 {
        is_prime[1] = false;
    }
    
    // Sieve of Eratosthenes
    let sqrt_n = (n as f64).sqrt() as usize;
    for i in 2..=sqrt_n {
        if is_prime[i] {
            // Mark all multiples of i as not prime
            let mut j = i * i;
            while j <= n_usize {
                is_prime[j] = false;
                j += i;
            }
        }
    }
    
    // Collect all primes
    let primes: Vec<i32> = (0..=n_usize)
        .filter(|&i| is_prime[i])
        .map(|i| i as i32)
        .collect();
    
    Ok(primes)
}

/// Multiply two matrices.
#[pyfunction]
pub fn matrix_multiply(a: Vec<Vec<f64>>, b: Vec<Vec<f64>>) -> PyResult<Vec<Vec<f64>>> {
    if a.is_empty() || b.is_empty() || a[0].is_empty() || b[0].is_empty() {
        return Ok(vec![vec![]]);
    }
    
    let m = a.len();
    let n = a[0].len();
    let p = b[0].len();
    
    // Verify dimensions are compatible
    if b.len() != n {
        return Err(pyo3::exceptions::PyValueError::new_err(
            format!("Incompatible matrix dimensions: {}x{} and {}x{}", m, n, b.len(), p)
        ));
    }
    
    // Initialize result matrix with zeros
    let mut result = vec![vec![0.0; p]; m];
    
    // Perform matrix multiplication
    for i in 0..m {
        for j in 0..p {
            for k in 0..n {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    
    Ok(result)
}