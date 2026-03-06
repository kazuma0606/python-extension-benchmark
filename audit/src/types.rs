//! Core data types for the FFI audit system

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Diagnostics information for a library
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LibraryDiagnostics {
    pub implementation: String,
    pub library_exists: bool,
    pub library_loadable: bool,
    pub loading_errors: Vec<LoadingError>,
    pub missing_dependencies: Vec<String>,
    pub architecture_mismatch: bool,
    pub path_issues: Vec<PathIssue>,
}

/// Loading error information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoadingError {
    pub error_code: Option<u32>,
    pub error_message: String,
    pub error_type: LoadingErrorType,
}

/// Types of loading errors
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LoadingErrorType {
    FileNotFound,
    AccessDenied,
    InvalidFormat,
    DependencyMissing,
    ArchitectureMismatch,
    SymbolNotFound,
    Other(String),
}

/// Path-related issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathIssue {
    pub issue_type: PathIssueType,
    pub path: String,
    pub description: String,
    pub resolution_suggestion: String,
}

/// Types of path issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PathIssueType {
    RelativePathProblem,
    AbsolutePathProblem,
    EnvironmentVariableProblem,
    PathTooLong,
    InvalidCharacters,
    PermissionDenied,
}

/// DLL-specific issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DLLIssue {
    pub issue_type: DLLIssueType,
    pub error_code: Option<u32>,
    pub description: String,
    pub affected_library: String,
    pub resolution_steps: Vec<String>,
}

/// Types of DLL issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DLLIssueType {
    LoadFailure,
    SymbolNotFound,
    ArchitectureMismatch,
    DependencyMissing,
    PathResolutionFailure,
    CallingConventionMismatch,
    MemoryLayoutMismatch,
}

/// Symbol validation results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymbolValidation {
    pub implementation: String,
    pub symbols_found: Vec<String>,
    pub symbols_missing: Vec<String>,
    pub symbol_issues: Vec<SymbolIssue>,
}

/// Symbol-specific issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymbolIssue {
    pub symbol_name: String,
    pub issue_type: SymbolIssueType,
    pub description: String,
}

/// Types of symbol issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SymbolIssueType {
    NotExported,
    WrongSignature,
    CallingConventionMismatch,
    NameMangling,
}

/// Calling convention check results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CallingConventionCheck {
    pub implementation: String,
    pub expected_convention: String,
    pub actual_convention: Option<String>,
    pub is_compatible: bool,
    pub issues: Vec<String>,
}

/// Memory layout validation results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryLayoutValidation {
    pub implementation: String,
    pub layout_compatible: bool,
    pub alignment_issues: Vec<AlignmentIssue>,
    pub size_mismatches: Vec<SizeMismatch>,
}

/// Alignment issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlignmentIssue {
    pub structure_name: String,
    pub expected_alignment: usize,
    pub actual_alignment: usize,
}

/// Size mismatches
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SizeMismatch {
    pub type_name: String,
    pub expected_size: usize,
    pub actual_size: usize,
}

/// Path analysis results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathAnalysis {
    pub implementation: String,
    pub paths_analyzed: Vec<String>,
    pub resolution_results: Vec<PathResolutionResult>,
    pub recommendations: Vec<String>,
}

/// Path resolution results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathResolutionResult {
    pub path: String,
    pub exists: bool,
    pub readable: bool,
    pub absolute_path: Option<String>,
    pub issues: Vec<String>,
}

/// Dependency analysis results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DependencyAnalysis {
    pub implementation: String,
    pub dependencies_found: Vec<String>,
    pub dependencies_missing: Vec<String>,
    pub dependency_chain: Vec<String>,
}

/// Dependency chain entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DependencyChainEntry {
    pub library_name: String,
    pub depends_on: Vec<String>,
    pub is_available: bool,
    pub issues: Vec<String>,
}

/// Runtime error classification
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorClassification {
    pub total_errors: usize,
    pub error_categories: HashMap<String, usize>,
    pub critical_errors: Vec<RuntimeError>,
    pub recommendations: Vec<String>,
}

/// Runtime error information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuntimeError {
    pub error_type: String,
    pub error_message: String,
    pub context: String,
    pub severity: ErrorSeverity,
}

/// Error severity levels
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ErrorSeverity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

/// Build script information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BuildScript {
    pub language: String,
    pub script_content: String,
    pub required_tools: Vec<String>,
    pub environment_variables: HashMap<String, String>,
    pub build_commands: Vec<String>,
    pub validation_commands: Vec<String>,
}

/// Path correction information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathCorrection {
    pub implementation: String,
    pub original_paths: Vec<String>,
    pub corrected_paths: Vec<String>,
    pub corrections_applied: Vec<PathCorrectionEntry>,
}

/// Path correction entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathCorrectionEntry {
    pub original_path: String,
    pub corrected_path: String,
    pub correction_type: PathCorrectionType,
    pub description: String,
}

/// Types of path corrections
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PathCorrectionType {
    RelativeToAbsolute,
    EnvironmentVariableExpansion,
    PathNormalization,
    DirectorySeparatorFix,
    PermissionFix,
}

/// Symbol export validation results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymbolExportValidation {
    pub library_path: String,
    pub exported_symbols: Vec<String>,
    pub missing_symbols: Vec<String>,
    pub validation_successful: bool,
    pub issues: Vec<SymbolExportIssue>,
}

/// Symbol export issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SymbolExportIssue {
    pub symbol_name: String,
    pub issue_description: String,
    pub suggested_fix: String,
}

/// Compatibility layer information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompatibilityLayer {
    pub implementation: String,
    pub layer_type: CompatibilityLayerType,
    pub generated_code: String,
    pub installation_instructions: Vec<String>,
}

/// Types of compatibility layers
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CompatibilityLayerType {
    ABIWrapper,
    CallingConventionAdapter,
    MemoryLayoutAdapter,
    SymbolRedirection,
}