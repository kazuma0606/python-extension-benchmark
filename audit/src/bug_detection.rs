//! Bug Detection Engine
//! 
//! This module provides functionality to detect and classify bugs
//! in existing FFI implementations.

use crate::error::{Result, PathAnalysisResult, DependencyAnalysisResult, ErrorClassificationResult};
use crate::types::*;
use pyo3::prelude::*;
use std::path::{Path, PathBuf};
use std::collections::HashMap;

#[cfg(target_os = "windows")]
use winapi::um::libloaderapi::{LoadLibraryA, GetProcAddress, FreeLibrary};
#[cfg(target_os = "windows")]
use winapi::um::errhandlingapi::GetLastError;
#[cfg(target_os = "windows")]
use winapi::shared::winerror;
#[cfg(target_os = "windows")]
use std::ffi::CString;

/// Bug Detection Engine
/// 
/// Detects and classifies bugs in existing FFI implementations
/// that cause fallback to pure Python implementations.
#[pyclass]
#[derive(Debug, Clone)]
pub struct BugDetectionEngine {
    /// Cache for analyzed implementations
    analysis_cache: HashMap<String, Vec<DLLIssue>>,
}

#[pymethods]
impl BugDetectionEngine {
    #[new]
    pub fn new() -> Self {
        Self {
            analysis_cache: HashMap::new(),
        }
    }
}

impl BugDetectionEngine {
    /// Detect DLL loading issues
    pub fn detect_dll_loading_issues(&self, ffi_impl: &str) -> Result<Vec<DLLIssue>> {
        let mut issues = Vec::new();
        
        // Get the expected library paths for this FFI implementation
        let library_paths = self.get_expected_library_paths(ffi_impl)?;
        
        for library_path in library_paths {
            // Check if library file exists
            if !Path::new(&library_path).exists() {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("Library file not found: {}", library_path),
                    affected_library: library_path.clone(),
                    resolution_steps: vec![
                        "Check if the library was built successfully".to_string(),
                        "Verify the build output directory".to_string(),
                        "Run the build script for this FFI implementation".to_string(),
                    ],
                });
                continue;
            }

            // Attempt to load the library and detect specific issues
            #[cfg(target_os = "windows")]
            {
                let loading_result = self.test_dll_loading(&library_path);
                if let Err(issue) = loading_result {
                    issues.push(issue);
                }
            }

