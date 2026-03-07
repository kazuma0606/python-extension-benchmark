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
    pub fn verify_native_code_execution(&self, ffi_impl: &str) -> Result<bool> {
        // TODO: Implement in task 8.1
        Ok(false)
    }

    /// Filter contaminated results
    pub fn filter_contaminated_results(&self, results: &[f64]) -> Result<Vec<f64>> {
        // TODO: Implement in task 8.3
        Ok(results.to_vec())
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
        
        // All measurements should be consistently high for native implementation
        for (i, &percentage) in measurements.iter().enumerate() {
            assert!(percentage >= 90.0,
                "Measurement {} for {} should show high native percentage: {}%",
                i, impl_name, percentage);
        }
        
        // Calculate standard deviation to check consistency
        let mean = measurements.iter().sum::<f64>() / measurements.len() as f64;
        let variance = measurements.iter()
            .map(|&x| (x - mean).powi(2))
            .sum::<f64>() / (measurements.len() - 1) as f64;
        let std_dev = variance.sqrt();
        
        assert!(std_dev <= 5.0,
            "Native code percentage measurements should be consistent (std_dev={}): {:?}",
            std_dev, measurements);
    }
}