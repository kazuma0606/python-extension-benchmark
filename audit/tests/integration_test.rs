// Integration test without PyO3 dependencies
use windows_ffi_audit::diagnostics::FFIImplementationDebugger;
use windows_ffi_audit::fixer::FFIImplementationFixer;
use windows_ffi_audit::bug_detection::BugDetectionEngine;
use windows_ffi_audit::types::DLLIssue;

#[test]
fn test_rust_go_diagnosis_integration() {
    let debugger = FFIImplementationDebugger::new();
    
    // Test Rust diagnosis
    let rust_result = debugger.diagnose_rust_go_issues("rust_ext");
    assert!(rust_result.is_ok(), "Rust diagnosis should succeed");
    
    // Test Go diagnosis
    let go_result = debugger.diagnose_rust_go_issues("go_ext");
    assert!(go_result.is_ok(), "Go diagnosis should succeed");
    
    // Test unsupported implementation
    let unsupported_result = debugger.diagnose_rust_go_issues("unsupported_ext");
    assert!(unsupported_result.is_ok(), "Unsupported implementation should return empty issues");
    let issues = unsupported_result.unwrap();
    assert!(issues.is_empty(), "Unsupported implementation should have no issues");
}

#[test]
fn test_rust_go_fix_integration() {
    let fixer = FFIImplementationFixer::new();
    
    // Test Rust fix functionality
    let rust_issues = vec![
        DLLIssue {
            issue_type: windows_ffi_audit::types::DLLIssueType::DependencyMissing,
            error_code: None,
            description: "Rust toolchain not found".to_string(),
            affected_library: "rustc".to_string(),
            resolution_steps: vec![],
        },
    ];
    
    let rust_result = fixer.fix_rust_go_issues("rust_ext", &rust_issues);
    assert!(rust_result.is_ok(), "Rust fix should succeed");
    let rust_actions = rust_result.unwrap();
    assert!(!rust_actions.is_empty(), "Rust fix should provide actions");
    
    // Test Go fix functionality
    let go_issues = vec![
        DLLIssue {
            issue_type: windows_ffi_audit::types::DLLIssueType::DependencyMissing,
            error_code: None,
            description: "Go compiler not found".to_string(),
            affected_library: "go".to_string(),
            resolution_steps: vec![],
        },
    ];
    
    let go_result = fixer.fix_rust_go_issues("go_ext", &go_issues);
    assert!(go_result.is_ok(), "Go fix should succeed");
    let go_actions = go_result.unwrap();
    assert!(!go_actions.is_empty(), "Go fix should provide actions");
}

#[test]
fn test_modern_language_diagnosis_integration() {
    let debugger = FFIImplementationDebugger::new();
    
    // Test Zig diagnosis
    let zig_result = debugger.diagnose_modern_language_issues("zig_ext");
    assert!(zig_result.is_ok(), "Zig diagnosis should succeed");
    let zig_issues = zig_result.unwrap();
    println!("Zig issues found: {}", zig_issues.len());
    
    // Test Nim diagnosis
    let nim_result = debugger.diagnose_modern_language_issues("nim_ext");
    assert!(nim_result.is_ok(), "Nim diagnosis should succeed");
    let nim_issues = nim_result.unwrap();
    println!("Nim issues found: {}", nim_issues.len());
    
    // Test Julia diagnosis
    let julia_result = debugger.diagnose_modern_language_issues("julia_ext");
    assert!(julia_result.is_ok(), "Julia diagnosis should succeed");
    let julia_issues = julia_result.unwrap();
    println!("Julia issues found: {}", julia_issues.len());
    
    // Test Kotlin diagnosis
    let kotlin_result = debugger.diagnose_modern_language_issues("kotlin_ext");
    assert!(kotlin_result.is_ok(), "Kotlin diagnosis should succeed");
    let kotlin_issues = kotlin_result.unwrap();
    println!("Kotlin issues found: {}", kotlin_issues.len());
    
    // Test unsupported implementation
    let unsupported_result = debugger.diagnose_modern_language_issues("unsupported_ext");
    assert!(unsupported_result.is_ok(), "Unsupported implementation should return empty issues");
    let issues = unsupported_result.unwrap();
    assert!(issues.is_empty(), "Unsupported implementation should have no issues");
}

