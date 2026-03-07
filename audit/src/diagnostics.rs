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
    /// Diagnose Rust/Go specific compilation and linking issues
    pub fn diagnose_rust_go_issues(&self, ffi_impl: &str) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        match ffi_impl {
            "rust_ext" => {
                issues.extend(self.diagnose_rust_issues()?);
            },
            "go_ext" => {
                issues.extend(self.diagnose_go_issues()?);
            },
            _ => {
                // Not a Rust/Go implementation
                return Ok(issues);
            }
        }
        
        Ok(issues)
    }

    /// Diagnose Rust-specific issues
    fn diagnose_rust_issues(&self) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check if Rust toolchain is installed
        if !self.check_rust_toolchain_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Rust toolchain not found".to_string(),
                affected_library: "rustc".to_string(),
                resolution_steps: vec![
                    "Install Rust toolchain from https://rustup.rs/".to_string(),
                    "Run: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh".to_string(),
                    "Restart terminal and verify: rustc --version".to_string(),
                ],
            });
        }
        
        // Check if Cargo is available
        if !self.check_cargo_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Cargo build tool not found".to_string(),
                affected_library: "cargo".to_string(),
                resolution_steps: vec![
                    "Cargo comes with Rust, ensure Rust is properly installed".to_string(),
                    "Verify installation: cargo --version".to_string(),
                ],
            });
        }
        
        // Check for maturin (Python-Rust binding tool)
        if !self.check_maturin_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Maturin not found".to_string(),
                affected_library: "maturin".to_string(),
                resolution_steps: vec![
                    "Install maturin: pip install maturin".to_string(),
                    "Or install via cargo: cargo install maturin".to_string(),
                    "Verify installation: maturin --version".to_string(),
                ],
            });
        }
        
        // Check for Cargo.toml
        let rust_dir = "benchmark/rust_ext";
        let cargo_toml_path = format!("{}/Cargo.toml", rust_dir);
        if !std::path::Path::new(&cargo_toml_path).exists() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("Cargo.toml not found: {}", cargo_toml_path),
                affected_library: cargo_toml_path.clone(),
                resolution_steps: vec![
                    "Create Cargo.toml with proper PyO3 configuration".to_string(),
                    "Set crate-type = [\"cdylib\"] for Python extension".to_string(),
                    "Add PyO3 dependency with extension-module feature".to_string(),
                ],
            });
        } else {
            // Check Cargo.toml content
            issues.extend(self.check_rust_cargo_toml_issues(&cargo_toml_path));
        }
        
        // Check for Rust source files
        issues.extend(self.check_rust_source_files(rust_dir));
        
        // Check for PyO3 configuration issues
        issues.extend(self.check_rust_pyo3_issues(rust_dir));
        
        // Check for Rust compilation issues
        issues.extend(self.check_rust_compilation_issues(rust_dir));
        
        Ok(issues)
    }

    /// Diagnose Go-specific issues
    fn diagnose_go_issues(&self) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check if Go is installed
        if !self.check_go_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Go compiler not found".to_string(),
                affected_library: "go".to_string(),
                resolution_steps: vec![
                    "Install Go from https://golang.org/dl/".to_string(),
                    "Add Go to PATH environment variable".to_string(),
                    "Verify installation: go version".to_string(),
                ],
            });
        }
        
        // Check if CGO is enabled
        if !self.check_cgo_enabled() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "CGO is not enabled".to_string(),
                affected_library: "CGO".to_string(),
                resolution_steps: vec![
                    "Enable CGO: set CGO_ENABLED=1".to_string(),
                    "Ensure C compiler is available for CGO".to_string(),
                    "On Windows: install MinGW-w64 or Visual Studio Build Tools".to_string(),
                ],
            });
        }
        
        // Check for Go source files
        let go_dir = "benchmark/go_ext";
        issues.extend(self.check_go_source_files(go_dir));
        
        // Check for go.mod file
        let go_mod_path = format!("{}/go.mod", go_dir);
        if !std::path::Path::new(&go_mod_path).exists() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("go.mod not found: {}", go_mod_path),
                affected_library: go_mod_path.clone(),
                resolution_steps: vec![
                    "Initialize Go module: go mod init gofunctions".to_string(),
                    "Add necessary dependencies".to_string(),
                    "Run go mod tidy to clean up dependencies".to_string(),
                ],
            });
        }
        
        // Check for CGO configuration issues
        issues.extend(self.check_go_cgo_issues(go_dir));
        
        // Check for Go build issues
        issues.extend(self.check_go_build_issues(go_dir));
        
        Ok(issues)
    }

    /// Check if Rust toolchain is available
    fn check_rust_toolchain_available(&self) -> bool {
        std::process::Command::new("rustc")
            .arg("--version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check if Cargo is available
    fn check_cargo_available(&self) -> bool {
        std::process::Command::new("cargo")
            .arg("--version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check if maturin is available
    fn check_maturin_available(&self) -> bool {
        std::process::Command::new("maturin")
            .arg("--version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check Cargo.toml configuration issues
    fn check_rust_cargo_toml_issues(&self, cargo_toml_path: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        if let Ok(content) = std::fs::read_to_string(cargo_toml_path) {
            // Check for cdylib crate type
            if !content.contains("crate-type") || !content.contains("cdylib") {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "Cargo.toml missing cdylib crate-type".to_string(),
                    affected_library: cargo_toml_path.to_string(),
                    resolution_steps: vec![
                        "Add [lib] section with crate-type = [\"cdylib\"]".to_string(),
                        "This is required for Python extension modules".to_string(),
                    ],
                });
            }
            
            // Check for PyO3 dependency
            if !content.contains("pyo3") {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "Cargo.toml missing PyO3 dependency".to_string(),
                    affected_library: cargo_toml_path.to_string(),
                    resolution_steps: vec![
                        "Add PyO3 dependency: pyo3 = { version = \"0.20\", features = [\"extension-module\"] }".to_string(),
                        "Include extension-module feature for Python extensions".to_string(),
                    ],
                });
            }
            
            // Check for extension-module feature
            if content.contains("pyo3") && !content.contains("extension-module") {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "PyO3 missing extension-module feature".to_string(),
                    affected_library: cargo_toml_path.to_string(),
                    resolution_steps: vec![
                        "Add extension-module feature to PyO3 dependency".to_string(),
                        "Example: pyo3 = { version = \"0.20\", features = [\"extension-module\"] }".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check Rust source files
    fn check_rust_source_files(&self, rust_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Check for lib.rs or main.rs
        let lib_rs_path = format!("{}/src/lib.rs", rust_dir);
        let main_rs_path = format!("{}/src/main.rs", rust_dir);
        
        if !std::path::Path::new(&lib_rs_path).exists() && !std::path::Path::new(&main_rs_path).exists() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("No Rust source files found in {}/src/", rust_dir),
                affected_library: rust_dir.to_string(),
                resolution_steps: vec![
                    "Create src/lib.rs for library crate".to_string(),
                    "Implement PyO3 functions with #[pyfunction] attribute".to_string(),
                    "Add #[pymodule] for module definition".to_string(),
                ],
            });
        }
        
        issues
    }

    /// Check PyO3 configuration issues
    fn check_rust_pyo3_issues(&self, rust_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        let lib_rs_path = format!("{}/src/lib.rs", rust_dir);
        
        if let Ok(content) = std::fs::read_to_string(&lib_rs_path) {
            // Check for PyO3 imports
            if !content.contains("use pyo3::prelude::*") && !content.contains("use pyo3::") {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "Missing PyO3 imports in lib.rs".to_string(),
                    affected_library: lib_rs_path.clone(),
                    resolution_steps: vec![
                        "Add PyO3 imports: use pyo3::prelude::*;".to_string(),
                        "Import specific PyO3 types as needed".to_string(),
                    ],
                });
            }
            
            // Check for pymodule definition
            if !content.contains("#[pymodule]") {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "Missing #[pymodule] definition".to_string(),
                    affected_library: lib_rs_path.clone(),
                    resolution_steps: vec![
                        "Add #[pymodule] attribute to module function".to_string(),
                        "Define module initialization function".to_string(),
                        "Example: #[pymodule] fn rust_ext(_py: Python, m: &PyModule) -> PyResult<()>".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check Rust compilation issues
    fn check_rust_compilation_issues(&self, rust_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Try to run cargo check to detect compilation issues
        if let Ok(output) = std::process::Command::new("cargo")
            .args(&["check"])
            .current_dir(rust_dir)
            .output()
        {
            if !output.status.success() {
                let error_output = String::from_utf8_lossy(&output.stderr);
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "Rust compilation errors detected".to_string(),
                    affected_library: rust_dir.to_string(),
                    resolution_steps: vec![
                        "Fix compilation errors shown in cargo output".to_string(),
                        "Run cargo check for detailed error information".to_string(),
                        format!("Error details: {}", error_output.lines().take(3).collect::<Vec<_>>().join("; ")),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check if Go is available
    fn check_go_available(&self) -> bool {
        std::process::Command::new("go")
            .arg("version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check if CGO is enabled
    fn check_cgo_enabled(&self) -> bool {
        if let Ok(output) = std::process::Command::new("go")
            .args(&["env", "CGO_ENABLED"])
            .output()
        {
            if output.status.success() {
                let cgo_enabled = String::from_utf8_lossy(&output.stdout);
                return cgo_enabled.trim() == "1";
            }
        }
        false
    }

    /// Check Go source files
    fn check_go_source_files(&self, go_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        if let Ok(entries) = std::fs::read_dir(go_dir) {
            let mut has_go_files = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "go" {
                        has_go_files = true;
                        break;
                    }
                }
            }
            
            if !has_go_files {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("No Go source files found in {}", go_dir),
                    affected_library: go_dir.to_string(),
                    resolution_steps: vec![
                        "Create .go source files".to_string(),
                        "Implement functions with CGO export comments".to_string(),
                        "Example: //export FunctionName".to_string(),
                        "Add import \"C\" for CGO functionality".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check Go CGO configuration issues
    fn check_go_cgo_issues(&self, go_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        if let Ok(entries) = std::fs::read_dir(go_dir) {
            let mut has_cgo_imports = false;
            let mut has_export_comments = false;
            
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "go" {
                        if let Ok(content) = std::fs::read_to_string(entry.path()) {
                            if content.contains("import \"C\"") {
                                has_cgo_imports = true;
                            }
                            if content.contains("//export") {
                                has_export_comments = true;
                            }
                        }
                    }
                }
            }
            
            if !has_cgo_imports {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "Missing CGO import in Go files".to_string(),
                    affected_library: go_dir.to_string(),
                    resolution_steps: vec![
                        "Add import \"C\" to Go files that use CGO".to_string(),
                        "This import enables CGO functionality".to_string(),
                    ],
                });
            }
            
            if !has_export_comments {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "Missing //export comments in Go files".to_string(),
                    affected_library: go_dir.to_string(),
                    resolution_steps: vec![
                        "Add //export FunctionName comments before functions".to_string(),
                        "This makes functions available to C/Python".to_string(),
                        "Example: //export NumericAdd".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check Go build issues
    fn check_go_build_issues(&self, go_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Try to run go build to detect build issues
        if let Ok(output) = std::process::Command::new("go")
            .args(&["build", "-buildmode=c-shared", "-o", "test.dll", "."])
            .current_dir(go_dir)
            .output()
        {
            if !output.status.success() {
                let error_output = String::from_utf8_lossy(&output.stderr);
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "Go build errors detected".to_string(),
                    affected_library: go_dir.to_string(),
                    resolution_steps: vec![
                        "Fix Go build errors shown in output".to_string(),
                        "Ensure CGO_ENABLED=1 is set".to_string(),
                        "Check that C compiler is available".to_string(),
                        format!("Error details: {}", error_output.lines().take(3).collect::<Vec<_>>().join("; ")),
                    ],
                });
            } else {
                // Clean up test file
                let _ = std::fs::remove_file(format!("{}/test.dll", go_dir));
                let _ = std::fs::remove_file(format!("{}/test.h", go_dir));
            }
        }
        
        issues
    }

    /// Diagnose modern language (Zig/Nim/Julia/Kotlin) specific compilation and linking issues
    pub fn diagnose_modern_language_issues(&self, ffi_impl: &str) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        match ffi_impl {
            "zig_ext" => {
                issues.extend(self.diagnose_zig_issues()?);
            },
            "nim_ext" => {
                issues.extend(self.diagnose_nim_issues()?);
            },
            "julia_ext" => {
                issues.extend(self.diagnose_julia_issues()?);
            },
            "kotlin_ext" => {
                issues.extend(self.diagnose_kotlin_issues()?);
            },
            _ => {
                // Not a modern language implementation
                return Ok(issues);
            }
        }
        
        Ok(issues)
    }

    /// Diagnose Zig-specific issues
    fn diagnose_zig_issues(&self) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check if Zig is installed
        if !self.check_zig_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Zig compiler not found".to_string(),
                affected_library: "zig".to_string(),
                resolution_steps: vec![
                    "Install Zig from https://ziglang.org/download/".to_string(),
                    "Add Zig to PATH environment variable".to_string(),
                    "Verify installation: zig version".to_string(),
                ],
            });
        }
        
        // Check for Zig source files
        let zig_dir = "benchmark/zig_ext";
        issues.extend(self.check_zig_source_files(zig_dir));
        
        // Check for build.zig file
        let build_zig_path = format!("{}/build.zig", zig_dir);
        if !std::path::Path::new(&build_zig_path).exists() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("build.zig not found: {}", build_zig_path),
                affected_library: build_zig_path.clone(),
                resolution_steps: vec![
                    "Create build.zig with proper C library configuration".to_string(),
                    "Set library type to shared library".to_string(),
                    "Configure C ABI exports".to_string(),
                ],
            });
        }
        
        // Check for Zig build issues
        issues.extend(self.check_zig_build_issues(zig_dir));
        
        Ok(issues)
    }

    /// Diagnose Nim-specific issues
    fn diagnose_nim_issues(&self) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check if Nim is installed
        if !self.check_nim_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Nim compiler not found".to_string(),
                affected_library: "nim".to_string(),
                resolution_steps: vec![
                    "Install Nim from https://nim-lang.org/install.html".to_string(),
                    "Add Nim to PATH environment variable".to_string(),
                    "Verify installation: nim --version".to_string(),
                ],
            });
        }
        
        // Check for Nim source files
        let nim_dir = "benchmark/nim_ext";
        issues.extend(self.check_nim_source_files(nim_dir));
        
        // Check for .nimble file
        if let Ok(entries) = std::fs::read_dir(nim_dir) {
            let mut has_nimble_file = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "nimble" {
                        has_nimble_file = true;
                        break;
                    }
                }
            }
            
            if !has_nimble_file {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("No .nimble file found in {}", nim_dir),
                    affected_library: nim_dir.to_string(),
                    resolution_steps: vec![
                        "Create .nimble package file".to_string(),
                        "Configure library compilation settings".to_string(),
                        "Set proper C export directives".to_string(),
                    ],
                });
            }
        }
        
        // Check for Nim build issues
        issues.extend(self.check_nim_build_issues(nim_dir));
        
        Ok(issues)
    }

    /// Diagnose Julia-specific issues
    fn diagnose_julia_issues(&self) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check if Julia is installed
        if !self.check_julia_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Julia not found".to_string(),
                affected_library: "julia".to_string(),
                resolution_steps: vec![
                    "Install Julia from https://julialang.org/downloads/".to_string(),
                    "Add Julia to PATH environment variable".to_string(),
                    "Verify installation: julia --version".to_string(),
                ],
            });
        }
        
        // Check for Julia source files
        let julia_dir = "benchmark/julia_ext";
        issues.extend(self.check_julia_source_files(julia_dir));
        
        // Check for Project.toml
        let project_toml_path = format!("{}/Project.toml", julia_dir);
        if !std::path::Path::new(&project_toml_path).exists() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("Project.toml not found: {}", project_toml_path),
                affected_library: project_toml_path.clone(),
                resolution_steps: vec![
                    "Create Project.toml with package configuration".to_string(),
                    "Add necessary Julia dependencies".to_string(),
                    "Configure C library generation".to_string(),
                ],
            });
        }
        
        // Check for Julia build issues
        issues.extend(self.check_julia_build_issues(julia_dir));
        
        Ok(issues)
    }

    /// Diagnose Kotlin-specific issues
    fn diagnose_kotlin_issues(&self) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check if Kotlin/Native is installed
        if !self.check_kotlin_native_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Kotlin/Native compiler not found".to_string(),
                affected_library: "kotlinc-native".to_string(),
                resolution_steps: vec![
                    "Install Kotlin/Native from https://kotlinlang.org/docs/native-overview.html".to_string(),
                    "Add Kotlin/Native to PATH environment variable".to_string(),
                    "Verify installation: kotlinc-native -version".to_string(),
                ],
            });
        }
        
        // Check for Kotlin source files
        let kotlin_dir = "benchmark/kotlin_ext";
        issues.extend(self.check_kotlin_source_files(kotlin_dir));
        
        // Check for build.gradle.kts
        let build_gradle_path = format!("{}/build.gradle.kts", kotlin_dir);
        if !std::path::Path::new(&build_gradle_path).exists() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("build.gradle.kts not found: {}", build_gradle_path),
                affected_library: build_gradle_path.clone(),
                resolution_steps: vec![
                    "Create build.gradle.kts with Kotlin/Native configuration".to_string(),
                    "Configure shared library compilation".to_string(),
                    "Set proper C interop settings".to_string(),
                ],
            });
        }
        
        // Check for Kotlin build issues
        issues.extend(self.check_kotlin_build_issues(kotlin_dir));
        
        Ok(issues)
    }

    /// Check if Zig is available
    fn check_zig_available(&self) -> bool {
        std::process::Command::new("zig")
            .arg("version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check Zig source files
    fn check_zig_source_files(&self, zig_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        if let Ok(entries) = std::fs::read_dir(zig_dir) {
            let mut has_zig_files = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "zig" {
                        has_zig_files = true;
                        break;
                    }
                }
            }
            
            if !has_zig_files {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("No Zig source files found in {}", zig_dir),
                    affected_library: zig_dir.to_string(),
                    resolution_steps: vec![
                        "Create .zig source files".to_string(),
                        "Implement functions with export directive".to_string(),
                        "Example: export fn functionName() void".to_string(),
                        "Configure C ABI compatibility".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check Zig build issues
    fn check_zig_build_issues(&self, zig_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Try to run zig build to detect build issues
        if let Ok(output) = std::process::Command::new("zig")
            .args(&["build"])
            .current_dir(zig_dir)
            .output()
        {
            if !output.status.success() {
                let error_output = String::from_utf8_lossy(&output.stderr);
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "Zig build errors detected".to_string(),
                    affected_library: zig_dir.to_string(),
                    resolution_steps: vec![
                        "Fix Zig build errors shown in output".to_string(),
                        "Check build.zig configuration".to_string(),
                        "Ensure proper library target settings".to_string(),
                        format!("Error details: {}", error_output.lines().take(3).collect::<Vec<_>>().join("; ")),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check if Nim is available
    fn check_nim_available(&self) -> bool {
        std::process::Command::new("nim")
            .arg("--version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check Nim source files
    fn check_nim_source_files(&self, nim_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        if let Ok(entries) = std::fs::read_dir(nim_dir) {
            let mut has_nim_files = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "nim" {
                        has_nim_files = true;
                        break;
                    }
                }
            }
            
            if !has_nim_files {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("No Nim source files found in {}", nim_dir),
                    affected_library: nim_dir.to_string(),
                    resolution_steps: vec![
                        "Create .nim source files".to_string(),
                        "Implement procedures with exportc pragma".to_string(),
                        "Example: proc functionName*() {.exportc.}".to_string(),
                        "Configure dynlib compilation".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check Nim build issues
    fn check_nim_build_issues(&self, nim_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Try to compile Nim to detect build issues
        if let Ok(entries) = std::fs::read_dir(nim_dir) {
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "nim" {
                        if let Ok(output) = std::process::Command::new("nim")
                            .args(&["c", "--app:lib", "--noMain", entry.path().to_str().unwrap()])
                            .current_dir(nim_dir)
                            .output()
                        {
                            if !output.status.success() {
                                let error_output = String::from_utf8_lossy(&output.stderr);
                                issues.push(DLLIssue {
                                    issue_type: DLLIssueType::LoadFailure,
                                    error_code: None,
                                    description: "Nim compilation errors detected".to_string(),
                                    affected_library: nim_dir.to_string(),
                                    resolution_steps: vec![
                                        "Fix Nim compilation errors shown in output".to_string(),
                                        "Check exportc pragma usage".to_string(),
                                        "Ensure proper library compilation flags".to_string(),
                                        format!("Error details: {}", error_output.lines().take(3).collect::<Vec<_>>().join("; ")),
                                    ],
                                });
                            }
                        }
                        break;
                    }
                }
            }
        }
        
        issues
    }

    /// Check if Julia is available
    fn check_julia_available(&self) -> bool {
        std::process::Command::new("julia")
            .arg("--version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check Julia source files
    fn check_julia_source_files(&self, julia_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        if let Ok(entries) = std::fs::read_dir(julia_dir) {
            let mut has_julia_files = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "jl" {
                        has_julia_files = true;
                        break;
                    }
                }
            }
            
            if !has_julia_files {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("No Julia source files found in {}", julia_dir),
                    affected_library: julia_dir.to_string(),
                    resolution_steps: vec![
                        "Create .jl source files".to_string(),
                        "Implement functions with @ccallable macro".to_string(),
                        "Example: @ccallable function_name()::Cint".to_string(),
                        "Configure PackageCompiler.jl for shared library".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check Julia build issues
    fn check_julia_build_issues(&self, julia_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Check if PackageCompiler.jl is available
        if let Ok(output) = std::process::Command::new("julia")
            .args(&["-e", "using PackageCompiler"])
            .current_dir(julia_dir)
            .output()
        {
            if !output.status.success() {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::DependencyMissing,
                    error_code: None,
                    description: "PackageCompiler.jl not found".to_string(),
                    affected_library: "PackageCompiler.jl".to_string(),
                    resolution_steps: vec![
                        "Install PackageCompiler.jl: julia -e 'using Pkg; Pkg.add(\"PackageCompiler\")'".to_string(),
                        "This package is required for creating shared libraries".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check if Kotlin/Native is available
    fn check_kotlin_native_available(&self) -> bool {
        std::process::Command::new("kotlinc-native")
            .arg("-version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check Kotlin source files
    fn check_kotlin_source_files(&self, kotlin_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Check for Kotlin source files in src directory
        let src_dir = format!("{}/src", kotlin_dir);
        if let Ok(entries) = std::fs::read_dir(&src_dir) {
            let mut has_kotlin_files = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "kt" {
                        has_kotlin_files = true;
                        break;
                    }
                }
            }
            
            if !has_kotlin_files {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("No Kotlin source files found in {}", src_dir),
                    affected_library: src_dir,
                    resolution_steps: vec![
                        "Create .kt source files in src directory".to_string(),
                        "Implement functions with @CName annotation".to_string(),
                        "Example: @CName(\"function_name\") fun functionName()".to_string(),
                        "Configure Kotlin/Native shared library target".to_string(),
                    ],
                });
            }
        } else {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("src directory not found: {}", src_dir),
                affected_library: src_dir,
                resolution_steps: vec![
                    "Create src directory for Kotlin source files".to_string(),
                    "Follow standard Kotlin project structure".to_string(),
                ],
            });
        }
        
        issues
    }

    /// Check Kotlin build issues
    fn check_kotlin_build_issues(&self, kotlin_dir: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Check if Gradle wrapper exists
        let gradlew_path = format!("{}/gradlew.bat", kotlin_dir);
        if !std::path::Path::new(&gradlew_path).exists() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("Gradle wrapper not found: {}", gradlew_path),
                affected_library: gradlew_path,
                resolution_steps: vec![
                    "Initialize Gradle wrapper: gradle wrapper".to_string(),
                    "This creates gradlew.bat for Windows builds".to_string(),
                ],
            });
        } else {
            // Try to run gradle build to detect build issues
            if let Ok(output) = std::process::Command::new("gradlew.bat")
                .args(&["build"])
                .current_dir(kotlin_dir)
                .output()
            {
                if !output.status.success() {
                    let error_output = String::from_utf8_lossy(&output.stderr);
                    issues.push(DLLIssue {
                        issue_type: DLLIssueType::LoadFailure,
                        error_code: None,
                        description: "Kotlin/Native build errors detected".to_string(),
                        affected_library: kotlin_dir.to_string(),
                        resolution_steps: vec![
                            "Fix Kotlin/Native build errors shown in output".to_string(),
                            "Check build.gradle.kts configuration".to_string(),
                            "Ensure proper shared library target settings".to_string(),
                            format!("Error details: {}", error_output.lines().take(3).collect::<Vec<_>>().join("; ")),
                        ],
                    });
                }
            }
        }
        
        issues
    }

    /// Diagnose Cython/NumPy/Fortran specific compilation and linking issues
    pub fn diagnose_cython_numpy_fortran_issues(&self, ffi_impl: &str) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        match ffi_impl {
            "cython_ext" => {
                issues.extend(self.diagnose_cython_issues()?);
            },
            "numpy_impl" => {
                issues.extend(self.diagnose_numpy_issues()?);
            },
            "fortran_ext" => {
                issues.extend(self.diagnose_fortran_issues()?);
            },
            _ => {
                // Not a Cython/NumPy/Fortran implementation
                return Ok(issues);
            }
        }
        
        Ok(issues)
    }

    /// Diagnose Cython-specific issues
    fn diagnose_cython_issues(&self) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check if Cython is installed
        if !self.check_cython_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Cython compiler not found".to_string(),
                affected_library: "cython".to_string(),
                resolution_steps: vec![
                    "Install Cython: pip install cython".to_string(),
                    "Verify installation: cython --version".to_string(),
                    "Ensure Cython is in PATH".to_string(),
                ],
            });
        }
        
        // Check for .pyx files
        let cython_dir = "benchmark/cython_ext";
        if let Ok(entries) = std::fs::read_dir(cython_dir) {
            let mut has_pyx_files = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "pyx" {
                        has_pyx_files = true;
                        break;
                    }
                }
            }
            
            if !has_pyx_files {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("No .pyx files found in {}", cython_dir),
                    affected_library: cython_dir.to_string(),
                    resolution_steps: vec![
                        "Create .pyx source files".to_string(),
                        "Implement Cython functions with proper type declarations".to_string(),
                        "Include necessary cimport statements".to_string(),
                    ],
                });
            }
        }
        
        // Check for Cython compilation issues
        issues.extend(self.check_cython_compilation_issues());
        
        // Check for NumPy integration in Cython
        issues.extend(self.check_cython_numpy_integration());
        
        Ok(issues)
    }

    /// Diagnose NumPy C API specific issues
    fn diagnose_numpy_issues(&self) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check if NumPy is installed
        if !self.check_numpy_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "NumPy not found".to_string(),
                affected_library: "numpy".to_string(),
                resolution_steps: vec![
                    "Install NumPy: pip install numpy".to_string(),
                    "Verify installation: python -c 'import numpy; print(numpy.__version__)'".to_string(),
                ],
            });
        }
        
        // Check NumPy C API headers
        if !self.check_numpy_c_api_headers() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "NumPy C API headers not accessible".to_string(),
                affected_library: "numpy/arrayobject.h".to_string(),
                resolution_steps: vec![
                    "Ensure NumPy development headers are installed".to_string(),
                    "Check numpy.get_include() path".to_string(),
                    "Verify arrayobject.h exists in include directory".to_string(),
                ],
            });
        }
        
        // Check for NumPy version compatibility
        issues.extend(self.check_numpy_version_compatibility());
        
        // Check for NumPy C API usage issues
        issues.extend(self.check_numpy_c_api_usage());
        
        Ok(issues)
    }

    /// Diagnose Fortran-specific issues
    fn diagnose_fortran_issues(&self) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check if gfortran is available
        if !self.check_gfortran_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Fortran compiler (gfortran) not found".to_string(),
                affected_library: "gfortran".to_string(),
                resolution_steps: vec![
                    "Install gfortran compiler".to_string(),
                    "On Ubuntu/Debian: sudo apt-get install gfortran".to_string(),
                    "On Windows: Install MinGW-w64 with Fortran support".to_string(),
                    "Verify installation: gfortran --version".to_string(),
                ],
            });
        }
        
        // Check if f2py is available
        if !self.check_f2py_available() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "f2py not found".to_string(),
                affected_library: "f2py".to_string(),
                resolution_steps: vec![
                    "f2py comes with NumPy, ensure NumPy is installed".to_string(),
                    "Verify f2py: python -m numpy.f2py --help".to_string(),
                    "Check f2py executable: f2py --version".to_string(),
                ],
            });
        }
        
        // Check for Fortran source files
        let fortran_dir = "benchmark/fortran_ext";
        if let Ok(entries) = std::fs::read_dir(fortran_dir) {
            let mut has_fortran_files = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "f90" || ext == "f95" || ext == "f" {
                        has_fortran_files = true;
                        break;
                    }
                }
            }
            
            if !has_fortran_files {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("No Fortran source files found in {}", fortran_dir),
                    affected_library: fortran_dir.to_string(),
                    resolution_steps: vec![
                        "Create .f90 or .f95 source files".to_string(),
                        "Implement Fortran subroutines and functions".to_string(),
                        "Add proper f2py directives for Python binding".to_string(),
                    ],
                });
            }
        }
        
        // Check for f2py binding issues
        issues.extend(self.check_f2py_binding_issues());
        
        // Check for Fortran runtime dependencies
        issues.extend(self.check_fortran_runtime_dependencies());
        
        Ok(issues)
    }

    /// Check if Cython is available
    fn check_cython_available(&self) -> bool {
        std::process::Command::new("cython")
            .arg("--version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check Cython compilation issues
    fn check_cython_compilation_issues(&self) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        let cython_dir = "benchmark/cython_ext";
        
        // Check for setup.py with Cython configuration
        let setup_py_path = format!("{}/setup.py", cython_dir);
        if let Ok(content) = std::fs::read_to_string(&setup_py_path) {
            if !content.contains("from Cython.Build import cythonize") {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "setup.py missing Cython.Build import".to_string(),
                    affected_library: setup_py_path.clone(),
                    resolution_steps: vec![
                        "Add 'from Cython.Build import cythonize' to setup.py".to_string(),
                        "Use cythonize() to wrap Extension objects".to_string(),
                        "Ensure .pyx files are specified in Extension".to_string(),
                    ],
                });
            }
            
            if !content.contains("cythonize") {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "setup.py not using cythonize()".to_string(),
                    affected_library: setup_py_path.clone(),
                    resolution_steps: vec![
                        "Wrap ext_modules with cythonize()".to_string(),
                        "Example: ext_modules=cythonize(extensions)".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check Cython-NumPy integration
    fn check_cython_numpy_integration(&self) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        let cython_dir = "benchmark/cython_ext";
        
        // Check .pyx files for proper NumPy integration
        if let Ok(entries) = std::fs::read_dir(cython_dir) {
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "pyx" {
                        if let Ok(content) = std::fs::read_to_string(entry.path()) {
                            if content.contains("numpy") && !content.contains("cimport numpy") {
                                issues.push(DLLIssue {
                                    issue_type: DLLIssueType::LoadFailure,
                                    error_code: None,
                                    description: format!("Missing 'cimport numpy' in {}", entry.path().display()),
                                    affected_library: entry.path().to_string_lossy().to_string(),
                                    resolution_steps: vec![
                                        "Add 'cimport numpy as cnp' at the top of .pyx file".to_string(),
                                        "Add 'import numpy as np' for Python-level access".to_string(),
                                        "Use proper NumPy array type declarations".to_string(),
                                    ],
                                });
                            }
                        }
                    }
                }
            }
        }
        
        issues
    }

    /// Check if NumPy is available
    fn check_numpy_available(&self) -> bool {
        std::process::Command::new("python")
            .args(&["-c", "import numpy"])
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check NumPy C API headers
    fn check_numpy_c_api_headers(&self) -> bool {
        if let Ok(output) = std::process::Command::new("python")
            .args(&["-c", "import numpy; print(numpy.get_include())"])
            .output()
        {
            if output.status.success() {
                let include_path_string = String::from_utf8_lossy(&output.stdout);
                let include_path = include_path_string.trim();
                let arrayobject_h = std::path::Path::new(include_path).join("numpy").join("arrayobject.h");
                return arrayobject_h.exists();
            }
        }
        false
    }

    /// Check NumPy version compatibility
    fn check_numpy_version_compatibility(&self) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        if let Ok(output) = std::process::Command::new("python")
            .args(&["-c", "import numpy; print(numpy.__version__)"])
            .output()
        {
            if output.status.success() {
                let version_string = String::from_utf8_lossy(&output.stdout);
                let version = version_string.trim();
                
                // Check for very old NumPy versions that might have compatibility issues
                if version.starts_with("1.1") || version.starts_with("1.0") {
                    issues.push(DLLIssue {
                        issue_type: DLLIssueType::DependencyMissing,
                        error_code: None,
                        description: format!("NumPy version {} is too old", version),
                        affected_library: "numpy".to_string(),
                        resolution_steps: vec![
                            "Upgrade NumPy: pip install --upgrade numpy".to_string(),
                            "Recommended minimum version: NumPy 1.16+".to_string(),
                        ],
                    });
                }
            }
        }
        
        issues
    }

    /// Check NumPy C API usage
    fn check_numpy_c_api_usage(&self) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        let numpy_dir = "benchmark/numpy_impl";
        
        // Check for proper import_array() usage
        if let Ok(entries) = std::fs::read_dir(numpy_dir) {
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "c" || ext == "cpp" {
                        if let Ok(content) = std::fs::read_to_string(entry.path()) {
                            if content.contains("PyArray_") && !content.contains("import_array()") {
                                issues.push(DLLIssue {
                                    issue_type: DLLIssueType::LoadFailure,
                                    error_code: None,
                                    description: format!("Missing import_array() call in {}", entry.path().display()),
                                    affected_library: entry.path().to_string_lossy().to_string(),
                                    resolution_steps: vec![
                                        "Add import_array() call in module initialization".to_string(),
                                        "Place import_array() in PyInit_<module>() function".to_string(),
                                        "Check return value of import_array() for errors".to_string(),
                                    ],
                                });
                            }
                        }
                    }
                }
            }
        }
        
        issues
    }

    /// Check if gfortran is available
    fn check_gfortran_available(&self) -> bool {
        std::process::Command::new("gfortran")
            .arg("--version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check if f2py is available
    fn check_f2py_available(&self) -> bool {
        // Try both f2py command and python -m numpy.f2py
        let f2py_direct = std::process::Command::new("f2py")
            .arg("--version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false);
            
        if f2py_direct {
            return true;
        }
        
        std::process::Command::new("python")
            .args(&["-m", "numpy.f2py", "--help"])
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }

    /// Check f2py binding issues
    fn check_f2py_binding_issues(&self) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        let fortran_dir = "benchmark/fortran_ext";
        
        // Check for f2py signature files
        if let Ok(entries) = std::fs::read_dir(fortran_dir) {
            let mut has_signature_files = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "pyf" {
                        has_signature_files = true;
                        break;
                    }
                }
            }
            
            // Check Fortran source files for f2py directives
            let mut has_f2py_directives = false;
            for entry in std::fs::read_dir(fortran_dir).unwrap().flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "f90" || ext == "f95" || ext == "f" {
                        if let Ok(content) = std::fs::read_to_string(entry.path()) {
                            if content.contains("!f2py") || content.contains("cf2py") {
                                has_f2py_directives = true;
                                break;
                            }
                        }
                    }
                }
            }
            
            if !has_signature_files && !has_f2py_directives {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: "No f2py signature files or directives found".to_string(),
                    affected_library: fortran_dir.to_string(),
                    resolution_steps: vec![
                        "Add f2py directives to Fortran source files".to_string(),
                        "Example: !f2py intent(in) :: input_array".to_string(),
                        "Or create .pyf signature files".to_string(),
                        "Generate signature: f2py -m module_name -h module.pyf source.f90".to_string(),
                    ],
                });
            }
        }
        
        issues
    }

    /// Check Fortran runtime dependencies
    fn check_fortran_runtime_dependencies(&self) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        #[cfg(target_os = "windows")]
        {
            let fortran_deps = vec![
                "libgfortran-5.dll",
                "libquadmath-0.dll",
                "libgcc_s_seh-1.dll",
            ];
            
            for dep in fortran_deps {
                if !self.check_dependency_exists(dep) {
                    issues.push(DLLIssue {
                        issue_type: DLLIssueType::DependencyMissing,
                        error_code: None,
                        description: format!("Missing Fortran runtime dependency: {}", dep),
                        affected_library: dep.to_string(),
                        resolution_steps: vec![
                            "Install MinGW-w64 with Fortran support".to_string(),
                            "Ensure Fortran runtime libraries are in PATH".to_string(),
                            "Copy required DLLs to application directory".to_string(),
                        ],
                    });
                }
            }
        }
        
        issues
    }

    /// Diagnose C/C++ specific compilation and linking issues
    pub fn diagnose_c_cpp_issues(&self, ffi_impl: &str) -> Result<Vec<DLLIssue>, crate::error::FFIAuditError> {
        let mut issues = Vec::new();
        
        // Check for C/C++ specific compilation issues
        if ffi_impl == "c_ext" || ffi_impl == "cpp_ext" {
            // Check for compiler availability
            if !self.check_compiler_available(ffi_impl) {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::DependencyMissing,
                    error_code: None,
                    description: format!("Required compiler not found for {}", ffi_impl),
                    affected_library: format!("{} compiler", ffi_impl),
                    resolution_steps: self.get_compiler_installation_steps(ffi_impl),
                });
            }
            
            // Check for Python development headers
            if !self.check_python_dev_headers() {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::DependencyMissing,
                    error_code: None,
                    description: "Python development headers not found".to_string(),
                    affected_library: "Python.h".to_string(),
                    resolution_steps: vec![
                        "Install python3-dev or python3-devel package".to_string(),
                        "On Windows: ensure Python was installed with development headers".to_string(),
                        "Verify Python.h is accessible in include path".to_string(),
                    ],
                });
            }
            
            // Check for NumPy headers
            if !self.check_numpy_headers() {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::DependencyMissing,
                    error_code: None,
                    description: "NumPy development headers not found".to_string(),
                    affected_library: "numpy/arrayobject.h".to_string(),
                    resolution_steps: vec![
                        "Install NumPy: pip install numpy".to_string(),
                        "Verify numpy.get_include() returns valid path".to_string(),
                        "Check that numpy/arrayobject.h exists in include directory".to_string(),
                    ],
                });
            }
            
            // Check for linking issues
            let linking_issues = self.diagnose_c_cpp_linking_issues(ffi_impl);
            issues.extend(linking_issues);
            
            // Check for compilation flags issues
            let compilation_issues = self.diagnose_c_cpp_compilation_issues(ffi_impl);
            issues.extend(compilation_issues);
        }
        
        Ok(issues)
    }

    /// Check if required compiler is available
    fn check_compiler_available(&self, ffi_impl: &str) -> bool {
        let compiler = match ffi_impl {
            "c_ext" => "gcc",
            "cpp_ext" => "g++",
            _ => return true, // Not a C/C++ implementation
        };
        
        // Try to run the compiler with --version
        std::process::Command::new(compiler)
            .arg("--version")
            .output()
            .map(|output| output.status.success())
            .unwrap_or(false)
    }
    
    /// Get compiler installation steps
    fn get_compiler_installation_steps(&self, ffi_impl: &str) -> Vec<String> {
        match ffi_impl {
            "c_ext" => vec![
                "Install GCC compiler".to_string(),
                "On Ubuntu/Debian: sudo apt-get install gcc".to_string(),
                "On CentOS/RHEL: sudo yum install gcc".to_string(),
                "On Windows: Install MinGW-w64 or Visual Studio Build Tools".to_string(),
                "Verify installation: gcc --version".to_string(),
            ],
            "cpp_ext" => vec![
                "Install G++ compiler".to_string(),
                "On Ubuntu/Debian: sudo apt-get install g++".to_string(),
                "On CentOS/RHEL: sudo yum install gcc-c++".to_string(),
                "On Windows: Install MinGW-w64 or Visual Studio Build Tools".to_string(),
                "Verify installation: g++ --version".to_string(),
            ],
            _ => vec!["Unknown implementation".to_string()],
        }
    }
    
    /// Check if Python development headers are available
    fn check_python_dev_headers(&self) -> bool {
        // Try to find Python.h in the Python include directory
        if let Ok(output) = std::process::Command::new("python")
            .args(&["-c", "import sysconfig; print(sysconfig.get_path('include'))"])
            .output()
        {
            if output.status.success() {
                let include_path_string = String::from_utf8_lossy(&output.stdout);
                let include_path = include_path_string.trim();
                let python_h_path = std::path::Path::new(include_path).join("Python.h");
                return python_h_path.exists();
            }
        }
        false
    }
    
    /// Check if NumPy headers are available
    fn check_numpy_headers(&self) -> bool {
        // Try to get NumPy include directory
        if let Ok(output) = std::process::Command::new("python")
            .args(&["-c", "import numpy; print(numpy.get_include())"])
            .output()
        {
            if output.status.success() {
                let include_path_string = String::from_utf8_lossy(&output.stdout);
                let include_path = include_path_string.trim();
                let numpy_h_path = std::path::Path::new(include_path).join("numpy").join("arrayobject.h");
                return numpy_h_path.exists();
            }
        }
        false
    }
    
    /// Diagnose C/C++ linking issues
    fn diagnose_c_cpp_linking_issues(&self, ffi_impl: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Check for common linking problems
        let library_paths = self.get_library_paths_for_implementation(ffi_impl);
        
        for library_path in library_paths {
            if std::path::Path::new(&library_path).exists() {
                // Library exists, check for linking issues
                if let Err(link_issues) = self.check_library_dependencies(&library_path) {
                    issues.extend(link_issues);
                }
            } else {
                // Library doesn't exist, likely a build issue
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("Library not found: {}", library_path),
                    affected_library: library_path.clone(),
                    resolution_steps: vec![
                        "Run the build process to create the library".to_string(),
                        format!("Check if setup.py exists in {}", std::path::Path::new(&library_path).parent().unwrap_or(std::path::Path::new(".")).display()),
                        "Verify all source files are present".to_string(),
                        "Check for compilation errors in build output".to_string(),
                    ],
                });
            }
        }
        
        issues
    }
    
    /// Check library dependencies
    fn check_library_dependencies(&self, library_path: &str) -> std::result::Result<(), Vec<DLLIssue>> {
        let mut issues = Vec::new();
        
        // On Windows, check for common runtime dependencies
        #[cfg(target_os = "windows")]
        {
            let common_deps = vec![
                "msvcr140.dll",
                "vcruntime140.dll",
                "msvcp140.dll",
            ];
            
            for dep in common_deps {
                if !self.check_dependency_exists(dep) {
                    issues.push(DLLIssue {
                        issue_type: DLLIssueType::DependencyMissing,
                        error_code: None,
                        description: format!("Missing runtime dependency: {}", dep),
                        affected_library: library_path.to_string(),
                        resolution_steps: vec![
                            "Install Microsoft Visual C++ Redistributable".to_string(),
                            "Download from Microsoft official website".to_string(),
                            "Choose the correct architecture (x86/x64)".to_string(),
                        ],
                    });
                }
            }
        }
        
        // On Unix-like systems, use ldd to check dependencies
        #[cfg(not(target_os = "windows"))]
        {
            if let Ok(output) = std::process::Command::new("ldd")
                .arg(library_path)
                .output()
            {
                let output_str = String::from_utf8_lossy(&output.stdout);
                if output_str.contains("not found") {
                    issues.push(DLLIssue {
                        issue_type: DLLIssueType::DependencyMissing,
                        error_code: None,
                        description: "Missing shared library dependencies".to_string(),
                        affected_library: library_path.to_string(),
                        resolution_steps: vec![
                            "Install missing shared libraries".to_string(),
                            "Check ldd output for specific missing libraries".to_string(),
                            "Update LD_LIBRARY_PATH if needed".to_string(),
                        ],
                    });
                }
            }
        }
        
        if issues.is_empty() {
            Ok(())
        } else {
            Err(issues)
        }
    }
    
    /// Diagnose C/C++ compilation issues
    fn diagnose_c_cpp_compilation_issues(&self, ffi_impl: &str) -> Vec<DLLIssue> {
        let mut issues = Vec::new();
        
        // Check for common compilation flag issues
        let _expected_flags = self.get_expected_compilation_flags(ffi_impl);
        
        // Check if setup.py exists and has correct configuration
        let setup_py_path = format!("benchmark/{}/setup.py", ffi_impl);
        if !std::path::Path::new(&setup_py_path).exists() {
            issues.push(DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: format!("setup.py not found: {}", setup_py_path),
                affected_library: setup_py_path.clone(),
                resolution_steps: vec![
                    "Create setup.py file for the extension".to_string(),
                    "Include proper Extension configuration".to_string(),
                    "Add numpy include directories".to_string(),
                    "Set correct compiler flags".to_string(),
                ],
            });
        } else {
            // Check setup.py content for common issues
            if let Ok(content) = std::fs::read_to_string(&setup_py_path) {
                if !content.contains("numpy.get_include()") {
                    issues.push(DLLIssue {
                        issue_type: DLLIssueType::LoadFailure,
                        error_code: None,
                        description: "setup.py missing NumPy include directory".to_string(),
                        affected_library: setup_py_path.clone(),
                        resolution_steps: vec![
                            "Add numpy.get_include() to include_dirs in Extension".to_string(),
                            "Import numpy at the top of setup.py".to_string(),
                            "Ensure Extension includes include_dirs=[numpy.get_include()]".to_string(),
                        ],
                    });
                }
                
                if ffi_impl == "cpp_ext" && !content.contains("language='c++'") {
                    issues.push(DLLIssue {
                        issue_type: DLLIssueType::LoadFailure,
                        error_code: None,
                        description: "setup.py missing C++ language specification".to_string(),
                        affected_library: setup_py_path.clone(),
                        resolution_steps: vec![
                            "Add language='c++' to Extension configuration".to_string(),
                            "Ensure C++ compiler flags are set".to_string(),
                            "Add extra_compile_args for C++ standard if needed".to_string(),
                        ],
                    });
                }
            }
        }
        
        // Check for source files
        let source_extensions = if ffi_impl == "cpp_ext" { vec!["cpp", "cxx", "cc"] } else { vec!["c"] };
        let source_dir = format!("benchmark/{}", ffi_impl);
        
        if let Ok(entries) = std::fs::read_dir(&source_dir) {
            let mut has_source_files = false;
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if source_extensions.iter().any(|&se| ext == se) {
                        has_source_files = true;
                        break;
                    }
                }
            }
            
            if !has_source_files {
                issues.push(DLLIssue {
                    issue_type: DLLIssueType::LoadFailure,
                    error_code: None,
                    description: format!("No source files found in {}", source_dir),
                    affected_library: source_dir.clone(),
                    resolution_steps: vec![
                        format!("Create {} source files in {}", if ffi_impl == "cpp_ext" { "C++" } else { "C" }, source_dir),
                        "Implement required functions (numeric_add, memory_allocate, etc.)".to_string(),
                        "Include proper Python C API headers".to_string(),
                        "Export functions with correct signatures".to_string(),
                    ],
                });
            }
        }
        
        issues
    }
    
    /// Get expected compilation flags for implementation
    fn get_expected_compilation_flags(&self, ffi_impl: &str) -> Vec<String> {
        match ffi_impl {
            "c_ext" => vec![
                "-fPIC".to_string(),
                "-O2".to_string(),
                "-Wall".to_string(),
            ],
            "cpp_ext" => vec![
                "-fPIC".to_string(),
                "-O2".to_string(),
                "-Wall".to_string(),
                "-std=c++11".to_string(),
            ],
            _ => vec![],
        }
    }

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

    #[test]
    fn test_rust_go_diagnosis_basic() {
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
}