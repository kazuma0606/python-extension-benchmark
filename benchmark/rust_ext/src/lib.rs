use pyo3::prelude::*;

mod numeric;
mod memory;
mod parallel;

use numeric::{find_primes, matrix_multiply};
use memory::{sort_array, filter_array};
use parallel::parallel_compute;

/// A Python module implemented in Rust.
#[pymodule]
fn rust_ext(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_primes, m)?)?;
    m.add_function(wrap_pyfunction!(matrix_multiply, m)?)?;
    m.add_function(wrap_pyfunction!(sort_array, m)?)?;
    m.add_function(wrap_pyfunction!(filter_array, m)?)?;
    m.add_function(wrap_pyfunction!(parallel_compute, m)?)?;
    Ok(())
}