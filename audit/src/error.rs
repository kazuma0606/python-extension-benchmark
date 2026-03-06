//! Error types for the FFI audit system

use thiserror::Error;
use std::fmt;

/// Main error type for the FFI audit system
#[derive(Error, Debug, Clone)]
pub enum AuditError {
    #[error("Unsupported FFI implementation: {0}")]
    UnsupportedImplementation(String),
    
    #[error("Library loading failed: {0}")]
    LibraryLoadingFailed(String),
    
    #[error("Symbol resolution failed: {0}")]
    SymbolResolutionFailed(String),
    
    #[error("DLL issue detected: {0}")]
    DLLIssue(String),
    
    #[error("Path resolution failed: {0}")]
    PathResolutionFailed(String),
    
    #[error("Dependency missing: {0}")]
    DependencyMissing(String),
    
    #[error("Architecture mismatch: {0}")]
    ArchitectureMismatch(String),
    
    #[error("Calling convention error: {0}")]
    CallingConventionError(String),
    
    #[error("Memory layout validation failed: {0}")]
    MemoryLayoutValidationFailed(String),
    
    #[error("Fallback detected: {0}")]
    FallbackDetected(String),
    
    #[error("Performance anomaly detected: {0}")]
    PerformanceAnomalyDetected(String),
    
    #[error("Build script generation failed: {0}")]
    BuildScriptGenerationFailed(String),
    
    #[error("Fix application failed: {0}")]
    FixApplicationFailed(String),
    
    #[error("Validation failed: {0}")]
    ValidationFailed(String),
    
    #[error("Report generation failed: {0}")]
    ReportGenerationFailed(String),
    
    #[error("Invalid arguments: {0}")]
    InvalidArguments(String),
    
    #[error("IO error: {0}")]
    IoError(String),
    
    #[error("Serialization error: {0}")]
    SerializationError(String),
    
    #[error("Windows API error: {0}")]
    WindowsApiError(String),
    
    #[error("Python integration error: {0}")]
    PythonIntegrationError(String),
    
    #[error("Unknown error: {0}")]
    Unknown(String),
}

// Keep the old name for backward compatibility
pub type FFIAuditError = AuditError;

impl From<std::io::Error> for AuditError {
    fn from(error: std::io::Error) -> Self {
        AuditError::IoError(error.to_string())
    }
}

impl From<serde_json::Error> for AuditError {
    fn from(error: serde_json::Error) -> Self {
        AuditError::SerializationError(error.to_string())
    }
}

impl From<anyhow::Error> for AuditError {
    fn from(error: anyhow::Error) -> Self {
        AuditError::Unknown(error.to_string())
    }
}

#[cfg(feature = "pyo3")]
impl From<pyo3::PyErr> for AuditError {
    fn from(error: pyo3::PyErr) -> Self {
        AuditError::PythonIntegrationError(error.to_string())
    }
}

/// Result type alias for the FFI audit system
pub type Result<T> = std::result::Result<T, AuditError>;

/// Specialized result types for different components
pub type LibraryDiagnosticsResult = Result<crate::types::LibraryDiagnostics>;
pub type SymbolValidationResult = Result<crate::types::SymbolValidation>;
pub type CallingConventionResult = Result<crate::types::CallingConventionCheck>;
pub type MemoryLayoutResult = Result<crate::types::MemoryLayoutValidation>;
pub type PathAnalysisResult = Result<crate::types::PathAnalysis>;
pub type DependencyAnalysisResult = Result<crate::types::DependencyAnalysis>;
pub type ErrorClassificationResult = Result<crate::types::ErrorClassification>;
pub type BuildScriptResult = Result<crate::types::BuildScript>;
pub type PathCorrectionResult = Result<crate::types::PathCorrection>;
pub type SymbolExportValidationResult = Result<crate::types::SymbolExportValidation>;
pub type CompatibilityLayerResult = Result<crate::types::CompatibilityLayer>;