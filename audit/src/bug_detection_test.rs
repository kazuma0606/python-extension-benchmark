//! Tests for the Bug Detection Engine

#[cfg(test)]
mod tests {
    use crate::bug_detection::BugDetectionEngine;
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
    #[cfg(feature = "proptest")]
    use proptest::prelude::*;

    #[cfg(feature = "proptest")]
    proptest! {
        #[test]
        fn property_windows_problem_complete_diagnosis(
            ffi_impl in prop::sample::select(vec!["c_ext", "cpp_ext", "rust_ext", "go_ext"])
        ) {
            let engine = BugDetectionEngine::new();
            
            // Test DLL loading issue detection
            let dll_issues = engine.detect_dll_loading_issues(&ffi_impl);
            prop_assert!(dll_issues.is_ok());
            
            // Test path resolution analysis
            let path_analysis = engine.analyze_path_resolution(&ffi_impl);
            prop_assert!(path_analysis.is_ok());
            let analysis = path_analysis.unwrap();
            prop_assert_eq!(analysis.implementation, ffi_impl);
            
            // Test dependency chain analysis
            let dep_analysis = engine.analyze_dependency_chain(&ffi_impl);
            prop_assert!(dep_analysis.is_ok());
            let deps = dep_analysis.unwrap();
            prop_assert_eq!(deps.implementation, ffi_impl);
        }

        // Property-based test for language-specific bug identification
        // Feature: windows-ffi-audit, Property 9: 言語固有バグ特定
        #[test]
        fn property_language_specific_bug_identification(
            ffi_impl in prop::sample::select(vec![
                "c_ext", "cpp_ext", "cython_ext", "rust_ext", "go_ext", 
                "zig_ext", "nim_ext", "fortran_ext", "julia_ext", "kotlin_ext"
            ])
        ) {
            let engine = BugDetectionEngine::new();
            
            // Property: For any supported language, language-specific FFI implementation bugs 
            // (compilation issues, linking issues, ABI mismatches) must be identified
            
            // 1. DLL loading issues must be detected and categorized by language-specific patterns
            let dll_issues_result = engine.detect_dll_loading_issues(&ffi_impl);
            prop_assert!(dll_issues_result.is_ok(), "DLL loading issue detection must succeed for {}", ffi_impl);
            
            let dll_issues = dll_issues_result.unwrap();
            
            // 2. Each detected issue must have language-specific characteristics
            for issue in &dll_issues {
                prop_assert!(!issue.description.is_empty(), "Issue description must not be empty");
                prop_assert!(!issue.affected_library.is_empty(), "Affected library must be specified");
                prop_assert!(!issue.resolution_steps.is_empty(), "Resolution steps must be provided");
                
                // 3. Issue types must be appropriate for the language
                match ffi_impl {
                    "c_ext" | "cpp_ext" => {
                        // C/C++ specific issues: compilation, linking, symbol export
                        if issue.issue_type == DLLIssueType::LoadFailure {
                            prop_assert!(
                                issue.description.contains("library") || 
                                issue.description.contains("not found") ||
                                issue.description.contains("compilation"),
                                "C/C++ issues should relate to compilation or library loading"
                            );
                        }
                    },
                    "cython_ext" => {
                        // Cython specific issues: compilation, Python C API
                        if issue.issue_type == DLLIssueType::LoadFailure {
                            prop_assert!(
                                issue.description.contains("cython") || 
                                issue.description.contains("compilation") ||
                                issue.description.contains("Python"),
                                "Cython issues should relate to Cython compilation or Python API"
                            );
                        }
                    },
                    "rust_ext" => {
                        // Rust specific issues: cargo build, target architecture
                        if issue.issue_type == DLLIssueType::LoadFailure {
                            prop_assert!(
                                issue.description.contains("rust") || 
                                issue.description.contains("cargo") ||
                                issue.description.contains("target"),
                                "Rust issues should relate to cargo build or target configuration"
                            );
                        }
                    },
                    "go_ext" => {
                        // Go specific issues: CGO, shared library creation
                        if issue.issue_type == DLLIssueType::LoadFailure {
                            prop_assert!(
                                issue.description.contains("go") || 
                                issue.description.contains("cgo") ||
                                issue.description.contains("shared"),
                                "Go issues should relate to CGO or shared library creation"
                            );
                        }
                    },
                    "fortran_ext" => {
                        // Fortran specific issues: f2py, gfortran
                        if issue.issue_type == DLLIssueType::LoadFailure {
                            prop_assert!(
                                issue.description.contains("fortran") || 
                                issue.description.contains("f2py") ||
                                issue.description.contains("gfortran"),
                                "Fortran issues should relate to f2py or gfortran"
                            );
                        }
                    },
                    _ => {
                        // Modern languages (Zig, Nim, Julia, Kotlin) - general FFI issues
                        prop_assert!(
                            !issue.description.is_empty(),
                            "Modern language issues must have descriptive error messages"
                        );
                    }
                }
            }
            
            // 4. Path analysis must identify language-specific path patterns
            let path_analysis_result = engine.analyze_path_resolution(&ffi_impl);
            prop_assert!(path_analysis_result.is_ok(), "Path analysis must succeed for {}", ffi_impl);
            
            let path_analysis = path_analysis_result.unwrap();
            prop_assert_eq!(path_analysis.implementation, ffi_impl);
            prop_assert!(!path_analysis.paths_analyzed.is_empty(), "Must analyze language-specific paths");
            
            // 5. Verify language-specific path patterns
            let expected_extensions = match ffi_impl {
                "c_ext" | "cpp_ext" | "cython_ext" | "fortran_ext" => {
                    if cfg!(target_os = "windows") { vec![".pyd", ".dll"] } else { vec![".so"] }
                },
                "rust_ext" => {
                    if cfg!(target_os = "windows") { vec![".dll"] } else { vec![".so"] }
                },
                "go_ext" | "zig_ext" | "nim_ext" => {
                    if cfg!(target_os = "windows") { vec![".dll"] } else { vec![".so"] }
                },
                "julia_ext" => vec![".jl"],
                "kotlin_ext" => vec![".jar"],
                _ => vec![],
            };
            
            if !expected_extensions.is_empty() {
                let has_expected_extension = path_analysis.paths_analyzed.iter().any(|path| {
                    expected_extensions.iter().any(|ext| path.ends_with(ext))
                });
                prop_assert!(has_expected_extension, 
                    "Language {} must have paths with expected extensions {:?}", 
                    ffi_impl, expected_extensions);
            }
            
            // 6. Dependency analysis must identify language-specific dependencies
            let dep_analysis_result = engine.analyze_dependency_chain(&ffi_impl);
            prop_assert!(dep_analysis_result.is_ok(), "Dependency analysis must succeed for {}", ffi_impl);
            
            let dep_analysis = dep_analysis_result.unwrap();
            prop_assert_eq!(dep_analysis.implementation, ffi_impl);
            
            // 7. Verify language-specific dependencies are checked
            let expected_deps = match ffi_impl {
                "c_ext" | "cpp_ext" => vec!["gcc"],
                "cython_ext" => vec!["cython", "gcc"],
                "rust_ext" => vec!["cargo", "rustc"],
                "go_ext" => vec!["go"],
                "zig_ext" => vec!["zig"],
                "nim_ext" => vec!["nim"],
                "fortran_ext" => vec!["gfortran", "f2py"],
                "julia_ext" => vec!["julia"],
                "kotlin_ext" => vec!["kotlin", "gradle"],
                _ => vec![],
            };
            
            for expected_dep in expected_deps {
                prop_assert!(
                    dep_analysis.dependency_chain.contains(&expected_dep.to_string()) ||
                    dep_analysis.dependencies_found.contains(&expected_dep.to_string()) ||
                    dep_analysis.dependencies_missing.contains(&expected_dep.to_string()),
                    "Language {} must check for dependency {}", ffi_impl, expected_dep
                );
            }
            
            // 8. Language-specific error patterns must be recognized
            let test_errors = create_language_specific_test_errors(&ffi_impl);
            if !test_errors.is_empty() {
                let classification_result = engine.classify_runtime_errors(&test_errors);
                prop_assert!(classification_result.is_ok(), "Error classification must succeed");
                
                let classification = classification_result.unwrap();
                prop_assert!(classification.total_errors > 0, "Must classify language-specific errors");
                prop_assert!(!classification.recommendations.is_empty(), "Must provide language-specific recommendations");
                
                // Verify language-specific recommendations are provided
                let has_language_specific_recommendation = classification.recommendations.iter().any(|rec| {
                    match ffi_impl {
                        "c_ext" | "cpp_ext" => rec.contains("gcc") || rec.contains("compilation") || rec.contains("linking"),
                        "cython_ext" => rec.contains("cython") || rec.contains("Python"),
                        "rust_ext" => rec.contains("cargo") || rec.contains("rust"),
                        "go_ext" => rec.contains("go") || rec.contains("cgo"),
                        "fortran_ext" => rec.contains("fortran") || rec.contains("f2py"),
                        _ => true, // For other languages, any recommendation is acceptable
                    }
                });
                
                prop_assert!(has_language_specific_recommendation, 
                    "Must provide language-specific recommendations for {}", ffi_impl);
            }
        }
    }

