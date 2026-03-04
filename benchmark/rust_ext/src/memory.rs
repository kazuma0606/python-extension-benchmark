use pyo3::prelude::*;

/// Sort an array of integers.
#[pyfunction]
pub fn sort_array(mut arr: Vec<i32>) -> PyResult<Vec<i32>> {
    arr.sort_unstable();
    Ok(arr)
}

/// Filter array elements >= threshold.
#[pyfunction]
pub fn filter_array(arr: Vec<i32>, threshold: i32) -> PyResult<Vec<i32>> {
    let filtered: Vec<i32> = arr.into_iter()
        .filter(|&x| x >= threshold)
        .collect();
    Ok(filtered)
}