//! Comprehensive Audit Reporter
//!
//! Generates structured reports on FFI implementation audits (Task 10).
//! - 10.1  Bug analysis report  (Requirement 1.5)
//! - 10.2  Performance validation report (Requirements 6.1-6.5)

use crate::error::Result;
use crate::types::*;
use pyo3::prelude::*;
use std::collections::HashMap;

/// Comprehensive Audit Reporter
#[pyclass]
#[derive(Debug, Clone)]
pub struct ComprehensiveAuditReporter {}

// ── Python-visible API ────────────────────────────────────────────────────────

#[pymethods]
impl ComprehensiveAuditReporter {
    #[new]
    pub fn new() -> Self {
        Self {}
    }

    /// Generate a plain-text bug analysis report (Python binding).
    pub fn generate_bug_analysis_report_text(
        &self,
        implementations: Vec<String>,
    ) -> PyResult<String> {
        // Build minimal diagnostics for each name supplied from Python
        let diagnostics: Vec<LibraryDiagnostics> = implementations
            .into_iter()
            .map(|name| LibraryDiagnostics {
                implementation: name,
                library_exists: false,
                library_loadable: false,
                loading_errors: vec![],
                missing_dependencies: vec![],
                architecture_mismatch: false,
                path_issues: vec![],
            })
            .collect();
        self.generate_bug_analysis_report(&diagnostics)
            .map(|r| r.report_text)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    /// Generate a plain-text performance validation report (Python binding).
    pub fn generate_performance_validation_report_text(
        &self,
        results: Vec<f64>,
    ) -> PyResult<String> {
        self.generate_performance_validation_report(&results)
            .map(|r| r.report_text)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    /// Generate the full combined audit report (Python binding).
    pub fn generate_comprehensive_report_text(
        &self,
        implementations: Vec<String>,
        performance_results: Vec<f64>,
    ) -> PyResult<String> {
        let diagnostics: Vec<LibraryDiagnostics> = implementations
            .into_iter()
            .map(|name| LibraryDiagnostics {
                implementation: name,
                library_exists: false,
                library_loadable: false,
                loading_errors: vec![],
                missing_dependencies: vec![],
                architecture_mismatch: false,
                path_issues: vec![],
            })
            .collect();
        self.generate_comprehensive_report(&diagnostics, &[], &performance_results)
            .map(|r| r.report_text)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    // ── Task 11.1: Additional Python bindings ─────────────────────────────────

    /// Analyse a list of (name, timing_ns) tuples for fallback patterns.
    ///
    /// Returns a dict with:
    ///   suspected_fallbacks: list[str]
    ///   clean_implementations: list[str]
    ///   summary: str
    pub fn analyze_benchmark_results_py(
        &self,
        py: pyo3::Python<'_>,
        results: Vec<(String, f64)>,
    ) -> pyo3::PyResult<pyo3::PyObject> {
        const FALLBACK_THRESHOLD_NS: f64 = 10_000_000.0; // 10 ms

        let mut suspected: Vec<String> = Vec::new();
        let mut clean: Vec<String> = Vec::new();

        for (name, time_ns) in &results {
            let name_flag = name.contains("python") || name.contains("fallback") || name.contains("pure");
            if name_flag || *time_ns >= FALLBACK_THRESHOLD_NS {
                suspected.push(name.clone());
            } else {
                clean.push(name.clone());
            }
        }

        let summary = format!(
            "Analyzed {} implementations: {} suspected fallbacks, {} clean.",
            results.len(), suspected.len(), clean.len()
        );

        let d = pyo3::types::PyDict::new(py);
        d.set_item("suspected_fallbacks", &suspected)?;
        d.set_item("clean_implementations", &clean)?;
        d.set_item("summary", &summary)?;
        Ok(d.into())
    }
}

// ── Internal Rust API ─────────────────────────────────────────────────────────

impl ComprehensiveAuditReporter {
    // ─── Task 10.1: Bug Analysis Report ──────────────────────────────────────

    /// Generate a detailed bug analysis report from library diagnostics.
    ///
    /// Satisfies Requirement 1.5: document which implementations work and which
    /// fail, together with auto-generated fix steps.
    pub fn generate_bug_analysis_report(
        &self,
        diagnostics: &[LibraryDiagnostics],
    ) -> Result<BugAnalysisReport> {
        let timestamp = self.current_timestamp();
        let mut summaries: Vec<ImplementationBugSummary> = Vec::new();
        let mut critical_issues: Vec<String> = Vec::new();
        let mut fix_priority: Vec<String> = Vec::new();

        for diag in diagnostics {
            let status = self.classify_status(diag);
            let fix_steps = self.generate_fix_steps(diag);

            // Collect critical issues
            for err in &diag.loading_errors {
                if matches!(err.error_type, LoadingErrorType::DependencyMissing | LoadingErrorType::ArchitectureMismatch) {
                    critical_issues.push(format!(
                        "[{}] {}", diag.implementation, err.error_message
                    ));
                }
            }
            if diag.architecture_mismatch {
                critical_issues.push(format!(
                    "[{}] Architecture mismatch detected", diag.implementation
                ));
            }

            if status == ImplementationStatus::Failed {
                fix_priority.push(diag.implementation.clone());
            }

            summaries.push(ImplementationBugSummary {
                implementation: diag.implementation.clone(),
                status,
                dll_issues: vec![], // populated when DLLIssue data is available separately
                loading_errors: diag.loading_errors.clone(),
                missing_dependencies: diag.missing_dependencies.clone(),
                architecture_mismatch: diag.architecture_mismatch,
                path_issues: diag.path_issues.clone(),
                fix_steps,
            });
        }

        let working_count = summaries.iter().filter(|s| s.status == ImplementationStatus::Working).count();
        let failed_count  = summaries.iter().filter(|s| s.status == ImplementationStatus::Failed).count();
        let partial_count = summaries.iter().filter(|s| s.status == ImplementationStatus::PartiallyWorking).count();

        let report_text = self.render_bug_report(
            &summaries, &critical_issues, &fix_priority, &timestamp,
        );

        Ok(BugAnalysisReport {
            report_title: "FFI Implementation Bug Analysis Report".to_string(),
            generated_at: timestamp,
            total_implementations: summaries.len(),
            working_count,
            failed_count,
            partial_count,
            implementation_summaries: summaries,
            critical_issues,
            fix_priority_list: fix_priority,
            report_text,
        })
    }

    /// Extended variant that also ingests per-implementation DLL issues.
    pub fn generate_bug_analysis_report_with_issues(
        &self,
        diagnostics: &[LibraryDiagnostics],
        dll_issues_map: &HashMap<String, Vec<DLLIssue>>,
    ) -> Result<BugAnalysisReport> {
        let mut report = self.generate_bug_analysis_report(diagnostics)?;

        // Merge DLL issue data into each summary
        for summary in &mut report.implementation_summaries {
            if let Some(issues) = dll_issues_map.get(&summary.implementation) {
                summary.dll_issues = issues.clone();
                // Elevate critical DLL issues to the critical list
                for issue in issues {
                    if matches!(issue.issue_type, DLLIssueType::ArchitectureMismatch | DLLIssueType::DependencyMissing) {
                        report.critical_issues.push(format!(
                            "[{}] DLL issue: {}", summary.implementation, issue.description
                        ));
                    }
                }
            }
        }

        // Re-render the report text with the updated summaries
        let timestamp = report.generated_at.clone();
        report.report_text = self.render_bug_report(
            &report.implementation_summaries,
            &report.critical_issues,
            &report.fix_priority_list,
            &timestamp,
        );
        Ok(report)
    }

    // ─── Task 10.2: Performance Validation Report ─────────────────────────────

    /// Generate a performance validation report from raw timing results.
    ///
    /// Used when only raw FFI timings are available (no Python baseline).
    /// Satisfies Requirements 6.1-6.5.
    pub fn generate_performance_validation_report(
        &self,
        results: &[f64],
    ) -> Result<PerformanceValidationReport> {
        let timestamp = self.current_timestamp();

        if results.is_empty() {
            let report_text = format!(
                "Performance Validation Report\nGenerated: {}\n\nNo results provided.\n",
                timestamp
            );
            return Ok(PerformanceValidationReport {
                report_title: "FFI Performance Validation Report".to_string(),
                generated_at: timestamp,
                total_implementations: 0,
                passing_count: 0,
                failing_count: 0,
                suspected_fallback_count: 0,
                average_speedup_percentage: 0.0,
                entries: vec![],
                fallback_detections: vec![],
                report_text,
            });
        }

        // Treat each element as an anonymous implementation result
        let mean = results.iter().sum::<f64>() / results.len() as f64;
        let fallback_threshold = 10_000_000.0_f64; // 10 ms threshold for Python fallback

        let mut entries = Vec::new();
        let mut fallback_detections = Vec::new();

        for (i, &val) in results.iter().enumerate() {
            let fallback_suspected = val >= fallback_threshold;
            if fallback_suspected {
                fallback_detections.push(format!("Result #{}: {:.0} ns (potential fallback)", i + 1, val));
            }
            entries.push(ImplementationPerformanceEntry {
                implementation: format!("impl_{}", i + 1),
                performance_ratio: if val > 0.0 { mean / val } else { 0.0 },
                speedup_percentage: if mean > 0.0 { (mean - val) / mean * 100.0 } else { 0.0 },
                is_significantly_faster: !fallback_suspected && val < mean,
                fallback_suspected,
                p_value: 1.0, // no baseline comparison available
                effect_size: 0.0,
                flags: if fallback_suspected { vec!["PotentialFallback".to_string()] } else { vec![] },
                sample_size: 1,
            });
        }

        let passing_count = entries.iter().filter(|e| e.is_significantly_faster).count();
        let suspected_count = entries.iter().filter(|e| e.fallback_suspected).count();
        let failing_count = entries.len() - passing_count;

        let report_text = self.render_performance_report_simple(results, &entries, &fallback_detections, &timestamp);

        Ok(PerformanceValidationReport {
            report_title: "FFI Performance Validation Report".to_string(),
            generated_at: timestamp,
            total_implementations: entries.len(),
            passing_count,
            failing_count,
            suspected_fallback_count: suspected_count,
            average_speedup_percentage: 0.0,
            entries,
            fallback_detections,
            report_text,
        })
    }

    /// Full performance validation from `PerformanceReport` (Task 9 output).
    pub fn generate_performance_validation_report_from_comparison(
        &self,
        perf_report: &PerformanceReport,
    ) -> Result<PerformanceValidationReport> {
        let timestamp = self.current_timestamp();
        let mut entries = Vec::new();
        let mut fallback_detections = Vec::new();

        for cmp in &perf_report.comparisons {
            if cmp.fallback_suspected {
                fallback_detections.push(format!(
                    "[{}] Potential fallback detected (ratio={:.2}, p={:.4})",
                    cmp.implementation,
                    cmp.performance_ratio,
                    cmp.statistical_significance.p_value
                ));
            }

            let flag_strings: Vec<String> = cmp.performance_flags
                .iter()
                .map(|f| format!("{:?}", f))
                .collect();

            entries.push(ImplementationPerformanceEntry {
                implementation: cmp.implementation.clone(),
                performance_ratio: cmp.performance_ratio,
                speedup_percentage: cmp.speedup_percentage,
                is_significantly_faster: cmp.is_significantly_faster,
                fallback_suspected: cmp.fallback_suspected,
                p_value: cmp.statistical_significance.p_value,
                effect_size: cmp.statistical_significance.effect_size,
                flags: flag_strings,
                sample_size: cmp.ffi_results_ns.len(),
            });
        }

        let passing_count  = perf_report.passing_implementations.len();
        let failing_count  = perf_report.failing_implementations.len();
        let suspected_count = perf_report.suspected_fallbacks.len();

        let report_text = self.render_performance_report_full(&entries, &fallback_detections, perf_report, &timestamp);

        Ok(PerformanceValidationReport {
            report_title: "FFI Performance Validation Report".to_string(),
            generated_at: timestamp,
            total_implementations: entries.len(),
            passing_count,
            failing_count,
            suspected_fallback_count: suspected_count,
            average_speedup_percentage: perf_report.average_speedup_percentage,
            entries,
            fallback_detections,
            report_text,
        })
    }

    // ─── Combined Report ──────────────────────────────────────────────────────

    /// Generate the combined comprehensive audit report.
    pub fn generate_comprehensive_report(
        &self,
        diagnostics: &[LibraryDiagnostics],
        builds: &[BuildScript],
        performance_results: &[f64],
    ) -> Result<ComprehensiveAuditReport> {
        let timestamp = self.current_timestamp();
        let bug_report  = self.generate_bug_analysis_report(diagnostics)?;
        let perf_report = self.generate_performance_validation_report(performance_results)?;

        let overall_summary = self.build_overall_summary(&bug_report, &perf_report, builds.len());
        let report_text = format!(
            "{}\n\n{}\n\n=== OVERALL SUMMARY ===\n{}",
            bug_report.report_text,
            perf_report.report_text,
            overall_summary
        );

        Ok(ComprehensiveAuditReport {
            report_title: "Windows FFI Comprehensive Audit Report".to_string(),
            generated_at: timestamp,
            bug_analysis: bug_report,
            performance_validation: perf_report,
            overall_summary,
            report_text,
        })
    }

    /// Extended combined report that uses full performance comparison data.
    pub fn generate_comprehensive_report_full(
        &self,
        diagnostics: &[LibraryDiagnostics],
        dll_issues_map: &HashMap<String, Vec<DLLIssue>>,
        builds: &[BuildScript],
        perf_report: &PerformanceReport,
    ) -> Result<ComprehensiveAuditReport> {
        let timestamp = self.current_timestamp();
        let bug_report  = self.generate_bug_analysis_report_with_issues(diagnostics, dll_issues_map)?;
        let perf_valid  = self.generate_performance_validation_report_from_comparison(perf_report)?;

        let overall_summary = self.build_overall_summary(&bug_report, &perf_valid, builds.len());
        let report_text = format!(
            "{}\n\n{}\n\n=== OVERALL SUMMARY ===\n{}",
            bug_report.report_text,
            perf_valid.report_text,
            overall_summary
        );

        Ok(ComprehensiveAuditReport {
            report_title: "Windows FFI Comprehensive Audit Report".to_string(),
            generated_at: timestamp,
            bug_analysis: bug_report,
            performance_validation: perf_valid,
            overall_summary,
            report_text,
        })
    }

    // ─── Helpers ──────────────────────────────────────────────────────────────

    fn classify_status(&self, diag: &LibraryDiagnostics) -> ImplementationStatus {
        if !diag.library_exists {
            ImplementationStatus::Failed
        } else if diag.architecture_mismatch || !diag.missing_dependencies.is_empty() {
            ImplementationStatus::Failed
        } else if !diag.loading_errors.is_empty() || !diag.path_issues.is_empty() {
            ImplementationStatus::PartiallyWorking
        } else if diag.library_loadable {
            ImplementationStatus::Working
        } else {
            ImplementationStatus::Unknown
        }
    }

    fn generate_fix_steps(&self, diag: &LibraryDiagnostics) -> Vec<String> {
        let mut steps: Vec<String> = Vec::new();

        if !diag.library_exists {
            steps.push(format!(
                "Build the {} library: run the project's build script.",
                diag.implementation
            ));
        }
        if diag.architecture_mismatch {
            steps.push("Fix architecture mismatch: ensure the library targets x86_64 (64-bit).".to_string());
        }
        for dep in &diag.missing_dependencies {
            steps.push(format!("Install missing dependency: {}", dep));
        }
        for err in &diag.loading_errors {
            steps.push(format!("Resolve loading error: {}", err.error_message));
        }
        for path in &diag.path_issues {
            steps.push(format!("Fix path issue: {} — {}", path.path, path.resolution_suggestion));
        }
        if steps.is_empty() && diag.library_loadable {
            steps.push("No action required — implementation is working.".to_string());
        }
        steps
    }

    fn current_timestamp(&self) -> String {
        // Simple wall-clock timestamp without external crates
        use std::time::{SystemTime, UNIX_EPOCH};
        let secs = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
        format!("unix:{}", secs)
    }

    // ─── Rendering ────────────────────────────────────────────────────────────

    fn render_bug_report(
        &self,
        summaries: &[ImplementationBugSummary],
        critical_issues: &[String],
        fix_priority: &[String],
        timestamp: &str,
    ) -> String {
        let mut out = String::new();

        out.push_str("╔══════════════════════════════════════════════════════════════╗\n");
        out.push_str("║         FFI Implementation Bug Analysis Report               ║\n");
        out.push_str("╚══════════════════════════════════════════════════════════════╝\n");
        out.push_str(&format!("Generated: {}\n\n", timestamp));

        // Summary table
        let working = summaries.iter().filter(|s| s.status == ImplementationStatus::Working).count();
        let failed  = summaries.iter().filter(|s| s.status == ImplementationStatus::Failed).count();
        let partial = summaries.iter().filter(|s| s.status == ImplementationStatus::PartiallyWorking).count();
        out.push_str("── SUMMARY ─────────────────────────────────────────────────────\n");
        out.push_str(&format!("  Total implementations : {}\n", summaries.len()));
        out.push_str(&format!("  Working               : {}\n", working));
        out.push_str(&format!("  Failed                : {}\n", failed));
        out.push_str(&format!("  Partially working     : {}\n\n", partial));

        // Per-implementation details
        out.push_str("── PER-IMPLEMENTATION DETAILS ───────────────────────────────────\n");
        for s in summaries {
            let status_icon = match s.status {
                ImplementationStatus::Working          => "✓",
                ImplementationStatus::Failed           => "✗",
                ImplementationStatus::PartiallyWorking => "~",
                ImplementationStatus::Unknown          => "?",
            };
            out.push_str(&format!("  {} {} [{}]\n", status_icon, s.implementation, s.status));

            if !s.missing_dependencies.is_empty() {
                out.push_str(&format!(
                    "      Missing deps: {}\n",
                    s.missing_dependencies.join(", ")
                ));
            }
            if s.architecture_mismatch {
                out.push_str("      Architecture mismatch\n");
            }
            if !s.loading_errors.is_empty() {
                for err in &s.loading_errors {
                    out.push_str(&format!("      Error: {}\n", err.error_message));
                }
            }
            if !s.dll_issues.is_empty() {
                for issue in &s.dll_issues {
                    out.push_str(&format!("      DLL: {}\n", issue.description));
                }
            }
            if !s.fix_steps.is_empty() {
                out.push_str("      Fix steps:\n");
                for (i, step) in s.fix_steps.iter().enumerate() {
                    out.push_str(&format!("        {}. {}\n", i + 1, step));
                }
            }
        }

        // Critical issues
        if !critical_issues.is_empty() {
            out.push_str("\n── CRITICAL ISSUES ──────────────────────────────────────────────\n");
            for issue in critical_issues {
                out.push_str(&format!("  ⚠ {}\n", issue));
            }
        }

        // Fix priority
        if !fix_priority.is_empty() {
            out.push_str("\n── FIX PRIORITY LIST ────────────────────────────────────────────\n");
            for (i, impl_name) in fix_priority.iter().enumerate() {
                out.push_str(&format!("  {}. {}\n", i + 1, impl_name));
            }
        }

        out
    }

    fn render_performance_report_simple(
        &self,
        results: &[f64],
        entries: &[ImplementationPerformanceEntry],
        fallback_detections: &[String],
        timestamp: &str,
    ) -> String {
        let mut out = String::new();
        out.push_str("╔══════════════════════════════════════════════════════════════╗\n");
        out.push_str("║           FFI Performance Validation Report                  ║\n");
        out.push_str("╚══════════════════════════════════════════════════════════════╝\n");
        out.push_str(&format!("Generated: {}\n\n", timestamp));

        if results.is_empty() {
            out.push_str("No performance data provided.\n");
            return out;
        }

        let mean = results.iter().sum::<f64>() / results.len() as f64;
        let min  = results.iter().cloned().fold(f64::INFINITY, f64::min);
        let max  = results.iter().cloned().fold(f64::NEG_INFINITY, f64::max);

        out.push_str("── AGGREGATE STATISTICS ─────────────────────────────────────────\n");
        out.push_str(&format!("  Samples : {}\n", results.len()));
        out.push_str(&format!("  Mean    : {:.0} ns\n", mean));
        out.push_str(&format!("  Min     : {:.0} ns\n", min));
        out.push_str(&format!("  Max     : {:.0} ns\n\n", max));

        out.push_str("── RESULT TABLE ─────────────────────────────────────────────────\n");
        out.push_str("  #   Value (ns)     Ratio    Fallback?\n");
        out.push_str("  ─────────────────────────────────────\n");
        for entry in entries {
            let fb = if entry.fallback_suspected { "YES" } else { "no" };
            out.push_str(&format!(
                "  {:<4}{:<16.0}{:<9.2}{}\n",
                entry.implementation.trim_start_matches("impl_"),
                entry.performance_ratio * mean,
                entry.performance_ratio,
                fb
            ));
        }

        if !fallback_detections.is_empty() {
            out.push_str("\n── FALLBACK DETECTIONS ──────────────────────────────────────────\n");
            for det in fallback_detections {
                out.push_str(&format!("  ⚠ {}\n", det));
            }
        }
        out
    }

    fn render_performance_report_full(
        &self,
        entries: &[ImplementationPerformanceEntry],
        fallback_detections: &[String],
        perf_report: &PerformanceReport,
        timestamp: &str,
    ) -> String {
        let mut out = String::new();
        out.push_str("╔══════════════════════════════════════════════════════════════╗\n");
        out.push_str("║           FFI Performance Validation Report                  ║\n");
        out.push_str("╚══════════════════════════════════════════════════════════════╝\n");
        out.push_str(&format!("Generated: {}\n\n", timestamp));

        out.push_str("── SUMMARY ─────────────────────────────────────────────────────\n");
        out.push_str(&format!("  Total    : {}\n", entries.len()));
        out.push_str(&format!("  Passing  : {}\n", perf_report.passing_implementations.len()));
        out.push_str(&format!("  Failing  : {}\n", perf_report.failing_implementations.len()));
        out.push_str(&format!("  Suspected: {}\n", perf_report.suspected_fallbacks.len()));
        out.push_str(&format!(
            "  Avg speedup (passing): {:.1}%\n\n",
            perf_report.average_speedup_percentage
        ));

        out.push_str("── PERFORMANCE TABLE ────────────────────────────────────────────\n");
        out.push_str("  Implementation       Ratio   Speedup%  p-value  d     Fallback?\n");
        out.push_str("  ──────────────────────────────────────────────────────────────\n");
        for e in entries {
            let fb = if e.fallback_suspected { "YES" } else { "no" };
            out.push_str(&format!(
                "  {:<21}{:<8.2}{:<10.1}{:<9.4}{:<6.2}{}\n",
                e.implementation, e.performance_ratio, e.speedup_percentage,
                e.p_value, e.effect_size, fb
            ));
        }

        if !perf_report.passing_implementations.is_empty() {
            out.push_str("\n── CONFIRMED PASSING ────────────────────────────────────────────\n");
            for name in &perf_report.passing_implementations {
                out.push_str(&format!("  ✓ {}\n", name));
            }
        }

        if !fallback_detections.is_empty() {
            out.push_str("\n── FALLBACK DETECTIONS ──────────────────────────────────────────\n");
            for det in fallback_detections {
                out.push_str(&format!("  ⚠ {}\n", det));
            }
        }

        if !perf_report.suspected_fallbacks.is_empty() {
            out.push_str("\n── INVESTIGATION RECOMMENDED ────────────────────────────────────\n");
            for name in &perf_report.suspected_fallbacks {
                out.push_str(&format!(
                    "  → {}: performance resembles Python fallback — check library loading.\n",
                    name
                ));
            }
        }

        out
    }

    fn build_overall_summary(
        &self,
        bug: &BugAnalysisReport,
        perf: &PerformanceValidationReport,
        builds_applied: usize,
    ) -> String {
        format!(
            "Audit complete.\n\
             Bug analysis   : {}/{} implementations working, {} failed.\n\
             Fixes applied  : {} build scripts generated.\n\
             Performance    : {}/{} implementations passed baseline check.\n\
             Fallbacks      : {} suspected.\n\
             Average speedup: {:.1}%.",
            bug.working_count,
            bug.total_implementations,
            bug.failed_count,
            builds_applied,
            perf.passing_count,
            perf.total_implementations,
            perf.suspected_fallback_count,
            perf.average_speedup_percentage
        )
    }
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn make_working_diag(name: &str) -> LibraryDiagnostics {
        LibraryDiagnostics {
            implementation: name.to_string(),
            library_exists: true,
            library_loadable: true,
            loading_errors: vec![],
            missing_dependencies: vec![],
            architecture_mismatch: false,
            path_issues: vec![],
        }
    }

    fn make_failed_diag(name: &str) -> LibraryDiagnostics {
        LibraryDiagnostics {
            implementation: name.to_string(),
            library_exists: false,
            library_loadable: false,
            loading_errors: vec![LoadingError {
                error_code: Some(0xc0000135),
                error_message: "DLL not found".to_string(),
                error_type: LoadingErrorType::FileNotFound,
            }],
            missing_dependencies: vec!["libfoo.dll".to_string()],
            architecture_mismatch: false,
            path_issues: vec![],
        }
    }

    // ── Task 10.1 tests ──────────────────────────────────────────────────────

    #[test]
    fn test_bug_report_counts_are_correct() {
        let reporter = ComprehensiveAuditReporter::new();
        let diags = vec![
            make_working_diag("rust_ext"),
            make_failed_diag("go_ext"),
            make_working_diag("c_ext"),
        ];
        let report = reporter.generate_bug_analysis_report(&diags).unwrap();

        assert_eq!(report.total_implementations, 3);
        assert_eq!(report.working_count, 2);
        assert_eq!(report.failed_count, 1);
        assert_eq!(report.partial_count, 0);
    }

    #[test]
    fn test_bug_report_contains_implementation_names() {
        let reporter = ComprehensiveAuditReporter::new();
        let diags = vec![make_working_diag("rust_ext"), make_failed_diag("go_ext")];
        let report = reporter.generate_bug_analysis_report(&diags).unwrap();

        assert!(report.report_text.contains("rust_ext"));
        assert!(report.report_text.contains("go_ext"));
    }

    #[test]
    fn test_failed_impl_in_fix_priority() {
        let reporter = ComprehensiveAuditReporter::new();
        let diags = vec![make_failed_diag("broken_ext"), make_working_diag("good_ext")];
        let report = reporter.generate_bug_analysis_report(&diags).unwrap();

        assert!(report.fix_priority_list.contains(&"broken_ext".to_string()));
        assert!(!report.fix_priority_list.contains(&"good_ext".to_string()));
    }

    #[test]
    fn test_fix_steps_generated_for_failed_impl() {
        let reporter = ComprehensiveAuditReporter::new();
        let diags = vec![make_failed_diag("missing_ext")];
        let report = reporter.generate_bug_analysis_report(&diags).unwrap();

        let summary = &report.implementation_summaries[0];
        assert!(!summary.fix_steps.is_empty(), "Failed impl should have fix steps");
    }

    #[test]
    fn test_working_impl_has_no_action_step() {
        let reporter = ComprehensiveAuditReporter::new();
        let diags = vec![make_working_diag("rust_ext")];
        let report = reporter.generate_bug_analysis_report(&diags).unwrap();

        let summary = &report.implementation_summaries[0];
        assert!(
            summary.fix_steps.iter().any(|s| s.contains("No action required")),
            "Working impl should note no action required"
        );
    }

    #[test]
    fn test_architecture_mismatch_is_critical() {
        let reporter = ComprehensiveAuditReporter::new();
        let diag = LibraryDiagnostics {
            implementation: "arch_mismatch_ext".to_string(),
            library_exists: true,
            library_loadable: false,
            loading_errors: vec![],
            missing_dependencies: vec![],
            architecture_mismatch: true,
            path_issues: vec![],
        };
        let report = reporter.generate_bug_analysis_report(&[diag]).unwrap();

        assert!(!report.critical_issues.is_empty(), "Architecture mismatch should create a critical issue");
        assert!(report.critical_issues.iter().any(|i| i.contains("arch_mismatch_ext")));
    }

    #[test]
    fn test_empty_diagnostics_produces_valid_report() {
        let reporter = ComprehensiveAuditReporter::new();
        let report = reporter.generate_bug_analysis_report(&[]).unwrap();
        assert_eq!(report.total_implementations, 0);
        assert!(!report.report_text.is_empty());
    }

    // ── Task 10.2 tests ──────────────────────────────────────────────────────

    #[test]
    fn test_perf_report_empty_results() {
        let reporter = ComprehensiveAuditReporter::new();
        let report = reporter.generate_performance_validation_report(&[]).unwrap();
        assert_eq!(report.total_implementations, 0);
        assert!(!report.report_text.is_empty());
    }

    #[test]
    fn test_perf_report_flags_slow_results_as_fallback() {
        let reporter = ComprehensiveAuditReporter::new();
        // Values above 10_000_000 ns should be flagged as potential fallback
        let results = vec![500_000.0, 12_000_000.0, 600_000.0];
        let report = reporter.generate_performance_validation_report(&results).unwrap();

        assert!(!report.fallback_detections.is_empty(), "Slow result should be flagged");
        assert!(report.suspected_fallback_count > 0);
    }

    #[test]
    fn test_perf_report_from_comparison_result() {
        let reporter = ComprehensiveAuditReporter::new();
        let system = crate::fallback_prevention::FallbackPreventionSystem::new();

        let ffi_results: Vec<f64> = (0..10).map(|_| 500.0).collect();
        let python_baseline: Vec<f64> = (0..10).map(|_| 5000.0).collect();

        let cmp = system.compare_with_python_baseline("rust_ext", &ffi_results, &python_baseline).unwrap();
        let perf_report = system.generate_performance_report(&[cmp]).unwrap();
        let val_report = reporter.generate_performance_validation_report_from_comparison(&perf_report).unwrap();

        assert_eq!(val_report.total_implementations, 1);
        assert!(val_report.report_text.contains("rust_ext"));
    }

    #[test]
    fn test_perf_report_shows_ratio_table() {
        let reporter = ComprehensiveAuditReporter::new();
        let results = vec![1_000.0, 2_000.0, 3_000.0];
        let report = reporter.generate_performance_validation_report(&results).unwrap();
        // Report text should contain a table with Ratio column
        assert!(report.report_text.contains("Ratio") || report.report_text.contains("ratio") || report.report_text.contains("RESULT"),
            "Report should contain a ratio table");
    }

    // ── Combined report test ─────────────────────────────────────────────────

    #[test]
    fn test_comprehensive_report_combines_both() {
        let reporter = ComprehensiveAuditReporter::new();
        let diags = vec![make_working_diag("rust_ext"), make_failed_diag("go_ext")];
        let perf_results = vec![500_000.0, 12_000_000.0];

        let report = reporter.generate_comprehensive_report(&diags, &[], &perf_results).unwrap();

        assert!(report.report_text.contains("Bug Analysis"),
            "Comprehensive report should include bug analysis section");
        assert!(report.report_text.contains("Performance"),
            "Comprehensive report should include performance section");
        assert!(!report.overall_summary.is_empty());
    }
}
