//! Core data types for the FFI audit system

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use pyo3::prelude::*;

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
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum CompatibilityLayerType {
    ABIWrapper,
    CallingConventionAdapter,
    MemoryLayoutAdapter,
    SymbolRedirection,
    PythonWrapper,
    SharedLibrary,
    F2PyWrapper,
    JNIWrapper,
}

/// Performance metrics for execution monitoring
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct PerformanceMetrics {
    #[pyo3(get)]
    pub cpu_time_ns: u64,
    #[pyo3(get)]
    pub wall_time_ns: u64,
    #[pyo3(get)]
    pub memory_usage_bytes: usize,
    #[pyo3(get)]
    pub native_code_percentage: f64,
    #[pyo3(get)]
    pub python_overhead_percentage: f64,
}

#[pymethods]
impl PerformanceMetrics {
    #[new]
    pub fn new(cpu_time_ns: u64, wall_time_ns: u64, memory_usage_bytes: usize, 
               native_code_percentage: f64, python_overhead_percentage: f64) -> Self {
        Self {
            cpu_time_ns,
            wall_time_ns,
            memory_usage_bytes,
            native_code_percentage,
            python_overhead_percentage,
        }
    }
}

/// Execution path monitoring results
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct ExecutionPathMonitoring {
    #[pyo3(get)]
    pub implementation: String,
    #[pyo3(get)]
    pub execution_type: u8, // Changed to u8 for PyO3 compatibility
    #[pyo3(get)]
    pub execution_time_ns: u64,
    #[pyo3(get)]
    pub call_stack_depth: usize,
    #[pyo3(get)]
    pub native_calls_detected: usize,
    #[pyo3(get)]
    pub python_calls_detected: usize,
    #[pyo3(get)]
    pub fallback_detected: bool,
    #[pyo3(get)]
    pub performance_metrics: PerformanceMetrics,
}

#[pymethods]
impl ExecutionPathMonitoring {
    #[new]
    pub fn new(implementation: String, execution_type: u8, execution_time_ns: u64,
               call_stack_depth: usize, native_calls_detected: usize, python_calls_detected: usize,
               fallback_detected: bool, performance_metrics: PerformanceMetrics) -> Self {
        Self {
            implementation,
            execution_type,
            execution_time_ns,
            call_stack_depth,
            native_calls_detected,
            python_calls_detected,
            fallback_detected,
            performance_metrics,
        }
    }
}

/// Types of execution
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ExecutionType {
    NativeOnly,
    PythonOnly,
    Mixed,
    Unknown,
}

impl ExecutionType {
    pub fn as_u8(&self) -> u8 {
        match self {
            ExecutionType::NativeOnly => 0,
            ExecutionType::PythonOnly => 1,
            ExecutionType::Mixed => 2,
            ExecutionType::Unknown => 3,
        }
    }
}

/// Execution trace entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionTraceEntry {
    pub timestamp_ns: u64,
    pub function_name: String,
    pub execution_type: ExecutionType,
    pub duration_ns: u64,
    pub call_depth: usize,
}

/// Execution monitoring configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionMonitoringConfig {
    pub enable_call_tracing: bool,
    pub enable_performance_monitoring: bool,
    pub fallback_detection_threshold: f64,
    pub max_trace_entries: usize,
    pub sampling_interval_ns: u64,
}

/// Fallback detection result with detailed diagnostics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FallbackDetectionResult {
    pub implementation: String,
    pub fallback_detected: bool,
    pub detection_timestamp_ns: u64,
    pub execution_stopped: bool,
    pub diagnostic_info: FallbackDiagnosticInfo,
    pub execution_path_monitoring: ExecutionPathMonitoring,
}

/// Detailed diagnostic information for fallback detection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FallbackDiagnosticInfo {
    pub detection_reason: String,
    pub python_overhead_percentage: f64,
    pub expected_native_percentage: f64,
    pub actual_native_percentage: f64,
    pub performance_anomalies: Vec<String>,
    pub recommended_actions: Vec<String>,
    pub execution_context: ExecutionContext,
}

/// Execution context information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionContext {
    pub call_stack: Vec<String>,
    pub environment_variables: std::collections::HashMap<String, String>,
    pub library_paths: Vec<String>,
    pub loaded_libraries: Vec<String>,
    pub system_info: SystemInfo,
}

/// System information for diagnostics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    pub os_version: String,
    pub architecture: String,
    pub python_version: String,
    pub available_memory_mb: usize,
    pub cpu_cores: usize,
}

/// Performance anomaly detection result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceAnomalyResult {
    pub implementation: String,
    pub anomalies_detected: bool,
    pub anomaly_score: f64,
    pub baseline_performance: PerformanceBaseline,
    pub current_performance: PerformanceSnapshot,
    pub detected_anomalies: Vec<PerformanceAnomaly>,
    pub statistical_analysis: StatisticalAnalysis,
    pub fallback_suspicion_level: SuspicionLevel,
}

/// Performance baseline for comparison
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceBaseline {
    pub implementation_type: String,
    pub expected_execution_time_ns: f64,
    pub expected_memory_usage_mb: f64,
    pub expected_cpu_utilization: f64,
    pub expected_native_percentage: f64,
    pub baseline_source: BaselineSource,
}

