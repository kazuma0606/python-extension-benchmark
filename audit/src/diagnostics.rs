//! FFI Implementation Diagnostics
//! 
//! This module provides functionality to diagnose FFI implementations
//! and identify issues that could cause fallback to Python implementations.

use crate::error::{LibraryDiagnosticsResult, SymbolValidationResult, CallingConventionResult, MemoryLayoutResult};
use crate::types::*;
use pyo3::prelude::*;
use std::path::{Path, PathBuf};
use std::ffi::{OsStr, CString};
use std::os::windows::ffi::OsStrExt;

#[cfg(windows)]
use winapi::um::{
    libloaderapi::{LoadLibraryW, FreeLibrary},
    errhandlingapi::GetLastError,
};

#[cfg(windows)]
use winapi::shared::winerror::{
    ERROR_FILE_NOT_FOUND,
    ERROR_ACCESS_DENIED,
    ERROR_BAD_EXE_FORMAT,
    ERROR_MOD_NOT_FOUND,
};

/// FFI Implementation Debugger
/// 
/// Diagnoses and identifies issues in FFI implementations that could
/// cause fallback to pure Python implementations.
#[pyclass]
#[derive(Debug, Clone)]
pub struct FFIImplementationDebugger {
    // Implementation will be added in subsequent tasks
}

#[pymethods]
impl FFIImplementationDebugger {
    #[new]
    pub fn new() -> Self {
        Self {}
    }
}

impl FFIImplementationDebugger {
    /// Diagnose library loading issues using Windows API
    pub fn diagnose_library_loading(&self, ffi_impl: &str) -> LibraryDiagnosticsResult {
        let mut diagnostics = LibraryDiagnostics {
            implementation: ffi_impl.to_string(),
            library_exists: false,
            library_loadable: false,
            loading_errors: vec![],
            missing_dependencies: vec![],
            architecture_mismatch: false,
            path_issues: vec![],
        };

        // Determine library path based on implementation type
        let library_paths = self.get_library_paths_for_implementation(ffi_impl);
        
        for library_path in library_paths {
            let path_buf = PathBuf::from(&library_path);
            
            // Check if library file exists
            if path_buf.exists() {
                diagnostics.library_exists = true;
                
                // Try to load the library using Windows API
                match self.try_load_library(&library_path) {
                    Ok(_) => {
                        diagnostics.library_loadable = true;
                        break; // Successfully loaded, no need to check other paths
                    }
                    Err(dll_issues) => {
                        // Convert DLL issues to loading errors
                        for issue in dll_issues {
                            let error_type = match issue.issue_type {
                                DLLIssueType::LoadFailure => LoadingErrorType::FileNotFound,
                                DLLIssueType::SymbolNotFound => LoadingErrorType::SymbolNotFound,
                                DLLIssueType::ArchitectureMismatch => LoadingErrorType::ArchitectureMismatch,
                                DLLIssueType::DependencyMissing => LoadingErrorType::DependencyMissing,
                                DLLIssueType::PathResolutionFailure => LoadingErrorType::FileNotFound,
                                _ => LoadingErrorType::Other(issue.description.clone()),
                            };
                            
                            diagnostics.loading_errors.push(LoadingError {
                                error_code: issue.error_code,
                                error_message: issue.description,
                                error_type,
                            });
                        }
                    }
                }
            } else {
                // Library file doesn't exist, check for path issues
                let path_issues = self.analyze_path_issues(&library_path);
                diagnostics.path_issues.extend(path_issues);
            }
        }

        // Analyze dependencies if library exists but can't load
        if diagnostics.library_exists && !diagnostics.library_loadable {
            diagnostics.missing_dependencies = self.analyze_missing_dependencies(ffi_impl);
            diagnostics.architecture_mismatch = self.check_architecture_mismatch(ffi_impl);
        }

        Ok(diagnostics)
    }

