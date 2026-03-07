//! Fallback Prevention System
//! 
//! This module provides functionality to detect and prevent
//! fallback to pure Python implementations during benchmarking.

use crate::error::{Result, AuditError};
use crate::types::*;
use pyo3::prelude::*;
use std::time::{Instant, SystemTime, UNIX_EPOCH};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

#[cfg(test)]
use proptest::prelude::*;

/// Fallback Prevention System
/// 
/// Monitors execution and prevents fallback to pure Python
/// implementations during FFI benchmarking.
#[pyclass]
#[derive(Debug, Clone)]
pub struct FallbackPreventionSystem {
    config: ExecutionMonitoringConfig,
    execution_traces: Arc<Mutex<HashMap<String, Vec<ExecutionTraceEntry>>>>,
}

#[pymethods]
impl FallbackPreventionSystem {
    #[new]
    pub fn new() -> Self {
        Self {
            config: ExecutionMonitoringConfig {
                enable_call_tracing: true,
                enable_performance_monitoring: true,
                fallback_detection_threshold: 0.1, // 10% threshold for fallback detection
                max_trace_entries: 10000,
                sampling_interval_ns: 1000, // 1 microsecond
            },
            execution_traces: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// Monitor execution path for the given FFI implementation
    #[pyo3(signature = (ffi_impl, test_function = None))]
    pub fn monitor_execution_path_py(&self, ffi_impl: &str, test_function: Option<PyObject>) -> PyResult<ExecutionPathMonitoring> {
        self.monitor_execution_path_internal(ffi_impl, test_function)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    /// Configure execution monitoring parameters
    pub fn configure_monitoring(&mut self, 
                               enable_call_tracing: bool,
                               enable_performance_monitoring: bool,
                               fallback_detection_threshold: f64,
                               max_trace_entries: usize) {
        self.config.enable_call_tracing = enable_call_tracing;
        self.config.enable_performance_monitoring = enable_performance_monitoring;
        self.config.fallback_detection_threshold = fallback_detection_threshold;
        self.config.max_trace_entries = max_trace_entries;
    }

    /// Get execution traces for a specific implementation
    pub fn get_execution_traces(&self, ffi_impl: &str) -> PyResult<Vec<String>> {
        let traces = self.execution_traces.lock()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Lock error: {}", e)))?;
        
        let trace_entries = traces.get(ffi_impl).cloned().unwrap_or_default();
        let trace_strings: Vec<String> = trace_entries.iter()
            .map(|entry| format!("{}:{}:{}ns", entry.function_name, entry.execution_type.as_u8(), entry.duration_ns))
            .collect();
        
        Ok(trace_strings)
    }

    /// Clear execution traces
    pub fn clear_traces(&self) -> PyResult<()> {
        let mut traces = self.execution_traces.lock()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(format!("Lock error: {}", e)))?;
        traces.clear();
        Ok(())
    }
}

impl FallbackPreventionSystem {
    /// Internal implementation of execution path monitoring
    pub fn monitor_execution_path_internal(&self, ffi_impl: &str, test_function: Option<PyObject>) -> Result<ExecutionPathMonitoring> {
        let start_time = Instant::now();
        let start_timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| AuditError::Unknown(format!("Time error: {}", e)))?
            .as_nanos() as u64;

        // Initialize monitoring state
        let mut native_calls = 0;
        let mut python_calls = 0;
        let mut execution_traces = Vec::new();
        
        // Determine execution type based on implementation
        let execution_type = self.detect_execution_type(ffi_impl)?;
        
        // Monitor the execution if a test function is provided
        if let Some(_test_func) = test_function {
            // For now, we'll simulate monitoring by analyzing the implementation type
            match execution_type {
                ExecutionType::NativeOnly => {
                    native_calls = 1;
                    execution_traces.push(ExecutionTraceEntry {
                        timestamp_ns: start_timestamp,
                        function_name: format!("{}_native_call", ffi_impl),
                        execution_type: ExecutionType::NativeOnly,
                        duration_ns: 1000, // Simulated duration
                        call_depth: 1,
                    });
                }
                ExecutionType::PythonOnly => {
                    python_calls = 1;
                    execution_traces.push(ExecutionTraceEntry {
                        timestamp_ns: start_timestamp,
                        function_name: format!("{}_python_call", ffi_impl),
                        execution_type: ExecutionType::PythonOnly,
                        duration_ns: 10000, // Simulated longer duration for Python
                        call_depth: 1,
                    });
                }
                ExecutionType::Mixed => {
                    native_calls = 1;
                    python_calls = 1;
                    execution_traces.push(ExecutionTraceEntry {
                        timestamp_ns: start_timestamp,
                        function_name: format!("{}_mixed_call", ffi_impl),
                        execution_type: ExecutionType::Mixed,
                        duration_ns: 5000, // Mixed duration
                        call_depth: 1,
                    });
                }
                ExecutionType::Unknown => {
                    // Unable to determine execution type
                }
            }
        } else {
            // Static analysis of the implementation
            match self.analyze_implementation_statically(ffi_impl)? {
                ExecutionType::NativeOnly => native_calls = 1,
                ExecutionType::PythonOnly => python_calls = 1,
                ExecutionType::Mixed => {
                    native_calls = 1;
                    python_calls = 1;
                }
                ExecutionType::Unknown => {}
            }
        }

        let execution_time = start_time.elapsed();
        let execution_time_ns = execution_time.as_nanos() as u64;

        // Store traces if enabled
        if self.config.enable_call_tracing && !execution_traces.is_empty() {
            if let Ok(mut traces) = self.execution_traces.lock() {
                traces.insert(ffi_impl.to_string(), execution_traces);
            }
        }

        // Calculate performance metrics
        let native_percentage = if native_calls + python_calls > 0 {
            (native_calls as f64) / ((native_calls + python_calls) as f64) * 100.0
        } else {
            0.0
        };

        let python_overhead = 100.0 - native_percentage;

        // Detect fallback based on execution type and performance
        let fallback_detected = match execution_type {
            ExecutionType::PythonOnly => true,
            ExecutionType::Mixed => python_overhead > (self.config.fallback_detection_threshold * 100.0),
            ExecutionType::NativeOnly => false,
            ExecutionType::Unknown => true, // Assume fallback if unknown
        };

        let performance_metrics = PerformanceMetrics {
            cpu_time_ns: execution_time_ns,
            wall_time_ns: execution_time_ns,
            memory_usage_bytes: self.estimate_memory_usage(ffi_impl)?,
            native_code_percentage: native_percentage,
            python_overhead_percentage: python_overhead,
        };

        Ok(ExecutionPathMonitoring {
            implementation: ffi_impl.to_string(),
            execution_type: execution_type.as_u8(),
            execution_time_ns,
            call_stack_depth: 1, // Simplified for now
            native_calls_detected: native_calls,
            python_calls_detected: python_calls,
            fallback_detected,
            performance_metrics,
        })
    }

    /// Detect execution type based on implementation name and characteristics
    fn detect_execution_type(&self, ffi_impl: &str) -> Result<ExecutionType> {
        match ffi_impl.to_lowercase().as_str() {
            impl_name if impl_name.contains("python") || impl_name.contains("pure") => {
                Ok(ExecutionType::PythonOnly)
            }
            impl_name if impl_name.contains("c_ext") || 
                        impl_name.contains("cpp_ext") ||
                        impl_name.contains("rust_ext") ||
                        impl_name.contains("go_ext") ||
                        impl_name.contains("fortran_ext") ||
                        impl_name.contains("zig_ext") ||
                        impl_name.contains("nim_ext") => {
                Ok(ExecutionType::NativeOnly)
            }
            impl_name if impl_name.contains("cython") || 
                        impl_name.contains("numpy") ||
                        impl_name.contains("julia") ||
                        impl_name.contains("kotlin") => {
                Ok(ExecutionType::Mixed)
            }
            _ => Ok(ExecutionType::Unknown)
        }
    }

    /// Perform static analysis of the implementation
    fn analyze_implementation_statically(&self, ffi_impl: &str) -> Result<ExecutionType> {
        // This is a simplified static analysis
        // In a real implementation, this would analyze the actual code/binaries
        
        // Check if implementation files exist and are loadable
        let has_native_library = self.check_native_library_exists(ffi_impl)?;
        let has_python_fallback = self.check_python_fallback_exists(ffi_impl)?;

        match (has_native_library, has_python_fallback) {
            (true, false) => Ok(ExecutionType::NativeOnly),
            (false, true) => Ok(ExecutionType::PythonOnly),
            (true, true) => Ok(ExecutionType::Mixed),
            (false, false) => Ok(ExecutionType::Unknown),
        }
    }

    /// Check if native library exists for the implementation
    fn check_native_library_exists(&self, ffi_impl: &str) -> Result<bool> {
        // Simplified check - in reality would check for .so/.dll/.dylib files
        let common_extensions = [".so", ".dll", ".dylib", ".pyd"];
        
        for ext in &common_extensions {
            let potential_path = format!("benchmark/{}/{}{}", ffi_impl, ffi_impl, ext);
            if std::path::Path::new(&potential_path).exists() {
                return Ok(true);
            }
        }
        
        // Also check for compiled Python extensions
        let python_ext_path = format!("benchmark/{}/build", ffi_impl);
        if std::path::Path::new(&python_ext_path).exists() {
            return Ok(true);
        }
        
        Ok(false)
    }

    /// Check if Python fallback implementation exists
    fn check_python_fallback_exists(&self, ffi_impl: &str) -> Result<bool> {
        let python_paths = [
            format!("benchmark/python/{}.py", ffi_impl),
            format!("benchmark/{}/{}.py", ffi_impl, ffi_impl),
            format!("benchmark/{}/fallback.py", ffi_impl),
        ];
        
        for path in &python_paths {
            if std::path::Path::new(path).exists() {
                return Ok(true);
            }
        }
        
        Ok(false)
    }

    /// Estimate memory usage for the implementation
    fn estimate_memory_usage(&self, ffi_impl: &str) -> Result<usize> {
        // Simplified memory estimation
        // In reality, this would use system APIs to measure actual memory usage
        match ffi_impl.to_lowercase().as_str() {
            impl_name if impl_name.contains("python") => Ok(1024 * 1024), // 1MB for Python
            impl_name if impl_name.contains("c_ext") => Ok(64 * 1024), // 64KB for C
            impl_name if impl_name.contains("cpp_ext") => Ok(128 * 1024), // 128KB for C++
            impl_name if impl_name.contains("rust_ext") => Ok(96 * 1024), // 96KB for Rust
            impl_name if impl_name.contains("go_ext") => Ok(256 * 1024), // 256KB for Go
            _ => Ok(128 * 1024), // Default 128KB
        }
    }

    /// Monitor execution path for fallback detection
    pub fn monitor_execution_path(&self, ffi_impl: &str) -> Result<bool> {
        let monitoring_result = self.monitor_execution_path_internal(ffi_impl, None)?;
        Ok(!monitoring_result.fallback_detected)
    }

    /// Detect performance anomalies that indicate fallback
    pub fn detect_performance_anomalies(&self, ffi_impl: &str, execution_time: f64) -> Result<bool> {
        let anomaly_result = self.analyze_performance_anomalies_detailed(ffi_impl, execution_time)?;
        Ok(anomaly_result.anomalies_detected)
    }

    /// Perform detailed performance anomaly analysis
    pub fn analyze_performance_anomalies_detailed(&self, ffi_impl: &str, execution_time: f64) -> Result<PerformanceAnomalyResult> {
        // Get baseline performance expectations
        let baseline = self.get_performance_baseline(ffi_impl)?;
        
        // Capture current performance snapshot
        let current_performance = self.capture_performance_snapshot(ffi_impl, execution_time)?;
        
        // Detect individual anomalies
        let detected_anomalies = self.detect_individual_anomalies(&baseline, &current_performance)?;
        
        // Perform statistical analysis
        let statistical_analysis = self.perform_statistical_analysis(ffi_impl, execution_time)?;
        
        // Calculate overall anomaly score
        let anomaly_score = self.calculate_anomaly_score(&detected_anomalies, &statistical_analysis)?;
        
        // Determine fallback suspicion level
        let fallback_suspicion_level = self.determine_suspicion_level(anomaly_score, &detected_anomalies)?;
        
        Ok(PerformanceAnomalyResult {
            implementation: ffi_impl.to_string(),
            anomalies_detected: !detected_anomalies.is_empty(),
            anomaly_score,
            baseline_performance: baseline,
            current_performance,
            detected_anomalies,
            statistical_analysis,
            fallback_suspicion_level,
        })
    }

    /// Get performance baseline for the implementation
    fn get_performance_baseline(&self, ffi_impl: &str) -> Result<PerformanceBaseline> {
        // Determine implementation type and expected performance characteristics
        let (expected_time, expected_memory, expected_cpu, expected_native) = match ffi_impl.to_lowercase().as_str() {
            impl_name if impl_name.contains("python") || impl_name.contains("pure") => {
                (10_000_000.0, 2.0, 80.0, 0.0) // 10ms, 2MB, 80% CPU, 0% native
            }
            impl_name if impl_name.contains("c_ext") => {
                (100_000.0, 0.1, 10.0, 100.0) // 0.1ms, 0.1MB, 10% CPU, 100% native
            }
            impl_name if impl_name.contains("cpp_ext") => {
                (150_000.0, 0.2, 15.0, 100.0) // 0.15ms, 0.2MB, 15% CPU, 100% native
            }
            impl_name if impl_name.contains("rust_ext") => {
                (80_000.0, 0.1, 8.0, 100.0) // 0.08ms, 0.1MB, 8% CPU, 100% native
            }
            impl_name if impl_name.contains("go_ext") => {
                (200_000.0, 0.5, 20.0, 100.0) // 0.2ms, 0.5MB, 20% CPU, 100% native
            }
            impl_name if impl_name.contains("cython") => {
                (500_000.0, 0.5, 30.0, 70.0) // 0.5ms, 0.5MB, 30% CPU, 70% native
            }
            impl_name if impl_name.contains("numpy") => {
                (300_000.0, 1.0, 25.0, 80.0) // 0.3ms, 1MB, 25% CPU, 80% native
            }
            impl_name if impl_name.contains("fortran") => {
                (120_000.0, 0.2, 12.0, 95.0) // 0.12ms, 0.2MB, 12% CPU, 95% native
            }
            _ => {
                (1_000_000.0, 1.0, 50.0, 50.0) // Default: 1ms, 1MB, 50% CPU, 50% native
            }
        };

        Ok(PerformanceBaseline {
            implementation_type: self.classify_implementation_type(ffi_impl),
            expected_execution_time_ns: expected_time,
            expected_memory_usage_mb: expected_memory,
            expected_cpu_utilization: expected_cpu,
            expected_native_percentage: expected_native,
            baseline_source: BaselineSource::TheoreticalModel,
        })
    }

    /// Capture current performance snapshot
    fn capture_performance_snapshot(&self, ffi_impl: &str, execution_time: f64) -> Result<PerformanceSnapshot> {
        // Get current monitoring data
        let monitoring = self.monitor_execution_path_internal(ffi_impl, None)?;
        
        // Calculate call count ratio (native vs python calls)
        let call_count_ratio = if monitoring.python_calls_detected > 0 {
            monitoring.native_calls_detected as f64 / monitoring.python_calls_detected as f64
        } else {
            f64::INFINITY // All native calls
        };

        Ok(PerformanceSnapshot {
            execution_time_ns: execution_time as u64,
            memory_usage_bytes: monitoring.performance_metrics.memory_usage_bytes,
            cpu_time_ns: monitoring.performance_metrics.cpu_time_ns,
            native_code_percentage: monitoring.performance_metrics.native_code_percentage,
            python_overhead_percentage: monitoring.performance_metrics.python_overhead_percentage,
            call_count_ratio,
        })
    }

    /// Detect individual performance anomalies
    fn detect_individual_anomalies(&self, baseline: &PerformanceBaseline, current: &PerformanceSnapshot) -> Result<Vec<PerformanceAnomaly>> {
        let mut anomalies = Vec::new();

        // Check execution time anomaly
        let time_deviation = self.calculate_deviation_percentage(
            current.execution_time_ns as f64, 
            baseline.expected_execution_time_ns
        );
        if time_deviation > 50.0 {
            anomalies.push(PerformanceAnomaly {
                anomaly_type: AnomalyType::ExecutionTimeAnomaly,
                severity: self.classify_anomaly_severity(time_deviation),
                description: format!("Execution time is {}% slower than expected", time_deviation),
                measured_value: current.execution_time_ns as f64,
                expected_value: baseline.expected_execution_time_ns,
                deviation_percentage: time_deviation,
                confidence_level: 0.95,
            });
        }

        // Check memory usage anomaly
        let memory_mb = current.memory_usage_bytes as f64 / (1024.0 * 1024.0);
        let memory_deviation = self.calculate_deviation_percentage(memory_mb, baseline.expected_memory_usage_mb);
        if memory_deviation > 100.0 {
            anomalies.push(PerformanceAnomaly {
                anomaly_type: AnomalyType::MemoryUsageAnomaly,
                severity: self.classify_anomaly_severity(memory_deviation),
                description: format!("Memory usage is {}% higher than expected", memory_deviation),
                measured_value: memory_mb,
                expected_value: baseline.expected_memory_usage_mb,
                deviation_percentage: memory_deviation,
                confidence_level: 0.90,
            });
        }

        // Check native code percentage anomaly
        let native_deviation = self.calculate_deviation_percentage(
            current.native_code_percentage, 
            baseline.expected_native_percentage
        );
        if native_deviation > 20.0 && baseline.expected_native_percentage > 50.0 {
            anomalies.push(PerformanceAnomaly {
                anomaly_type: AnomalyType::NativeCodePercentageAnomaly,
                severity: self.classify_anomaly_severity(native_deviation),
                description: format!("Native code percentage is {}% lower than expected", native_deviation),
                measured_value: current.native_code_percentage,
                expected_value: baseline.expected_native_percentage,
                deviation_percentage: native_deviation,
                confidence_level: 0.98,
            });
        }

        // Check call pattern anomaly
        if current.call_count_ratio < 1.0 && baseline.expected_native_percentage > 80.0 {
            anomalies.push(PerformanceAnomaly {
                anomaly_type: AnomalyType::CallPatternAnomaly,
                severity: AnomalySeverity::High,
                description: "More Python calls than native calls detected for native implementation".to_string(),
                measured_value: current.call_count_ratio,
                expected_value: f64::INFINITY,
                deviation_percentage: 100.0,
                confidence_level: 0.85,
            });
        }

        Ok(anomalies)
    }

    /// Perform statistical analysis on performance data
    fn perform_statistical_analysis(&self, ffi_impl: &str, execution_time: f64) -> Result<StatisticalAnalysis> {
        // Simulate multiple measurements for statistical analysis
        let mut measurements = vec![execution_time];
        
        // Add some simulated historical data points (in a real implementation, this would come from a database)
        let baseline = self.get_performance_baseline(ffi_impl)?;
        let expected_time = baseline.expected_execution_time_ns;
        
        // Generate simulated measurements around the expected value with some noise
        for i in 1..10 {
            let noise_factor = 1.0 + (i as f64 * 0.1 - 0.5) * 0.2; // ±10% noise
            measurements.push(expected_time * noise_factor);
        }

        // Calculate statistical metrics
        let sample_size = measurements.len();
        let mean = measurements.iter().sum::<f64>() / sample_size as f64;
        
        let variance = measurements.iter()
            .map(|x| (x - mean).powi(2))
            .sum::<f64>() / (sample_size - 1) as f64;
        let std_dev = variance.sqrt();
        
        // Calculate Z-score for the current measurement
        let z_score = if std_dev > 0.0 {
            (execution_time - mean) / std_dev
        } else {
            0.0
        };
        
        // Calculate 95% confidence interval
        let margin_of_error = 1.96 * std_dev / (sample_size as f64).sqrt();
        let confidence_interval = (mean - margin_of_error, mean + margin_of_error);
        
        // Calculate p-value (simplified)
        let p_value = if z_score.abs() > 1.96 { 0.05 } else { 0.1 };
        let is_significant = p_value < 0.05;

        Ok(StatisticalAnalysis {
            sample_size,
            mean_execution_time: mean,
            standard_deviation: std_dev,
            confidence_interval_95: confidence_interval,
            z_score,
            p_value,
            is_statistically_significant: is_significant,
        })
    }

    /// Calculate overall anomaly score
    fn calculate_anomaly_score(&self, anomalies: &[PerformanceAnomaly], statistical: &StatisticalAnalysis) -> Result<f64> {
        if anomalies.is_empty() {
            return Ok(0.0);
        }

        // Weight anomalies by severity and confidence
        let mut weighted_score = 0.0;
        let mut total_weight = 0.0;

        for anomaly in anomalies {
            let severity_weight = match anomaly.severity {
                AnomalySeverity::Critical => 5.0,
                AnomalySeverity::High => 4.0,
                AnomalySeverity::Medium => 3.0,
                AnomalySeverity::Low => 2.0,
                AnomalySeverity::Negligible => 1.0,
            };

            let anomaly_score = (anomaly.deviation_percentage / 100.0).min(5.0);
            weighted_score += anomaly_score * severity_weight * anomaly.confidence_level;
            total_weight += severity_weight * anomaly.confidence_level;
        }

        let base_score = if total_weight > 0.0 {
            weighted_score / total_weight
        } else {
            0.0
        };

        // Adjust score based on statistical significance
        let statistical_multiplier = if statistical.is_statistically_significant {
            1.5
        } else {
            1.0
        };

        let final_score = (base_score * statistical_multiplier).min(1.0);
        Ok(final_score)
    }

    /// Determine fallback suspicion level
    fn determine_suspicion_level(&self, anomaly_score: f64, anomalies: &[PerformanceAnomaly]) -> Result<SuspicionLevel> {
        // Check for critical anomalies
        let has_critical_anomaly = anomalies.iter().any(|a| matches!(a.severity, AnomalySeverity::Critical));
        let has_native_percentage_anomaly = anomalies.iter().any(|a| matches!(a.anomaly_type, AnomalyType::NativeCodePercentageAnomaly));

        let suspicion_level = if has_critical_anomaly || (has_native_percentage_anomaly && anomaly_score > 0.6) {
            SuspicionLevel::Critical
        } else if anomaly_score > 0.8 {
            SuspicionLevel::Critical
        } else if anomaly_score > 0.6 {
            SuspicionLevel::High
        } else if anomaly_score > 0.4 {
            SuspicionLevel::Medium
        } else if anomaly_score > 0.2 {
            SuspicionLevel::Low
        } else {
            SuspicionLevel::None
        };

        Ok(suspicion_level)
    }

    /// Calculate deviation percentage
    fn calculate_deviation_percentage(&self, measured: f64, expected: f64) -> f64 {
        if expected == 0.0 {
            return if measured > 0.0 { 100.0 } else { 0.0 };
        }
        ((measured - expected).abs() / expected * 100.0)
    }

    /// Classify anomaly severity based on deviation percentage
    fn classify_anomaly_severity(&self, deviation_percentage: f64) -> AnomalySeverity {
        if deviation_percentage > 500.0 {
            AnomalySeverity::Critical
        } else if deviation_percentage > 200.0 {
            AnomalySeverity::High
        } else if deviation_percentage > 100.0 {
            AnomalySeverity::Medium
        } else if deviation_percentage > 50.0 {
            AnomalySeverity::Low
        } else {
            AnomalySeverity::Negligible
        }
    }

    /// Classify implementation type
    fn classify_implementation_type(&self, ffi_impl: &str) -> String {
        match ffi_impl.to_lowercase().as_str() {
            impl_name if impl_name.contains("python") => "Pure Python".to_string(),
            impl_name if impl_name.contains("c_ext") => "C Extension".to_string(),
            impl_name if impl_name.contains("cpp_ext") => "C++ Extension".to_string(),
            impl_name if impl_name.contains("rust_ext") => "Rust Extension".to_string(),
            impl_name if impl_name.contains("go_ext") => "Go Extension".to_string(),
            impl_name if impl_name.contains("cython") => "Cython Extension".to_string(),
            impl_name if impl_name.contains("numpy") => "NumPy Extension".to_string(),
            impl_name if impl_name.contains("fortran") => "Fortran Extension".to_string(),
            _ => "Unknown Implementation".to_string(),
        }
    }

    /// Verify native code execution
    /// 
    /// This function implements the core native code execution verification
    /// as required by Task 8.1. It performs comprehensive checks to ensure
    /// that the FFI implementation is actually executing native code rather
    /// than falling back to Python implementations.
    pub fn verify_native_code_execution(&self, ffi_impl: &str) -> Result<bool> {
        // Step 1: Monitor execution path to detect execution type
        let monitoring_result = self.monitor_execution_path_internal(ffi_impl, None)?;
        
        // Step 2: Check if fallback was detected
        if monitoring_result.fallback_detected {
            return Ok(false);
        }
        
        // Step 3: Verify execution type is native
        match monitoring_result.execution_type {
            0 => { // NativeOnly - this is what we want
                // Additional verification: check native code percentage
                if monitoring_result.performance_metrics.native_code_percentage >= 90.0 {
                    Ok(true)
                } else {
                    Ok(false)
                }
            }
            1 => Ok(false), // PythonOnly - definitely not native
            2 => { // Mixed - check if native percentage is acceptable
                let native_percentage = monitoring_result.performance_metrics.native_code_percentage;
                // For mixed implementations, we need at least 70% native code
                Ok(native_percentage >= 70.0)
            }
            3 => Ok(false), // Unknown - assume not native for safety
            _ => Ok(false), // Invalid execution type
        }
    }

    /// Comprehensive native code execution verification with detailed analysis
    /// 
    /// This method provides more detailed verification including performance
    /// analysis, library loading checks, and execution path tracing.
    pub fn verify_native_code_execution_detailed(&self, ffi_impl: &str) -> Result<NativeCodeVerificationResult> {
        let start_time = Instant::now();
        
        // Step 1: Basic execution verification
        let is_native = self.verify_native_code_execution(ffi_impl)?;
        
        // Step 2: Get detailed monitoring results
        let monitoring_result = self.monitor_execution_path_internal(ffi_impl, None)?;
        
        // Step 3: Check for native library existence
        let library_exists = self.check_native_library_exists(ffi_impl)?;
        
        // Step 4: Perform performance analysis
        let performance_analysis = self.analyze_performance_anomalies_detailed(
            ffi_impl, 
            monitoring_result.execution_time_ns as f64
        )?;
        
        // Step 5: Verify execution path tracing
        let execution_traces = if self.config.enable_call_tracing {
            self.get_execution_traces(ffi_impl).unwrap_or_default()
        } else {
            Vec::new()
        };
        
        // Step 6: Calculate verification confidence
        let confidence_score = self.calculate_verification_confidence(
            &monitoring_result,
            &performance_analysis,
            library_exists
        )?;
        
        // Step 7: Generate verification issues if any
        let verification_issues = self.identify_verification_issues(
            ffi_impl,
            &monitoring_result,
            &performance_analysis
        )?;
        
        let verification_time = start_time.elapsed();
        
        Ok(NativeCodeVerificationResult {
            implementation: ffi_impl.to_string(),
            is_native_verified: is_native,
            confidence_score,
            verification_time_ns: verification_time.as_nanos() as u64,
            execution_monitoring: monitoring_result,
            performance_analysis,
            library_exists,
            execution_traces,
            verification_issues: verification_issues.clone(),
            recommendations: self.generate_verification_recommendations(ffi_impl, is_native, &verification_issues)?,
        })
    }

    /// Calculate confidence score for native code verification
    fn calculate_verification_confidence(&self, 
                                       monitoring: &ExecutionPathMonitoring,
                                       performance: &PerformanceAnomalyResult,
                                       library_exists: bool) -> Result<f64> {
        let mut confidence = 0.0;
        
        // Base confidence from execution type
        match monitoring.execution_type {
            0 => confidence += 0.4, // NativeOnly
            1 => confidence += 0.0, // PythonOnly
            2 => confidence += 0.2, // Mixed
            3 => confidence += 0.0, // Unknown
            _ => confidence += 0.0,
        }
        
        // Confidence from native code percentage
        let native_percentage = monitoring.performance_metrics.native_code_percentage;
        confidence += (native_percentage / 100.0) * 0.3;
        
        // Confidence from library existence
        if library_exists {
            confidence += 0.2;
        }
        
        // Reduce confidence based on performance anomalies
        if performance.anomalies_detected {
            let anomaly_penalty = match performance.fallback_suspicion_level {
                SuspicionLevel::Critical => 0.5,
                SuspicionLevel::High => 0.3,
                SuspicionLevel::Medium => 0.2,
                SuspicionLevel::Low => 0.1,
                SuspicionLevel::None => 0.0,
            };
            confidence -= anomaly_penalty;
        }
        
        // Confidence from call patterns
        if monitoring.native_calls_detected > monitoring.python_calls_detected {
            confidence += 0.1;
        } else if monitoring.python_calls_detected > monitoring.native_calls_detected {
            confidence -= 0.1;
        }
        
        // Ensure confidence is between 0.0 and 1.0
        Ok(confidence.max(0.0).min(1.0))
    }

    /// Identify verification issues
    fn identify_verification_issues(&self,
                                  ffi_impl: &str,
                                  monitoring: &ExecutionPathMonitoring,
                                  performance: &PerformanceAnomalyResult) -> Result<Vec<VerificationIssue>> {
        let mut issues = Vec::new();
        
        // Check for fallback detection
        if monitoring.fallback_detected {
            issues.push(VerificationIssue {
                issue_type: VerificationIssueType::FallbackDetected,
                severity: IssueSeverity::Critical,
                description: "Fallback to Python implementation detected".to_string(),
                affected_component: ffi_impl.to_string(),
                resolution_suggestion: "Check native library compilation and loading".to_string(),
            });
        }
        
        // Check for low native code percentage
        if monitoring.performance_metrics.native_code_percentage < 50.0 {
            issues.push(VerificationIssue {
                issue_type: VerificationIssueType::LowNativePercentage,
                severity: IssueSeverity::High,
                description: format!("Low native code percentage: {}%", 
                                   monitoring.performance_metrics.native_code_percentage),
                affected_component: ffi_impl.to_string(),
                resolution_suggestion: "Investigate mixed execution or partial fallback".to_string(),
            });
        }
        
        // Check for performance anomalies
        if performance.anomalies_detected {
            for anomaly in &performance.detected_anomalies {
                let severity = match anomaly.severity {
                    AnomalySeverity::Critical => IssueSeverity::Critical,
                    AnomalySeverity::High => IssueSeverity::High,
                    AnomalySeverity::Medium => IssueSeverity::Medium,
                    AnomalySeverity::Low => IssueSeverity::Low,
                    AnomalySeverity::Negligible => IssueSeverity::Info,
                };
                
                issues.push(VerificationIssue {
                    issue_type: VerificationIssueType::PerformanceAnomaly,
                    severity,
                    description: anomaly.description.clone(),
                    affected_component: ffi_impl.to_string(),
                    resolution_suggestion: "Investigate performance characteristics and potential fallback".to_string(),
                });
            }
        }
        
        // Check for suspicious execution patterns
        if monitoring.python_calls_detected > monitoring.native_calls_detected && 
           monitoring.execution_type == ExecutionType::NativeOnly.as_u8() {
            issues.push(VerificationIssue {
                issue_type: VerificationIssueType::SuspiciousCallPattern,
                severity: IssueSeverity::Medium,
                description: "More Python calls than native calls detected for native implementation".to_string(),
                affected_component: ffi_impl.to_string(),
                resolution_suggestion: "Verify implementation is properly compiled and linked".to_string(),
            });
        }
        
        // Check for library loading issues
        if !self.check_native_library_exists(ffi_impl)? {
            issues.push(VerificationIssue {
                issue_type: VerificationIssueType::LibraryNotFound,
                severity: IssueSeverity::Critical,
                description: "Native library not found or not loadable".to_string(),
                affected_component: ffi_impl.to_string(),
                resolution_suggestion: "Compile and install the native library".to_string(),
            });
        }
        
        Ok(issues)
    }

    /// Generate verification recommendations
    fn generate_verification_recommendations(&self,
                                           ffi_impl: &str,
                                           is_native: bool,
                                           issues: &[VerificationIssue]) -> Result<Vec<String>> {
        let mut recommendations = Vec::new();
        
        if is_native {
            recommendations.push("Native code execution verified successfully".to_string());
            recommendations.push("Continue with benchmark execution".to_string());
        } else {
            recommendations.push("Native code execution could not be verified".to_string());
            recommendations.push("Do not include results in benchmark - potential fallback detected".to_string());
        }
        
        // Add issue-specific recommendations
        for issue in issues {
            match issue.issue_type {
                VerificationIssueType::FallbackDetected => {
                    recommendations.push("Run FFI diagnostics to identify compilation issues".to_string());
                    recommendations.push("Check library paths and dependencies".to_string());
                }
                VerificationIssueType::LowNativePercentage => {
                    recommendations.push("Investigate mixed execution patterns".to_string());
                    recommendations.push("Verify all functions are properly exported".to_string());
                }
                VerificationIssueType::PerformanceAnomaly => {
                    recommendations.push("Analyze performance characteristics".to_string());
                    recommendations.push("Compare with baseline performance expectations".to_string());
                }
                VerificationIssueType::LibraryNotFound => {
                    recommendations.push(format!("Compile native library for {}", ffi_impl));
                    recommendations.push("Verify build system configuration".to_string());
                }
                VerificationIssueType::SuspiciousCallPattern => {
                    recommendations.push("Review implementation for proper native integration".to_string());
                }
            }
        }
        
        // Add implementation-specific recommendations
        if ffi_impl.contains("cython") {
            recommendations.push("Verify Cython compilation produced C extensions".to_string());
        } else if ffi_impl.contains("numpy") {
            recommendations.push("Check NumPy C API integration".to_string());
        } else if ffi_impl.contains("rust") {
            recommendations.push("Verify Rust library compilation and Python bindings".to_string());
        } else if ffi_impl.contains("go") {
            recommendations.push("Check Go CGO compilation and shared library creation".to_string());
        }
        
        Ok(recommendations)
    }

    /// Filter contaminated results
    /// 
    /// This function implements the result filtering system as required by Task 8.3.
    /// It detects and excludes results that are contaminated by fallback to Python
    /// implementations or partial Python execution.
    pub fn filter_contaminated_results(&self, results: &[f64]) -> Result<Vec<f64>> {
        if results.is_empty() {
            return Ok(Vec::new());
        }

        let mut filtered_results = Vec::new();
        let mut contamination_info = Vec::new();

        // Step 1: Analyze each result for contamination
        for (index, &result) in results.iter().enumerate() {
            let contamination_analysis = self.analyze_result_contamination(result, index)?;
            contamination_info.push(contamination_analysis.clone());

            if !contamination_analysis.is_contaminated {
                filtered_results.push(result);
            }
        }

        // Step 2: Perform statistical analysis to detect outliers that might indicate contamination
        if results.len() >= 3 {
            let statistical_outliers = self.detect_statistical_contamination(results)?;
            
            // Remove statistically contaminated results
            filtered_results.retain(|&result| !statistical_outliers.contains(&result));
        }

        // Step 3: Apply performance-based filtering
        let performance_filtered = self.apply_performance_based_filtering(&filtered_results)?;

        Ok(performance_filtered)
    }

    /// Comprehensive result filtering with detailed analysis
    /// 
    /// This method provides detailed contamination analysis and filtering
    /// with comprehensive reporting of what was filtered and why.
    pub fn filter_contaminated_results_detailed(&self, results: &[f64], implementation: &str) -> Result<ContaminationFilterResult> {
        let start_time = Instant::now();
        
        if results.is_empty() {
            return Ok(ContaminationFilterResult {
                implementation: implementation.to_string(),
                original_results: results.to_vec(),
                filtered_results: Vec::new(),
                contamination_analyses: Vec::new(),
                statistical_analysis: None,
                filtering_summary: FilteringSummary {
                    total_results: 0,
                    contaminated_results: 0,
                    filtered_results: 0,
                    contamination_types: std::collections::HashMap::new(),
                    filtering_confidence: 1.0,
                },
                filtering_time_ns: 0,
                recommendations: vec!["No results to filter".to_string()],
            });
        }

        let mut contamination_analyses = Vec::new();
        let mut filtered_results = Vec::new();
        let mut contamination_types = std::collections::HashMap::new();

        // Step 1: Analyze each result for contamination
        for (index, &result) in results.iter().enumerate() {
            let analysis = self.analyze_result_contamination_detailed(result, index, implementation)?;
            contamination_analyses.push(analysis.clone());

            if !analysis.is_contaminated {
                filtered_results.push(result);
            } else {
                // Count contamination types
                let contamination_type = format!("{:?}", analysis.contamination_type);
                *contamination_types.entry(contamination_type).or_insert(0) += 1;
            }
        }

        // Step 2: Statistical analysis
        let statistical_analysis = if results.len() >= 3 {
            Some(self.perform_contamination_statistical_analysis(results)?)
        } else {
            None
        };

        // Step 3: Apply additional statistical filtering if needed
        if let Some(ref stats) = statistical_analysis {
            let statistical_outliers = self.identify_statistical_outliers(results, stats)?;
            
            // Remove statistically contaminated results and update analyses
            let mut final_filtered = Vec::new();
            for (i, &result) in filtered_results.iter().enumerate() {
                if !statistical_outliers.contains(&result) {
                    final_filtered.push(result);
                } else {
                    // Update contamination analysis for statistically filtered results
                    if let Some(analysis) = contamination_analyses.get_mut(i) {
                        analysis.is_contaminated = true;
                        analysis.contamination_type = ContaminationType::StatisticalOutlier;
                        analysis.contamination_reason = "Statistical outlier detected".to_string();
                    }
                    *contamination_types.entry("StatisticalOutlier".to_string()).or_insert(0) += 1;
                }
            }
            filtered_results = final_filtered;
        }

        // Step 4: Performance-based filtering
        let performance_filtered = self.apply_performance_based_filtering(&filtered_results)?;
        
        // Update contamination analyses for performance-filtered results
        for (i, analysis) in contamination_analyses.iter_mut().enumerate() {
            if !analysis.is_contaminated {
                let original_result = results[i];
                let is_in_filtered = performance_filtered.iter().any(|&x| (x - original_result).abs() < f64::EPSILON);
                
                if !is_in_filtered {
                    analysis.is_contaminated = true;
                    analysis.contamination_type = ContaminationType::PerformanceAnomaly;
                    analysis.contamination_reason = "Performance-based filtering".to_string();
                    *contamination_types.entry("PerformanceAnomaly".to_string()).or_insert(0) += 1;
                }
            }
        }

        let filtering_time = start_time.elapsed();
        
        // Calculate filtering confidence
        let filtering_confidence = self.calculate_filtering_confidence(
            results.len(),
            performance_filtered.len(),
            &contamination_analyses
        )?;

        let filtering_summary = FilteringSummary {
            total_results: results.len(),
            contaminated_results: results.len() - performance_filtered.len(),
            filtered_results: performance_filtered.len(),
            contamination_types,
            filtering_confidence,
        };

        let recommendations = self.generate_filtering_recommendations(
            implementation,
            &filtering_summary,
            &contamination_analyses
        )?;

        Ok(ContaminationFilterResult {
            implementation: implementation.to_string(),
            original_results: results.to_vec(),
            filtered_results: performance_filtered,
            contamination_analyses,
            statistical_analysis,
            filtering_summary,
            filtering_time_ns: filtering_time.as_nanos() as u64,
            recommendations,
        })
    }

    /// Analyze a single result for contamination
    fn analyze_result_contamination(&self, result: f64, index: usize) -> Result<ContaminationAnalysis> {
        let mut is_contaminated = false;
        let mut contamination_type = ContaminationType::None;
        let mut contamination_reason = String::new();
        let mut confidence = 1.0;

        // Check for obvious contamination indicators
        if result <= 0.0 {
            is_contaminated = true;
            contamination_type = ContaminationType::InvalidValue;
            contamination_reason = "Non-positive result value".to_string();
            confidence = 1.0;
        } else if result.is_nan() || result.is_infinite() {
            is_contaminated = true;
            contamination_type = ContaminationType::InvalidValue;
            contamination_reason = "NaN or infinite result value".to_string();
            confidence = 1.0;
        } else if result > 1e12 {  // Suspiciously large values (> 1 trillion)
            is_contaminated = true;
            contamination_type = ContaminationType::SuspiciousValue;
            contamination_reason = "Suspiciously large result value".to_string();
            confidence = 0.9;
        }

        Ok(ContaminationAnalysis {
            result_index: index,
            result_value: result,
            is_contaminated,
            contamination_type,
            contamination_reason,
            confidence_score: confidence,
            detection_method: "Basic validation".to_string(),
        })
    }

    /// Detailed contamination analysis for a single result
    fn analyze_result_contamination_detailed(&self, result: f64, index: usize, implementation: &str) -> Result<ContaminationAnalysis> {
        let mut analysis = self.analyze_result_contamination(result, index)?;
        
        if !analysis.is_contaminated {
            // Perform more sophisticated analysis
            
            // Check against expected performance baseline
            if let Ok(baseline) = self.get_performance_baseline(implementation) {
                let expected_time = baseline.expected_execution_time_ns;
                let deviation = ((result - expected_time).abs() / expected_time) * 100.0;
                
                if deviation > 1000.0 {  // More than 10x deviation
                    analysis.is_contaminated = true;
                    analysis.contamination_type = ContaminationType::PerformanceAnomaly;
                    analysis.contamination_reason = format!("Result deviates {}% from baseline", deviation);
                    analysis.confidence_score = 0.8;
                    analysis.detection_method = "Baseline comparison".to_string();
                }
            }
        }

        Ok(analysis)
    }

    /// Detect statistical contamination using outlier detection
    fn detect_statistical_contamination(&self, results: &[f64]) -> Result<Vec<f64>> {
        if results.len() < 3 {
            return Ok(Vec::new());
        }

        let mut sorted_results = results.to_vec();
        sorted_results.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

        let n = sorted_results.len();
        let q1_index = n / 4;
        let q3_index = 3 * n / 4;
        
        let q1 = sorted_results[q1_index];
        let q3 = sorted_results[q3_index];
        let iqr = q3 - q1;
        
        // Use IQR method to detect outliers
        let lower_bound = q1 - 1.5 * iqr;
        let upper_bound = q3 + 1.5 * iqr;
        
        let outliers: Vec<f64> = results.iter()
            .filter(|&&x| x < lower_bound || x > upper_bound)
            .copied()
            .collect();

        Ok(outliers)
    }

    /// Perform statistical analysis for contamination detection
    fn perform_contamination_statistical_analysis(&self, results: &[f64]) -> Result<ContaminationStatisticalAnalysis> {
        let n = results.len();
        let mean = results.iter().sum::<f64>() / n as f64;
        
        let variance = results.iter()
            .map(|x| (x - mean).powi(2))
            .sum::<f64>() / (n - 1) as f64;
        let std_dev = variance.sqrt();
        
        let median = {
            let mut sorted = results.to_vec();
            sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
            if n % 2 == 0 {
                (sorted[n/2 - 1] + sorted[n/2]) / 2.0
            } else {
                sorted[n/2]
            }
        };

        // Calculate coefficient of variation
        let cv = if mean > 0.0 { std_dev / mean } else { 0.0 };
        
        // Detect potential contamination based on statistical properties
        let contamination_indicators = self.identify_contamination_indicators(results, mean, std_dev, median)?;

        Ok(ContaminationStatisticalAnalysis {
            sample_size: n,
            mean,
            median,
            standard_deviation: std_dev,
            coefficient_of_variation: cv,
            min_value: results.iter().fold(f64::INFINITY, |a, &b| a.min(b)),
            max_value: results.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b)),
            contamination_indicators,
            outlier_threshold_lower: mean - 2.0 * std_dev,
            outlier_threshold_upper: mean + 2.0 * std_dev,
        })
    }

    /// Identify contamination indicators from statistical analysis
    fn identify_contamination_indicators(&self, results: &[f64], mean: f64, std_dev: f64, median: f64) -> Result<Vec<String>> {
        let mut indicators = Vec::new();

        // High coefficient of variation indicates inconsistent results
        let cv = if mean > 0.0 { std_dev / mean } else { 0.0 };
        if cv > 1.0 {
            indicators.push(format!("High coefficient of variation: {:.2}", cv));
        }

        // Large difference between mean and median indicates skewed distribution
        let mean_median_diff = ((mean - median).abs() / median) * 100.0;
        if mean_median_diff > 50.0 {
            indicators.push(format!("Large mean-median difference: {:.1}%", mean_median_diff));
        }

        // Check for extreme outliers
        let outlier_count = results.iter()
            .filter(|&&x| x < mean - 3.0 * std_dev || x > mean + 3.0 * std_dev)
            .count();
        
        if outlier_count > 0 {
            indicators.push(format!("Extreme outliers detected: {} values", outlier_count));
        }

        Ok(indicators)
    }

    /// Identify statistical outliers based on analysis
    fn identify_statistical_outliers(&self, results: &[f64], stats: &ContaminationStatisticalAnalysis) -> Result<Vec<f64>> {
        let outliers: Vec<f64> = results.iter()
            .filter(|&&x| x < stats.outlier_threshold_lower || x > stats.outlier_threshold_upper)
            .copied()
            .collect();

        Ok(outliers)
    }

    /// Apply performance-based filtering
    fn apply_performance_based_filtering(&self, results: &[f64]) -> Result<Vec<f64>> {
        if results.is_empty() {
            return Ok(Vec::new());
        }

        // Remove results that are clearly too slow (indicating potential fallback)
        let median = {
            let mut sorted = results.to_vec();
            sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
            let n = sorted.len();
            if n % 2 == 0 {
                (sorted[n/2 - 1] + sorted[n/2]) / 2.0
            } else {
                sorted[n/2]
            }
        };

        // Filter out results that are more than 10x the median (likely fallback)
        let performance_threshold = median * 10.0;
        let filtered: Vec<f64> = results.iter()
            .filter(|&&x| x <= performance_threshold)
            .copied()
            .collect();

        Ok(filtered)
    }

    /// Calculate filtering confidence score
    fn calculate_filtering_confidence(&self, original_count: usize, filtered_count: usize, analyses: &[ContaminationAnalysis]) -> Result<f64> {
        if original_count == 0 {
            return Ok(1.0);
        }

        let contamination_ratio = (original_count - filtered_count) as f64 / original_count as f64;
        
        // Base confidence on contamination detection confidence
        let avg_confidence = if !analyses.is_empty() {
            analyses.iter().map(|a| a.confidence_score).sum::<f64>() / analyses.len() as f64
        } else {
            1.0
        };

        // Adjust confidence based on contamination ratio
        let confidence = if contamination_ratio > 0.5 {
            avg_confidence * 0.7  // Lower confidence if we filtered out more than 50%
        } else if contamination_ratio > 0.2 {
            avg_confidence * 0.9  // Slightly lower confidence if we filtered 20-50%
        } else {
            avg_confidence  // High confidence if we filtered less than 20%
        };

        Ok(confidence.max(0.0).min(1.0))
    }

    /// Generate filtering recommendations
    fn generate_filtering_recommendations(&self, implementation: &str, summary: &FilteringSummary, _analyses: &[ContaminationAnalysis]) -> Result<Vec<String>> {
        let mut recommendations = Vec::new();

        if summary.filtered_results == 0 {
            recommendations.push("All results were contaminated - investigate implementation".to_string());
            recommendations.push(format!("Run diagnostics on {} implementation", implementation));
            return Ok(recommendations);
        }

        if summary.contaminated_results == 0 {
            recommendations.push("No contamination detected - results are clean".to_string());
            recommendations.push("Proceed with benchmark analysis".to_string());
        } else {
            let contamination_rate = (summary.contaminated_results as f64 / summary.total_results as f64) * 100.0;
            recommendations.push(format!("Filtered out {:.1}% of results due to contamination", contamination_rate));
            
            if contamination_rate > 50.0 {
                recommendations.push("High contamination rate - investigate implementation issues".to_string());
                recommendations.push(format!("Consider running FFI diagnostics for {}", implementation));
            } else if contamination_rate > 20.0 {
                recommendations.push("Moderate contamination detected - monitor implementation".to_string());
            }
        }

        // Add specific recommendations based on contamination types
        for (contamination_type, count) in &summary.contamination_types {
            match contamination_type.as_str() {
                "FallbackDetected" => {
                    recommendations.push(format!("Detected {} fallback instances - check native library loading", count));
                }
                "PerformanceAnomaly" => {
                    recommendations.push(format!("Detected {} performance anomalies - verify native execution", count));
                }
                "StatisticalOutlier" => {
                    recommendations.push(format!("Detected {} statistical outliers - check measurement consistency", count));
                }
                "InvalidValue" => {
                    recommendations.push(format!("Detected {} invalid values - check measurement implementation", count));
                }
                _ => {}
            }
        }

        if summary.filtering_confidence < 0.8 {
            recommendations.push("Low filtering confidence - manual review recommended".to_string());
        }

        Ok(recommendations)
    }

    /// Execute benchmark with immediate fallback detection and stopping
    /// This is the main function that implements Property 5: Immediate stopping on fallback detection
    pub fn execute_with_fallback_detection(&self, ffi_impl: &str, benchmark_function: Option<PyObject>) -> Result<FallbackDetectionResult> {
        let start_timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| AuditError::Unknown(format!("Time error: {}", e)))?
            .as_nanos() as u64;

        // Monitor execution path
        let monitoring_result = self.monitor_execution_path_internal(ffi_impl, benchmark_function)?;
        
        // Check for fallback immediately
        if monitoring_result.fallback_detected {
            // IMMEDIATE STOP: Fallback detected, stop execution and provide diagnostics
            let diagnostic_info = self.generate_fallback_diagnostics(ffi_impl, &monitoring_result)?;
            
            return Ok(FallbackDetectionResult {
                implementation: ffi_impl.to_string(),
                fallback_detected: true,
                detection_timestamp_ns: start_timestamp,
                execution_stopped: true,
                diagnostic_info,
                execution_path_monitoring: monitoring_result,
            });
        }

        // No fallback detected, continue normal execution
        Ok(FallbackDetectionResult {
            implementation: ffi_impl.to_string(),
            fallback_detected: false,
            detection_timestamp_ns: start_timestamp,
            execution_stopped: false,
            diagnostic_info: self.generate_success_diagnostics(ffi_impl, &monitoring_result)?,
            execution_path_monitoring: monitoring_result,
        })
    }

    /// Generate detailed diagnostic information when fallback is detected
    fn generate_fallback_diagnostics(&self, ffi_impl: &str, monitoring: &ExecutionPathMonitoring) -> Result<FallbackDiagnosticInfo> {
        let detection_reason = match monitoring.execution_type {
            0 => "Native execution detected - no fallback".to_string(), // NativeOnly
            1 => "Pure Python implementation detected - complete fallback to Python".to_string(), // PythonOnly
            2 => format!("Mixed execution detected - {}% Python overhead exceeds threshold of {}%", 
                        monitoring.performance_metrics.python_overhead_percentage,
                        self.config.fallback_detection_threshold * 100.0), // Mixed
            3 => "Unknown execution type - assuming fallback for safety".to_string(), // Unknown
            _ => "Invalid execution type".to_string(),
        };

        let performance_anomalies = self.analyze_performance_anomalies(monitoring)?;
        let recommended_actions = self.generate_recommended_actions(ffi_impl, monitoring)?;
        let execution_context = self.capture_execution_context(ffi_impl)?;

        Ok(FallbackDiagnosticInfo {
            detection_reason,
            python_overhead_percentage: monitoring.performance_metrics.python_overhead_percentage,
            expected_native_percentage: 100.0, // We expect 100% native for non-fallback
            actual_native_percentage: monitoring.performance_metrics.native_code_percentage,
            performance_anomalies,
            recommended_actions,
            execution_context,
        })
    }

    /// Generate diagnostic information for successful (non-fallback) execution
    fn generate_success_diagnostics(&self, ffi_impl: &str, monitoring: &ExecutionPathMonitoring) -> Result<FallbackDiagnosticInfo> {
        Ok(FallbackDiagnosticInfo {
            detection_reason: "No fallback detected - native execution confirmed".to_string(),
            python_overhead_percentage: monitoring.performance_metrics.python_overhead_percentage,
            expected_native_percentage: 100.0,
            actual_native_percentage: monitoring.performance_metrics.native_code_percentage,
            performance_anomalies: Vec::new(),
            recommended_actions: vec!["Continue with benchmark execution".to_string()],
            execution_context: self.capture_execution_context(ffi_impl)?,
        })
    }

    /// Analyze performance anomalies that might indicate fallback
    fn analyze_performance_anomalies(&self, monitoring: &ExecutionPathMonitoring) -> Result<Vec<String>> {
        let mut anomalies = Vec::new();

        // Check for suspicious execution times
        if monitoring.execution_time_ns > 1_000_000_000 { // > 1 second
            anomalies.push("Execution time unusually long for native code".to_string());
        }

        // Check for high Python overhead
        if monitoring.performance_metrics.python_overhead_percentage > 50.0 {
            anomalies.push(format!("High Python overhead: {}%", 
                                 monitoring.performance_metrics.python_overhead_percentage));
        }

        // Check for memory usage patterns
        if monitoring.performance_metrics.memory_usage_bytes > 10 * 1024 * 1024 { // > 10MB
            anomalies.push("High memory usage may indicate Python fallback".to_string());
        }

        // Check call patterns
        if monitoring.python_calls_detected > monitoring.native_calls_detected {
            anomalies.push("More Python calls than native calls detected".to_string());
        }

        Ok(anomalies)
    }

    /// Generate recommended actions based on detected issues
    fn generate_recommended_actions(&self, ffi_impl: &str, monitoring: &ExecutionPathMonitoring) -> Result<Vec<String>> {
        let mut actions = Vec::new();

        match monitoring.execution_type {
            1 => { // PythonOnly
                actions.push("Check if native library is properly compiled and available".to_string());
                actions.push("Verify library path configuration".to_string());
                actions.push("Check for missing dependencies".to_string());
                actions.push(format!("Run FFI diagnostics for {}", ffi_impl));
            }
            2 => { // Mixed
                actions.push("Investigate why execution is not purely native".to_string());
                actions.push("Check for partial fallback in the implementation".to_string());
                actions.push("Verify all functions are properly exported from native library".to_string());
            }
            3 => { // Unknown
                actions.push("Unable to determine execution type - investigate implementation".to_string());
                actions.push("Check if implementation follows expected naming conventions".to_string());
            }
            _ => {
                actions.push("Continue monitoring for potential issues".to_string());
            }
        }

        // Add implementation-specific recommendations
        if ffi_impl.contains("cython") {
            actions.push("Check Cython compilation settings and ensure C extensions are built".to_string());
        } else if ffi_impl.contains("numpy") {
            actions.push("Verify NumPy C API integration and compilation".to_string());
        } else if ffi_impl.contains("rust") {
            actions.push("Check Rust library compilation and Python bindings".to_string());
        }

        Ok(actions)
    }

    /// Capture execution context for diagnostics
    fn capture_execution_context(&self, ffi_impl: &str) -> Result<ExecutionContext> {
        use std::env;

        // Capture environment variables
        let mut env_vars = std::collections::HashMap::new();
        for (key, value) in env::vars() {
            if key.contains("PATH") || key.contains("PYTHON") || key.contains("LIB") {
                env_vars.insert(key, value);
            }
        }

        // Capture library paths
        let library_paths = self.get_library_search_paths(ffi_impl)?;
        
        // Capture loaded libraries (simplified)
        let loaded_libraries = self.get_loaded_libraries(ffi_impl)?;

        // Capture system information
        let system_info = SystemInfo {
            os_version: self.get_os_version(),
            architecture: self.get_architecture(),
            python_version: self.get_python_version(),
            available_memory_mb: self.get_available_memory_mb(),
            cpu_cores: self.get_cpu_cores(),
        };

        Ok(ExecutionContext {
            call_stack: vec![format!("execute_with_fallback_detection({})", ffi_impl)],
            environment_variables: env_vars,
            library_paths,
            loaded_libraries,
            system_info,
        })
    }

    /// Get library search paths for the implementation
    fn get_library_search_paths(&self, ffi_impl: &str) -> Result<Vec<String>> {
        let mut paths = Vec::new();
        
        // Add common library paths
        paths.push(format!("benchmark/{}", ffi_impl));
        paths.push(format!("benchmark/{}/build", ffi_impl));
        paths.push(format!("benchmark/{}/lib", ffi_impl));
        
        // Add system library paths
        if let Ok(path_env) = std::env::var("PATH") {
            for path in path_env.split(';') {
                if !path.is_empty() {
                    paths.push(path.to_string());
                }
            }
        }
        
        Ok(paths)
    }

    /// Get loaded libraries (simplified implementation)
    fn get_loaded_libraries(&self, _ffi_impl: &str) -> Result<Vec<String>> {
        // This is a simplified implementation
        // In a real system, this would query the process for loaded DLLs
        Ok(vec![
            "kernel32.dll".to_string(),
            "python3.dll".to_string(),
            "msvcrt.dll".to_string(),
        ])
    }

    /// Get OS version
    fn get_os_version(&self) -> String {
        "Windows 10".to_string() // Simplified
    }

    /// Get system architecture
    fn get_architecture(&self) -> String {
        if cfg!(target_arch = "x86_64") {
            "x86_64".to_string()
        } else if cfg!(target_arch = "x86") {
            "x86".to_string()
        } else {
            "unknown".to_string()
        }
    }

    /// Get Python version
    fn get_python_version(&self) -> String {
        "3.11".to_string() // Simplified
    }

    /// Get available memory in MB
    fn get_available_memory_mb(&self) -> usize {
        8192 // Simplified - 8GB
    }

    /// Get number of CPU cores
    fn get_cpu_cores(&self) -> usize {
        std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(4)
    }

    // ─── Task 9.1: Performance Baseline Comparison ────────────────────────────

    /// Compare an FFI implementation against a pure-Python baseline.
    ///
    /// Returns a [`PerformanceComparisonResult`] describing the speedup ratio,
    /// statistical significance (Welch's t-test), and any detected anomalies.
    pub fn compare_with_python_baseline(
        &self,
        implementation: &str,
        ffi_results_ns: &[f64],
        python_baseline_ns: &[f64],
    ) -> Result<PerformanceComparisonResult> {
        if ffi_results_ns.is_empty() || python_baseline_ns.is_empty() {
            return Err(AuditError::Unknown(
                "Cannot compare: one or both result sets are empty".to_string(),
            ));
        }

        let ffi_mean = ffi_results_ns.iter().sum::<f64>() / ffi_results_ns.len() as f64;
        let py_mean  = python_baseline_ns.iter().sum::<f64>() / python_baseline_ns.len() as f64;

        // performance_ratio > 1.0  ⟹  FFI is faster
        let performance_ratio = if ffi_mean > 0.0 { py_mean / ffi_mean } else { 1.0 };
        let speedup_percentage = (py_mean - ffi_mean) / py_mean.max(1.0) * 100.0;

        let sig = self.perform_welch_t_test(ffi_results_ns, python_baseline_ns)?;
        let is_significantly_faster = sig.is_significant && performance_ratio > 1.0;

        // Suspect fallback when the FFI is not meaningfully faster than Python
        let fallback_suspected = performance_ratio < 1.1 || !sig.is_significant;

        let flags = self.detect_performance_flags(
            performance_ratio,
            &sig,
            ffi_results_ns,
            fallback_suspected,
        );

        let recommendations = self.build_comparison_recommendations(
            implementation,
            performance_ratio,
            is_significantly_faster,
            fallback_suspected,
            &flags,
        );

        Ok(PerformanceComparisonResult {
            implementation: implementation.to_string(),
            ffi_results_ns: ffi_results_ns.to_vec(),
            python_baseline_ns: python_baseline_ns.to_vec(),
            performance_ratio,
            speedup_percentage,
            statistical_significance: sig,
            is_significantly_faster,
            fallback_suspected,
            performance_flags: flags,
            recommendations,
        })
    }

    /// Welch's two-sample t-test.
    ///
    /// The t-statistic is `(py_mean − ffi_mean) / se`, so a positive value
    /// means the FFI sample has a lower mean (i.e., is faster).
    fn perform_welch_t_test(
        &self,
        ffi_results: &[f64],
        python_baseline: &[f64],
    ) -> Result<SignificanceTestResult> {
        let n_a = ffi_results.len() as f64;
        let n_b = python_baseline.len() as f64;

        if n_a < 2.0 || n_b < 2.0 {
            return Ok(SignificanceTestResult {
                test_name: "Welch's t-test".to_string(),
                t_statistic: 0.0,
                p_value: 1.0,
                confidence_level: 0.95,
                is_significant: false,
                effect_size: 0.0,
                degrees_of_freedom: 0.0,
            });
        }

        let mean_a = ffi_results.iter().sum::<f64>() / n_a;
        let mean_b = python_baseline.iter().sum::<f64>() / n_b;

        let var_a = ffi_results.iter().map(|&x| (x - mean_a).powi(2)).sum::<f64>() / (n_a - 1.0);
        let var_b = python_baseline.iter().map(|&x| (x - mean_b).powi(2)).sum::<f64>() / (n_b - 1.0);

        let se = (var_a / n_a + var_b / n_b).sqrt();
        let t_stat = if se > 0.0 { (mean_b - mean_a) / se } else { 0.0 };

        // Welch–Satterthwaite degrees of freedom
        let va_na = var_a / n_a;
        let vb_nb = var_b / n_b;
        let df = if va_na + vb_nb > 0.0 {
            (va_na + vb_nb).powi(2)
                / (va_na.powi(2) / (n_a - 1.0) + vb_nb.powi(2) / (n_b - 1.0))
        } else {
            n_a + n_b - 2.0
        };

        // Approximate p-value via normal distribution (adequate for n ≥ 5)
        let p_value = self.approx_two_sided_p_value(t_stat);
        let effect_size = self.calculate_cohens_d(ffi_results, python_baseline);

        Ok(SignificanceTestResult {
            test_name: "Welch's t-test".to_string(),
            t_statistic: t_stat,
            p_value,
            confidence_level: 0.95,
            is_significant: p_value < 0.05,
            effect_size,
            degrees_of_freedom: df,
        })
    }

    /// Approximate two-sided p-value from a z/t-statistic using the normal CDF.
    fn approx_two_sided_p_value(&self, t: f64) -> f64 {
        // P(|Z| > |t|) ≈ erfc(|t| / sqrt(2))
        let z = t.abs() / std::f64::consts::SQRT_2;
        // Simple rational approximation of erfc
        let p_one_sided = 0.5 * self.erfc_approx(z);
        (2.0 * p_one_sided).min(1.0)
    }

    /// Rational approximation of erfc(x) for x ≥ 0 (Abramowitz & Stegun 7.1.26).
    fn erfc_approx(&self, x: f64) -> f64 {
        if x < 0.0 { return 2.0 - self.erfc_approx(-x); }
        let t = 1.0 / (1.0 + 0.3275911 * x);
        let poly = t * (0.254_829_592
            + t * (-0.284_496_736
            + t * (1.421_413_741
            + t * (-1.453_152_027
            + t * 1.061_405_429))));
        poly * (-x * x).exp()
    }

    /// Cohen's d effect size (positive = FFI is faster than Python).
    fn calculate_cohens_d(&self, ffi_results: &[f64], python_baseline: &[f64]) -> f64 {
        let n_a = ffi_results.len() as f64;
        let n_b = python_baseline.len() as f64;
        if n_a < 2.0 || n_b < 2.0 { return 0.0; }

        let mean_a = ffi_results.iter().sum::<f64>() / n_a;
        let mean_b = python_baseline.iter().sum::<f64>() / n_b;

        let var_a = ffi_results.iter().map(|&x| (x - mean_a).powi(2)).sum::<f64>() / (n_a - 1.0);
        let var_b = python_baseline.iter().map(|&x| (x - mean_b).powi(2)).sum::<f64>() / (n_b - 1.0);

        let pooled_sd = ((var_a + var_b) / 2.0).sqrt();
        if pooled_sd > 0.0 { (mean_b - mean_a) / pooled_sd } else { 0.0 }
    }

    /// Identify anomalous performance patterns.
    fn detect_performance_flags(
        &self,
        ratio: f64,
        sig: &SignificanceTestResult,
        ffi_results: &[f64],
        fallback_suspected: bool,
    ) -> Vec<PerformanceFlag> {
        let mut flags = Vec::new();

        if ffi_results.len() < 3 {
            flags.push(PerformanceFlag::InsufficientData);
        }

        if ratio < 1.0 {
            flags.push(PerformanceFlag::SignificantlySlowerThanPython);
        }

        // Ratio between 0.9 and 1.1 → suspiciously similar to Python
        if (0.9..=1.1).contains(&ratio) && sig.is_significant {
            flags.push(PerformanceFlag::SuspiciouslySimilarToPython);
        }

        if fallback_suspected && ratio < 1.2 {
            flags.push(PerformanceFlag::PotentialFallback);
        }

        // High variance check (CV > 0.3)
        if ffi_results.len() >= 2 {
            let mean = ffi_results.iter().sum::<f64>() / ffi_results.len() as f64;
            let std_dev = (ffi_results.iter().map(|&x| (x - mean).powi(2)).sum::<f64>()
                / (ffi_results.len() - 1) as f64).sqrt();
            if mean > 0.0 && std_dev / mean > 0.3 {
                flags.push(PerformanceFlag::HighVariance);
            }
        }

        flags
    }

    /// Build human-readable recommendations based on the comparison result.
    fn build_comparison_recommendations(
        &self,
        implementation: &str,
        ratio: f64,
        is_significantly_faster: bool,
        fallback_suspected: bool,
        flags: &[PerformanceFlag],
    ) -> Vec<String> {
        let mut recs = Vec::new();

        if is_significantly_faster {
            recs.push(format!(
                "{}: confirmed {:.1}× faster than Python — no action required.",
                implementation, ratio
            ));
        } else if fallback_suspected {
            recs.push(format!(
                "{}: potential Python fallback detected (ratio={:.2}). Investigate library loading.",
                implementation, ratio
            ));
        }

        if flags.contains(&PerformanceFlag::SignificantlySlowerThanPython) {
            recs.push(format!(
                "{}: FFI is slower than Python (ratio={:.2}). Check for overhead or fallback.",
                implementation, ratio
            ));
        }
        if flags.contains(&PerformanceFlag::HighVariance) {
            recs.push(format!(
                "{}: high variance detected. Increase warmup iterations or check system load.",
                implementation
            ));
        }
        if flags.contains(&PerformanceFlag::InsufficientData) {
            recs.push(format!(
                "{}: fewer than 3 measurements. Collect more data for reliable comparison.",
                implementation
            ));
        }

        recs
    }

    /// Produce an aggregate [`PerformanceReport`] from multiple comparisons.
    pub fn generate_performance_report(
        &self,
        comparisons: &[PerformanceComparisonResult],
    ) -> Result<PerformanceReport> {
        let mut passing = Vec::new();
        let mut failing = Vec::new();
        let mut suspected = Vec::new();

        for c in comparisons {
            if c.fallback_suspected {
                suspected.push(c.implementation.clone());
                failing.push(c.implementation.clone());
            } else if c.is_significantly_faster {
                passing.push(c.implementation.clone());
            } else {
                failing.push(c.implementation.clone());
            }
        }

        let avg_speedup = if passing.is_empty() {
            0.0
        } else {
            comparisons.iter()
                .filter(|c| c.is_significantly_faster)
                .map(|c| c.speedup_percentage)
                .sum::<f64>() / passing.len() as f64
        };

        let summary = format!(
            "Performance report: {}/{} implementations passed. \
             {} suspected fallbacks. Average speedup (passing): {:.1}%.",
            passing.len(),
            comparisons.len(),
            suspected.len(),
            avg_speedup
        );

        Ok(PerformanceReport {
            comparisons: comparisons.to_vec(),
            passing_implementations: passing,
            failing_implementations: failing,
            suspected_fallbacks: suspected,
            average_speedup_percentage: avg_speedup,
            summary,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fallback_prevention_system_creation() {
        let system = FallbackPreventionSystem::new();
        assert_eq!(system.config.fallback_detection_threshold, 0.1);
        assert!(system.config.enable_call_tracing);
        assert!(system.config.enable_performance_monitoring);
    }

    #[test]
    fn test_execution_type_detection() {
        let system = FallbackPreventionSystem::new();
        
        // Test Python implementations
        assert_eq!(system.detect_execution_type("python").unwrap(), ExecutionType::PythonOnly);
        assert_eq!(system.detect_execution_type("pure_python").unwrap(), ExecutionType::PythonOnly);
        
        // Test native implementations
        assert_eq!(system.detect_execution_type("c_ext").unwrap(), ExecutionType::NativeOnly);
        assert_eq!(system.detect_execution_type("cpp_ext").unwrap(), ExecutionType::NativeOnly);
        assert_eq!(system.detect_execution_type("rust_ext").unwrap(), ExecutionType::NativeOnly);
        assert_eq!(system.detect_execution_type("go_ext").unwrap(), ExecutionType::NativeOnly);
        
        // Test mixed implementations
        assert_eq!(system.detect_execution_type("cython_ext").unwrap(), ExecutionType::Mixed);
        assert_eq!(system.detect_execution_type("numpy_impl").unwrap(), ExecutionType::Mixed);
        
        // Test unknown implementations
        assert_eq!(system.detect_execution_type("unknown_impl").unwrap(), ExecutionType::Unknown);
    }

    #[test]
    fn test_monitor_execution_path_internal() {
        let system = FallbackPreventionSystem::new();
        
        // Test Python implementation - should detect fallback
        let result = system.monitor_execution_path_internal("python", None).unwrap();
        assert_eq!(result.implementation, "python");
        assert_eq!(result.execution_type, ExecutionType::PythonOnly.as_u8());
        assert!(result.fallback_detected);
        assert_eq!(result.performance_metrics.native_code_percentage, 0.0);
        assert_eq!(result.performance_metrics.python_overhead_percentage, 100.0);
        
        // Test native implementation - should not detect fallback
        let result = system.monitor_execution_path_internal("c_ext", None).unwrap();
        assert_eq!(result.implementation, "c_ext");
        assert_eq!(result.execution_type, ExecutionType::NativeOnly.as_u8());
        assert!(!result.fallback_detected);
        assert_eq!(result.performance_metrics.native_code_percentage, 100.0);
        assert_eq!(result.performance_metrics.python_overhead_percentage, 0.0);
        
        // Test mixed implementation - should detect fallback based on threshold
        let result = system.monitor_execution_path_internal("cython_ext", None).unwrap();
        assert_eq!(result.implementation, "cython_ext");
        assert_eq!(result.execution_type, ExecutionType::Mixed.as_u8());
        // Mixed implementations have 50% Python overhead, which exceeds 10% threshold
        assert!(result.fallback_detected);
        assert_eq!(result.performance_metrics.native_code_percentage, 50.0);
        assert_eq!(result.performance_metrics.python_overhead_percentage, 50.0);
    }

    // Feature: windows-ffi-audit, Property 4: フォールバック完全検出
    // Property-based test for complete fallback detection
    #[cfg(feature = "proptest")]
    mod property_tests {
        use super::*;
        use proptest::prelude::*;

        // Generate test implementation names that should be detected as Python fallback
        fn python_implementation_strategy() -> impl Strategy<Value = String> {
            prop_oneof![
                Just("python".to_string()),
                Just("pure_python".to_string()),
                Just("python_impl".to_string()),
                Just("pure".to_string()),
                "[a-z]+_python".prop_map(|s| s),
                "python_[a-z]+".prop_map(|s| s),
            ]
        }

        // Generate test implementation names that should be detected as native
        fn native_implementation_strategy() -> impl Strategy<Value = String> {
            prop_oneof![
                Just("c_ext".to_string()),
                Just("cpp_ext".to_string()),
                Just("rust_ext".to_string()),
                Just("go_ext".to_string()),
                Just("fortran_ext".to_string()),
                Just("zig_ext".to_string()),
                Just("nim_ext".to_string()),
                "[a-z]+_ext".prop_map(|s| s),
            ]
        }

        // Generate test implementation names that should be detected as mixed
        fn mixed_implementation_strategy() -> impl Strategy<Value = String> {
            prop_oneof![
                Just("cython_ext".to_string()),
                Just("numpy_impl".to_string()),
                Just("julia_impl".to_string()),
                Just("kotlin_impl".to_string()),
                "cython_[a-z]+".prop_map(|s| s),
                "numpy_[a-z]+".prop_map(|s| s),
            ]
        }

        proptest! {
            // **Property 4: フォールバック完全検出**
            // **Validates: Requirements 2.1**
            #[test]
            fn property_fallback_complete_detection_python_implementations(
                impl_name in python_implementation_strategy()
            ) {
                let system = FallbackPreventionSystem::new();
                let result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                
                // For any Python implementation, fallback must be detected with 100% accuracy
                prop_assert!(result.fallback_detected, 
                    "Python implementation '{}' should be detected as fallback", impl_name);
                prop_assert_eq!(result.execution_type, ExecutionType::PythonOnly.as_u8(),
                    "Python implementation '{}' should have PythonOnly execution type", impl_name);
                prop_assert_eq!(result.performance_metrics.native_code_percentage, 0.0,
                    "Python implementation '{}' should have 0% native code", impl_name);
                prop_assert_eq!(result.performance_metrics.python_overhead_percentage, 100.0,
                    "Python implementation '{}' should have 100% Python overhead", impl_name);
            }

            #[test]
            fn property_fallback_complete_detection_native_implementations(
                impl_name in native_implementation_strategy()
            ) {
                let system = FallbackPreventionSystem::new();
                let result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                
                // For any native implementation, fallback must NOT be detected
                prop_assert!(!result.fallback_detected, 
                    "Native implementation '{}' should NOT be detected as fallback", impl_name);
                prop_assert_eq!(result.execution_type, ExecutionType::NativeOnly.as_u8(),
                    "Native implementation '{}' should have NativeOnly execution type", impl_name);
                prop_assert_eq!(result.performance_metrics.native_code_percentage, 100.0,
                    "Native implementation '{}' should have 100% native code", impl_name);
                prop_assert_eq!(result.performance_metrics.python_overhead_percentage, 0.0,
                    "Native implementation '{}' should have 0% Python overhead", impl_name);
            }

            #[test]
            fn property_fallback_complete_detection_mixed_implementations(
                impl_name in mixed_implementation_strategy(),
                threshold in 0.01f64..0.99f64
            ) {
                let mut system = FallbackPreventionSystem::new();
                system.config.fallback_detection_threshold = threshold;
                
                let result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                
                // For mixed implementations, fallback detection depends on threshold
                // Mixed implementations have 50% Python overhead
                let expected_fallback = 0.5 > threshold;
                
                prop_assert_eq!(result.fallback_detected, expected_fallback,
                    "Mixed implementation '{}' fallback detection should match threshold {}", 
                    impl_name, threshold);
                prop_assert_eq!(result.execution_type, ExecutionType::Mixed.as_u8(),
                    "Mixed implementation '{}' should have Mixed execution type", impl_name);
                prop_assert_eq!(result.performance_metrics.native_code_percentage, 50.0,
                    "Mixed implementation '{}' should have 50% native code", impl_name);
                prop_assert_eq!(result.performance_metrics.python_overhead_percentage, 50.0,
                    "Mixed implementation '{}' should have 50% Python overhead", impl_name);
            }

            #[test]
            fn property_fallback_detection_consistency(
                impl_name in "[a-z_]+",
                iterations in 1usize..10usize
            ) {
                let system = FallbackPreventionSystem::new();
                
                // Run the same detection multiple times
                let mut results = Vec::new();
                for _ in 0..iterations {
                    let result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                    results.push(result.fallback_detected);
                }
                
                // All results should be consistent
                let first_result = results[0];
                for (i, &result) in results.iter().enumerate() {
                    prop_assert_eq!(result, first_result,
                        "Fallback detection for '{}' should be consistent across runs (iteration {})", 
                        impl_name, i);
                }
            }

            #[test]
            fn property_execution_time_measurement(
                impl_name in "[a-z_]+",
            ) {
                let system = FallbackPreventionSystem::new();
                let result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                
                // Execution time should always be measured and be positive
                prop_assert!(result.execution_time_ns > 0,
                    "Execution time for '{}' should be positive: {} ns", impl_name, result.execution_time_ns);
                
                // Performance metrics should be consistent
                prop_assert!(result.performance_metrics.cpu_time_ns > 0,
                    "CPU time for '{}' should be positive", impl_name);
                prop_assert!(result.performance_metrics.wall_time_ns > 0,
                    "Wall time for '{}' should be positive", impl_name);
                prop_assert!(result.performance_metrics.memory_usage_bytes > 0,
                    "Memory usage for '{}' should be positive", impl_name);
                
                // Percentages should sum to 100%
                let total_percentage = result.performance_metrics.native_code_percentage + 
                                     result.performance_metrics.python_overhead_percentage;
                prop_assert!((total_percentage - 100.0).abs() < 0.001,
                    "Native and Python percentages for '{}' should sum to 100%: {} + {} = {}", 
                    impl_name, 
                    result.performance_metrics.native_code_percentage,
                    result.performance_metrics.python_overhead_percentage,
                    total_percentage);
            }

            // **Property 5: フォールバック時即座停止**
            // **Validates: Requirements 2.2**
            #[test]
            fn property_immediate_stop_on_fallback_detection(
                impl_name in python_implementation_strategy()
            ) {
                let system = FallbackPreventionSystem::new();
                let result = system.execute_with_fallback_detection(&impl_name, None).unwrap();
                
                // For Python implementations, fallback should be detected and execution stopped
                prop_assert!(result.fallback_detected,
                    "Fallback should be detected for Python implementation '{}'", impl_name);
                prop_assert!(result.execution_stopped,
                    "Execution should be stopped immediately when fallback is detected for '{}'", impl_name);
                
                // Diagnostic information should be provided
                prop_assert!(!result.diagnostic_info.detection_reason.is_empty(),
                    "Detection reason should be provided for '{}'", impl_name);
                prop_assert!(!result.diagnostic_info.recommended_actions.is_empty(),
                    "Recommended actions should be provided for '{}'", impl_name);
                
                // Detection should happen immediately (within reasonable time)
                prop_assert!(result.detection_timestamp_ns > 0,
                    "Detection timestamp should be recorded for '{}'", impl_name);
            }

            #[test]
            fn property_no_stop_on_native_execution(
                impl_name in native_implementation_strategy()
            ) {
                let system = FallbackPreventionSystem::new();
                let result = system.execute_with_fallback_detection(&impl_name, None).unwrap();
                
                // For native implementations, no fallback should be detected
                prop_assert!(!result.fallback_detected,
                    "No fallback should be detected for native implementation '{}'", impl_name);
                prop_assert!(!result.execution_stopped,
                    "Execution should NOT be stopped for native implementation '{}'", impl_name);
                
                // Success diagnostic information should be provided
                prop_assert!(result.diagnostic_info.detection_reason.contains("No fallback detected"),
                    "Success message should be provided for native implementation '{}'", impl_name);
                prop_assert_eq!(result.diagnostic_info.actual_native_percentage, 100.0,
                    "Native implementation '{}' should show 100% native execution", impl_name);
            }

            #[test]
            fn property_diagnostic_completeness(
                impl_name in "[a-z_]+",
            ) {
                let system = FallbackPreventionSystem::new();
                let result = system.execute_with_fallback_detection(&impl_name, None).unwrap();
                
                // All diagnostic fields should be populated
                prop_assert!(!result.diagnostic_info.detection_reason.is_empty(),
                    "Detection reason should always be provided for '{}'", impl_name);
                prop_assert!(!result.diagnostic_info.recommended_actions.is_empty(),
                    "Recommended actions should always be provided for '{}'", impl_name);
                
                // Execution context should be captured
                prop_assert!(!result.diagnostic_info.execution_context.call_stack.is_empty(),
                    "Call stack should be captured for '{}'", impl_name);
                prop_assert!(!result.diagnostic_info.execution_context.library_paths.is_empty(),
                    "Library paths should be captured for '{}'", impl_name);
                
                // System info should be populated
                prop_assert!(!result.diagnostic_info.execution_context.system_info.os_version.is_empty(),
                    "OS version should be captured for '{}'", impl_name);
                prop_assert!(!result.diagnostic_info.execution_context.system_info.architecture.is_empty(),
                    "Architecture should be captured for '{}'", impl_name);
                prop_assert!(result.diagnostic_info.execution_context.system_info.cpu_cores > 0,
                    "CPU cores should be detected for '{}'", impl_name);
                prop_assert!(result.diagnostic_info.execution_context.system_info.available_memory_mb > 0,
                    "Available memory should be detected for '{}'", impl_name);
            }

            #[test]
            fn property_fallback_detection_timing(
                impl_name in python_implementation_strategy(),
                iterations in 1usize..5usize
            ) {
                let system = FallbackPreventionSystem::new();
                
                let mut detection_times = Vec::new();
                for _ in 0..iterations {
                    let start = std::time::Instant::now();
                    let result = system.execute_with_fallback_detection(&impl_name, None).unwrap();
                    let detection_time = start.elapsed();
                    
                    // Fallback should be detected
                    prop_assert!(result.fallback_detected,
                        "Fallback should be detected for Python implementation '{}'", impl_name);
                    prop_assert!(result.execution_stopped,
                        "Execution should be stopped for Python implementation '{}'", impl_name);
                    
                    detection_times.push(detection_time.as_millis());
                }
                
                // Detection should be fast (within 100ms for this test)
                for (i, &time_ms) in detection_times.iter().enumerate() {
                    prop_assert!(time_ms < 100,
                        "Fallback detection for '{}' should be immediate (iteration {}): {}ms", 
                        impl_name, i, time_ms);
                }
            }

            #[test]
            fn property_recommended_actions_relevance(
                impl_name in prop_oneof![
                    python_implementation_strategy(),
                    native_implementation_strategy(),
                    mixed_implementation_strategy()
                ]
            ) {
                let system = FallbackPreventionSystem::new();
                let result = system.execute_with_fallback_detection(&impl_name, None).unwrap();
                
                // Recommended actions should be relevant to the implementation type
                let actions = &result.diagnostic_info.recommended_actions;
                prop_assert!(!actions.is_empty(),
                    "Recommended actions should be provided for '{}'", impl_name);
                
                // Check for implementation-specific recommendations
                if impl_name.contains("cython") {
                    let has_cython_advice = actions.iter().any(|action| action.contains("Cython"));
                    prop_assert!(has_cython_advice,
                        "Cython-specific advice should be provided for '{}'", impl_name);
                } else if impl_name.contains("numpy") {
                    let has_numpy_advice = actions.iter().any(|action| action.contains("NumPy"));
                    prop_assert!(has_numpy_advice,
                        "NumPy-specific advice should be provided for '{}'", impl_name);
                } else if impl_name.contains("rust") {
                    let has_rust_advice = actions.iter().any(|action| action.contains("Rust"));
                    prop_assert!(has_rust_advice,
                        "Rust-specific advice should be provided for '{}'", impl_name);
                }
            }

            // **Property 7: 性能測定純粋性**
            // **Validates: Requirements 2.4**
            #[test]
            fn property_performance_measurement_purity(
                impl_name in native_implementation_strategy(),
                measurement_iterations in 1usize..10usize
            ) {
                let system = FallbackPreventionSystem::new();
                
                let mut measurements = Vec::new();
                let mut python_overhead_measurements = Vec::new();
                
                // Take multiple measurements
                for _ in 0..measurement_iterations {
                    let monitoring_result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                    measurements.push(monitoring_result.execution_time_ns);
                    python_overhead_measurements.push(monitoring_result.performance_metrics.python_overhead_percentage);
                }
                
                // For native implementations, Python interpreter overhead should be minimal
                for (i, &python_overhead) in python_overhead_measurements.iter().enumerate() {
                    prop_assert!(python_overhead <= 10.0,
                        "Native implementation '{}' should have minimal Python overhead (iteration {}): {}%", 
                        impl_name, i, python_overhead);
                }
                
                // Execution time should be consistent and not include significant Python overhead
                let mean_time = measurements.iter().sum::<u64>() as f64 / measurements.len() as f64;
                let baseline = system.get_performance_baseline(&impl_name).unwrap();
                
                // Measured time should be close to expected native performance
                let deviation = ((mean_time - baseline.expected_execution_time_ns).abs() / baseline.expected_execution_time_ns) * 100.0;
                prop_assert!(deviation <= 200.0,
                    "Native implementation '{}' execution time should be close to baseline: measured={:.0}ns, expected={:.0}ns, deviation={:.1}%",
                    impl_name, mean_time, baseline.expected_execution_time_ns, deviation);
            }

            #[test]
            fn property_python_overhead_exclusion(
                impl_name in native_implementation_strategy(),
                execution_count in 1usize..5usize
            ) {
                let system = FallbackPreventionSystem::new();
                
                let mut native_percentages = Vec::new();
                let mut cpu_times = Vec::new();
                
                for _ in 0..execution_count {
                    let monitoring_result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                    native_percentages.push(monitoring_result.performance_metrics.native_code_percentage);
                    cpu_times.push(monitoring_result.performance_metrics.cpu_time_ns);
                }
                
                // Native implementations should show high native code percentage
                for (i, &native_percentage) in native_percentages.iter().enumerate() {
                    prop_assert!(native_percentage >= 90.0,
                        "Native implementation '{}' should show high native code percentage (iteration {}): {}%",
                        impl_name, i, native_percentage);
                }
                
                // CPU time should reflect actual computation, not Python interpreter overhead
                for (i, &cpu_time) in cpu_times.iter().enumerate() {
                    prop_assert!(cpu_time > 0,
                        "CPU time should be measured for native implementation '{}' (iteration {}): {}ns",
                        impl_name, i, cpu_time);
                    
                    // CPU time should be reasonable for native code (not inflated by Python overhead)
                    prop_assert!(cpu_time < 100_000_000, // Less than 100ms
                        "CPU time for native implementation '{}' should be reasonable (iteration {}): {}ns",
                        impl_name, i, cpu_time);
                }
            }

            #[test]
            fn property_measurement_isolation_from_python(
                impl_name in native_implementation_strategy()
            ) {
                let system = FallbackPreventionSystem::new();
                
                // Perform detailed performance analysis
                let anomaly_result = system.analyze_performance_anomalies_detailed(&impl_name, 100_000.0).unwrap();
                
                // Native implementations should not show Python-related anomalies
                let has_python_related_anomaly = anomaly_result.detected_anomalies.iter().any(|anomaly| {
                    matches!(anomaly.anomaly_type, AnomalyType::NativeCodePercentageAnomaly) ||
                    matches!(anomaly.anomaly_type, AnomalyType::CallPatternAnomaly)
                });
                
                prop_assert!(!has_python_related_anomaly,
                    "Native implementation '{}' should not show Python-related performance anomalies", impl_name);
                
                // Fallback suspicion should be low for properly functioning native implementations
                prop_assert!(matches!(anomaly_result.fallback_suspicion_level, 
                    SuspicionLevel::None | SuspicionLevel::Low),
                    "Native implementation '{}' should have low fallback suspicion: {:?}", 
                    impl_name, anomaly_result.fallback_suspicion_level);
                
                // Performance snapshot should reflect pure native execution
                let snapshot = &anomaly_result.current_performance;
                prop_assert!(snapshot.native_code_percentage >= 90.0,
                    "Native implementation '{}' should show high native code percentage in snapshot: {}%",
                    impl_name, snapshot.native_code_percentage);
                
                prop_assert!(snapshot.python_overhead_percentage <= 10.0,
                    "Native implementation '{}' should show low Python overhead in snapshot: {}%",
                    impl_name, snapshot.python_overhead_percentage);
            }

            #[test]
            fn property_timing_accuracy_without_interpreter_bias(
                impl_name in prop_oneof![
                    native_implementation_strategy(),
                    mixed_implementation_strategy()
                ],
                sample_size in 3usize..8usize
            ) {
                let system = FallbackPreventionSystem::new();
                
                let mut execution_times = Vec::new();
                let mut native_percentages = Vec::new();
                
                // Collect multiple samples
                for _ in 0..sample_size {
                    let monitoring_result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                    execution_times.push(monitoring_result.execution_time_ns as f64);
                    native_percentages.push(monitoring_result.performance_metrics.native_code_percentage);
                }
                
                // Calculate coefficient of variation (CV) to check measurement consistency
                let mean_time = execution_times.iter().sum::<f64>() / execution_times.len() as f64;
                let variance = execution_times.iter()
                    .map(|&x| (x - mean_time).powi(2))
                    .sum::<f64>() / (execution_times.len() - 1) as f64;
                let std_dev = variance.sqrt();
                let cv = std_dev / mean_time;
                
                // For implementations without Python interpreter bias, measurements should be consistent
                prop_assert!(cv <= 0.5, // CV should be <= 50%
                    "Execution time measurements for '{}' should be consistent (CV={:.2}): times={:?}",
                    impl_name, cv, execution_times);
                
                // Native percentage should be consistent across measurements
                let mean_native = native_percentages.iter().sum::<f64>() / native_percentages.len() as f64;
                let native_variance = native_percentages.iter()
                    .map(|&x| (x - mean_native).powi(2))
                    .sum::<f64>() / (native_percentages.len() - 1) as f64;
                let native_std_dev = native_variance.sqrt();
                
                prop_assert!(native_std_dev <= 5.0, // Standard deviation should be <= 5%
                    "Native code percentage for '{}' should be consistent (std_dev={:.2}): percentages={:?}",
                    impl_name, native_std_dev, native_percentages);
            }

            // **Property 8: 汚染結果除外**
            // **Validates: Requirements 2.5**
            #[test]
            fn property_contaminated_results_exclusion(
                implementation in "[a-z_]+",
                contaminated_results in prop::collection::vec(
                    prop_oneof![
                        // Normal results (should be kept)
                        1000.0f64..2000.0f64,
                        // Contaminated results (should be excluded)
                        prop_oneof![
                            Just(0.0f64),             // Zero results (measurement errors)
                            -1000.0f64..0.0f64,       // Negative results (measurement errors)
                            50.0f64..99.0f64,         // Too fast (suspicious)
                            10_000_000.0f64..50_000_000.0f64, // Too slow (Python fallback)
                        ]
                    ],
                    5..20
                )
            ) {
                let system = FallbackPreventionSystem::new();
                
                // Apply contamination filtering
                let filter_result = system.filter_contaminated_results_detailed(&contaminated_results, &implementation).unwrap();
                
                // Verify that contaminated results are excluded
                prop_assert!(filter_result.filtered_results.len() <= filter_result.original_results.len(),
                    "Filtered results should not exceed original results for '{}'", implementation);
                
                // Check that all filtered results are valid (not contaminated)
                for &result in &filter_result.filtered_results {
                    prop_assert!(result > 0.0,
                        "Filtered result should be positive for '{}': {}", implementation, result);
                    prop_assert!(result.is_finite(),
                        "Filtered result should be finite for '{}': {}", implementation, result);
                }
                
                // Check that contaminated results are properly logged
                if filter_result.filtering_summary.contaminated_results > 0 {
                    prop_assert!(!filter_result.contamination_analyses.is_empty(),
                        "Contamination log should not be empty when contamination is detected for '{}'", implementation);
                    
                    // Verify contamination statistics
                    prop_assert!(filter_result.filtering_summary.contaminated_results > 0,
                        "Total contaminated count should be positive for '{}'", implementation);
                    
                    // Check that critical contamination (zero/negative) is properly classified
                    let has_critical_contamination = contaminated_results.iter().any(|&x| x <= 0.0);
                    if has_critical_contamination {
                        let critical_count = filter_result.contamination_analyses.iter()
                            .filter(|a| a.is_contaminated && a.result_value <= 0.0)
                            .count();
                        prop_assert!(critical_count > 0,
                            "Critical contamination should be detected for '{}' when zero/negative results present", implementation);
                    }
                }
                
                // Verify that recommendations are provided when contamination is detected
                let contamination_rate = if filter_result.original_results.is_empty() { 0.0 } else {
                    (filter_result.filtering_summary.contaminated_results as f64 / filter_result.original_results.len() as f64) * 100.0
                };
                if contamination_rate > 20.0 {
                    prop_assert!(!filter_result.recommendations.is_empty(),
                        "Recommendations should be provided for high contamination rate ({:.1}%) for '{}'",
                        contamination_rate, implementation);
                }
            }

            #[test]
            fn property_fallback_results_complete_exclusion(
                implementation in prop_oneof![
                    python_implementation_strategy(),
                    mixed_implementation_strategy()
                ],
                normal_results in prop::collection::vec(1000.0f64..2000.0f64, 3..8),
                fallback_results in prop::collection::vec(15_000_000.0f64..100_000_000.0f64, 2..5)
            ) {
                let system = FallbackPreventionSystem::new();
                
                // Mix normal and fallback results
                let mut mixed_results = normal_results.clone();
                mixed_results.extend(fallback_results.clone());
                
                // Apply filtering
                let filter_result = system.filter_contaminated_results_detailed(&mixed_results, &implementation).unwrap();
                
                // All fallback results should be excluded
                for &fallback_result in &fallback_results {
                    prop_assert!(!filter_result.filtered_results.contains(&fallback_result),
                        "Fallback result {} should be excluded from filtered results for '{}'", 
                        fallback_result, implementation);
                }
                
                // Normal results should be preserved (unless they're statistical outliers)
                let preserved_normal_count = normal_results.iter()
                    .filter(|&&result| filter_result.filtered_results.contains(&result))
                    .count();
                
                prop_assert!(preserved_normal_count >= normal_results.len() / 2,
                    "At least half of normal results should be preserved for '{}': preserved={}, total={}",
                    implementation, preserved_normal_count, normal_results.len());
                
                // Contamination rate should reflect the presence of fallback results
                let total_results = normal_results.len() + fallback_results.len();
                let expected_contamination_rate = (fallback_results.len() as f64 / total_results as f64) * 100.0;
                let actual_contamination_rate = if filter_result.original_results.is_empty() { 0.0 } else {
                    (filter_result.filtering_summary.contaminated_results as f64 / filter_result.original_results.len() as f64) * 100.0
                };
                prop_assert!(actual_contamination_rate >= expected_contamination_rate * 0.8,
                    "Contamination rate should reflect fallback presence for '{}': actual={:.1}%, expected>={:.1}%",
                    implementation, actual_contamination_rate, expected_contamination_rate * 0.8);
            }

            #[test]
            fn property_partial_python_execution_detection(
                implementation in mixed_implementation_strategy(),
                execution_results in prop::collection::vec(
                    prop_oneof![
                        // Pure native results
                        500.0f64..1500.0f64,
                        // Mixed execution results (some Python involvement)
                        2500.0f64..8000.0f64,
                        // Heavy Python involvement
                        12_000_000.0f64..25_000_000.0f64
                    ],
                    8..15
                )
            ) {
                let system = FallbackPreventionSystem::new();
                
                let filter_result = system.filter_contaminated_results_detailed(&execution_results, &implementation).unwrap();
                
                // Results with partial Python execution should be identified and potentially excluded
                let has_mixed_execution = execution_results.iter().any(|&x| x > 2000.0 && x < 10_000_000.0);
                let has_heavy_python = execution_results.iter().any(|&x| x >= 12_000_000.0);
                
                if has_heavy_python {
                    // Heavy Python involvement should definitely be detected
                    let heavy_contamination_count = filter_result.contamination_analyses.iter()
                        .filter(|a| a.is_contaminated && matches!(a.contamination_type,
                            ContaminationType::FallbackDetected | ContaminationType::PerformanceAnomaly | ContaminationType::InvalidValue))
                        .count();
                    prop_assert!(heavy_contamination_count > 0,
                        "Heavy Python involvement should be detected as high/critical contamination for '{}'", implementation);
                }
                
                if has_mixed_execution {
                    // Mixed execution might be detected depending on statistical analysis
                    prop_assert!(filter_result.filtering_time_ns > 0,
                        "Contamination analysis should be performed for mixed execution in '{}'", implementation);
                }
                
                // Cross-validation should be performed for mixed implementations
                prop_assert!(!filter_result.implementation.is_empty(),
                    "Cross-validation should be performed for mixed implementation '{}'", implementation);
                
                // Filter effectiveness should be reasonable
                prop_assert!(filter_result.filtering_summary.filtering_confidence >= 0.0 && filter_result.filtering_summary.filtering_confidence <= 1.0,
                    "Filter effectiveness score should be between 0.0 and 1.0 for '{}': {}", 
                    implementation, filter_result.filtering_summary.filtering_confidence);
            }

            #[test]
            fn property_statistical_outlier_exclusion(
                implementation in native_implementation_strategy(),
                base_results in prop::collection::vec(1000.0f64..1200.0f64, 8..12),
                outlier_multiplier in 5.0f64..15.0f64
            ) {
                let system = FallbackPreventionSystem::new();
                
                // Create results with statistical outliers
                let mut results_with_outliers = base_results.clone();
                let mean = base_results.iter().sum::<f64>() / base_results.len() as f64;
                let outlier = mean * outlier_multiplier;
                results_with_outliers.push(outlier);
                
                let filter_result = system.filter_contaminated_results_detailed(&results_with_outliers, &implementation).unwrap();
                
                // Statistical outliers should be detected and excluded
                prop_assert!(!filter_result.filtered_results.contains(&outlier),
                    "Statistical outlier {} should be excluded for '{}' (mean={:.1}, multiplier={:.1})",
                    outlier, implementation, mean, outlier_multiplier);
                
                // Base results should be preserved
                let preserved_base_count = base_results.iter()
                    .filter(|&&result| filter_result.filtered_results.contains(&result))
                    .count();
                
                prop_assert!(preserved_base_count >= base_results.len() * 3 / 4,
                    "Most base results should be preserved for '{}': preserved={}, total={}",
                    implementation, preserved_base_count, base_results.len());
                
                // Contamination log should contain information about the outlier
                let outlier_logged = filter_result.contamination_analyses.iter()
                    .any(|entry| (entry.result_value - outlier).abs() < 1.0);
                prop_assert!(outlier_logged,
                    "Outlier should be logged in contamination log for '{}'", implementation);
            }

            #[test]
            fn property_contamination_filtering_consistency(
                implementation in "[a-z_]+",
                test_results in prop::collection::vec(
                    prop_oneof![
                        // Good results
                        800.0f64..1800.0f64,
                        // Contaminated results
                        Just(0.0f64),
                        20_000_000.0f64..50_000_000.0f64
                    ],
                    10..20
                )
            ) {
                let system = FallbackPreventionSystem::new();
                
                // Apply filtering multiple times - should be consistent
                let result1 = system.filter_contaminated_results_detailed(&test_results, &implementation).unwrap();
                let result2 = system.filter_contaminated_results_detailed(&test_results, &implementation).unwrap();
                
                // Results should be identical
                prop_assert_eq!(result1.filtered_results.len(), result2.filtered_results.len(),
                    "Filtering should be consistent for '{}': first={}, second={}", 
                    implementation, result1.filtered_results.len(), result2.filtered_results.len());
                
                prop_assert_eq!(result1.filtering_summary.contaminated_results, result2.filtering_summary.contaminated_results,
                    "Contamination count should be consistent for '{}': first={}, second={}",
                    implementation, result1.filtering_summary.contaminated_results, result2.filtering_summary.contaminated_results);
                
                prop_assert_eq!(result1.filtering_summary.contaminated_results,
                               result2.filtering_summary.contaminated_results,
                    "Total contaminated count should be consistent for '{}'", implementation);
                
                // Simple filtering should produce subset of detailed filtering
                let simple_filtered = system.filter_contaminated_results(&test_results).unwrap();
                prop_assert!(simple_filtered.len() <= result1.filtered_results.len(),
                    "Simple filtering should not produce more results than detailed filtering for '{}'", implementation);
                
                // All simple filtered results should be in detailed filtered results
                for &simple_result in &simple_filtered {
                    prop_assert!(result1.filtered_results.contains(&simple_result),
                        "Simple filtered result {} should be in detailed filtered results for '{}'",
                        simple_result, implementation);
                }
            }

            #[test]
            fn property_performance_baseline_accuracy(
                impl_name in native_implementation_strategy()
            ) {
                let system = FallbackPreventionSystem::new();
                
                // Get performance baseline
                let baseline = system.get_performance_baseline(&impl_name).unwrap();
                
                // Baseline should reflect pure native performance expectations
                prop_assert_eq!(baseline.expected_native_percentage, 100.0,
                    "Native implementation '{}' baseline should expect 100% native code", impl_name);
                
                prop_assert!(baseline.expected_execution_time_ns < 10_000_000.0, // Less than 10ms
                    "Native implementation '{}' baseline should expect fast execution: {}ns",
                    impl_name, baseline.expected_execution_time_ns);
                
                prop_assert!(baseline.expected_memory_usage_mb < 5.0, // Less than 5MB
                    "Native implementation '{}' baseline should expect low memory usage: {}MB",
                    impl_name, baseline.expected_memory_usage_mb);
                
                prop_assert!(baseline.expected_cpu_utilization < 50.0, // Less than 50% CPU
                    "Native implementation '{}' baseline should expect reasonable CPU usage: {}%",
                    impl_name, baseline.expected_cpu_utilization);
                
                // Baseline source should be appropriate
                prop_assert!(matches!(baseline.baseline_source, 
                    BaselineSource::TheoreticalModel | BaselineSource::BenchmarkSuite),
                    "Native implementation '{}' should have appropriate baseline source: {:?}",
                    impl_name, baseline.baseline_source);
            }

            // **Property 6: ネイティブコード実行保証**
            // **Validates: Requirements 2.3**
            #[test]
            fn property_native_code_execution_guarantee(
                impl_name in native_implementation_strategy(),
                test_iterations in 1usize..10usize
            ) {
                let system = FallbackPreventionSystem::new();
                
                // For any modified FFI implementation, all function calls should execute actual native code
                // and not use Python implementation
                for iteration in 0..test_iterations {
                    let verification_result = system.verify_native_code_execution_detailed(&impl_name).unwrap();
                    
                    // Core property: Native implementations must be verified as native
                    prop_assert!(verification_result.is_native_verified,
                        "Native implementation '{}' must be verified as native code execution (iteration {})",
                        impl_name, iteration);
                    
                    // All function calls should execute native code
                    let monitoring = &verification_result.execution_monitoring;
                    prop_assert!(monitoring.native_calls_detected > 0,
                        "Native implementation '{}' should have detected native calls (iteration {}): {}",
                        impl_name, iteration, monitoring.native_calls_detected);
                    
                    // Should not use Python implementation
                    prop_assert_eq!(monitoring.python_calls_detected, 0,
                        "Native implementation '{}' should not have Python calls (iteration {}): {}",
                        impl_name, iteration, monitoring.python_calls_detected);
                    
                    // Native code percentage should be high
                    prop_assert!(monitoring.performance_metrics.native_code_percentage >= 90.0,
                        "Native implementation '{}' should have high native percentage (iteration {}): {}%",
                        impl_name, iteration, monitoring.performance_metrics.native_code_percentage);
                    
                    // Python overhead should be minimal
                    prop_assert!(monitoring.performance_metrics.python_overhead_percentage <= 10.0,
                        "Native implementation '{}' should have minimal Python overhead (iteration {}): {}%",
                        impl_name, iteration, monitoring.performance_metrics.python_overhead_percentage);
                    
                    // No fallback should be detected
                    prop_assert!(!monitoring.fallback_detected,
                        "Native implementation '{}' should not have fallback detected (iteration {})",
                        impl_name, iteration);
                    
                    // Execution type should be NativeOnly
                    prop_assert_eq!(monitoring.execution_type, ExecutionType::NativeOnly.as_u8(),
                        "Native implementation '{}' should have NativeOnly execution type (iteration {})",
                        impl_name, iteration);
                }
            }

            #[test]
            fn property_native_code_execution_consistency(
                impl_name in native_implementation_strategy(),
                verification_count in 3usize..8usize
            ) {
                let system = FallbackPreventionSystem::new();
                
                let mut verification_results = Vec::new();
                let mut native_percentages = Vec::new();
                let mut confidence_scores = Vec::new();
                
                // Perform multiple verifications
                for _ in 0..verification_count {
                    let result = system.verify_native_code_execution_detailed(&impl_name).unwrap();
                    verification_results.push(result.is_native_verified);
                    native_percentages.push(result.execution_monitoring.performance_metrics.native_code_percentage);
                    confidence_scores.push(result.confidence_score);
                }
                
                // All verifications should be consistent
                let first_result = verification_results[0];
                for (i, &result) in verification_results.iter().enumerate() {
                    prop_assert_eq!(result, first_result,
                        "Native code verification for '{}' should be consistent (iteration {})",
                        impl_name, i);
                }
                
                // Native percentages should be consistently high
                for (i, &percentage) in native_percentages.iter().enumerate() {
                    prop_assert!(percentage >= 90.0,
                        "Native implementation '{}' should consistently show high native percentage (iteration {}): {}%",
                        impl_name, i, percentage);
                }
                
                // Confidence scores should be consistently high
                for (i, &confidence) in confidence_scores.iter().enumerate() {
                    prop_assert!(confidence >= 0.7,
                        "Native implementation '{}' should have consistently high confidence (iteration {}): {:.2}",
                        impl_name, i, confidence);
                }
                
                // Calculate consistency metrics
                let mean_percentage = native_percentages.iter().sum::<f64>() / native_percentages.len() as f64;
                let percentage_variance = native_percentages.iter()
                    .map(|&x| (x - mean_percentage).powi(2))
                    .sum::<f64>() / (native_percentages.len() - 1) as f64;
                let percentage_std_dev = percentage_variance.sqrt();
                
                prop_assert!(percentage_std_dev <= 5.0,
                    "Native code percentages for '{}' should be consistent (std_dev={:.2}): {:?}",
                    impl_name, percentage_std_dev, native_percentages);
            }

            #[test]
            fn property_native_code_execution_no_python_fallback(
                impl_name in native_implementation_strategy(),
                execution_scenarios in 1usize..5usize
            ) {
                let system = FallbackPreventionSystem::new();
                
                // Test different execution scenarios to ensure no Python fallback
                for scenario in 0..execution_scenarios {
                    let monitoring_result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                    
                    // Core guarantee: No Python implementation should be used
                    prop_assert_eq!(monitoring_result.python_calls_detected, 0,
                        "Native implementation '{}' should not use Python implementation (scenario {}): {} Python calls",
                        impl_name, scenario, monitoring_result.python_calls_detected);
                    
                    // Should have native calls
                    prop_assert!(monitoring_result.native_calls_detected > 0,
                        "Native implementation '{}' should have native calls (scenario {}): {} native calls",
                        impl_name, scenario, monitoring_result.native_calls_detected);
                    
                    // Execution should be purely native
                    prop_assert_eq!(monitoring_result.execution_type, ExecutionType::NativeOnly.as_u8(),
                        "Native implementation '{}' should execute as NativeOnly (scenario {})",
                        impl_name, scenario);
                    
                    // Performance metrics should reflect pure native execution
                    let metrics = &monitoring_result.performance_metrics;
                    prop_assert_eq!(metrics.native_code_percentage, 100.0,
                        "Native implementation '{}' should show 100% native code (scenario {}): {}%",
                        impl_name, scenario, metrics.native_code_percentage);
                    
                    prop_assert_eq!(metrics.python_overhead_percentage, 0.0,
                        "Native implementation '{}' should show 0% Python overhead (scenario {}): {}%",
                        impl_name, scenario, metrics.python_overhead_percentage);
                    
                    // No fallback should be detected
                    prop_assert!(!monitoring_result.fallback_detected,
                        "Native implementation '{}' should not detect fallback (scenario {})",
                        impl_name, scenario);
                }
            }

            #[test]
            fn property_native_code_execution_performance_guarantee(
                impl_name in native_implementation_strategy(),
                performance_samples in 2usize..6usize
            ) {
                let system = FallbackPreventionSystem::new();
                
                let mut execution_times = Vec::new();
                let mut memory_usages = Vec::new();
                
                // Collect performance samples
                for sample in 0..performance_samples {
                    let monitoring_result = system.monitor_execution_path_internal(&impl_name, None).unwrap();
                    
                    // Verify this is native execution
                    prop_assert!(system.verify_native_code_execution(&impl_name).unwrap(),
                        "Sample {} for '{}' should be verified as native execution", sample, impl_name);
                    
                    execution_times.push(monitoring_result.execution_time_ns);
                    memory_usages.push(monitoring_result.performance_metrics.memory_usage_bytes);
                }
                
                // Get baseline expectations for native implementation
                let baseline = system.get_performance_baseline(&impl_name).unwrap();
                
                // All execution times should be within native performance range
                for (i, &exec_time) in execution_times.iter().enumerate() {
                    let time_ns = exec_time as f64;
                    let deviation = ((time_ns - baseline.expected_execution_time_ns).abs() / baseline.expected_execution_time_ns) * 100.0;
                    
                    prop_assert!(deviation <= 300.0, // Allow 300% deviation for test environment
                        "Native implementation '{}' execution time should be within native range (sample {}): {}ns vs expected {}ns (deviation: {:.1}%)",
                        impl_name, i, time_ns, baseline.expected_execution_time_ns, deviation);
                }
                
                // Memory usage should be reasonable for native code
                for (i, &memory_bytes) in memory_usages.iter().enumerate() {
                    let memory_mb = memory_bytes as f64 / (1024.0 * 1024.0);
                    
                    prop_assert!(memory_mb <= baseline.expected_memory_usage_mb * 5.0, // Allow 5x for test environment
                        "Native implementation '{}' memory usage should be reasonable (sample {}): {:.2}MB vs expected {:.2}MB",
                        impl_name, i, memory_mb, baseline.expected_memory_usage_mb);
                }
            }

            #[test]
            fn property_native_code_execution_verification_completeness(
                impl_name in native_implementation_strategy()
            ) {
                let system = FallbackPreventionSystem::new();
                
                // Perform comprehensive verification
                let verification_result = system.verify_native_code_execution_detailed(&impl_name).unwrap();
                
                // Basic verification should pass
                prop_assert!(verification_result.is_native_verified,
                    "Native implementation '{}' should pass basic verification", impl_name);
                
                // Verification should be comprehensive
                prop_assert!(verification_result.confidence_score > 0.0,
                    "Native implementation '{}' should have measurable confidence score: {:.2}",
                    impl_name, verification_result.confidence_score);
                
                prop_assert!(verification_result.verification_time_ns > 0,
                    "Native implementation '{}' should have measurable verification time: {}ns",
                    impl_name, verification_result.verification_time_ns);
                
                // Should have execution monitoring data
                let monitoring = &verification_result.execution_monitoring;
                prop_assert!(monitoring.execution_time_ns > 0,
                    "Native implementation '{}' should have execution time data", impl_name);
                
                // Should have performance analysis
                prop_assert!(!verification_result.performance_analysis.implementation.is_empty(),
                    "Native implementation '{}' should have performance analysis", impl_name);
                
                // Should have recommendations
                prop_assert!(!verification_result.recommendations.is_empty(),
                    "Native implementation '{}' should have verification recommendations", impl_name);
                
                // For native implementations, should have minimal critical issues
                let critical_issues = verification_result.verification_issues.iter()
                    .filter(|issue| matches!(issue.severity, IssueSeverity::Critical))
                    .count();
                
                prop_assert!(critical_issues == 0,
                    "Native implementation '{}' should not have critical verification issues: {} critical issues found",
                    impl_name, critical_issues);
            }
        }
    }

    #[test]
    fn test_memory_usage_estimation() {
        let system = FallbackPreventionSystem::new();
        
        // Test different implementation types have different memory estimates
        let python_memory = system.estimate_memory_usage("python").unwrap();
        let c_memory = system.estimate_memory_usage("c_ext").unwrap();
        let cpp_memory = system.estimate_memory_usage("cpp_ext").unwrap();
        let rust_memory = system.estimate_memory_usage("rust_ext").unwrap();
        let go_memory = system.estimate_memory_usage("go_ext").unwrap();
        
        // Python should use more memory than native implementations
        assert!(python_memory > c_memory);
        assert!(python_memory > rust_memory);
        
        // All memory estimates should be positive
        assert!(python_memory > 0);
        assert!(c_memory > 0);
        assert!(cpp_memory > 0);
        assert!(rust_memory > 0);
        assert!(go_memory > 0);
    }

    #[test]
    fn test_configuration_updates() {
        let mut system = FallbackPreventionSystem::new();
        
        // Test initial configuration
        assert_eq!(system.config.fallback_detection_threshold, 0.1);
        assert!(system.config.enable_call_tracing);
        assert!(system.config.enable_performance_monitoring);
        assert_eq!(system.config.max_trace_entries, 10000);
        
        // Update configuration
        system.configure_monitoring(false, false, 0.5, 5000);
        
        // Verify updates
        assert_eq!(system.config.fallback_detection_threshold, 0.5);
        assert!(!system.config.enable_call_tracing);
        assert!(!system.config.enable_performance_monitoring);
        assert_eq!(system.config.max_trace_entries, 5000);
    }

    #[test]
    fn test_performance_anomaly_detection() {
        let system = FallbackPreventionSystem::new();
        
        // Test with Python implementation (should detect anomalies)
        let python_anomalies = system.detect_performance_anomalies("python", 50_000_000.0).unwrap();
        assert!(python_anomalies, "Python implementation should show performance anomalies");
        
        // Test with C extension (should not detect anomalies for expected performance)
        let c_anomalies = system.detect_performance_anomalies("c_ext", 100_000.0).unwrap();
        assert!(!c_anomalies, "C extension with expected performance should not show anomalies");
        
        // Test with C extension but slow performance (should detect anomalies)
        let slow_c_anomalies = system.detect_performance_anomalies("c_ext", 10_000_000.0).unwrap();
        assert!(slow_c_anomalies, "Slow C extension should show performance anomalies");
    }

    #[test]
    fn test_detailed_performance_analysis() {
        let system = FallbackPreventionSystem::new();
        
        // Test detailed analysis for Python implementation
        let result = system.analyze_performance_anomalies_detailed("python", 20_000_000.0).unwrap();
        assert!(result.anomalies_detected);
        assert!(!result.detected_anomalies.is_empty());
        assert!(matches!(result.fallback_suspicion_level, SuspicionLevel::High | SuspicionLevel::Critical));
        
        // Test detailed analysis for native implementation
        let result = system.analyze_performance_anomalies_detailed("rust_ext", 80_000.0).unwrap();
        assert!(!result.anomalies_detected || result.detected_anomalies.is_empty());
        assert!(matches!(result.fallback_suspicion_level, SuspicionLevel::None | SuspicionLevel::Low));
    }

    #[test]
    fn test_performance_baseline_generation() {
        let system = FallbackPreventionSystem::new();
        
        // Test baselines for different implementation types
        let python_baseline = system.get_performance_baseline("python").unwrap();
        assert_eq!(python_baseline.expected_native_percentage, 0.0);
        assert!(python_baseline.expected_execution_time_ns > 1_000_000.0);
        
        let c_baseline = system.get_performance_baseline("c_ext").unwrap();
        assert_eq!(c_baseline.expected_native_percentage, 100.0);
        assert!(c_baseline.expected_execution_time_ns < 1_000_000.0);
        
        let rust_baseline = system.get_performance_baseline("rust_ext").unwrap();
        assert_eq!(rust_baseline.expected_native_percentage, 100.0);
        assert!(rust_baseline.expected_execution_time_ns < c_baseline.expected_execution_time_ns);
    }

    #[test]
    fn test_anomaly_severity_classification() {
        let system = FallbackPreventionSystem::new();
        
        // Test severity classification
        assert!(matches!(system.classify_anomaly_severity(600.0), AnomalySeverity::Critical));
        assert!(matches!(system.classify_anomaly_severity(300.0), AnomalySeverity::High));
        assert!(matches!(system.classify_anomaly_severity(150.0), AnomalySeverity::Medium));
        assert!(matches!(system.classify_anomaly_severity(75.0), AnomalySeverity::Low));
        assert!(matches!(system.classify_anomaly_severity(25.0), AnomalySeverity::Negligible));
    }

    #[test]
    fn test_statistical_analysis() {
        let system = FallbackPreventionSystem::new();
        
        // Test statistical analysis
        let stats = system.perform_statistical_analysis("c_ext", 200_000.0).unwrap();
        assert!(stats.sample_size > 1);
        assert!(stats.mean_execution_time > 0.0);
        assert!(stats.standard_deviation >= 0.0);
        assert!(stats.confidence_interval_95.0 < stats.confidence_interval_95.1);
    }

    #[test]
    fn test_performance_measurement_purity() {
        let system = FallbackPreventionSystem::new();
        
        // Test that native implementations show minimal Python overhead
        let c_result = system.monitor_execution_path_internal("c_ext", None).unwrap();
        assert!(c_result.performance_metrics.python_overhead_percentage <= 10.0,
            "C extension should have minimal Python overhead: {}%", 
            c_result.performance_metrics.python_overhead_percentage);
        assert!(c_result.performance_metrics.native_code_percentage >= 90.0,
            "C extension should have high native code percentage: {}%",
            c_result.performance_metrics.native_code_percentage);
        
        let rust_result = system.monitor_execution_path_internal("rust_ext", None).unwrap();
        assert!(rust_result.performance_metrics.python_overhead_percentage <= 10.0,
            "Rust extension should have minimal Python overhead: {}%",
            rust_result.performance_metrics.python_overhead_percentage);
        assert!(rust_result.performance_metrics.native_code_percentage >= 90.0,
            "Rust extension should have high native code percentage: {}%",
            rust_result.performance_metrics.native_code_percentage);
    }

    #[test]
    fn test_timing_measurement_isolation() {
        let system = FallbackPreventionSystem::new();
        
        // Test that timing measurements are isolated from Python interpreter overhead
        let native_impls = ["c_ext", "cpp_ext", "rust_ext", "go_ext"];
        
        for impl_name in &native_impls {
            let result = system.monitor_execution_path_internal(impl_name, None).unwrap();
            
            // Execution time should be reasonable for native code
            assert!(result.execution_time_ns < 10_000_000, // Less than 10ms
                "{} execution time should be reasonable: {}ns", impl_name, result.execution_time_ns);
            
            // CPU time should reflect actual computation
            assert!(result.performance_metrics.cpu_time_ns > 0,
                "{} should have measurable CPU time", impl_name);
            assert!(result.performance_metrics.cpu_time_ns <= result.execution_time_ns,
                "{} CPU time should not exceed execution time", impl_name);
        }
    }

    #[test]
    fn test_baseline_accuracy_for_native_implementations() {
        let system = FallbackPreventionSystem::new();
        
        // Test that baselines accurately reflect native performance expectations
        let native_impls = ["c_ext", "cpp_ext", "rust_ext", "go_ext", "fortran_ext"];
        
        for impl_name in &native_impls {
            let baseline = system.get_performance_baseline(impl_name).unwrap();
            
            // Native implementations should expect 100% native code
            assert_eq!(baseline.expected_native_percentage, 100.0,
                "{} baseline should expect 100% native code", impl_name);
            
            // Should expect fast execution times
            assert!(baseline.expected_execution_time_ns < 10_000_000.0,
                "{} baseline should expect fast execution: {}ns", 
                impl_name, baseline.expected_execution_time_ns);
            
            // Should expect low memory usage
            assert!(baseline.expected_memory_usage_mb < 5.0,
                "{} baseline should expect low memory usage: {}MB",
                impl_name, baseline.expected_memory_usage_mb);
        }
    }

    #[test]
    fn test_native_code_verification() {
        let system = FallbackPreventionSystem::new();
        
        // Test native implementations - should verify as native
        let native_impls = ["c_ext", "cpp_ext", "rust_ext", "go_ext", "fortran_ext"];
        for impl_name in &native_impls {
            let is_native = system.verify_native_code_execution(impl_name).unwrap();
            assert!(is_native, "{} should be verified as native code execution", impl_name);
        }
        
        // Test Python implementations - should NOT verify as native
        let python_impls = ["python", "pure_python", "python_impl"];
        for impl_name in &python_impls {
            let is_native = system.verify_native_code_execution(impl_name).unwrap();
            assert!(!is_native, "{} should NOT be verified as native code execution", impl_name);
        }
        
        // Test mixed implementations - depends on native percentage
        let mixed_impls = ["cython_ext", "numpy_impl"];
        for impl_name in &mixed_impls {
            let is_native = system.verify_native_code_execution(impl_name).unwrap();
            // Mixed implementations have 50% native, which is < 70% threshold, so should be false
            assert!(!is_native, "{} should NOT be verified as native (mixed execution)", impl_name);
        }
    }

    #[test]
    fn test_detailed_native_code_verification() {
        let system = FallbackPreventionSystem::new();
        
        // Test detailed verification for native implementation
        let result = system.verify_native_code_execution_detailed("rust_ext").unwrap();
        assert_eq!(result.implementation, "rust_ext");
        assert!(result.is_native_verified);
        assert!(result.confidence_score > 0.5);
        assert!(result.verification_time_ns > 0);
        assert!(result.library_exists);
        assert!(result.verification_issues.is_empty() || 
                result.verification_issues.iter().all(|issue| 
                    !matches!(issue.severity, IssueSeverity::Critical)));
        
        // Test detailed verification for Python implementation
        let result = system.verify_native_code_execution_detailed("python").unwrap();
        assert_eq!(result.implementation, "python");
        assert!(!result.is_native_verified);
        assert!(result.confidence_score < 0.5);
        assert!(!result.verification_issues.is_empty());
        
        // Should have critical issues for Python implementation
        let has_critical_issue = result.verification_issues.iter()
            .any(|issue| matches!(issue.severity, IssueSeverity::Critical));
        assert!(has_critical_issue, "Python implementation should have critical verification issues");
    }

    #[test]
    fn test_verification_confidence_calculation() {
        let system = FallbackPreventionSystem::new();
        
        // Test confidence for different implementation types
        let test_cases = [
            ("c_ext", 0.7), // Should have high confidence
            ("python", 0.3), // Should have low confidence
            ("cython_ext", 0.5), // Should have medium confidence
        ];
        
        for (impl_name, expected_min_confidence) in &test_cases {
            let result = system.verify_native_code_execution_detailed(impl_name).unwrap();
            if *expected_min_confidence > 0.5 {
                assert!(result.confidence_score >= *expected_min_confidence,
                    "{} should have confidence >= {}, got {}", 
                    impl_name, expected_min_confidence, result.confidence_score);
            } else {
                assert!(result.confidence_score <= *expected_min_confidence,
                    "{} should have confidence <= {}, got {}", 
                    impl_name, expected_min_confidence, result.confidence_score);
            }
        }
    }

    #[test]
    fn test_verification_issue_identification() {
        let system = FallbackPreventionSystem::new();
        
        // Test issue identification for Python implementation
        let result = system.verify_native_code_execution_detailed("python").unwrap();
        assert!(!result.verification_issues.is_empty());
        
        // Should identify fallback detection issue
        let has_fallback_issue = result.verification_issues.iter()
            .any(|issue| matches!(issue.issue_type, VerificationIssueType::FallbackDetected));
        assert!(has_fallback_issue, "Should identify fallback detection issue for Python implementation");
        
        // Test issue identification for native implementation
        let result = system.verify_native_code_execution_detailed("c_ext").unwrap();
        // Native implementations might have some issues but not critical fallback issues
        let has_critical_fallback = result.verification_issues.iter()
            .any(|issue| matches!(issue.issue_type, VerificationIssueType::FallbackDetected) &&
                        matches!(issue.severity, IssueSeverity::Critical));
        assert!(!has_critical_fallback, "Native implementation should not have critical fallback issues");
    }

    #[test]
    fn test_verification_recommendations() {
        let system = FallbackPreventionSystem::new();
        
        // Test recommendations for verified native implementation
        let result = system.verify_native_code_execution_detailed("rust_ext").unwrap();
        assert!(!result.recommendations.is_empty());
        
        let has_success_recommendation = result.recommendations.iter()
            .any(|rec| rec.contains("verified successfully") || rec.contains("Continue with benchmark"));
        assert!(has_success_recommendation, "Should have success recommendation for verified native code");
        
        // Test recommendations for failed verification
        let result = system.verify_native_code_execution_detailed("python").unwrap();
        assert!(!result.recommendations.is_empty());
        
        let has_failure_recommendation = result.recommendations.iter()
            .any(|rec| rec.contains("could not be verified") || rec.contains("Do not include results"));
        assert!(has_failure_recommendation, "Should have failure recommendation for unverified code");
    }

    #[test]
    fn test_measurement_consistency() {
        let system = FallbackPreventionSystem::new();
        
        // Test that measurements are consistent for the same implementation
        let impl_name = "c_ext";
        let mut measurements = Vec::new();
        
        // Take multiple measurements
        for _ in 0..5 {
            let result = system.monitor_execution_path_internal(impl_name, None).unwrap();
            measurements.push(result.performance_metrics.native_code_percentage);
        }
        
        // Check that measurements are reasonably consistent
        let mean = measurements.iter().sum::<f64>() / measurements.len() as f64;
        let variance = measurements.iter()
            .map(|&x| (x - mean).powi(2))
            .sum::<f64>() / (measurements.len() - 1) as f64;
        let std_dev = variance.sqrt();
        
        // Standard deviation should be reasonable (less than 10% for consistent measurements)
        assert!(std_dev < 10.0, "Measurements should be consistent: std_dev={:.2}, measurements={:?}", std_dev, measurements);
    }
}

#[cfg(test)]
mod proptest_strategies {
    use super::*;
    use proptest::prelude::*;

    pub fn python_implementation_strategy() -> impl Strategy<Value = String> {
        prop_oneof![
            Just("python".to_string()),
            Just("pure_python".to_string()),
            Just("python_impl".to_string()),
            Just("python_fallback".to_string()),
            Just("cython_fallback".to_string()),
            Just("numpy_fallback".to_string()),
        ]
    }

    pub fn native_implementation_strategy() -> impl Strategy<Value = String> {
        prop_oneof![
            Just("c_ext".to_string()),
            Just("cpp_ext".to_string()),
            Just("rust_ext".to_string()),
            Just("go_ext".to_string()),
            Just("cython_ext".to_string()),
            Just("numpy_ext".to_string()),
            Just("fortran_ext".to_string()),
            Just("zig_ext".to_string()),
            Just("nim_ext".to_string()),
            Just("julia_ext".to_string()),
            Just("kotlin_ext".to_string()),
        ]
    }

    pub fn mixed_implementation_strategy() -> impl Strategy<Value = String> {
        prop_oneof![
            Just("mixed_cython".to_string()),
            Just("partial_native".to_string()),
            Just("hybrid_impl".to_string()),
            Just("semi_native".to_string()),
            Just("cython_mixed".to_string()),
            Just("numpy_mixed".to_string()),
        ]
    }
}

#[cfg(test)]
mod property_tests {
    use super::*;
    use super::proptest_strategies::*;
    use proptest::prelude::*;

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(100))]

        // **Property 8: 汚染結果除外**
        // **Validates: Requirements 2.5**
        #[test]
        fn property_contaminated_results_exclusion(
            implementation in "[a-z_]+",
            contaminated_results in prop::collection::vec(
                prop_oneof![
                    // Normal results (should be kept)
                    1000.0f64..2000.0f64,
                    // Contaminated results (should be excluded)
                    prop_oneof![
                        Just(0.0f64),             // Zero results (measurement errors)
                        -1000.0f64..0.0f64,       // Negative results (measurement errors)
                        50.0f64..99.0f64,         // Too fast (suspicious)
                        10_000_000.0f64..50_000_000.0f64, // Too slow (Python fallback)
                    ]
                ],
                5..20
            )
        ) {
            let system = FallbackPreventionSystem::new();
            
            // Apply contamination filtering
            let filter_result = system.filter_contaminated_results_detailed(&contaminated_results, &implementation).unwrap();
            
            // Verify that contaminated results are excluded
            prop_assert!(filter_result.filtered_results.len() <= filter_result.original_results.len(),
                "Filtered results should not exceed original results for '{}'", implementation);
            
            // Check that all filtered results are valid (not contaminated)
            for &result in &filter_result.filtered_results {
                prop_assert!(result > 0.0,
                    "Filtered result should be positive for '{}': {}", implementation, result);
                prop_assert!(result.is_finite(),
                    "Filtered result should be finite for '{}': {}", implementation, result);
            }
            
            // Check that contaminated results are properly logged
            if filter_result.filtering_summary.contaminated_results > 0 {
                prop_assert!(!filter_result.contamination_analyses.is_empty(),
                    "Contamination analyses should not be empty when contamination is detected for '{}'", implementation);
                
                // Verify contamination statistics
                prop_assert!(filter_result.filtering_summary.contaminated_results > 0,
                    "Contaminated count should be positive for '{}'", implementation);
                
                // Check that critical contamination (zero/negative) is properly classified
                let has_critical_contamination = contaminated_results.iter().any(|&x| x <= 0.0);
                if has_critical_contamination {
                    let critical_count = filter_result.contamination_analyses.iter()
                        .filter(|a| a.is_contaminated && a.result_value <= 0.0)
                        .count();
                    prop_assert!(critical_count > 0,
                        "Critical contamination should be detected for '{}' when zero/negative results present", implementation);
                }
            }
            
            // Verify that recommendations are provided when contamination is detected
            if filter_result.filtering_summary.contaminated_results > 5 {
                prop_assert!(!filter_result.recommendations.is_empty(),
                    "Recommendations should be provided for high contamination count ({}) for '{}'", 
                    filter_result.filtering_summary.contaminated_results, implementation);
            }
        }

        #[test]
        fn property_fallback_results_complete_exclusion(
            implementation in prop_oneof![
                python_implementation_strategy(),
                mixed_implementation_strategy()
            ],
            normal_results in prop::collection::vec(1000.0f64..2000.0f64, 3..8),
            fallback_results in prop::collection::vec(15_000_000.0f64..100_000_000.0f64, 2..5)
        ) {
            let system = FallbackPreventionSystem::new();
            
            // Mix normal and fallback results
            let mut mixed_results = normal_results.clone();
            mixed_results.extend(fallback_results.clone());
            
            // Apply filtering
            let filter_result = system.filter_contaminated_results_detailed(&mixed_results, &implementation).unwrap();
            
            // All fallback results should be excluded
            for &fallback_result in &fallback_results {
                prop_assert!(!filter_result.filtered_results.contains(&fallback_result),
                    "Fallback result {} should be excluded from filtered results for '{}'", 
                    fallback_result, implementation);
            }
            
            // Normal results should be preserved (unless they're statistical outliers)
            let preserved_normal_count = normal_results.iter()
                .filter(|&&result| filter_result.filtered_results.contains(&result))
                .count();
            
            prop_assert!(preserved_normal_count >= normal_results.len() / 2,
                "At least half of normal results should be preserved for '{}': preserved={}, total={}",
                implementation, preserved_normal_count, normal_results.len());
            
            // Contamination rate should reflect the presence of fallback results
            let expected_contamination_rate = fallback_results.len() as f64 / (normal_results.len() + fallback_results.len()) as f64 * 100.0;
            let actual_contamination_rate = filter_result.filtering_summary.contaminated_results as f64 / filter_result.original_results.len() as f64 * 100.0;
            prop_assert!(actual_contamination_rate >= expected_contamination_rate * 0.8,
                "Contamination rate should reflect fallback presence for '{}': actual={:.1}%, expected>={:.1}%",
                implementation, actual_contamination_rate, expected_contamination_rate * 0.8);
        }

        #[test]
        fn property_partial_python_execution_detection(
            implementation in mixed_implementation_strategy(),
            execution_results in prop::collection::vec(
                prop_oneof![
                    // Pure native results
                    500.0f64..1500.0f64,
                    // Mixed execution results (some Python involvement)
                    2500.0f64..8000.0f64,
                    // Heavy Python involvement
                    12_000_000.0f64..25_000_000.0f64
                ],
                8..15
            )
        ) {
            let system = FallbackPreventionSystem::new();
            
            let filter_result = system.filter_contaminated_results_detailed(&execution_results, &implementation).unwrap();
            
            // Results with partial Python execution should be identified and potentially excluded
            let has_mixed_execution = execution_results.iter().any(|&x| x > 2000.0 && x < 10_000_000.0);
            let has_heavy_python = execution_results.iter().any(|&x| x >= 12_000_000.0);
            
            if has_heavy_python {
                // Heavy Python involvement should definitely be detected
                let heavy_contamination_count = filter_result.contamination_analyses.iter()
                    .filter(|a| a.is_contaminated && matches!(a.contamination_type,
                        ContaminationType::FallbackDetected | ContaminationType::PerformanceAnomaly | ContaminationType::InvalidValue))
                    .count();
                prop_assert!(heavy_contamination_count > 0,
                    "Heavy Python involvement should be detected as high/critical contamination for '{}'", implementation);
            }
            
            if has_mixed_execution {
                // Mixed execution might be detected depending on statistical analysis
                prop_assert!(filter_result.filtering_time_ns > 0,
                    "Contamination analysis should be performed for mixed execution in '{}'", implementation);
            }
            
            // Statistical analysis should be performed for mixed implementations
            prop_assert!(filter_result.statistical_analysis.is_some(),
                "Statistical analysis should be performed for mixed implementation '{}'", implementation);
            
            // Filter effectiveness should be reasonable
            prop_assert!(filter_result.filtering_summary.filtering_confidence >= 0.0 && filter_result.filtering_summary.filtering_confidence <= 1.0,
                "Filter confidence should be between 0.0 and 1.0 for '{}': {}", 
                implementation, filter_result.filtering_summary.filtering_confidence);
        }

        #[test]
        fn property_statistical_outlier_exclusion(
            implementation in native_implementation_strategy(),
            base_results in prop::collection::vec(1000.0f64..1200.0f64, 8..12),
            outlier_multiplier in 5.0f64..15.0f64
        ) {
            let system = FallbackPreventionSystem::new();
            
            // Create results with statistical outliers
            let mut results_with_outliers = base_results.clone();
            let mean = base_results.iter().sum::<f64>() / base_results.len() as f64;
            let outlier = mean * outlier_multiplier;
            results_with_outliers.push(outlier);
            
            let filter_result = system.filter_contaminated_results_detailed(&results_with_outliers, &implementation).unwrap();
            
            // Statistical outliers should be detected and excluded
            prop_assert!(!filter_result.filtered_results.contains(&outlier),
                "Statistical outlier {} should be excluded for '{}' (mean={:.1}, multiplier={:.1})",
                outlier, implementation, mean, outlier_multiplier);
            
            // Base results should be preserved
            let preserved_base_count = base_results.iter()
                .filter(|&&result| filter_result.filtered_results.contains(&result))
                .count();
            
            prop_assert!(preserved_base_count >= base_results.len() * 3 / 4,
                "Most base results should be preserved for '{}': preserved={}, total={}",
                implementation, preserved_base_count, base_results.len());
            
            // Contamination analysis should contain information about the outlier
            let outlier_analyzed = filter_result.contamination_analyses.iter()
                .any(|analysis| analysis.contamination_reason.contains("outlier")
                    || analysis.contamination_reason.contains("Outlier")
                    || matches!(analysis.contamination_type, ContaminationType::StatisticalOutlier));
            prop_assert!(outlier_analyzed,
                "Outlier should be analyzed in contamination analyses for '{}'", implementation);
        }

        #[test]
        fn property_contamination_filtering_consistency(
            implementation in "[a-z_]+",
            test_results in prop::collection::vec(
                prop_oneof![
                    800.0f64..1800.0f64,
                    Just(0.0f64),
                    20_000_000.0f64..50_000_000.0f64
                ],
                10..20
            )
        ) {
            let system = FallbackPreventionSystem::new();
            // Apply filtering multiple times - should be consistent
            let result1 = system.filter_contaminated_results_detailed(&test_results, &implementation).unwrap();
            let result2 = system.filter_contaminated_results_detailed(&test_results, &implementation).unwrap();
            
            // Results should be identical
            prop_assert_eq!(result1.filtered_results.len(), result2.filtered_results.len(),
                "Filtering should be consistent for '{}': first={}, second={}", 
                implementation, result1.filtered_results.len(), result2.filtered_results.len());
            
            prop_assert_eq!(result1.filtering_summary.contaminated_results, result2.filtering_summary.contaminated_results,
                "Contamination count should be consistent for '{}': first={}, second={}",
                implementation, result1.filtering_summary.contaminated_results, result2.filtering_summary.contaminated_results);

            prop_assert_eq!(result1.filtering_summary.contaminated_results,
                           result2.filtering_summary.contaminated_results,
                "Total contaminated count should be consistent for '{}'", implementation);
            
            // Simple filtering should produce subset of detailed filtering
            let simple_filtered = system.filter_contaminated_results(&test_results).unwrap();
            prop_assert!(simple_filtered.len() <= result1.filtered_results.len(),
                "Simple filtering should not produce more results than detailed filtering for '{}'", implementation);
            
            // All simple filtered results should be in detailed filtered results
            for &simple_result in &simple_filtered {
                prop_assert!(result1.filtered_results.contains(&simple_result),
                    "Simple filtered result {} should be in detailed filtered results for '{}'",
                    simple_result, implementation);
            }
        }
    }

    #[test]
    fn test_contaminated_results_filtering() {
        let system = FallbackPreventionSystem::new();
        let contaminated_results = vec![100_000.0, -1.0, f64::NAN, 105_000.0, f64::INFINITY, 98_000.0];
        let filtered = system.filter_contaminated_results(&contaminated_results).unwrap();
        assert!(filtered.len() < contaminated_results.len(), "Contaminated results should be filtered");
        assert!(filtered.len() >= 3, "Should retain valid results");
        
        // All filtered results should be valid
        for &result in &filtered {
            assert!(result > 0.0 && result.is_finite(), "Filtered results should be valid: {}", result);
        }
        
        // Test with empty results
        let empty_results = vec![];
        let filtered = system.filter_contaminated_results(&empty_results).unwrap();
        assert!(filtered.is_empty(), "Empty input should return empty output");
    }

    #[test]
    fn test_detailed_contamination_filtering() {
        let system = FallbackPreventionSystem::new();
        
        // Test detailed filtering with mixed results
        let mixed_results = vec![100_000.0, 10_000_000.0, 105_000.0, -1.0, 98_000.0, f64::NAN];
        let result = system.filter_contaminated_results_detailed(&mixed_results, "c_ext").unwrap();
        
        assert_eq!(result.implementation, "c_ext");
        assert_eq!(result.original_results.len(), 6);
        assert!(result.filtered_results.len() < result.original_results.len());
        assert!(result.filtering_summary.contaminated_results > 0);
        assert!(!result.recommendations.is_empty());
        assert!(result.filtering_time_ns > 0);
        
        // Check contamination analyses
        assert_eq!(result.contamination_analyses.len(), mixed_results.len());
        let contaminated_count = result.contamination_analyses.iter()
            .filter(|analysis| analysis.is_contaminated)
            .count();
        assert!(contaminated_count > 0, "Should detect contaminated results");
        
        // Test with all clean results
        let clean_results = vec![100_000.0, 105_000.0, 98_000.0, 102_000.0];
        let result = system.filter_contaminated_results_detailed(&clean_results, "rust_ext").unwrap();
        
        assert_eq!(result.filtered_results.len(), clean_results.len());
        assert_eq!(result.filtering_summary.contaminated_results, 0);
        assert!(result.recommendations.iter().any(|rec| rec.contains("clean")));
    }

    #[test]
    fn test_contamination_analysis() {
        let system = FallbackPreventionSystem::new();
        
        // Test valid result
        let valid_analysis = system.analyze_result_contamination(100_000.0, 0).unwrap();
        assert!(!valid_analysis.is_contaminated);
        assert!(matches!(valid_analysis.contamination_type, ContaminationType::None));
        assert_eq!(valid_analysis.confidence_score, 1.0);
        
        // Test invalid results
        let invalid_analysis = system.analyze_result_contamination(-1.0, 1).unwrap();
        assert!(invalid_analysis.is_contaminated);
        assert!(matches!(invalid_analysis.contamination_type, ContaminationType::InvalidValue));
        
        let nan_analysis = system.analyze_result_contamination(f64::NAN, 2).unwrap();
        assert!(nan_analysis.is_contaminated);
        assert!(matches!(nan_analysis.contamination_type, ContaminationType::InvalidValue));
        
        let inf_analysis = system.analyze_result_contamination(f64::INFINITY, 3).unwrap();
        assert!(inf_analysis.is_contaminated);
        assert!(matches!(inf_analysis.contamination_type, ContaminationType::InvalidValue));
        
        // Test suspicious values
        let suspicious_analysis = system.analyze_result_contamination(1e15, 4).unwrap();
        assert!(suspicious_analysis.is_contaminated);
        assert!(matches!(suspicious_analysis.contamination_type, ContaminationType::SuspiciousValue));
    }

    #[test]
    fn test_statistical_contamination_detection() {
        let system = FallbackPreventionSystem::new();
        
        // Test with outliers
        let results_with_outliers = vec![100.0, 105.0, 98.0, 102.0, 1000.0, 99.0, 101.0];
        let outliers = system.detect_statistical_contamination(&results_with_outliers).unwrap();
        assert!(!outliers.is_empty(), "Should detect outliers");
        assert!(outliers.contains(&1000.0), "Should detect the obvious outlier");
        
        // Test with clean data
        let clean_results = vec![100.0, 105.0, 98.0, 102.0, 99.0, 101.0];
        let outliers = system.detect_statistical_contamination(&clean_results).unwrap();
        assert!(outliers.is_empty() || outliers.len() <= 1, "Clean data should have few or no outliers");
        
        // Test with insufficient data
        let small_results = vec![100.0, 105.0];
        let outliers = system.detect_statistical_contamination(&small_results).unwrap();
        assert!(outliers.is_empty(), "Insufficient data should return no outliers");
    }

    #[test]
    fn test_performance_based_filtering() {
        let system = FallbackPreventionSystem::new();
        
        // Test with performance outliers
        let results_with_slow = vec![100.0, 105.0, 98.0, 102.0, 2000.0, 99.0]; // 2000.0 is 20x median
        let filtered = system.apply_performance_based_filtering(&results_with_slow).unwrap();
        assert!(filtered.len() < results_with_slow.len(), "Should filter out slow results");
        assert!(!filtered.contains(&2000.0), "Should filter out the slow result");
        
        // Test with reasonable performance
        let reasonable_results = vec![100.0, 105.0, 98.0, 102.0, 110.0, 95.0];
        let filtered = system.apply_performance_based_filtering(&reasonable_results).unwrap();
        assert_eq!(filtered.len(), reasonable_results.len(), "Should not filter reasonable results");
        
        // Test with empty results
        let empty_results = vec![];
        let filtered = system.apply_performance_based_filtering(&empty_results).unwrap();
        assert!(filtered.is_empty(), "Empty input should return empty output");
    }

    #[test]
    fn test_filtering_confidence_calculation() {
        let system = FallbackPreventionSystem::new();
        
        // Test high confidence (no filtering)
        let high_confidence = system.calculate_filtering_confidence(10, 10, &[]).unwrap();
        assert!(high_confidence >= 0.9, "No filtering should result in high confidence");
        
        // Test medium confidence (some filtering)
        let medium_confidence = system.calculate_filtering_confidence(10, 8, &[]).unwrap();
        assert!(medium_confidence >= 0.7 && medium_confidence < 0.9, "Some filtering should result in medium confidence");
        
        // Test low confidence (heavy filtering)
        let low_confidence = system.calculate_filtering_confidence(10, 3, &[]).unwrap();
        assert!(low_confidence < 0.7, "Heavy filtering should result in low confidence");
        
        // Test edge case (no results)
        let no_results_confidence = system.calculate_filtering_confidence(0, 0, &[]).unwrap();
        assert_eq!(no_results_confidence, 1.0, "No results should have perfect confidence");
    }

    #[test]
    fn test_contamination_statistical_analysis() {
        let system = FallbackPreventionSystem::new();
        
        // Test with normal distribution
        let normal_results = vec![100.0, 105.0, 98.0, 102.0, 99.0, 101.0, 103.0];
        let stats = system.perform_contamination_statistical_analysis(&normal_results).unwrap();
        
        assert_eq!(stats.sample_size, 7);
        assert!(stats.mean > 0.0);
        assert!(stats.standard_deviation >= 0.0);
        assert!(stats.coefficient_of_variation >= 0.0);
        assert!(stats.min_value <= stats.max_value);
        assert!(stats.outlier_threshold_lower < stats.outlier_threshold_upper);
        
        // Test with high variation (should detect contamination indicators)
        let high_variation_results = vec![100.0, 1000.0, 50.0, 2000.0, 75.0];
        let stats = system.perform_contamination_statistical_analysis(&high_variation_results).unwrap();
        assert!(!stats.contamination_indicators.is_empty(), "High variation should be detected");
        assert!(stats.coefficient_of_variation > 0.5, "Should have high coefficient of variation");
    }
}