/// Current performance snapshot
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceSnapshot {
    pub execution_time_ns: u64,
    pub memory_usage_bytes: usize,
    pub cpu_time_ns: u64,
    pub native_code_percentage: f64,
    pub python_overhead_percentage: f64,
    pub call_count_ratio: f64,
}

/// Individual performance anomaly
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceAnomaly {
    pub anomaly_type: AnomalyType,
    pub severity: AnomalySeverity,
    pub description: String,
    pub measured_value: f64,
    pub expected_value: f64,
    pub deviation_percentage: f64,
    pub confidence_level: f64,
}

/// Types of performance anomalies
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AnomalyType {
    ExecutionTimeAnomaly,
    MemoryUsageAnomaly,
    CpuUtilizationAnomaly,
    NativeCodePercentageAnomaly,
    CallPatternAnomaly,
    ThroughputAnomaly,
    LatencyAnomaly,
}

/// Severity levels for anomalies
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AnomalySeverity {
    Critical,    // > 500% deviation
    High,        // 200-500% deviation
    Medium,      // 100-200% deviation
    Low,         // 50-100% deviation
    Negligible,  // < 50% deviation
}

/// Statistical analysis results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatisticalAnalysis {
    pub sample_size: usize,
    pub mean_execution_time: f64,
    pub standard_deviation: f64,
    pub confidence_interval_95: (f64, f64),
    pub z_score: f64,
    pub p_value: f64,
    pub is_statistically_significant: bool,
}

/// Suspicion level for fallback
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SuspicionLevel {
    None,        // 0-20% suspicion
    Low,         // 20-40% suspicion
    Medium,      // 40-60% suspicion
    High,        // 60-80% suspicion
    Critical,    // 80-100% suspicion
}

/// Source of performance baseline
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BaselineSource {
    HistoricalData,
    TheoreticalModel,
    BenchmarkSuite,
    UserProvided,
    DefaultEstimate,
}

/// Native code verification result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NativeCodeVerificationResult {
    pub implementation: String,
    pub is_native_verified: bool,
    pub confidence_score: f64,
    pub verification_time_ns: u64,
    pub execution_monitoring: ExecutionPathMonitoring,
    pub performance_analysis: PerformanceAnomalyResult,
    pub library_exists: bool,
    pub execution_traces: Vec<String>,
    pub verification_issues: Vec<VerificationIssue>,
    pub recommendations: Vec<String>,
}

/// Verification issue
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerificationIssue {
    pub issue_type: VerificationIssueType,
    pub severity: IssueSeverity,
    pub description: String,
    pub affected_component: String,
    pub resolution_suggestion: String,
}

/// Types of verification issues
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum VerificationIssueType {
    FallbackDetected,
    LowNativePercentage,
    PerformanceAnomaly,
    LibraryNotFound,
    SuspiciousCallPattern,
}

/// Issue severity levels
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum IssueSeverity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

/// Contamination analysis result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContaminationAnalysis {
    pub result_index: usize,
    pub result_value: f64,
    pub is_contaminated: bool,
    pub contamination_type: ContaminationType,
    pub contamination_reason: String,
    pub confidence_score: f64,
    pub detection_method: String,
}

/// Types of contamination
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ContaminationType {
    None,
    FallbackDetected,
    PerformanceAnomaly,
    StatisticalOutlier,
    InvalidValue,
    SuspiciousValue,
}

/// Statistical analysis for contamination detection
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContaminationStatisticalAnalysis {
    pub sample_size: usize,
    pub mean: f64,
    pub median: f64,
    pub standard_deviation: f64,
    pub coefficient_of_variation: f64,
    pub min_value: f64,
    pub max_value: f64,
    pub contamination_indicators: Vec<String>,
    pub outlier_threshold_lower: f64,
    pub outlier_threshold_upper: f64,
}

/// Filtering summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FilteringSummary {
    pub total_results: usize,
    pub contaminated_results: usize,
    pub filtered_results: usize,
    pub contamination_types: std::collections::HashMap<String, usize>,
    pub filtering_confidence: f64,
}

/// Complete contamination filter result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContaminationFilterResult {
    pub implementation: String,
    pub original_results: Vec<f64>,
    pub filtered_results: Vec<f64>,
    pub contamination_analyses: Vec<ContaminationAnalysis>,
    pub statistical_analysis: Option<ContaminationStatisticalAnalysis>,
    pub filtering_summary: FilteringSummary,
    pub filtering_time_ns: u64,
    pub recommendations: Vec<String>,
}

// ─── Task 9: Performance Baseline Comparison Types ────────────────────────────

