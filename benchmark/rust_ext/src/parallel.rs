use pyo3::prelude::*;
use rayon::prelude::*;
use std::sync::Once;

static INIT: Once = Once::new();

/// Perform parallel computation (sum) using multiple threads.
#[pyfunction]
pub fn parallel_compute(data: Vec<f64>, num_threads: usize) -> PyResult<f64> {
    // Only set the thread pool once
    INIT.call_once(|| {
        if let Err(_) = rayon::ThreadPoolBuilder::new()
            .num_threads(num_threads)
            .build_global()
        {
            // If we can't set the global pool, that's okay - use the default
        }
    });
    
    // Perform parallel sum using rayon
    let sum: f64 = data.par_iter().sum();
    
    Ok(sum)
}