//! Tests for the Bug Detection Engine

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
    }
}