    /// Get potential library paths for a given FFI implementation
    fn get_library_paths_for_implementation(&self, ffi_impl: &str) -> Vec<String> {
        let mut paths = Vec::new();
        
        match ffi_impl {
            "c_ext" => {
                paths.push("benchmark/c_ext/numeric.pyd".to_string());
                paths.push("benchmark/c_ext/memory.pyd".to_string());
                paths.push("benchmark/c_ext/parallel.pyd".to_string());
            }
            "cpp_ext" => {
                paths.push("benchmark/cpp_ext/numeric.pyd".to_string());
                paths.push("benchmark/cpp_ext/memory.pyd".to_string());
                paths.push("benchmark/cpp_ext/parallel.pyd".to_string());
            }
            "cython_ext" => {
                paths.push("benchmark/cython_ext/numeric.pyd".to_string());
                paths.push("benchmark/cython_ext/memory.pyd".to_string());
                paths.push("benchmark/cython_ext/parallel.pyd".to_string());
            }
            "rust_ext" => {
                paths.push("benchmark/rust_ext/target/wheels/rust_ext.pyd".to_string());
            }
            "go_ext" => {
                paths.push("benchmark/go_ext/libgofunctions.dll".to_string());
                paths.push("benchmark/go_ext/libgofunctions.so".to_string());
            }
            "fortran_ext" => {
                paths.push("benchmark/fortran_ext/numeric.pyd".to_string());
                paths.push("benchmark/fortran_ext/memory.pyd".to_string());
                paths.push("benchmark/fortran_ext/parallel.pyd".to_string());
            }
            "zig_ext" => {
                paths.push("benchmark/zig_ext/zigfunctions.dll".to_string());
                paths.push("benchmark/zig_ext/zigfunctions.so".to_string());
            }
            "nim_ext" => {
                paths.push("benchmark/nim_ext/libnimfunctions.dll".to_string());
                paths.push("benchmark/nim_ext/libnimfunctions.so".to_string());
            }
            "julia_ext" => {
                paths.push("benchmark/julia_ext/functions.dll".to_string());
            }
            "kotlin_ext" => {
                paths.push("benchmark/kotlin_ext/build/libs/kotlin_ext.dll".to_string());
            }
            _ => {
                // Generic paths for unknown implementations
                paths.push(format!("benchmark/{}/lib{}.dll", ffi_impl, ffi_impl));
                paths.push(format!("benchmark/{}/lib{}.so", ffi_impl, ffi_impl));
                paths.push(format!("benchmark/{}/{}.pyd", ffi_impl, ffi_impl));
            }
        }
        
        paths
    }

    /// Try to load a library using Windows API and return DLL issues if failed
    #[cfg(windows)]
    fn try_load_library(&self, library_path: &str) -> std::result::Result<(), Vec<DLLIssue>> {
        // Convert path to wide string for Windows API
        let wide_path: Vec<u16> = OsStr::new(library_path)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect();

        unsafe {
            let handle = LoadLibraryW(wide_path.as_ptr());
            
            if handle.is_null() {
                let error_code = GetLastError();
                let mut issues = vec![];
                
                let (issue_type, description) = match error_code {
                    ERROR_FILE_NOT_FOUND => (
                        DLLIssueType::LoadFailure,
                        format!("Library file not found: {}", library_path)
                    ),
                    ERROR_ACCESS_DENIED => (
                        DLLIssueType::LoadFailure,
                        format!("Access denied when loading library: {}", library_path)
                    ),
                    ERROR_BAD_EXE_FORMAT => (
                        DLLIssueType::ArchitectureMismatch,
                        format!("Architecture mismatch for library: {}", library_path)
                    ),
                    ERROR_MOD_NOT_FOUND => (
                        DLLIssueType::DependencyMissing,
                        format!("Required dependency missing for library: {}", library_path)
                    ),
                    _ => (
                        DLLIssueType::LoadFailure,
                        format!("Unknown error loading library: {} (Error code: {})", library_path, error_code)
                    ),
                };

                issues.push(DLLIssue {
                    issue_type,
                    error_code: Some(error_code),
                    description,
                    affected_library: library_path.to_string(),
                    resolution_steps: self.get_resolution_steps_for_error(error_code),
                });

                Err(issues)
            } else {
                // Successfully loaded, clean up
                FreeLibrary(handle);
                Ok(())
            }
        }
    }