    // Helper function to create language-specific test errors
    fn create_language_specific_test_errors(ffi_impl: &str) -> Vec<RuntimeError> {
        match ffi_impl {
            "c_ext" | "cpp_ext" => vec![
                RuntimeError {
                    error_type: "ImportError".to_string(),
                    error_message: "undefined symbol: missing_function".to_string(),
                    context: "Loading C/C++ extension".to_string(),
                    severity: ErrorSeverity::Critical,
                },
                RuntimeError {
                    error_type: "OSError".to_string(),
                    error_message: "compilation failed: gcc not found".to_string(),
                    context: "Building C/C++ extension".to_string(),
                    severity: ErrorSeverity::Critical,
                },
            ],
            "cython_ext" => vec![
                RuntimeError {
                    error_type: "ImportError".to_string(),
                    error_message: "cython compilation failed".to_string(),
                    context: "Loading Cython extension".to_string(),
                    severity: ErrorSeverity::Critical,
                },
            ],
            "rust_ext" => vec![
                RuntimeError {
                    error_type: "ImportError".to_string(),
                    error_message: "cargo build failed".to_string(),
                    context: "Building Rust extension".to_string(),
                    severity: ErrorSeverity::Critical,
                },
            ],
            "go_ext" => vec![
                RuntimeError {
                    error_type: "ImportError".to_string(),
                    error_message: "CGO compilation failed".to_string(),
                    context: "Building Go extension".to_string(),
                    severity: ErrorSeverity::Critical,
                },
            ],
            "fortran_ext" => vec![
                RuntimeError {
                    error_type: "ImportError".to_string(),
                    error_message: "f2py compilation failed".to_string(),
                    context: "Building Fortran extension".to_string(),
                    severity: ErrorSeverity::Critical,
                },
            ],
            _ => vec![], // No specific test errors for other languages
        }
    }
}