//! Windows FFI Audit System
//! 
//! A comprehensive system for auditing and verifying FFI implementations
//! on Windows platforms to prevent fallback to pure Python implementations.

pub mod error;
pub mod types;
pub mod diagnostics;
pub mod bug_detection;
pub mod fixer;
pub mod fallback_prevention;
pub mod reporter;
pub mod minimal_test_framework;

// Re-export main types
pub use error::{FFIAuditError, Result};
pub use types::*;
pub use fallback_prevention::FallbackPreventionSystem;

// Python bindings
use pyo3::prelude::*;

/// Python module initialization
#[pymodule]
fn windows_ffi_audit(_py: Python, m: &PyModule) -> PyResult<()> {
    // Classes
    m.add_class::<diagnostics::FFIImplementationDebugger>()?;
    m.add_class::<bug_detection::BugDetectionEngine>()?;
    m.add_class::<fixer::FFIImplementationFixer>()?;
    m.add_class::<fallback_prevention::FallbackPreventionSystem>()?;
    m.add_class::<reporter::ComprehensiveAuditReporter>()?;
    m.add_class::<types::ExecutionPathMonitoring>()?;
    m.add_class::<types::PerformanceMetrics>()?;
    m.add_class::<minimal_test_framework::MinimalTestFramework>()?;

    // Module-level constants (Task 11.1)
    m.add("__version__", "0.1.0")?;
    m.add("FALLBACK_THRESHOLD_NS", 10_000_000_u64)?;   // 10 ms — Python fallback indicator
    m.add("SIGNIFICANCE_LEVEL", 0.05_f64)?;             // default α for t-tests

    // Module-level utility functions (Task 11.1)
    m.add_function(wrap_pyfunction!(is_native_implementation, m)?)?;
    m.add_function(wrap_pyfunction!(classify_implementation, m)?)?;

    Ok(())
}

/// Return True if the implementation name is recognised as a native FFI impl.
#[pyfunction]
fn is_native_implementation(name: &str) -> bool {
    let native_suffixes = ["_ext", "_ffi", "_native", "rust", "c_", "cpp", "go_", "zig", "nim", "julia", "kotlin", "fortran", "cython", "numpy"];
    let python_keywords = ["python", "pure", "fallback"];

    if python_keywords.iter().any(|kw| name.contains(kw)) {
        return false;
    }
    native_suffixes.iter().any(|suf| name.contains(suf))
}

/// Classify implementation name as "native", "python", or "unknown".
#[pyfunction]
fn classify_implementation(name: &str) -> &'static str {
    let python_keywords = ["python", "pure_python", "fallback"];
    if python_keywords.iter().any(|kw| name.contains(kw)) {
        return "python";
    }
    if is_native_implementation(name) {
        return "native";
    }
    "unknown"
}