/// Result of comparing FFI performance against a pure-Python baseline
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceComparisonResult {
    /// Name of the FFI implementation being evaluated
    pub implementation: String,
    /// Measured execution times of the FFI implementation (nanoseconds)
    pub ffi_results_ns: Vec<f64>,
    /// Measured execution times of the pure-Python baseline (nanoseconds)
    pub python_baseline_ns: Vec<f64>,
    /// python_mean / ffi_mean  — values > 1.0 indicate the FFI is faster
    pub performance_ratio: f64,
    /// (python_mean − ffi_mean) / python_mean × 100  (positive = FFI is faster)
    pub speedup_percentage: f64,
    /// Result of the Welch's t-test comparing the two samples
    pub statistical_significance: SignificanceTestResult,
    /// True when the FFI is statistically significantly faster than Python
    pub is_significantly_faster: bool,
    /// True when the performance pattern suggests a Python fallback
    pub fallback_suspected: bool,
    /// Flags describing anomalous behaviour
    pub performance_flags: Vec<PerformanceFlag>,
    /// Human-readable recommendations
    pub recommendations: Vec<String>,
}

/// Result of a Welch's two-sample t-test
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignificanceTestResult {
    /// Human-readable name of the test performed
    pub test_name: String,
    /// Computed t-statistic (positive = FFI mean < Python mean, i.e., FFI is faster)
    pub t_statistic: f64,
    /// Two-sided p-value (approximated via the normal distribution)
    pub p_value: f64,
    /// Confidence level used for the significance decision (e.g., 0.95)
    pub confidence_level: f64,
    /// True when p_value < (1 − confidence_level)
    pub is_significant: bool,
    /// Cohen's d effect size
    pub effect_size: f64,
    /// Welch-Satterthwaite degrees of freedom
    pub degrees_of_freedom: f64,
}

/// Flags raised when a performance comparison shows anomalous patterns
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum PerformanceFlag {
    /// Performance ratio is suspiciously close to 1.0 (FFI ≈ Python speed)
    SuspiciouslySimilarToPython,
    /// FFI is measurably *slower* than Python (ratio < 1.0)
    SignificantlySlowerThanPython,
    /// Pattern strongly suggests the call fell back to Python
    PotentialFallback,
    /// High coefficient of variation in FFI results
    HighVariance,
    /// Fewer than 3 measurements — unreliable comparison
    InsufficientData,
}

/// Aggregate performance report covering multiple FFI implementations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceReport {
    /// One comparison entry per FFI implementation
    pub comparisons: Vec<PerformanceComparisonResult>,
    /// Implementations confirmed to be significantly faster than Python
    pub passing_implementations: Vec<String>,
    /// Implementations that failed the performance check
    pub failing_implementations: Vec<String>,
    /// Implementations flagged as potential fallbacks
    pub suspected_fallbacks: Vec<String>,
    /// Average speedup across all passing implementations
    pub average_speedup_percentage: f64,
    /// Human-readable summary
    pub summary: String,
}

// ─── Task 10: Comprehensive Report Types ──────────────────────────────────────

/// Per-implementation bug summary entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImplementationBugSummary {
    pub implementation: String,
    pub status: ImplementationStatus,
    pub dll_issues: Vec<DLLIssue>,
    pub loading_errors: Vec<LoadingError>,
    pub missing_dependencies: Vec<String>,
    pub architecture_mismatch: bool,
    pub path_issues: Vec<PathIssue>,
    pub fix_steps: Vec<String>,
}

/// Status of an FFI implementation
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ImplementationStatus {
    Working,
    Failed,
    PartiallyWorking,
    Unknown,
}

impl std::fmt::Display for ImplementationStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ImplementationStatus::Working => write!(f, "WORKING"),
            ImplementationStatus::Failed => write!(f, "FAILED"),
            ImplementationStatus::PartiallyWorking => write!(f, "PARTIAL"),
            ImplementationStatus::Unknown => write!(f, "UNKNOWN"),
        }
    }
}

/// Structured bug analysis report (Requirement 1.5)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BugAnalysisReport {
    pub report_title: String,
    pub generated_at: String,
    pub total_implementations: usize,
    pub working_count: usize,
    pub failed_count: usize,
    pub partial_count: usize,
    pub implementation_summaries: Vec<ImplementationBugSummary>,
    pub critical_issues: Vec<String>,
    pub fix_priority_list: Vec<String>,
    pub report_text: String,
}

/// Per-implementation performance entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImplementationPerformanceEntry {
    pub implementation: String,
    pub performance_ratio: f64,
    pub speedup_percentage: f64,
    pub is_significantly_faster: bool,
    pub fallback_suspected: bool,
    pub p_value: f64,
    pub effect_size: f64,
    pub flags: Vec<String>,
    pub sample_size: usize,
}

/// Structured performance validation report (Requirements 6.1-6.5)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceValidationReport {
    pub report_title: String,
    pub generated_at: String,
    pub total_implementations: usize,
    pub passing_count: usize,
    pub failing_count: usize,
    pub suspected_fallback_count: usize,
    pub average_speedup_percentage: f64,
    pub entries: Vec<ImplementationPerformanceEntry>,
    pub fallback_detections: Vec<String>,
    pub report_text: String,
}

/// Combined audit report
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComprehensiveAuditReport {
    pub report_title: String,
    pub generated_at: String,
    pub bug_analysis: BugAnalysisReport,
    pub performance_validation: PerformanceValidationReport,
    pub overall_summary: String,
    pub report_text: String,
}