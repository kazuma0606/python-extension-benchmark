//! FFI Audit CLI Tool
//! 
//! Command-line interface for the Windows FFI audit system.

use std::env;
use std::process;
use windows_ffi_audit::{Result, FFIAuditError};
use windows_ffi_audit::diagnostics::FFIImplementationDebugger;
use windows_ffi_audit::bug_detection::BugDetectionEngine;
use windows_ffi_audit::fixer::FFIImplementationFixer;

fn main() {
    if let Err(e) = run() {
        eprintln!("Error: {}", e);
        process::exit(1);
    }
}

fn run() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        print_usage();
        return Ok(());
    }
    
    match args[1].as_str() {
        "audit" => {
            println!("Starting comprehensive FFI implementation audit...");
            run_comprehensive_audit()
        }
        "diagnose" => {
            if args.len() < 3 {
                return Err(FFIAuditError::InvalidArguments(
                    "diagnose command requires implementation name".to_string()
                ));
            }
            println!("Diagnosing FFI implementation: {}", args[2]);
            run_diagnosis(&args[2])
        }
        "fix" => {
            if args.len() < 3 {
                return Err(FFIAuditError::InvalidArguments(
                    "fix command requires implementation name".to_string()
                ));
            }
            println!("Fixing FFI implementation: {}", args[2]);
            run_fix(&args[2])
        }
        "verify" => {
            println!("Verifying all FFI implementations...");
            run_verification()
        }
        "--help" | "-h" => {
            print_usage();
            Ok(())
        }
        _ => {
            return Err(FFIAuditError::InvalidArguments(
                format!("Unknown command: {}", args[1])
            ));
        }
    }
}

/// Run comprehensive audit of all FFI implementations
fn run_comprehensive_audit() -> Result<()> {
    let implementations = vec![
        "c_ext", "cpp_ext", "cython_ext", "rust_ext", "go_ext", 
        "zig_ext", "nim_ext", "julia_ext", "kotlin_ext", "fortran_ext"
    ];
    
    println!("Auditing {} FFI implementations...", implementations.len());
    
    for impl_name in implementations {
        println!("\n=== Auditing {} ===", impl_name);
        
        // Run diagnosis
        match run_diagnosis(impl_name) {
            Ok(_) => println!("✓ Diagnosis completed for {}", impl_name),
            Err(e) => println!("✗ Diagnosis failed for {}: {}", impl_name, e),
        }
    }
    
    println!("\nComprehensive audit completed.");
    Ok(())
}

/// Run diagnosis for a specific FFI implementation
fn run_diagnosis(impl_name: &str) -> Result<()> {
    let debugger = FFIImplementationDebugger::new();
    let bug_detector = BugDetectionEngine::new();
    
    println!("Running library loading diagnostics...");
    let library_diagnostics = debugger.diagnose_library_loading(impl_name)?;
    println!("Library exists: {}", library_diagnostics.library_exists);
    println!("Library loadable: {}", library_diagnostics.library_loadable);
    
    if !library_diagnostics.loading_errors.is_empty() {
        println!("Loading errors found:");
        for error in &library_diagnostics.loading_errors {
            println!("  - {:?}: {}", error.error_type, error.error_message);
        }
    }
    
    println!("Detecting DLL loading issues...");
    let dll_issues = bug_detector.detect_dll_loading_issues(impl_name)?;
    if !dll_issues.is_empty() {
        println!("DLL issues found:");
        for issue in &dll_issues {
            println!("  - {:?}: {}", issue.issue_type, issue.description);
            println!("    Affected library: {}", issue.affected_library);
            if !issue.resolution_steps.is_empty() {
                println!("    Resolution steps:");
                for step in &issue.resolution_steps {
                    println!("      • {}", step);
                }
            }
        }
    } else {
        println!("No DLL loading issues detected.");
    }
    
    println!("Analyzing path resolution...");
    let path_analysis = bug_detector.analyze_path_resolution(impl_name)?;
    println!("Paths analyzed: {}", path_analysis.paths_analyzed.len());
    
    for result in &path_analysis.resolution_results {
        println!("  Path: {} - Exists: {}, Readable: {}", 
                result.path, result.exists, result.readable);
        if !result.issues.is_empty() {
            for issue in &result.issues {
                println!("    Issue: {}", issue);
            }
        }
    }
    
    if !path_analysis.recommendations.is_empty() {
        println!("Path recommendations:");
        for rec in &path_analysis.recommendations {
            println!("  • {}", rec);
        }
    }
    
    println!("Analyzing dependency chain...");
    let dep_analysis = bug_detector.analyze_dependency_chain(impl_name)?;
    println!("Dependencies found: {:?}", dep_analysis.dependencies_found);
    if !dep_analysis.dependencies_missing.is_empty() {
        println!("Dependencies missing: {:?}", dep_analysis.dependencies_missing);
    }
    
    Ok(())
}

