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
    m.add_class::<diagnostics::FFIImplementationDebugger>()?;
    m.add_class::<bug_detection::BugDetectionEngine>()?;
    m.add_class::<fixer::FFIImplementationFixer>()?;
    m.add_class::<fallback_prevention::FallbackPreventionSystem>()?;
    m.add_class::<reporter::ComprehensiveAuditReporter>()?;
    m.add_class::<types::ExecutionPathMonitoring>()?;
    m.add_class::<types::PerformanceMetrics>()?;
    m.add_class::<minimal_test_framework::MinimalTestFramework>()?;
    Ok(())
}