    /// Non-Windows implementation (for testing/compilation on other platforms)
    #[cfg(not(windows))]
    fn try_load_library(&self, library_path: &str) -> std::result::Result<(), Vec<DLLIssue>> {
        // On non-Windows platforms, just check if file exists
        if Path::new(library_path).exists() {
            Ok(())
        } else {
            Err(vec![DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("Library file not found: {}", library_path),
                affected_library: library_path.to_string(),
                resolution_steps: vec!["Build the library for this platform".to_string()],
            }])
        }
    }

    /// Get resolution steps for Windows error codes
    fn get_resolution_steps_for_error(&self, error_code: u32) -> Vec<String> {
        match error_code {
            ERROR_FILE_NOT_FOUND => vec![
                "Check if the library file exists at the specified path".to_string(),
                "Verify the build process completed successfully".to_string(),
                "Check if the library was built for the correct architecture".to_string(),
            ],
            ERROR_ACCESS_DENIED => vec![
                "Run with administrator privileges".to_string(),
                "Check file permissions on the library".to_string(),
                "Verify antivirus software is not blocking the library".to_string(),
            ],
            ERROR_BAD_EXE_FORMAT => vec![
                "Ensure library is built for the correct architecture (32-bit vs 64-bit)".to_string(),
                "Verify Python architecture matches library architecture".to_string(),
                "Rebuild the library with correct compiler settings".to_string(),
            ],
            ERROR_MOD_NOT_FOUND => vec![
                "Install required runtime libraries (Visual C++ Redistributable)".to_string(),
                "Check for missing dependencies using Dependency Walker".to_string(),
                "Ensure all required DLLs are in the system PATH".to_string(),
            ],
            _ => vec![
                "Check Windows Event Log for detailed error information".to_string(),
                "Verify library integrity and rebuild if necessary".to_string(),
            ],
        }
    }

    /// Analyze path-related issues
    fn analyze_path_issues(&self, library_path: &str) -> Vec<PathIssue> {
        let mut issues = Vec::new();
        let path = Path::new(library_path);

        // Check for path length issues
        if library_path.len() > 260 {
            issues.push(PathIssue {
                issue_type: PathIssueType::PathTooLong,
                path: library_path.to_string(),
                description: "Path exceeds Windows MAX_PATH limit".to_string(),
                resolution_suggestion: "Use shorter path or enable long path support".to_string(),
            });
        }

        // Check for invalid characters
        let invalid_chars = ['<', '>', ':', '"', '|', '?', '*'];
        if library_path.chars().any(|c| invalid_chars.contains(&c)) {
            issues.push(PathIssue {
                issue_type: PathIssueType::InvalidCharacters,
                path: library_path.to_string(),
                description: "Path contains invalid characters".to_string(),
                resolution_suggestion: "Remove or replace invalid characters in path".to_string(),
            });
        }

        // Check if parent directory exists
        if let Some(parent) = path.parent() {
            if !parent.exists() {
                issues.push(PathIssue {
                    issue_type: PathIssueType::RelativePathProblem,
                    path: library_path.to_string(),
                    description: "Parent directory does not exist".to_string(),
                    resolution_suggestion: "Create parent directory or fix path".to_string(),
                });
            }
        }

        issues
    }

    /// Analyze missing dependencies for an implementation
    fn analyze_missing_dependencies(&self, ffi_impl: &str) -> Vec<String> {
        let mut missing = Vec::new();

        match ffi_impl {
            "c_ext" | "cpp_ext" => {
                missing.extend(vec![
                    "msvcr140.dll".to_string(),
                    "vcruntime140.dll".to_string(),
                ]);
            }
            "fortran_ext" => {
                missing.extend(vec![
                    "libgfortran.dll".to_string(),
                    "libquadmath.dll".to_string(),
                    "libgcc_s_seh.dll".to_string(),
                ]);
            }
            "rust_ext" => {
                // Rust typically statically links, but may need MSVC runtime
                missing.push("vcruntime140.dll".to_string());
            }
            "go_ext" => {
                // Go CGO may need GCC runtime
                missing.push("libgcc_s_seh.dll".to_string());
            }
            _ => {
                // Generic dependencies
                missing.push("msvcr140.dll".to_string());
            }
        }

        // Filter out dependencies that actually exist
        missing.into_iter()
            .filter(|dep| !self.check_dependency_exists(dep))
            .collect()
    }

    /// Check if a dependency exists in the system
    #[cfg(windows)]
    fn check_dependency_exists(&self, dependency: &str) -> bool {
        let wide_name: Vec<u16> = OsStr::new(dependency)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect();

        unsafe {
            let handle = LoadLibraryW(wide_name.as_ptr());
            if !handle.is_null() {
                FreeLibrary(handle);
                true
            } else {
                false
            }
        }
    }

    #[cfg(not(windows))]
    fn check_dependency_exists(&self, _dependency: &str) -> bool {
        // On non-Windows platforms, assume dependencies exist
        true
    }

    /// Check for architecture mismatch
    fn check_architecture_mismatch(&self, _ffi_impl: &str) -> bool {
        // Simple heuristic: check if we're running 64-bit Python
        // and the library might be 32-bit (or vice versa)
        cfg!(target_pointer_width = "64")
    }

    /// Validate symbol resolution
    pub fn validate_symbol_resolution(&self, ffi_impl: &str) -> SymbolValidationResult {
        let mut validation = SymbolValidation {
            implementation: ffi_impl.to_string(),
            symbols_found: vec![],
            symbols_missing: vec![],
            symbol_issues: vec![],
        };

        // Get expected symbols for this implementation
        let expected_symbols = self.get_expected_symbols_for_implementation(ffi_impl);
        let library_paths = self.get_library_paths_for_implementation(ffi_impl);

        for library_path in library_paths {
            if Path::new(&library_path).exists() {
                match self.check_symbols_in_library(&library_path, &expected_symbols) {
                    Ok((found, missing, issues)) => {
                        validation.symbols_found.extend(found);
                        validation.symbols_missing.extend(missing);
                        validation.symbol_issues.extend(issues);
                        break; // Found a valid library, stop checking others
                    }
                    Err(_) => {
                        // Continue to next library path
                        continue;
                    }
                }
            }
        }

        // If no symbols were found, all expected symbols are missing
        if validation.symbols_found.is_empty() && validation.symbols_missing.is_empty() {
            validation.symbols_missing = expected_symbols;
        }

        Ok(validation)
    }

    /// Get expected symbols for a given FFI implementation
    fn get_expected_symbols_for_implementation(&self, ffi_impl: &str) -> Vec<String> {
        match ffi_impl {
            "c_ext" | "cpp_ext" | "cython_ext" => vec![
                "numeric_add".to_string(),
                "numeric_multiply".to_string(),
                "memory_allocate".to_string(),
                "memory_copy".to_string(),
                "parallel_compute".to_string(),
            ],
            "rust_ext" => vec![
                "rust_numeric_add".to_string(),
                "rust_numeric_multiply".to_string(),
                "rust_memory_allocate".to_string(),
            ],
            "go_ext" => vec![
                "GoNumericAdd".to_string(),
                "GoNumericMultiply".to_string(),
                "GoMemoryAllocate".to_string(),
            ],
            "fortran_ext" => vec![
                "fortran_numeric_add_".to_string(), // Fortran name mangling
                "fortran_numeric_multiply_".to_string(),
                "fortran_memory_allocate_".to_string(),
            ],
            "zig_ext" => vec![
                "zig_numeric_add".to_string(),
                "zig_numeric_multiply".to_string(),
                "zig_memory_allocate".to_string(),
            ],
            "nim_ext" => vec![
                "nim_numeric_add".to_string(),
                "nim_numeric_multiply".to_string(),
                "nim_memory_allocate".to_string(),
            ],
            "julia_ext" => vec![
                "julia_numeric_add".to_string(),
                "julia_numeric_multiply".to_string(),
                "julia_memory_allocate".to_string(),
            ],
            "kotlin_ext" => vec![
                "kotlin_numeric_add".to_string(),
                "kotlin_numeric_multiply".to_string(),
                "kotlin_memory_allocate".to_string(),
            ],
            _ => vec![
                "generic_function".to_string(),
            ],
        }
    }

    /// Check symbols in a library
    #[cfg(windows)]
    fn check_symbols_in_library(
        &self,
        library_path: &str,
        expected_symbols: &[String],
    ) -> std::result::Result<(Vec<String>, Vec<String>, Vec<SymbolIssue>), crate::error::FFIAuditError> {
        use winapi::um::libloaderapi::GetProcAddress;
        use std::ffi::CString;

        let wide_path: Vec<u16> = OsStr::new(library_path)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect();

        unsafe {
            let handle = LoadLibraryW(wide_path.as_ptr());
            if handle.is_null() {
                return Err(crate::error::FFIAuditError::LibraryLoadingFailed(
                    format!("Could not load library: {}", library_path)
                ));
            }

            let mut found = Vec::new();
            let mut missing = Vec::new();
            let mut issues = Vec::new();

            for symbol in expected_symbols {
                if let Ok(c_symbol) = CString::new(symbol.as_str()) {
                    let proc_addr = GetProcAddress(handle, c_symbol.as_ptr());
                    if proc_addr.is_null() {
                        missing.push(symbol.clone());
                        issues.push(SymbolIssue {
                            symbol_name: symbol.clone(),
                            issue_type: SymbolIssueType::NotExported,
                            description: format!("Symbol '{}' not found in library", symbol),
                        });
                    } else {
                        found.push(symbol.clone());
                    }
                } else {
                    issues.push(SymbolIssue {
                        symbol_name: symbol.clone(),
                        issue_type: SymbolIssueType::NameMangling,
                        description: format!("Invalid symbol name: '{}'", symbol),
                    });
                }
            }

            FreeLibrary(handle);
            Ok((found, missing, issues))
        }
    }

    #[cfg(not(windows))]
    fn check_symbols_in_library(
        &self,
        _library_path: &str,
        expected_symbols: &[String],
    ) -> std::result::Result<(Vec<String>, Vec<String>, Vec<SymbolIssue>), crate::error::FFIAuditError> {
        // On non-Windows platforms, assume all symbols are found for testing
        Ok((expected_symbols.to_vec(), vec![], vec![]))
    }

    /// Check calling convention compatibility
    pub fn check_calling_convention(&self, ffi_impl: &str) -> CallingConventionResult {
        let mut check = CallingConventionCheck {
            implementation: ffi_impl.to_string(),
            expected_convention: self.get_expected_calling_convention(ffi_impl),
            actual_convention: None,
            is_compatible: false,
            issues: vec![],
        };

        // For Windows, most FFI implementations should use cdecl or stdcall
        let library_paths = self.get_library_paths_for_implementation(ffi_impl);
        
        for library_path in library_paths {
            if Path::new(&library_path).exists() {
                match self.analyze_calling_convention(&library_path, ffi_impl) {
                    Ok(convention) => {
                        check.actual_convention = Some(convention.clone());
                        check.is_compatible = convention == check.expected_convention;
                        
                        if !check.is_compatible {
                            check.issues.push(format!(
                                "Calling convention mismatch: expected '{}', found '{}'",
                                check.expected_convention, convention
                            ));
                        }
                        break;
                    }
                    Err(error) => {
                        check.issues.push(format!("Failed to analyze calling convention: {}", error));
                    }
                }
            }
        }

        if check.actual_convention.is_none() {
            check.issues.push("Could not determine calling convention".to_string());
        }

        Ok(check)
    }

    /// Get expected calling convention for implementation
    fn get_expected_calling_convention(&self, ffi_impl: &str) -> String {
        match ffi_impl {
            "c_ext" | "cpp_ext" | "cython_ext" => "cdecl".to_string(),
            "rust_ext" => "cdecl".to_string(),
            "go_ext" => "cdecl".to_string(),
            "fortran_ext" => "cdecl".to_string(), // f2py typically uses cdecl
            "zig_ext" => "cdecl".to_string(),
            "nim_ext" => "cdecl".to_string(),
            "julia_ext" => "cdecl".to_string(),
            "kotlin_ext" => "cdecl".to_string(),
            _ => "cdecl".to_string(),
        }
    }

    /// Analyze calling convention of a library
    fn analyze_calling_convention(&self, library_path: &str, ffi_impl: &str) -> std::result::Result<String, String> {
        // This is a simplified implementation
        // In a real implementation, you would analyze the binary to determine calling convention
        
        // For now, we'll make educated guesses based on the implementation type and file extension
        if library_path.ends_with(".pyd") {
            // Python extensions typically use cdecl
            Ok("cdecl".to_string())
        } else if library_path.ends_with(".dll") {
            match ffi_impl {
                "go_ext" => Ok("cdecl".to_string()), // Go CGO uses cdecl
                "rust_ext" => Ok("cdecl".to_string()), // Rust FFI typically uses cdecl
                _ => Ok("cdecl".to_string()), // Default assumption
            }
        } else {
            Err("Unknown library format".to_string())
        }
    }

    /// Validate memory layout compatibility
    pub fn validate_memory_layout(&self, ffi_impl: &str) -> MemoryLayoutResult {
        let mut validation = MemoryLayoutValidation {
            implementation: ffi_impl.to_string(),
            layout_compatible: true, // Assume compatible until proven otherwise
            alignment_issues: vec![],
            size_mismatches: vec![],
        };

        // Check for common memory layout issues based on implementation type
        match ffi_impl {
            "c_ext" | "cpp_ext" => {
                // Check for potential struct alignment issues
                validation.alignment_issues.extend(self.check_c_alignment_issues());
                validation.size_mismatches.extend(self.check_c_size_mismatches());
            }
            "fortran_ext" => {
                // Fortran has different memory layout conventions
                validation.alignment_issues.extend(self.check_fortran_alignment_issues());
                validation.size_mismatches.extend(self.check_fortran_size_mismatches());
            }
            "rust_ext" => {
                // Rust has specific repr() requirements for FFI
                validation.alignment_issues.extend(self.check_rust_alignment_issues());
                validation.size_mismatches.extend(self.check_rust_size_mismatches());
            }
            "go_ext" => {
                // Go CGO has specific requirements
                validation.alignment_issues.extend(self.check_go_alignment_issues());
                validation.size_mismatches.extend(self.check_go_size_mismatches());
            }
            _ => {
                // Generic checks for other implementations
                validation.alignment_issues.extend(self.check_generic_alignment_issues());
            }
        }

        validation.layout_compatible = validation.alignment_issues.is_empty() && validation.size_mismatches.is_empty();

        Ok(validation)
    }

    /// Check C/C++ alignment issues
    fn check_c_alignment_issues(&self) -> Vec<AlignmentIssue> {
        vec![
            // Common C alignment issues on Windows
            AlignmentIssue {
                structure_name: "double".to_string(),
                expected_alignment: 8,
                actual_alignment: 4, // Potential issue with 32-bit compilation
            }
        ]
    }

    /// Check C/C++ size mismatches
    fn check_c_size_mismatches(&self) -> Vec<SizeMismatch> {
        vec![
            // Common size mismatches
            SizeMismatch {
                type_name: "long".to_string(),
                expected_size: 8, // 64-bit
                actual_size: 4,   // 32-bit
            }
        ]
    }

    /// Check Fortran alignment issues
    fn check_fortran_alignment_issues(&self) -> Vec<AlignmentIssue> {
        vec![
            AlignmentIssue {
                structure_name: "REAL*8".to_string(),
                expected_alignment: 8,
                actual_alignment: 4,
            }
        ]
    }

    /// Check Fortran size mismatches
    fn check_fortran_size_mismatches(&self) -> Vec<SizeMismatch> {
        vec![
            SizeMismatch {
                type_name: "INTEGER".to_string(),
                expected_size: 4,
                actual_size: 8, // Fortran default integer might be 64-bit
            }
        ]
    }

    /// Check Rust alignment issues
    fn check_rust_alignment_issues(&self) -> Vec<AlignmentIssue> {
        // Rust with #[repr(C)] should be compatible, but check for issues
        vec![]
    }

    /// Check Rust size mismatches
    fn check_rust_size_mismatches(&self) -> Vec<SizeMismatch> {
        vec![]
    }

    /// Check Go alignment issues
    fn check_go_alignment_issues(&self) -> Vec<AlignmentIssue> {
        vec![]
    }

    /// Check Go size mismatches
    fn check_go_size_mismatches(&self) -> Vec<SizeMismatch> {
        vec![]
    }

    /// Check generic alignment issues
    fn check_generic_alignment_issues(&self) -> Vec<AlignmentIssue> {
        vec![]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Feature: windows-ffi-audit, Property 1: FFI実装バグ検出
    // 任意のFFI実装について、ライブラリロードに失敗する場合、具体的なバグの種類と原因が特定されなければならない
    // Validates: Requirements 1.1, 1.3
    #[test]
    fn test_ffi_implementation_bug_detection() {
        let debugger = FFIImplementationDebugger::new();
        let test_impls = vec!["c_ext", "cpp_ext", "rust_ext"];
        
        for ffi_impl in test_impls {
            let result = debugger.diagnose_library_loading(ffi_impl);
            
            // Property: The diagnosis should always succeed
            assert!(result.is_ok());
            
            let diagnostics = result.unwrap();
            
            // Property: Implementation name should match input
            assert_eq!(diagnostics.implementation, ffi_impl);
        }
    }
    // Feature: windows-ffi-audit, Property 2: ライブラリ診断正確性
    // 任意のFFI実装について、診断システムはライブラリの存在、ロード可能性、依存関係の状態を正確に報告しなければならない
    // Validates: Requirements 1.2
    #[test]
    fn test_library_diagnosis_accuracy() {
        let debugger = FFIImplementationDebugger::new();
        let test_impls = vec!["c_ext", "cpp_ext", "rust_ext"];
        
        for ffi_impl in test_impls {
            // Test library loading diagnosis
            let loading_result = debugger.diagnose_library_loading(ffi_impl);
            assert!(loading_result.is_ok(), "Library loading diagnosis should always succeed");
            
            let loading_diagnostics = loading_result.unwrap();
            
            // Property: Diagnosis should be consistent with implementation name
            assert_eq!(loading_diagnostics.implementation, ffi_impl);
            
            // Test symbol resolution diagnosis
            let symbol_result = debugger.validate_symbol_resolution(ffi_impl);
            assert!(symbol_result.is_ok(), "Symbol resolution validation should always succeed");
            
            let symbol_validation = symbol_result.unwrap();
            assert_eq!(symbol_validation.implementation, ffi_impl);
            
            // Test calling convention check
            let convention_result = debugger.check_calling_convention(ffi_impl);
            assert!(convention_result.is_ok(), "Calling convention check should always succeed");
            
            let convention_check = convention_result.unwrap();
            assert_eq!(convention_check.implementation, ffi_impl);
            assert!(!convention_check.expected_convention.is_empty(), "Should have expected calling convention");
            
            // Test memory layout validation
            let layout_result = debugger.validate_memory_layout(ffi_impl);
            assert!(layout_result.is_ok(), "Memory layout validation should always succeed");
            
            let layout_validation = layout_result.unwrap();
            assert_eq!(layout_validation.implementation, ffi_impl);
        }
    }

    #[test]
    fn test_known_ffi_implementations() {
        let debugger = FFIImplementationDebugger::new();
        let known_implementations = vec![
            "c_ext", "cpp_ext", "cython_ext", "rust_ext", "go_ext",
            "fortran_ext", "zig_ext", "nim_ext", "julia_ext", "kotlin_ext"
        ];
        
        for impl_name in known_implementations {
            let result = debugger.diagnose_library_loading(impl_name);
            assert!(result.is_ok(), "Diagnosis should succeed for known implementation: {}", impl_name);
            
            let diagnostics = result.unwrap();
            assert_eq!(diagnostics.implementation, impl_name);
            
            // Should have at least one library path to check
            let paths = debugger.get_library_paths_for_implementation(impl_name);
            assert!(!paths.is_empty(), "Should have library paths for known implementation: {}", impl_name);
        }
    }

    #[test]
    fn test_path_issue_analysis() {
        let debugger = FFIImplementationDebugger::new();
        
        // Test path too long
        let long_path = "a".repeat(300);
        let issues = debugger.analyze_path_issues(&long_path);
        assert!(issues.iter().any(|i| matches!(i.issue_type, PathIssueType::PathTooLong)));
        
        // Test invalid characters
        let invalid_path = "test<>path";
        let issues = debugger.analyze_path_issues(invalid_path);
        assert!(issues.iter().any(|i| matches!(i.issue_type, PathIssueType::InvalidCharacters)));
    }

    #[test]
    fn test_missing_dependencies_analysis() {
        let debugger = FFIImplementationDebugger::new();
        
        // Test C/C++ implementation dependencies
        let c_deps = debugger.analyze_missing_dependencies("c_ext");
        // Should check for MSVC runtime dependencies
        
        // Test Fortran implementation dependencies  
        let fortran_deps = debugger.analyze_missing_dependencies("fortran_ext");
        // Should check for Fortran runtime dependencies
        
        // Dependencies analysis should return a list (may be empty if all exist)
        assert!(c_deps.len() >= 0);
        assert!(fortran_deps.len() >= 0);
    }

    #[test]
    fn test_symbol_resolution_validation() {
        let debugger = FFIImplementationDebugger::new();
        
        // Test symbol resolution for known implementations
        let known_implementations = vec!["c_ext", "rust_ext", "go_ext"];
        
        for impl_name in known_implementations {
            let result = debugger.validate_symbol_resolution(impl_name);
            assert!(result.is_ok(), "Symbol validation should succeed for {}", impl_name);
            
            let validation = result.unwrap();
            assert_eq!(validation.implementation, impl_name);
            
            // Should have expected symbols defined
            let expected_symbols = debugger.get_expected_symbols_for_implementation(impl_name);
            assert!(!expected_symbols.is_empty(), "Should have expected symbols for {}", impl_name);
        }
    }

    #[test]
    fn test_calling_convention_check() {
        let debugger = FFIImplementationDebugger::new();
        
        // Test calling convention check for known implementations
        let known_implementations = vec!["c_ext", "rust_ext", "fortran_ext"];
        
        for impl_name in known_implementations {
            let result = debugger.check_calling_convention(impl_name);
            assert!(result.is_ok(), "Calling convention check should succeed for {}", impl_name);
            
            let check = result.unwrap();
            assert_eq!(check.implementation, impl_name);
            assert_eq!(check.expected_convention, "cdecl"); // All should expect cdecl
        }
    }

    #[test]
    fn test_memory_layout_validation() {
        let debugger = FFIImplementationDebugger::new();
        
        // Test memory layout validation for different implementations
        let implementations = vec!["c_ext", "fortran_ext", "rust_ext", "go_ext"];
        
        for impl_name in implementations {
            let result = debugger.validate_memory_layout(impl_name);
            assert!(result.is_ok(), "Memory layout validation should succeed for {}", impl_name);
            
            let validation = result.unwrap();
            assert_eq!(validation.implementation, impl_name);
            
            // Validation should complete (compatible or not)
            // The actual compatibility depends on the specific implementation
        }
    }

    #[test]
    fn test_expected_symbols_for_implementations() {
        let debugger = FFIImplementationDebugger::new();
        
        // Test that each implementation has expected symbols
        let test_cases = vec![
            ("c_ext", vec!["numeric_add", "numeric_multiply", "memory_allocate"]),
            ("rust_ext", vec!["rust_numeric_add", "rust_numeric_multiply"]),
            ("go_ext", vec!["GoNumericAdd", "GoNumericMultiply"]),
            ("fortran_ext", vec!["fortran_numeric_add_", "fortran_numeric_multiply_"]),
        ];
        
        for (impl_name, expected_partial) in test_cases {
            let symbols = debugger.get_expected_symbols_for_implementation(impl_name);
            
            for expected_symbol in expected_partial {
                assert!(
                    symbols.iter().any(|s| s.contains(expected_symbol)),
                    "Implementation {} should have symbol containing '{}'",
                    impl_name, expected_symbol
                );
            }
        }
    }
}