/// Run fix for a specific FFI implementation
fn run_fix(impl_name: &str) -> Result<()> {
    let bug_detector = BugDetectionEngine::new();
    let fixer = FFIImplementationFixer::new();
    
    println!("Detecting issues to fix...");
    let dll_issues = bug_detector.detect_dll_loading_issues(impl_name)?;
    
    if dll_issues.is_empty() {
        println!("No issues detected for {}. Nothing to fix.", impl_name);
        return Ok(());
    }
    
    println!("Found {} issues to fix:", dll_issues.len());
    for issue in &dll_issues {
        println!("  - {:?}: {}", issue.issue_type, issue.description);
    }
    
    // Apply appropriate fixes based on implementation type
    let fix_actions = match impl_name {
        "c_ext" | "cpp_ext" => {
            println!("Applying C/C++ specific fixes...");
            fixer.fix_c_cpp_issues(impl_name, &dll_issues)?
        }
        "cython_ext" | "numpy_impl" | "fortran_ext" => {
            println!("Applying Cython/NumPy/Fortran specific fixes...");
            fixer.fix_cython_numpy_fortran_issues(impl_name, &dll_issues)?
        }
        "rust_ext" | "go_ext" => {
            println!("Applying Rust/Go specific fixes...");
            fixer.fix_rust_go_issues(impl_name, &dll_issues)?
        }
        "zig_ext" | "nim_ext" | "julia_ext" | "kotlin_ext" => {
            println!("Applying modern language specific fixes...");
            fixer.fix_modern_language_issues(impl_name, &dll_issues)?
        }
        _ => {
            return Err(FFIAuditError::UnsupportedImplementation(impl_name.to_string()));
        }
    };
    
    if fix_actions.is_empty() {
        println!("No fix actions generated.");
    } else {
        println!("Fix actions to apply:");
        for (i, action) in fix_actions.iter().enumerate() {
            println!("  {}. {}", i + 1, action);
        }
        
        // Generate build script if needed
        println!("\nGenerating build script...");
        let build_script = fixer.generate_build_script(impl_name, &dll_issues)?;
        println!("Build script generated for {}", build_script.language);
        println!("Required tools: {:?}", build_script.required_tools);
        
        if !build_script.build_commands.is_empty() {
            println!("Build commands:");
            for cmd in &build_script.build_commands {
                println!("  {}", cmd);
            }
        }
        
        // Generate compatibility layer if needed
        println!("\nGenerating compatibility layer...");
        let compat_layer = fixer.generate_compatibility_layer(impl_name)?;
        println!("Compatibility layer type: {:?}", compat_layer.layer_type);
        
        if !compat_layer.installation_instructions.is_empty() {
            println!("Installation instructions:");
            for instruction in &compat_layer.installation_instructions {
                println!("  • {}", instruction);
            }
        }
    }
    
    println!("\nFix process completed for {}.", impl_name);
    Ok(())
}

/// Run verification of all FFI implementations
fn run_verification() -> Result<()> {
    let implementations = vec![
        "c_ext", "cpp_ext", "cython_ext", "rust_ext", "go_ext", 
        "zig_ext", "nim_ext", "julia_ext", "kotlin_ext", "fortran_ext"
    ];
    
    let debugger = FFIImplementationDebugger::new();
    let mut successful = 0;
    let mut failed = 0;
    
    println!("Verifying {} FFI implementations...", implementations.len());
    
    for impl_name in implementations {
        print!("Verifying {}... ", impl_name);
        
        match debugger.diagnose_library_loading(impl_name) {
            Ok(diagnostics) => {
                if diagnostics.library_exists && diagnostics.library_loadable && diagnostics.loading_errors.is_empty() {
                    println!("✓ PASS");
                    successful += 1;
                } else {
                    println!("✗ FAIL");
                    if !diagnostics.library_exists {
                        println!("  - Library does not exist");
                    }
                    if !diagnostics.library_loadable {
                        println!("  - Library is not loadable");
                    }
                    if !diagnostics.loading_errors.is_empty() {
                        println!("  - {} loading errors", diagnostics.loading_errors.len());
                    }
                    failed += 1;
                }
            }
            Err(e) => {
                println!("✗ ERROR: {}", e);
                failed += 1;
            }
        }
    }
    
    println!("\nVerification Summary:");
    println!("  Successful: {}", successful);
    println!("  Failed: {}", failed);
    println!("  Total: {}", successful + failed);
    
    if failed > 0 {
        println!("\nRun 'ffi-audit fix <implementation>' to fix specific issues.");
    }
    
    Ok(())
}

fn print_usage() {
    println!("FFI Audit Tool");
    println!("Usage: ffi-audit <command> [options]");
    println!();
    println!("Commands:");
    println!("  audit                    - Run comprehensive FFI audit");
    println!("  diagnose <implementation> - Diagnose specific FFI implementation");
    println!("  fix <implementation>     - Fix issues in FFI implementation");
    println!("  verify                   - Verify all FFI implementations");
    println!("  --help, -h              - Show this help message");
}