#[test]
fn test_modern_language_fix_integration() {
    let fixer = FFIImplementationFixer::new();
    
    // Test Zig fix functionality
    let zig_issues = vec![
        DLLIssue {
            issue_type: windows_ffi_audit::types::DLLIssueType::DependencyMissing,
            error_code: None,
            description: "Zig compiler not found".to_string(),
            affected_library: "zig".to_string(),
            resolution_steps: vec![],
        },
        DLLIssue {
            issue_type: windows_ffi_audit::types::DLLIssueType::LoadFailure,
            error_code: None,
            description: "build.zig not found".to_string(),
            affected_library: "benchmark/zig_ext/build.zig".to_string(),
            resolution_steps: vec![],
        },
    ];
    
    let zig_result = fixer.fix_modern_language_issues("zig_ext", &zig_issues);
    assert!(zig_result.is_ok(), "Zig fix should succeed");
    let zig_actions = zig_result.unwrap();
    assert!(!zig_actions.is_empty(), "Zig fix should provide actions");
    println!("Zig fix actions: {}", zig_actions.len());
    
    // Test Nim fix functionality
    let nim_issues = vec![
        DLLIssue {
            issue_type: windows_ffi_audit::types::DLLIssueType::DependencyMissing,
            error_code: None,
            description: "Nim compiler not found".to_string(),
            affected_library: "nim".to_string(),
            resolution_steps: vec![],
        },
    ];
    
    let nim_result = fixer.fix_modern_language_issues("nim_ext", &nim_issues);
    assert!(nim_result.is_ok(), "Nim fix should succeed");
    let nim_actions = nim_result.unwrap();
    assert!(!nim_actions.is_empty(), "Nim fix should provide actions");
    println!("Nim fix actions: {}", nim_actions.len());
    
    // Test Julia fix functionality
    let julia_issues = vec![
        DLLIssue {
            issue_type: windows_ffi_audit::types::DLLIssueType::DependencyMissing,
            error_code: None,
            description: "Julia not found".to_string(),
            affected_library: "julia".to_string(),
            resolution_steps: vec![],
        },
    ];
    
    let julia_result = fixer.fix_modern_language_issues("julia_ext", &julia_issues);
    assert!(julia_result.is_ok(), "Julia fix should succeed");
    let julia_actions = julia_result.unwrap();
    assert!(!julia_actions.is_empty(), "Julia fix should provide actions");
    println!("Julia fix actions: {}", julia_actions.len());
    
    // Test Kotlin fix functionality
    let kotlin_issues = vec![
        DLLIssue {
            issue_type: windows_ffi_audit::types::DLLIssueType::DependencyMissing,
            error_code: None,
            description: "Kotlin/Native not found".to_string(),
            affected_library: "kotlinc-native".to_string(),
            resolution_steps: vec![],
        },
    ];
    
    let kotlin_result = fixer.fix_modern_language_issues("kotlin_ext", &kotlin_issues);
    assert!(kotlin_result.is_ok(), "Kotlin fix should succeed");
    let kotlin_actions = kotlin_result.unwrap();
    assert!(!kotlin_actions.is_empty(), "Kotlin fix should provide actions");
    println!("Kotlin fix actions: {}", kotlin_actions.len());
}

#[test]
fn test_modern_language_bug_detection_integration() {
    let bug_detector = BugDetectionEngine::new();
    
    // Test modern language implementations with bug detection
    let modern_languages = vec!["zig_ext", "nim_ext", "julia_ext", "kotlin_ext"];
    
    for lang in modern_languages {
        println!("Testing bug detection for {}", lang);
        
        // Test DLL loading issue detection
        let dll_issues_result = bug_detector.detect_dll_loading_issues(lang);
        assert!(dll_issues_result.is_ok(), "DLL issue detection should succeed for {}", lang);
        let dll_issues = dll_issues_result.unwrap();
        println!("  DLL issues found: {}", dll_issues.len());
        
        // Test path resolution analysis
        let path_analysis_result = bug_detector.analyze_path_resolution(lang);
        assert!(path_analysis_result.is_ok(), "Path analysis should succeed for {}", lang);
        let path_analysis = path_analysis_result.unwrap();
        assert_eq!(path_analysis.implementation, lang);
        println!("  Paths analyzed: {}", path_analysis.paths_analyzed.len());
        
        // Test dependency chain analysis
        let dep_analysis_result = bug_detector.analyze_dependency_chain(lang);
        assert!(dep_analysis_result.is_ok(), "Dependency analysis should succeed for {}", lang);
        let dep_analysis = dep_analysis_result.unwrap();
        assert_eq!(dep_analysis.implementation, lang);
        println!("  Dependencies found: {}, missing: {}", 
                dep_analysis.dependencies_found.len(), 
                dep_analysis.dependencies_missing.len());
    }
}

#[test]
fn test_end_to_end_modern_language_workflow() {
    let debugger = FFIImplementationDebugger::new();
    let bug_detector = BugDetectionEngine::new();
    let fixer = FFIImplementationFixer::new();
    
    // Test complete workflow for Zig
    println!("Testing end-to-end workflow for zig_ext");
    
    // Step 1: Library loading diagnostics
    let library_diagnostics = debugger.diagnose_library_loading("zig_ext");
    assert!(library_diagnostics.is_ok(), "Library diagnostics should succeed");
    let diagnostics = library_diagnostics.unwrap();
    println!("  Library exists: {}, loadable: {}", diagnostics.library_exists, diagnostics.library_loadable);
    
    // Step 2: Modern language specific diagnosis
    let modern_issues = debugger.diagnose_modern_language_issues("zig_ext");
    assert!(modern_issues.is_ok(), "Modern language diagnosis should succeed");
    let issues = modern_issues.unwrap();
    println!("  Modern language issues: {}", issues.len());
    
    // Step 3: Bug detection
    let dll_issues = bug_detector.detect_dll_loading_issues("zig_ext");
    assert!(dll_issues.is_ok(), "Bug detection should succeed");
    let bugs = dll_issues.unwrap();
    println!("  Bugs detected: {}", bugs.len());
    
    // Step 4: Fix generation
    if !bugs.is_empty() {
        let fix_result = fixer.fix_modern_language_issues("zig_ext", &bugs);
        assert!(fix_result.is_ok(), "Fix generation should succeed");
        let fixes = fix_result.unwrap();
        println!("  Fix actions generated: {}", fixes.len());
        
        // Step 5: Build script generation
        let build_script = fixer.generate_build_script("zig_ext", &bugs);
        assert!(build_script.is_ok(), "Build script generation should succeed");
        let script = build_script.unwrap();
        println!("  Build script language: {}", script.language);
        println!("  Required tools: {:?}", script.required_tools);
        
        // Step 6: Compatibility layer generation
        let compat_layer = fixer.generate_compatibility_layer("zig_ext");
        assert!(compat_layer.is_ok(), "Compatibility layer generation should succeed");
        let layer = compat_layer.unwrap();
        println!("  Compatibility layer type: {:?}", layer.layer_type);
    }
    
    println!("End-to-end workflow completed successfully");
}