            #[cfg(not(target_os = "windows"))]
            {
                // For non-Windows platforms, use dlopen-style loading
                let loading_result = self.test_so_loading(&library_path);
                if let Err(issue) = loading_result {
                    issues.push(issue);
                }
            }
        }

        Ok(issues)
    }

    /// Analyze path resolution problems
    pub fn analyze_path_resolution(&self, ffi_impl: &str) -> PathAnalysisResult {
        let mut paths_analyzed = Vec::new();
        let mut resolution_results = Vec::new();
        let mut recommendations = Vec::new();

        // Get expected paths for this implementation
        let expected_paths = match self.get_expected_library_paths(ffi_impl) {
            Ok(paths) => paths,
            Err(_) => {
                recommendations.push("Unable to determine expected library paths".to_string());
                return Ok(PathAnalysis {
                    implementation: ffi_impl.to_string(),
                    paths_analyzed,
                    resolution_results,
                    recommendations,
                });
            }
        };

        for path in expected_paths {
            paths_analyzed.push(path.clone());
            
            let path_obj = Path::new(&path);
            let mut result = PathResolutionResult {
                path: path.clone(),
                exists: path_obj.exists(),
                readable: false,
                absolute_path: None,
                issues: Vec::new(),
            };

            if result.exists {
                // Check if readable
                result.readable = path_obj.metadata().is_ok();
                
                // Get absolute path
                if let Ok(abs_path) = path_obj.canonicalize() {
                    result.absolute_path = Some(abs_path.to_string_lossy().to_string());
                }
            } else {
                result.issues.push("File does not exist".to_string());
                
                // Check parent directory
                if let Some(parent) = path_obj.parent() {
                    if !parent.exists() {
                        result.issues.push("Parent directory does not exist".to_string());
                        recommendations.push(format!("Create directory: {}", parent.display()));
                    }
                }

                // Check for common path issues
                if path.contains("\\") && cfg!(not(target_os = "windows")) {
                    result.issues.push("Windows-style path separators on non-Windows system".to_string());
                    recommendations.push("Use forward slashes for path separators".to_string());
                }

                if path.contains("/") && cfg!(target_os = "windows") {
                    result.issues.push("Unix-style path separators on Windows system".to_string());
                    recommendations.push("Use backslashes for path separators on Windows".to_string());
                }
            }

            resolution_results.push(result);
        }

        Ok(PathAnalysis {
            implementation: ffi_impl.to_string(),
            paths_analyzed,
            resolution_results,
            recommendations,
        })
    }

    /// Analyze dependency chain
    pub fn analyze_dependency_chain(&self, ffi_impl: &str) -> DependencyAnalysisResult {
        let mut dependencies_found = Vec::new();
        let mut dependencies_missing = Vec::new();
        let mut dependency_chain = Vec::new();

        // Get expected dependencies for this implementation
        let expected_deps = self.get_expected_dependencies(ffi_impl);
        
        for dep in expected_deps {
            dependency_chain.push(dep.clone());
            
            if self.check_dependency_available(&dep) {
                dependencies_found.push(dep);
            } else {
                dependencies_missing.push(dep);
            }
        }

        Ok(DependencyAnalysis {
            implementation: ffi_impl.to_string(),
            dependencies_found,
            dependencies_missing,
            dependency_chain,
        })
    }

    /// Classify runtime errors
    pub fn classify_runtime_errors(&self, errors: &[RuntimeError]) -> ErrorClassificationResult {
        let mut error_categories = HashMap::new();
        let mut critical_errors = Vec::new();
        let mut recommendations = Vec::new();

        for error in errors {
            // Classify error by type
            let category = self.classify_error_type(error);
            *error_categories.entry(category.clone()).or_insert(0) += 1;

            // Check if this is a critical error
            if self.is_critical_error(error) {
                critical_errors.push(error.clone());
            }

            // Generate recommendations based on error type
            let error_recommendations = self.generate_error_recommendations(error);
            recommendations.extend(error_recommendations);

            // Add Windows-specific error analysis
            if let Some(windows_analysis) = self.analyze_windows_specific_error(error) {
                recommendations.extend(windows_analysis);
            }
        }

        // Remove duplicate recommendations
        recommendations.sort();
        recommendations.dedup();

        Ok(ErrorClassification {
            total_errors: errors.len(),
            error_categories,
            critical_errors,
            recommendations,
        })
    }

    /// Get expected library paths for an FFI implementation
    fn get_expected_library_paths(&self, ffi_impl: &str) -> Result<Vec<String>> {
        let mut paths = Vec::new();
        
        match ffi_impl {
            "c_ext" => {
                paths.push("benchmark/c_ext/numeric.so".to_string());
                paths.push("benchmark/c_ext/memory.so".to_string());
                paths.push("benchmark/c_ext/parallel.so".to_string());
                #[cfg(target_os = "windows")]
                {
                    paths.push("benchmark/c_ext/numeric.pyd".to_string());
                    paths.push("benchmark/c_ext/memory.pyd".to_string());
                    paths.push("benchmark/c_ext/parallel.pyd".to_string());
                }
            },
            "cpp_ext" => {
                paths.push("benchmark/cpp_ext/numeric.so".to_string());
                paths.push("benchmark/cpp_ext/memory.so".to_string());
                paths.push("benchmark/cpp_ext/parallel.so".to_string());
                #[cfg(target_os = "windows")]
                {
                    paths.push("benchmark/cpp_ext/numeric.pyd".to_string());
                    paths.push("benchmark/cpp_ext/memory.pyd".to_string());
                    paths.push("benchmark/cpp_ext/parallel.pyd".to_string());
                }
            },
            "cython_ext" => {
                paths.push("benchmark/cython_ext/numeric.so".to_string());
                paths.push("benchmark/cython_ext/memory.so".to_string());
                paths.push("benchmark/cython_ext/parallel.so".to_string());
            },
            "rust_ext" => {
                paths.push("benchmark/rust_ext/target/release/librustfunctions.so".to_string());
                #[cfg(target_os = "windows")]
                {
                    paths.push("benchmark/rust_ext/target/release/rustfunctions.dll".to_string());
                }
            },
            "go_ext" => {
                paths.push("benchmark/go_ext/libgofunctions.so".to_string());
                #[cfg(target_os = "windows")]
                {
                    paths.push("benchmark/go_ext/libgofunctions.dll".to_string());
                }
            },
            "zig_ext" => {
                paths.push("benchmark/zig_ext/zigfunctions.so".to_string());
                #[cfg(target_os = "windows")]
                {
                    paths.push("benchmark/zig_ext/zigfunctions.dll".to_string());
                }
            },
            "nim_ext" => {
                paths.push("benchmark/nim_ext/libnimfunctions.so".to_string());
                #[cfg(target_os = "windows")]
                {
                    paths.push("benchmark/nim_ext/libnimfunctions.dll".to_string());
                }
            },
            "fortran_ext" => {
                paths.push("benchmark/fortran_ext/numeric.so".to_string());
                paths.push("benchmark/fortran_ext/memory.so".to_string());
                paths.push("benchmark/fortran_ext/parallel.so".to_string());
            },
            "julia_ext" => {
                // Julia extensions are typically loaded dynamically
                paths.push("benchmark/julia_ext/functions.jl".to_string());
            },
            "kotlin_ext" => {
                paths.push("benchmark/kotlin_ext/build/libs/functions.jar".to_string());
            },
            _ => {
                return Err(crate::error::AuditError::UnsupportedImplementation(ffi_impl.to_string()));
            }
        }

        Ok(paths)
    }

    /// Get expected dependencies for an FFI implementation
    fn get_expected_dependencies(&self, ffi_impl: &str) -> Vec<String> {
        match ffi_impl {
            "c_ext" | "cpp_ext" => vec![
                "gcc".to_string(),
                "python3-dev".to_string(),
            ],
            "cython_ext" => vec![
                "cython".to_string(),
                "python3-dev".to_string(),
                "gcc".to_string(),
            ],
            "rust_ext" => vec![
                "cargo".to_string(),
                "rustc".to_string(),
            ],
            "go_ext" => vec![
                "go".to_string(),
            ],
            "zig_ext" => vec![
                "zig".to_string(),
            ],
            "nim_ext" => vec![
                "nim".to_string(),
            ],
            "fortran_ext" => vec![
                "gfortran".to_string(),
                "f2py".to_string(),
            ],
            "julia_ext" => vec![
                "julia".to_string(),
            ],
            "kotlin_ext" => vec![
                "kotlin".to_string(),
                "gradle".to_string(),
            ],
            _ => vec![],
        }
    }

    /// Check if a dependency is available
    fn check_dependency_available(&self, dep: &str) -> bool {
        // Try to find the dependency in PATH
        if let Ok(path_var) = std::env::var("PATH") {
            for path in std::env::split_paths(&path_var) {
                let dep_path = path.join(dep);
                if dep_path.exists() {
                    return true;
                }
                
                // Also check with .exe extension on Windows
                #[cfg(target_os = "windows")]
                {
                    let dep_path_exe = path.join(format!("{}.exe", dep));
                    if dep_path_exe.exists() {
                        return true;
                    }
                }
            }
        }
        
        false
    }

    /// Test DLL loading on Windows
    #[cfg(target_os = "windows")]
    fn test_dll_loading(&self, library_path: &str) -> std::result::Result<(), DLLIssue> {
        let c_path = match CString::new(library_path) {
            Ok(path) => path,
            Err(_) => {
                return Err(DLLIssue {
                    issue_type: DLLIssueType::PathResolutionFailure,
                    error_code: None,
                    description: "Invalid path string".to_string(),
                    affected_library: library_path.to_string(),
                    resolution_steps: vec!["Check for null bytes in path".to_string()],
                });
            }
        };

        unsafe {
            let handle = LoadLibraryA(c_path.as_ptr());
            if handle.is_null() {
                let error_code = GetLastError();
                let (issue_type, description, resolution_steps) = match error_code {
                    126 => (
                        DLLIssueType::DependencyMissing,
                        "The specified module could not be found".to_string(),
                        vec![
                            "Check if all required DLLs are in the same directory".to_string(),
                            "Verify Visual C++ Redistributable is installed".to_string(),
                            "Use Dependency Walker to identify missing dependencies".to_string(),
                        ]
                    ),
                    193 => (
                        DLLIssueType::ArchitectureMismatch,
                        "The specified module is not a valid Win32 application".to_string(),
                        vec![
                            "Check if DLL architecture matches Python architecture (32-bit vs 64-bit)".to_string(),
                            "Rebuild the library for the correct architecture".to_string(),
                        ]
                    ),
                    _ => (
                        DLLIssueType::LoadFailure,
                        format!("LoadLibrary failed with error code {}", error_code),
                        vec![
                            "Check Windows Event Log for detailed error information".to_string(),
                            "Verify file permissions".to_string(),
                            "Try running as administrator".to_string(),
                        ]
                    ),
                };

                return Err(DLLIssue {
                    issue_type,
                    error_code: Some(error_code),
                    description,
                    affected_library: library_path.to_string(),
                    resolution_steps,
                });
            } else {
                // Successfully loaded, clean up
                FreeLibrary(handle);
            }
        }

        Ok(())
    }

    /// Test shared library loading on Unix-like systems
    #[cfg(not(target_os = "windows"))]
    fn test_so_loading(&self, library_path: &str) -> std::result::Result<(), DLLIssue> {
        // Use dlopen to test loading
        use std::ffi::CString;
        
        let c_path = match CString::new(library_path) {
            Ok(path) => path,
            Err(_) => {
                return Err(DLLIssue {
                    issue_type: DLLIssueType::PathResolutionFailure,
                    error_code: None,
                    description: "Invalid path string".to_string(),
                    affected_library: library_path.to_string(),
                    resolution_steps: vec!["Check for null bytes in path".to_string()],
                });
            }
        };

        unsafe {
            let handle = libc::dlopen(c_path.as_ptr(), libc::RTLD_LAZY);
            if handle.is_null() {
                let error_msg = libc::dlerror();
                let error_str = if error_msg.is_null() {
                    "Unknown dlopen error".to_string()
                } else {
                    std::ffi::CStr::from_ptr(error_msg).to_string_lossy().to_string()
                };

                let (issue_type, resolution_steps) = if error_str.contains("No such file") {
                    (DLLIssueType::LoadFailure, vec![
                        "Check if the library file exists".to_string(),
                        "Verify the library path is correct".to_string(),
                    ])
                } else if error_str.contains("undefined symbol") {
                    (DLLIssueType::SymbolNotFound, vec![
                        "Check if all required symbols are exported".to_string(),
                        "Verify library was compiled with correct flags".to_string(),
                    ])
                } else {
                    (DLLIssueType::LoadFailure, vec![
                        "Check library dependencies with ldd".to_string(),
                        "Verify library permissions".to_string(),
                    ])
                };

                return Err(DLLIssue {
                    issue_type,
                    error_code: None,
                    description: error_str,
                    affected_library: library_path.to_string(),
                    resolution_steps,
                });
            } else {
                // Successfully loaded, clean up
                libc::dlclose(handle);
            }
        }

        Ok(())
    }

    /// Classify error type
    fn classify_error_type(&self, error: &RuntimeError) -> String {
        match error.error_type.as_str() {
            "ImportError" => "Import/Loading Error".to_string(),
            "AttributeError" => "Symbol/Function Not Found".to_string(),
            "OSError" => "Operating System Error".to_string(),
            "ValueError" => "Value/Parameter Error".to_string(),
            "TypeError" => "Type Mismatch Error".to_string(),
            _ => "Other Error".to_string(),
        }
    }

    /// Check if error is critical
    fn is_critical_error(&self, error: &RuntimeError) -> bool {
        matches!(error.error_type.as_str(), "ImportError" | "OSError")
    }

    /// Generate recommendations for an error
    fn generate_error_recommendations(&self, error: &RuntimeError) -> Vec<String> {
        match error.error_type.as_str() {
            "ImportError" => vec![
                "Check if the library was built successfully".to_string(),
                "Verify library is in the correct location".to_string(),
                "Check for missing dependencies".to_string(),
            ],
            "AttributeError" => vec![
                "Verify function/symbol is exported from the library".to_string(),
                "Check function name spelling and case".to_string(),
            ],
            "OSError" => vec![
                "Check file permissions".to_string(),
                "Verify system dependencies are installed".to_string(),
            ],
            _ => vec![
                "Check error message for specific details".to_string(),
            ],
        }
    }

    /// Analyze Windows-specific error patterns
    fn analyze_windows_specific_error(&self, error: &RuntimeError) -> Option<Vec<String>> {
        let error_msg = &error.error_message.to_lowercase();
        let mut recommendations = Vec::new();

        // Windows DLL loading errors
        if error_msg.contains("dll") || error_msg.contains("library") {
            if error_msg.contains("not found") || error_msg.contains("cannot find") {
                recommendations.extend(vec![
                    "Check if Visual C++ Redistributable is installed".to_string(),
                    "Verify DLL is in the same directory as the executable".to_string(),
                    "Add library directory to PATH environment variable".to_string(),
                ]);
            }
            
            if error_msg.contains("access") || error_msg.contains("permission") {
                recommendations.extend(vec![
                    "Run as administrator".to_string(),
                    "Check antivirus software blocking the DLL".to_string(),
                    "Verify file permissions on the library".to_string(),
                ]);
            }
        }

        // Architecture mismatch errors (can occur without DLL/library keywords)
        if error_msg.contains("architecture") || error_msg.contains("32") || error_msg.contains("64") || 
           error_msg.contains("mismatch") {
            recommendations.extend(vec![
                "Ensure DLL architecture matches Python architecture".to_string(),
                "Rebuild library for correct target architecture".to_string(),
                "Check if running 32-bit Python with 64-bit library or vice versa".to_string(),
            ]);
        }

        // Windows path-related errors
        if error_msg.contains("path") || error_msg.contains("directory") {
            if error_msg.contains("too long") || error_msg.contains("260") {
                recommendations.extend(vec![
                    "Enable long path support in Windows".to_string(),
                    "Use shorter file paths".to_string(),
                    "Move project to a directory with shorter path".to_string(),
                ]);
            }
            
            if error_msg.contains("invalid") || error_msg.contains("illegal") {
                recommendations.extend(vec![
                    "Remove invalid characters from path (< > : \" | ? *)".to_string(),
                    "Use forward slashes instead of backslashes".to_string(),
                    "Avoid spaces in directory names".to_string(),
                ]);
            }
        }

        // Windows registry and system errors
        if error_msg.contains("registry") || error_msg.contains("system") {
            recommendations.extend(vec![
                "Check Windows registry for corrupted entries".to_string(),
                "Run Windows System File Checker (sfc /scannow)".to_string(),
                "Reinstall affected software components".to_string(),
            ]);
        }

        // Windows service and process errors
        if error_msg.contains("service") || error_msg.contains("process") {
            recommendations.extend(vec![
                "Check if required Windows services are running".to_string(),
                "Verify process has sufficient privileges".to_string(),
                "Check for conflicting processes or services".to_string(),
            ]);
        }

        // Windows firewall and security errors
        if error_msg.contains("firewall") || error_msg.contains("security") || error_msg.contains("blocked") {
            recommendations.extend(vec![
                "Add exception to Windows Firewall".to_string(),
                "Check Windows Defender exclusions".to_string(),
                "Verify User Account Control (UAC) settings".to_string(),
            ]);
        }

        if recommendations.is_empty() {
            None
        } else {
            Some(recommendations)
        }
    }

    /// Classify error by severity and Windows-specific patterns
    fn classify_error_severity(&self, error: &RuntimeError) -> ErrorSeverity {
        let error_msg = &error.error_message.to_lowercase();
        
        // Critical errors that prevent system operation
        if error.error_type == "ImportError" || 
           error.error_type == "OSError" ||
           error_msg.contains("fatal") ||
           error_msg.contains("critical") ||
           error_msg.contains("system") {
            return ErrorSeverity::Critical;
        }
        
        // High priority errors that affect functionality
        if error.error_type == "AttributeError" ||
           error_msg.contains("dll") ||
           error_msg.contains("library") ||
           error_msg.contains("access denied") {
            return ErrorSeverity::High;
        }
        
        // Medium priority errors
        if error.error_type == "ValueError" ||
           error.error_type == "TypeError" ||
           error_msg.contains("warning") {
            return ErrorSeverity::Medium;
        }
        
        // Default to low priority
        ErrorSeverity::Low
    }

    /// Generate detailed Windows error code analysis
    #[cfg(target_os = "windows")]
    fn analyze_windows_error_code(&self, error_code: u32) -> Vec<String> {
        use winapi::shared::winerror::*;
        
        match error_code {
            ERROR_FILE_NOT_FOUND => vec![
                "File not found - check if the library file exists".to_string(),
                "Verify the file path is correct".to_string(),
                "Check if the file was moved or deleted".to_string(),
            ],
            ERROR_ACCESS_DENIED => vec![
                "Access denied - run as administrator".to_string(),
                "Check file permissions".to_string(),
                "Verify antivirus is not blocking the file".to_string(),
            ],
            ERROR_BAD_EXE_FORMAT => vec![
                "Invalid executable format - architecture mismatch".to_string(),
                "Ensure library matches Python architecture (32/64-bit)".to_string(),
                "Rebuild library for correct target platform".to_string(),
            ],
            ERROR_MOD_NOT_FOUND => vec![
                "Module not found - missing dependencies".to_string(),
                "Install Visual C++ Redistributable".to_string(),
                "Check for missing DLL dependencies".to_string(),
            ],
            ERROR_INVALID_PARAMETER => vec![
                "Invalid parameter - check function arguments".to_string(),
                "Verify calling convention matches".to_string(),
                "Check parameter types and order".to_string(),
            ],
            ERROR_NOT_ENOUGH_MEMORY => vec![
                "Insufficient memory - close other applications".to_string(),
                "Increase virtual memory".to_string(),
                "Check for memory leaks".to_string(),
            ],
            _ => vec![
                format!("Windows error code {} - check Windows documentation", error_code),
                "Use Windows Event Viewer for detailed error information".to_string(),
            ],
        }
    }

    #[cfg(not(target_os = "windows"))]
    fn analyze_windows_error_code(&self, error_code: u32) -> Vec<String> {
        vec![
            format!("Windows error code {} (not running on Windows)", error_code),
            "This error analysis is only available on Windows systems".to_string(),
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::*;

    #[test]
    fn test_bug_detection_engine_creation() {
        let engine = BugDetectionEngine::new();
        assert!(engine.analysis_cache.is_empty());
    }

    #[test]
    fn test_detect_dll_loading_issues_unsupported_impl() {
        let engine = BugDetectionEngine::new();
        let result = engine.detect_dll_loading_issues("unsupported_impl");
        assert!(result.is_err());
    }

    #[test]
    fn test_detect_dll_loading_issues_c_ext() {
        let engine = BugDetectionEngine::new();
        let result = engine.detect_dll_loading_issues("c_ext");
        assert!(result.is_ok());
        let issues = result.unwrap();
        // Should detect that libraries don't exist (since we're not in a built environment)
        assert!(!issues.is_empty());
    }

    #[test]
    fn test_analyze_path_resolution() {
        let engine = BugDetectionEngine::new();
        let result = engine.analyze_path_resolution("c_ext");
        assert!(result.is_ok());
        let analysis = result.unwrap();
        assert_eq!(analysis.implementation, "c_ext");
        assert!(!analysis.paths_analyzed.is_empty());
    }

    #[test]
    fn test_analyze_dependency_chain() {
        let engine = BugDetectionEngine::new();
        let result = engine.analyze_dependency_chain("c_ext");
        assert!(result.is_ok());
        let analysis = result.unwrap();
        assert_eq!(analysis.implementation, "c_ext");
        assert!(!analysis.dependency_chain.is_empty());
    }

    #[test]
    fn test_classify_runtime_errors() {
        let engine = BugDetectionEngine::new();
        let errors = vec![
            RuntimeError {
                error_type: "ImportError".to_string(),
                error_message: "No module named 'test'".to_string(),
                context: "Loading test module".to_string(),
                severity: ErrorSeverity::Critical,
            },
            RuntimeError {
                error_type: "AttributeError".to_string(),
                error_message: "Function not found".to_string(),
                context: "Calling function".to_string(),
                severity: ErrorSeverity::High,
            },
        ];

        let result = engine.classify_runtime_errors(&errors);
        assert!(result.is_ok());
        let classification = result.unwrap();
        assert_eq!(classification.total_errors, 2);
        assert!(!classification.error_categories.is_empty());
        assert!(!classification.critical_errors.is_empty());
    }

    #[test]
    fn test_windows_specific_error_analysis() {
        let engine = BugDetectionEngine::new();
        
        // Test DLL loading error
        let dll_error = RuntimeError {
            error_type: "ImportError".to_string(),
            error_message: "DLL not found: test.dll".to_string(),
            context: "Loading DLL".to_string(),
            severity: ErrorSeverity::Critical,
        };
        
        let recommendations = engine.analyze_windows_specific_error(&dll_error);
        println!("DLL error recommendations: {:?}", recommendations);
        assert!(recommendations.is_some());
        let recs = recommendations.unwrap();
        assert!(recs.iter().any(|r| r.contains("Visual C++ Redistributable")));
        
        // Test path error
        let path_error = RuntimeError {
            error_type: "OSError".to_string(),
            error_message: "Path too long: exceeds 260 characters".to_string(),
            context: "File operation".to_string(),
            severity: ErrorSeverity::High,
        };
        
        let recommendations = engine.analyze_windows_specific_error(&path_error);
        println!("Path error recommendations: {:?}", recommendations);
        assert!(recommendations.is_some());
        let recs = recommendations.unwrap();
        assert!(recs.iter().any(|r| r.contains("long path support")));
        
        // Test architecture error
        let arch_error = RuntimeError {
            error_type: "OSError".to_string(),
            error_message: "Architecture mismatch: 32-bit vs 64-bit".to_string(),
            context: "Library loading".to_string(),
            severity: ErrorSeverity::Critical,
        };
        
        let recommendations = engine.analyze_windows_specific_error(&arch_error);
        println!("Architecture error recommendations: {:?}", recommendations);
        assert!(recommendations.is_some());
        let recs = recommendations.unwrap();
        assert!(recs.iter().any(|r| r.contains("architecture matches")));
    }

    #[test]
    fn test_error_severity_classification() {
        let engine = BugDetectionEngine::new();
        
        // Test critical error
        let critical_error = RuntimeError {
            error_type: "ImportError".to_string(),
            error_message: "Fatal error loading library".to_string(),
            context: "System initialization".to_string(),
            severity: ErrorSeverity::Critical,
        };
        
        let severity = engine.classify_error_severity(&critical_error);
        assert!(matches!(severity, ErrorSeverity::Critical));
        
        // Test high priority error
        let high_error = RuntimeError {
            error_type: "AttributeError".to_string(),
            error_message: "DLL function not found".to_string(),
            context: "Function call".to_string(),
            severity: ErrorSeverity::High,
        };
        
        let severity = engine.classify_error_severity(&high_error);
        assert!(matches!(severity, ErrorSeverity::High));
        
        // Test medium priority error
        let medium_error = RuntimeError {
            error_type: "ValueError".to_string(),
            error_message: "Invalid parameter value".to_string(),
            context: "Parameter validation".to_string(),
            severity: ErrorSeverity::Medium,
        };
        
        let severity = engine.classify_error_severity(&medium_error);
        assert!(matches!(severity, ErrorSeverity::Medium));
    }

    #[cfg(target_os = "windows")]
    #[test]
    fn test_windows_error_code_analysis() {
        let engine = BugDetectionEngine::new();
        
        // Test file not found error
        let recommendations = engine.analyze_windows_error_code(2); // ERROR_FILE_NOT_FOUND
        assert!(!recommendations.is_empty());
        assert!(recommendations.iter().any(|r| r.contains("File not found")));
        
        // Test access denied error
        let recommendations = engine.analyze_windows_error_code(5); // ERROR_ACCESS_DENIED
        assert!(!recommendations.is_empty());
        assert!(recommendations.iter().any(|r| r.contains("Access denied")));
        
        // Test bad exe format error
        let recommendations = engine.analyze_windows_error_code(193); // ERROR_BAD_EXE_FORMAT
        assert!(!recommendations.is_empty());
        assert!(recommendations.iter().any(|r| r.contains("architecture mismatch")));
    }

    #[test]
    fn test_get_expected_library_paths() {
        let engine = BugDetectionEngine::new();
        
        let c_paths = engine.get_expected_library_paths("c_ext").unwrap();
        assert!(!c_paths.is_empty());
        assert!(c_paths.iter().any(|p| p.contains("numeric")));
        
        let rust_paths = engine.get_expected_library_paths("rust_ext").unwrap();
        assert!(!rust_paths.is_empty());
        assert!(rust_paths.iter().any(|p| p.contains("rust")));
    }

    #[test]
    fn test_get_expected_dependencies() {
        let engine = BugDetectionEngine::new();
        
        let c_deps = engine.get_expected_dependencies("c_ext");
        assert!(!c_deps.is_empty());
        assert!(c_deps.contains(&"gcc".to_string()));
        
        let rust_deps = engine.get_expected_dependencies("rust_ext");
        assert!(!rust_deps.is_empty());
        assert!(rust_deps.contains(&"cargo".to_string()));
    }

    // Property-based test for Windows problem complete diagnosis
    // Feature: windows-ffi-audit, Property 12: Windows問題完全診断
    #[test]
    fn test_windows_problem_complete_diagnosis() {
        let engine = BugDetectionEngine::new();
        let test_impls = vec!["c_ext", "cpp_ext", "rust_ext", "go_ext"];
        
        for ffi_impl in test_impls {
            // Test DLL loading issue detection
            let dll_issues = engine.detect_dll_loading_issues(ffi_impl);
            assert!(dll_issues.is_ok());
            
            // Test path resolution analysis
            let path_analysis = engine.analyze_path_resolution(ffi_impl);
            assert!(path_analysis.is_ok());
            let analysis = path_analysis.unwrap();
            assert_eq!(analysis.implementation, ffi_impl);
            
            // Test dependency chain analysis
            let dep_analysis = engine.analyze_dependency_chain(ffi_impl);
            assert!(dep_analysis.is_ok());
            let deps = dep_analysis.unwrap();
            assert_eq!(deps.implementation, ffi_impl);
        }
    }

    // Comprehensive property-based test for Windows problem complete diagnosis
    // Feature: windows-ffi-audit, Property 12: Windows問題完全診断
    #[cfg(test)]
    mod property_tests {
        use super::*;
        use proptest::prelude::*;

        proptest! {
            #![proptest_config(ProptestConfig::with_cases(100))]

            #[test]
            fn property_windows_problem_complete_diagnosis(
                ffi_impl in prop::sample::select(vec![
                    "c_ext", "cpp_ext", "cython_ext", "rust_ext", "go_ext", 
                    "zig_ext", "nim_ext", "fortran_ext", "julia_ext", "kotlin_ext"
                ])
            ) {
                let engine = BugDetectionEngine::new();
                
                // Property 1: DLL loading issue detection must always succeed and provide specific information
                let dll_issues_result = engine.detect_dll_loading_issues(&ffi_impl);
                prop_assert!(dll_issues_result.is_ok(), "DLL loading issue detection must always succeed");
                
                let dll_issues = dll_issues_result.unwrap();
                
                // Property 2: Each DLL issue must have specific error information
                for issue in &dll_issues {
                    prop_assert!(!issue.description.is_empty(), "DLL issue description must not be empty");
                    prop_assert!(!issue.affected_library.is_empty(), "Affected library must be specified");
                    prop_assert!(!issue.resolution_steps.is_empty(), "Resolution steps must be provided");
                    
                    // Property 3: Issue types must be valid
                    match issue.issue_type {
                        DLLIssueType::LoadFailure |
                        DLLIssueType::SymbolNotFound |
                        DLLIssueType::ArchitectureMismatch |
                        DLLIssueType::DependencyMissing |
                        DLLIssueType::PathResolutionFailure => {
                            // Valid issue type
                        }
                        _ => prop_assert!(false, "Invalid DLL issue type"),
                    }
                }
                
                // Property 4: Path resolution analysis must always succeed
                let path_analysis_result = engine.analyze_path_resolution(&ffi_impl);
                prop_assert!(path_analysis_result.is_ok(), "Path resolution analysis must always succeed");
                
                let path_analysis = path_analysis_result.unwrap();
                prop_assert_eq!(path_analysis.implementation, ffi_impl, "Implementation name must match");
                prop_assert!(!path_analysis.paths_analyzed.is_empty(), "Must analyze at least one path");
                
                // Property 5: Each path resolution result must be complete
                for result in &path_analysis.resolution_results {
                    prop_assert!(!result.path.is_empty(), "Path must not be empty");
                    
                    if !result.exists {
                        prop_assert!(!result.issues.is_empty(), "Non-existent paths must have issues reported");
                    }
                }
                
                // Property 6: Dependency chain analysis must always succeed
                let dep_analysis_result = engine.analyze_dependency_chain(&ffi_impl);
                prop_assert!(dep_analysis_result.is_ok(), "Dependency chain analysis must always succeed");
                
                let dep_analysis = dep_analysis_result.unwrap();
                prop_assert_eq!(dep_analysis.implementation, ffi_impl, "Implementation name must match");
                
                // Property 7: Dependencies must be categorized correctly
                let total_deps = dep_analysis.dependencies_found.len() + dep_analysis.dependencies_missing.len();
                prop_assert_eq!(total_deps, dep_analysis.dependency_chain.len(), 
                    "All dependencies must be categorized as found or missing");
                
                // Property 8: No dependency should appear in both found and missing lists
                for found_dep in &dep_analysis.dependencies_found {
                    prop_assert!(!dep_analysis.dependencies_missing.contains(found_dep),
                        "Dependency cannot be both found and missing");
                }
                
                // Property 9: Runtime error classification must handle all error types
                let test_errors = vec![
                    RuntimeError {
                        error_type: "ImportError".to_string(),
                        error_message: "Test import error".to_string(),
                        context: "Test context".to_string(),
                        severity: ErrorSeverity::Critical,
                    },
                    RuntimeError {
                        error_type: "OSError".to_string(),
                        error_message: "Test OS error".to_string(),
                        context: "Test context".to_string(),
                        severity: ErrorSeverity::High,
                    },
                ];
                
                let classification_result = engine.classify_runtime_errors(&test_errors);
                prop_assert!(classification_result.is_ok(), "Runtime error classification must always succeed");
                
                let classification = classification_result.unwrap();
                prop_assert_eq!(classification.total_errors, test_errors.len(), "Total error count must match");
                prop_assert!(!classification.error_categories.is_empty(), "Error categories must be populated");
                prop_assert!(!classification.recommendations.is_empty(), "Recommendations must be provided");
                
                // Property 10: Critical errors must be identified
                let critical_count = classification.critical_errors.len();
                let expected_critical = test_errors.iter()
                    .filter(|e| matches!(e.error_type.as_str(), "ImportError" | "OSError"))
                    .count();
                prop_assert_eq!(critical_count, expected_critical, "Critical errors must be correctly identified");
            }

            #[test]
            fn property_error_classification_consistency(
                error_types in prop::collection::vec(
                    prop::sample::select(vec![
                        "ImportError", "AttributeError", "OSError", "ValueError", "TypeError", "RuntimeError"
                    ]), 
                    1..10
                )
            ) {
                let engine = BugDetectionEngine::new();
                
                let errors: Vec<RuntimeError> = error_types.into_iter().enumerate().map(|(i, error_type)| {
                    RuntimeError {
                        error_type: error_type.to_string(),
                        error_message: format!("Test error {}", i),
                        context: format!("Test context {}", i),
                        severity: if error_type == "ImportError" || error_type == "OSError" {
                            ErrorSeverity::Critical
                        } else {
                            ErrorSeverity::Medium
                        },
                    }
                }).collect();
                
                let result = engine.classify_runtime_errors(&errors);
                prop_assert!(result.is_ok(), "Error classification must always succeed");
                
                let classification = result.unwrap();
                
                // Property: Total errors must match input
                prop_assert_eq!(classification.total_errors, errors.len());
                
                // Property: All error categories must have positive counts
                for (_, count) in &classification.error_categories {
                    prop_assert!(*count > 0, "Error category counts must be positive");
                }
                
                // Property: Sum of category counts must equal total errors
                let category_sum: usize = classification.error_categories.values().sum();
                prop_assert_eq!(category_sum, errors.len(), "Category counts must sum to total errors");
                
                // Property: Critical errors must be subset of total errors
                prop_assert!(classification.critical_errors.len() <= errors.len(), 
                    "Critical errors cannot exceed total errors");
            }

            #[test]
            fn property_path_analysis_deterministic(
                ffi_impl in prop::sample::select(vec!["c_ext", "cpp_ext", "rust_ext"])
            ) {
                let engine = BugDetectionEngine::new();
                
                // Run analysis twice
                let result1 = engine.analyze_path_resolution(&ffi_impl);
                let result2 = engine.analyze_path_resolution(&ffi_impl);
                
                prop_assert!(result1.is_ok() && result2.is_ok(), "Path analysis must be deterministic");
                
                let analysis1 = result1.unwrap();
                let analysis2 = result2.unwrap();
                
                // Property: Results must be identical
                prop_assert_eq!(analysis1.implementation, analysis2.implementation);
                prop_assert_eq!(analysis1.paths_analyzed, analysis2.paths_analyzed);
                prop_assert_eq!(analysis1.resolution_results.len(), analysis2.resolution_results.len());
                
                // Property: Each path result must be identical
                for (r1, r2) in analysis1.resolution_results.iter().zip(analysis2.resolution_results.iter()) {
                    prop_assert_eq!(&r1.path, &r2.path);
                    prop_assert_eq!(r1.exists, r2.exists);
                    prop_assert_eq!(r1.readable, r2.readable);
                }
            }
        }
    }
}