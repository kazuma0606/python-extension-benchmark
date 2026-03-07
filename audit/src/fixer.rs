//! FFI Implementation Fixer
//! 
//! This module provides functionality to fix detected issues
//! in FFI implementations.

use crate::error::{Result, BuildScriptResult, PathCorrectionResult, SymbolExportValidationResult, CompatibilityLayerResult};
use crate::types::*;
use pyo3::prelude::*;

/// FFI Implementation Fixer
/// 
/// Fixes detected issues in FFI implementations to prevent
/// fallback to pure Python implementations.
#[pyclass]
#[derive(Debug, Clone)]
pub struct FFIImplementationFixer {
    // Implementation will be added in subsequent tasks
}

#[pymethods]
impl FFIImplementationFixer {
    #[new]
    pub fn new() -> Self {
        Self {}
    }
}

impl FFIImplementationFixer {
    /// Fix Cython/NumPy/Fortran specific compilation and linking issues
    pub fn fix_cython_numpy_fortran_issues(&self, ffi_impl: &str, issues: &[DLLIssue]) -> Result<Vec<String>> {
        let mut fix_actions = Vec::new();
        
        for issue in issues {
            match ffi_impl {
                "cython_ext" => {
                    fix_actions.extend(self.fix_cython_specific_issue(issue));
                },
                "numpy_impl" => {
                    fix_actions.extend(self.fix_numpy_specific_issue(issue));
                },
                "fortran_ext" => {
                    fix_actions.extend(self.fix_fortran_specific_issue(issue));
                },
                _ => {
                    fix_actions.push(format!("Unsupported implementation for Cython/NumPy/Fortran fixes: {}", ffi_impl));
                }
            }
        }
        
        Ok(fix_actions)
    }

    /// Fix Cython-specific issues
    fn fix_cython_specific_issue(&self, issue: &DLLIssue) -> Vec<String> {
        let mut actions = Vec::new();
        
        match &issue.issue_type {
            DLLIssueType::DependencyMissing => {
                if issue.description.contains("Cython compiler") {
                    actions.extend(vec![
                        "Installing Cython...".to_string(),
                        "pip install cython".to_string(),
                        "Verifying Cython installation...".to_string(),
                        "cython --version".to_string(),
                    ]);
                }
            },
            DLLIssueType::LoadFailure => {
                if issue.description.contains("No .pyx files found") {
                    actions.extend(self.create_cython_source_files());
                } else if issue.description.contains("setup.py missing Cython.Build") {
                    actions.extend(self.fix_cython_setup_py());
                } else if issue.description.contains("Missing 'cimport numpy'") {
                    actions.extend(self.fix_cython_numpy_imports(&issue.affected_library));
                }
            },
            _ => {
                actions.push(format!("Manual intervention required for Cython issue: {}", issue.description));
            }
        }
        
        actions
    }

    /// Fix NumPy-specific issues
    fn fix_numpy_specific_issue(&self, issue: &DLLIssue) -> Vec<String> {
        let mut actions = Vec::new();
        
        match &issue.issue_type {
            DLLIssueType::DependencyMissing => {
                if issue.description.contains("NumPy not found") {
                    actions.extend(vec![
                        "Installing NumPy...".to_string(),
                        "pip install numpy".to_string(),
                        "Verifying NumPy installation...".to_string(),
                        "python -c 'import numpy; print(numpy.__version__)'".to_string(),
                    ]);
                } else if issue.description.contains("NumPy version") && issue.description.contains("too old") {
                    actions.extend(vec![
                        "Upgrading NumPy...".to_string(),
                        "pip install --upgrade numpy".to_string(),
                        "Verifying NumPy version...".to_string(),
                        "python -c 'import numpy; print(numpy.__version__)'".to_string(),
                    ]);
                } else if issue.description.contains("NumPy C API headers") {
                    actions.extend(self.fix_numpy_c_api_headers());
                }
            },
            DLLIssueType::LoadFailure => {
                if issue.description.contains("Missing import_array()") {
                    actions.extend(self.fix_numpy_import_array(&issue.affected_library));
                }
            },
            _ => {
                actions.push(format!("Manual intervention required for NumPy issue: {}", issue.description));
            }
        }
        
        actions
    }

    /// Fix Fortran-specific issues
    fn fix_fortran_specific_issue(&self, issue: &DLLIssue) -> Vec<String> {
        let mut actions = Vec::new();
        
        match &issue.issue_type {
            DLLIssueType::DependencyMissing => {
                if issue.description.contains("gfortran") {
                    actions.extend(self.fix_gfortran_missing());
                } else if issue.description.contains("f2py") {
                    actions.extend(self.fix_f2py_missing());
                } else if issue.description.contains("Fortran runtime dependency") {
                    actions.extend(self.fix_fortran_runtime_missing(&issue.affected_library));
                }
            },
            DLLIssueType::LoadFailure => {
                if issue.description.contains("No Fortran source files") {
                    actions.extend(self.create_fortran_source_files());
                } else if issue.description.contains("No f2py signature files") {
                    actions.extend(self.fix_f2py_signatures());
                }
            },
            _ => {
                actions.push(format!("Manual intervention required for Fortran issue: {}", issue.description));
            }
        }
        
        actions
    }

    /// Create Cython source files
    fn create_cython_source_files(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let cython_dir = "benchmark/cython_ext";
        
        // Create directory if it doesn't exist
        if let Err(_) = std::fs::create_dir_all(cython_dir) {
            actions.push(format!("Failed to create directory: {}", cython_dir));
            return actions;
        }
        
        // Create basic Cython files
        let cython_files = vec!["numeric", "memory", "parallel"];
        
        for module_name in cython_files {
            let file_path = format!("{}/{}.pyx", cython_dir, module_name);
            let content = self.generate_cython_source_content(module_name);
            
            match std::fs::write(&file_path, content) {
                Ok(_) => actions.push(format!("Created Cython file: {}", file_path)),
                Err(e) => actions.push(format!("Failed to create {}: {}", file_path, e)),
            }
        }
        
        // Create setup.py for Cython
        let setup_py_path = format!("{}/setup.py", cython_dir);
        let setup_content = self.generate_cython_setup_py();
        match std::fs::write(&setup_py_path, setup_content) {
            Ok(_) => actions.push(format!("Created Cython setup.py: {}", setup_py_path)),
            Err(e) => actions.push(format!("Failed to create setup.py: {}", e)),
        }
        
        actions
    }

    /// Generate Cython source content
    fn generate_cython_source_content(&self, module_name: &str) -> String {
        match module_name {
            "numeric" => r#"
# cython: language_level=3
import numpy as np
cimport numpy as cnp
from libc.math cimport sqrt

# Initialize NumPy C API
cnp.import_array()

def numeric_add(cnp.ndarray[double, ndim=1] a, cnp.ndarray[double, ndim=1] b):
    """Add two NumPy arrays element-wise using Cython"""
    if a.shape[0] != b.shape[0]:
        raise ValueError("Array shapes must match")
    
    cdef int n = a.shape[0]
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(n, dtype=np.float64)
    cdef int i
    
    for i in range(n):
        result[i] = a[i] + b[i]
    
    return result

def numeric_multiply(cnp.ndarray[double, ndim=1] a, cnp.ndarray[double, ndim=1] b):
    """Multiply two NumPy arrays element-wise using Cython"""
    if a.shape[0] != b.shape[0]:
        raise ValueError("Array shapes must match")
    
    cdef int n = a.shape[0]
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(n, dtype=np.float64)
    cdef int i
    
    for i in range(n):
        result[i] = a[i] * b[i]
    
    return result

def numeric_sqrt(cnp.ndarray[double, ndim=1] a):
    """Compute square root of array elements using Cython"""
    cdef int n = a.shape[0]
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(n, dtype=np.float64)
    cdef int i
    
    for i in range(n):
        result[i] = sqrt(a[i])
    
    return result
"#.to_string(),
            "memory" => r#"
# cython: language_level=3
import numpy as np
cimport numpy as cnp
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

# Initialize NumPy C API
cnp.import_array()

def memory_allocate(int size):
    """Allocate a NumPy array using Cython"""
    if size <= 0:
        raise ValueError("Size must be positive")
    
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(size, dtype=np.float64)
    return result

def memory_copy(cnp.ndarray[double, ndim=1] source):
    """Copy a NumPy array using Cython"""
    cdef int n = source.shape[0]
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(n, dtype=np.float64)
    cdef int i
    
    for i in range(n):
        result[i] = source[i]
    
    return result

def memory_fill(int size, double value):
    """Create and fill a NumPy array with a specific value using Cython"""
    if size <= 0:
        raise ValueError("Size must be positive")
    
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(size, dtype=np.float64)
    cdef int i
    
    for i in range(size):
        result[i] = value
    
    return result
"#.to_string(),
            "parallel" => r#"
# cython: language_level=3
import numpy as np
cimport numpy as cnp
from cython.parallel import prange
cimport openmp

# Initialize NumPy C API
cnp.import_array()

def parallel_compute(cnp.ndarray[double, ndim=1] input_array):
    """Compute square of array elements in parallel using Cython"""
    cdef int n = input_array.shape[0]
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(n, dtype=np.float64)
    cdef int i
    
    # Parallel computation
    for i in prange(n, nogil=True):
        result[i] = input_array[i] * input_array[i]
    
    return result

def parallel_sum(cnp.ndarray[double, ndim=1] input_array):
    """Compute sum of array elements in parallel using Cython"""
    cdef int n = input_array.shape[0]
    cdef double total = 0.0
    cdef int i
    
    # Parallel reduction
    for i in prange(n, nogil=True):
        total += input_array[i]
    
    return total

def parallel_reduce(cnp.ndarray[double, ndim=1] a, cnp.ndarray[double, ndim=1] b):
    """Perform parallel reduction operation using Cython"""
    if a.shape[0] != b.shape[0]:
        raise ValueError("Array shapes must match")
    
    cdef int n = a.shape[0]
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(n, dtype=np.float64)
    cdef int i
    
    for i in prange(n, nogil=True):
        result[i] = a[i] + b[i] * 2.0
    
    return result
"#.to_string(),
            _ => format!("# Placeholder Cython module for {}\n", module_name),
        }
    }

    /// Generate Cython setup.py
    fn generate_cython_setup_py(&self) -> String {
        r#"
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

# Define extensions
extensions = [
    Extension(
        "numeric",
        ["numeric.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-fopenmp"],
        extra_link_args=["-fopenmp"],
    ),
    Extension(
        "memory",
        ["memory.pyx"],
        include_dirs=[numpy.get_include()],
    ),
    Extension(
        "parallel",
        ["parallel.pyx"],
        include_dirs=[numpy.get_include()],
        extra_compile_args=["-fopenmp"],
        extra_link_args=["-fopenmp"],
    ),
]

setup(
    name="cython_ext",
    ext_modules=cythonize(extensions, compiler_directives={'language_level': 3}),
    zip_safe=False,
)
"#.to_string()
    }

    /// Fix Cython setup.py issues
    fn fix_cython_setup_py(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let setup_py_path = "benchmark/cython_ext/setup.py";
        
        if let Ok(content) = std::fs::read_to_string(setup_py_path) {
            let mut fixed_content = content;
            
            // Add Cython.Build import if missing
            if !fixed_content.contains("from Cython.Build import cythonize") {
                fixed_content = format!("from Cython.Build import cythonize\n{}", fixed_content);
            }
            
            // Add cythonize() wrapper if missing
            if !fixed_content.contains("cythonize(") {
                fixed_content = fixed_content.replace(
                    "ext_modules=extensions",
                    "ext_modules=cythonize(extensions, compiler_directives={'language_level': 3})"
                );
            }
            
            match std::fs::write(setup_py_path, fixed_content) {
                Ok(_) => actions.push(format!("Fixed Cython setup.py: {}", setup_py_path)),
                Err(e) => actions.push(format!("Failed to fix setup.py: {}", e)),
            }
        } else {
            // Create new setup.py
            let setup_content = self.generate_cython_setup_py();
            match std::fs::write(setup_py_path, setup_content) {
                Ok(_) => actions.push(format!("Created Cython setup.py: {}", setup_py_path)),
                Err(e) => actions.push(format!("Failed to create setup.py: {}", e)),
            }
        }
        
        actions
    }

    /// Fix Cython NumPy imports
    fn fix_cython_numpy_imports(&self, file_path: &str) -> Vec<String> {
        let mut actions = Vec::new();
        
        if let Ok(content) = std::fs::read_to_string(file_path) {
            let mut fixed_content = content;
            
            // Add cimport numpy if missing
            if !fixed_content.contains("cimport numpy") {
                fixed_content = format!("cimport numpy as cnp\n{}", fixed_content);
            }
            
            // Add import numpy if missing
            if !fixed_content.contains("import numpy") {
                fixed_content = format!("import numpy as np\n{}", fixed_content);
            }
            
            // Add import_array() call if missing
            if !fixed_content.contains("cnp.import_array()") {
                fixed_content = format!("{}\n# Initialize NumPy C API\ncnp.import_array()\n", fixed_content);
            }
            
            match std::fs::write(file_path, fixed_content) {
                Ok(_) => actions.push(format!("Fixed NumPy imports in: {}", file_path)),
                Err(e) => actions.push(format!("Failed to fix imports in {}: {}", file_path, e)),
            }
        }
        
        actions
    }

    /// Fix NumPy C API headers
    fn fix_numpy_c_api_headers(&self) -> Vec<String> {
        vec![
            "Checking NumPy C API headers...".to_string(),
            "python -c 'import numpy; print(numpy.get_include())'".to_string(),
            "Verifying arrayobject.h exists...".to_string(),
            "If headers are missing, reinstall NumPy: pip install --force-reinstall numpy".to_string(),
        ]
    }

    /// Fix NumPy import_array() issues
    fn fix_numpy_import_array(&self, file_path: &str) -> Vec<String> {
        let mut actions = Vec::new();
        
        if let Ok(content) = std::fs::read_to_string(file_path) {
            let mut fixed_content = content;
            
            // Find PyInit function and add import_array()
            if let Some(pos) = fixed_content.find("PyMODINIT_FUNC PyInit_") {
                if let Some(brace_pos) = fixed_content[pos..].find('{') {
                    let insert_pos = pos + brace_pos + 1;
                    let import_array_call = "\n    import_array();\n";
                    fixed_content.insert_str(insert_pos, import_array_call);
                }
            }
            
            match std::fs::write(file_path, fixed_content) {
                Ok(_) => actions.push(format!("Added import_array() call to: {}", file_path)),
                Err(e) => actions.push(format!("Failed to fix import_array() in {}: {}", file_path, e)),
            }
        }
        
        actions
    }

    /// Fix missing gfortran
    fn fix_gfortran_missing(&self) -> Vec<String> {
        vec![
            "Installing Fortran compiler...".to_string(),
            #[cfg(target_os = "windows")]
            "Install MinGW-w64 with Fortran support from https://www.mingw-w64.org/".to_string(),
            #[cfg(not(target_os = "windows"))]
            "sudo apt-get install gfortran || sudo yum install gcc-gfortran".to_string(),
            "Verifying gfortran installation...".to_string(),
            "gfortran --version".to_string(),
        ]
    }

    /// Fix missing f2py
    fn fix_f2py_missing(&self) -> Vec<String> {
        vec![
            "f2py comes with NumPy, ensuring NumPy is installed...".to_string(),
            "pip install numpy".to_string(),
            "Verifying f2py installation...".to_string(),
            "python -m numpy.f2py --help".to_string(),
            "f2py --version".to_string(),
        ]
    }

    /// Fix Fortran runtime dependencies
    fn fix_fortran_runtime_missing(&self, dependency: &str) -> Vec<String> {
        vec![
            format!("Installing Fortran runtime dependency: {}", dependency),
            "Ensure MinGW-w64 Fortran runtime is installed".to_string(),
            "Add MinGW-w64 bin directory to PATH".to_string(),
            "Copy required DLLs to application directory if needed".to_string(),
        ]
    }

    /// Create Fortran source files
    fn create_fortran_source_files(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let fortran_dir = "benchmark/fortran_ext";
        
        // Create directory if it doesn't exist
        if let Err(_) = std::fs::create_dir_all(fortran_dir) {
            actions.push(format!("Failed to create directory: {}", fortran_dir));
            return actions;
        }
        
        // Create basic Fortran files
        let fortran_files = vec!["numeric", "memory", "parallel"];
        
        for module_name in fortran_files {
            let file_path = format!("{}/{}.f90", fortran_dir, module_name);
            let content = self.generate_fortran_source_content(module_name);
            
            match std::fs::write(&file_path, content) {
                Ok(_) => actions.push(format!("Created Fortran file: {}", file_path)),
                Err(e) => actions.push(format!("Failed to create {}: {}", file_path, e)),
            }
        }
        
        actions
    }

    /// Generate Fortran source content
    fn generate_fortran_source_content(&self, module_name: &str) -> String {
        match module_name {
            "numeric" => r#"
! Fortran numeric operations module
module numeric_operations
    implicit none
    
contains
    
    !f2py intent(in) :: a, b
    !f2py intent(out) :: result
    !f2py depend(n) :: a, b, result
    subroutine numeric_add(a, b, result, n)
        implicit none
        integer, intent(in) :: n
        real(8), intent(in) :: a(n), b(n)
        real(8), intent(out) :: result(n)
        integer :: i
        
        do i = 1, n
            result(i) = a(i) + b(i)
        end do
    end subroutine numeric_add
    
    !f2py intent(in) :: a, b
    !f2py intent(out) :: result
    !f2py depend(n) :: a, b, result
    subroutine numeric_multiply(a, b, result, n)
        implicit none
        integer, intent(in) :: n
        real(8), intent(in) :: a(n), b(n)
        real(8), intent(out) :: result(n)
        integer :: i
        
        do i = 1, n
            result(i) = a(i) * b(i)
        end do
    end subroutine numeric_multiply
    
    !f2py intent(in) :: a
    !f2py intent(out) :: result
    !f2py depend(n) :: a, result
    subroutine numeric_sqrt(a, result, n)
        implicit none
        integer, intent(in) :: n
        real(8), intent(in) :: a(n)
        real(8), intent(out) :: result(n)
        integer :: i
        
        do i = 1, n
            result(i) = sqrt(a(i))
        end do
    end subroutine numeric_sqrt
    
end module numeric_operations
"#.to_string(),
            "memory" => r#"
! Fortran memory operations module
module memory_operations
    implicit none
    
contains
    
    !f2py intent(in) :: size
    !f2py intent(out) :: result
    !f2py depend(size) :: result
    subroutine memory_allocate(result, size)
        implicit none
        integer, intent(in) :: size
        real(8), intent(out) :: result(size)
        integer :: i
        
        do i = 1, size
            result(i) = 0.0d0
        end do
    end subroutine memory_allocate
    
    !f2py intent(in) :: source
    !f2py intent(out) :: result
    !f2py depend(n) :: source, result
    subroutine memory_copy(source, result, n)
        implicit none
        integer, intent(in) :: n
        real(8), intent(in) :: source(n)
        real(8), intent(out) :: result(n)
        integer :: i
        
        do i = 1, n
            result(i) = source(i)
        end do
    end subroutine memory_copy
    
    !f2py intent(in) :: size, value
    !f2py intent(out) :: result
    !f2py depend(size) :: result
    subroutine memory_fill(result, size, value)
        implicit none
        integer, intent(in) :: size
        real(8), intent(in) :: value
        real(8), intent(out) :: result(size)
        integer :: i
        
        do i = 1, size
            result(i) = value
        end do
    end subroutine memory_fill
    
end module memory_operations
"#.to_string(),
            "parallel" => r#"
! Fortran parallel operations module
module parallel_operations
    use omp_lib
    implicit none
    
contains
    
    !f2py intent(in) :: input_array
    !f2py intent(out) :: result
    !f2py depend(n) :: input_array, result
    subroutine parallel_compute(input_array, result, n)
        implicit none
        integer, intent(in) :: n
        real(8), intent(in) :: input_array(n)
        real(8), intent(out) :: result(n)
        integer :: i
        
        !$OMP PARALLEL DO
        do i = 1, n
            result(i) = input_array(i) * input_array(i)
        end do
        !$OMP END PARALLEL DO
    end subroutine parallel_compute
    
    !f2py intent(in) :: input_array
    !f2py intent(out) :: total
    !f2py depend(n) :: input_array
    subroutine parallel_sum(input_array, total, n)
        implicit none
        integer, intent(in) :: n
        real(8), intent(in) :: input_array(n)
        real(8), intent(out) :: total
        integer :: i
        
        total = 0.0d0
        !$OMP PARALLEL DO REDUCTION(+:total)
        do i = 1, n
            total = total + input_array(i)
        end do
        !$OMP END PARALLEL DO
    end subroutine parallel_sum
    
    !f2py intent(in) :: a, b
    !f2py intent(out) :: result
    !f2py depend(n) :: a, b, result
    subroutine parallel_reduce(a, b, result, n)
        implicit none
        integer, intent(in) :: n
        real(8), intent(in) :: a(n), b(n)
        real(8), intent(out) :: result(n)
        integer :: i
        
        !$OMP PARALLEL DO
        do i = 1, n
            result(i) = a(i) + b(i) * 2.0d0
        end do
        !$OMP END PARALLEL DO
    end subroutine parallel_reduce
    
end module parallel_operations
"#.to_string(),
            _ => format!("! Placeholder Fortran module for {}\n", module_name),
        }
    }

    /// Fix f2py signature issues
    fn fix_f2py_signatures(&self) -> Vec<String> {
        vec![
            "Adding f2py directives to Fortran source files...".to_string(),
            "f2py directives added as comments in .f90 files".to_string(),
            "Example: !f2py intent(in) :: input_parameter".to_string(),
            "Example: !f2py intent(out) :: output_parameter".to_string(),
            "Example: !f2py depend(n) :: array_parameter".to_string(),
            "Build with: f2py -c -m module_name source.f90".to_string(),
        ]
    }

    /// Fix C/C++ specific compilation and linking issues
    pub fn fix_c_cpp_issues(&self, ffi_impl: &str, issues: &[DLLIssue]) -> Result<Vec<String>> {
        let mut fix_actions = Vec::new();
        
        for issue in issues {
            match &issue.issue_type {
                DLLIssueType::DependencyMissing => {
                    if issue.description.contains("compiler") {
                        fix_actions.extend(self.fix_compiler_missing(ffi_impl));
                    } else if issue.description.contains("Python development headers") {
                        fix_actions.extend(self.fix_python_headers_missing());
                    } else if issue.description.contains("NumPy") {
                        fix_actions.extend(self.fix_numpy_headers_missing());
                    } else if issue.description.contains("runtime dependency") {
                        fix_actions.extend(self.fix_runtime_dependency_missing(&issue.description));
                    }
                },
                DLLIssueType::LoadFailure => {
                    if issue.description.contains("setup.py") {
                        fix_actions.extend(self.fix_setup_py_issues(ffi_impl, &issue.description));
                    } else if issue.description.contains("source files") {
                        fix_actions.extend(self.fix_missing_source_files(ffi_impl));
                    } else if issue.description.contains("Library not found") {
                        fix_actions.extend(self.fix_library_not_built(ffi_impl));
                    }
                },
                DLLIssueType::ArchitectureMismatch => {
                    fix_actions.extend(self.fix_architecture_mismatch(ffi_impl));
                },
                _ => {
                    // Generic fix for other issues
                    fix_actions.push(format!("Manual intervention required for: {}", issue.description));
                }
            }
        }
        
        Ok(fix_actions)
    }
    
    /// Fix missing compiler issue
    fn fix_compiler_missing(&self, ffi_impl: &str) -> Vec<String> {
        let compiler = match ffi_impl {
            "c_ext" => "gcc",
            "cpp_ext" => "g++",
            _ => "compiler",
        };
        
        vec![
            format!("Installing {} compiler...", compiler),
            self.generate_compiler_install_command(ffi_impl),
            format!("Verifying {} installation...", compiler),
            format!("{} --version", compiler),
        ]
    }
    
    /// Generate compiler installation command
    fn generate_compiler_install_command(&self, ffi_impl: &str) -> String {
        #[cfg(target_os = "windows")]
        {
            match ffi_impl {
                "c_ext" => "Install MinGW-w64 or Visual Studio Build Tools".to_string(),
                "cpp_ext" => "Install MinGW-w64 or Visual Studio Build Tools with C++ support".to_string(),
                _ => "Install appropriate compiler".to_string(),
            }
        }
        
        #[cfg(not(target_os = "windows"))]
        {
            match ffi_impl {
                "c_ext" => "sudo apt-get install gcc || sudo yum install gcc".to_string(),
                "cpp_ext" => "sudo apt-get install g++ || sudo yum install gcc-c++".to_string(),
                _ => "Install appropriate compiler".to_string(),
            }
        }
    }
    
    /// Fix missing Python headers
    fn fix_python_headers_missing(&self) -> Vec<String> {
        vec![
            "Installing Python development headers...".to_string(),
            #[cfg(target_os = "windows")]
            "Ensure Python was installed with development headers".to_string(),
            #[cfg(not(target_os = "windows"))]
            "sudo apt-get install python3-dev || sudo yum install python3-devel".to_string(),
            "Verifying Python.h availability...".to_string(),
            "python -c \"import sysconfig; print(sysconfig.get_path('include'))\"".to_string(),
        ]
    }
    
    /// Fix missing NumPy headers
    fn fix_numpy_headers_missing(&self) -> Vec<String> {
        vec![
            "Installing NumPy...".to_string(),
            "pip install numpy".to_string(),
            "Verifying NumPy headers...".to_string(),
            "python -c \"import numpy; print(numpy.get_include())\"".to_string(),
        ]
    }
    
    /// Fix missing runtime dependency
    fn fix_runtime_dependency_missing(&self, description: &str) -> Vec<String> {
        if description.contains("msvcr140") || description.contains("vcruntime140") {
            vec![
                "Installing Microsoft Visual C++ Redistributable...".to_string(),
                "Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe".to_string(),
                "Run the installer as administrator".to_string(),
                "Restart the system if required".to_string(),
            ]
        } else {
            vec![
                "Installing missing runtime dependencies...".to_string(),
                "Check system package manager for required libraries".to_string(),
            ]
        }
    }
    
    /// Fix setup.py issues
    fn fix_setup_py_issues(&self, ffi_impl: &str, description: &str) -> Vec<String> {
        let mut actions = Vec::new();
        
        if description.contains("not found") {
            actions.push("Creating setup.py file...".to_string());
            actions.push(self.create_setup_py_file(ffi_impl));
        } else if description.contains("NumPy include") {
            actions.push("Fixing NumPy include directory in setup.py...".to_string());
            actions.push(self.fix_setup_py_numpy_include(ffi_impl));
        } else if description.contains("C++ language") {
            actions.push("Adding C++ language specification to setup.py...".to_string());
            actions.push(self.fix_setup_py_cpp_language(ffi_impl));
        }
        
        actions
    }
    
    /// Create setup.py file
    fn create_setup_py_file(&self, ffi_impl: &str) -> String {
        let setup_py_content = match ffi_impl {
            "c_ext" => self.generate_c_setup_py(),
            "cpp_ext" => self.generate_cpp_setup_py(),
            _ => "# Generic setup.py\nfrom setuptools import setup, Extension\nsetup()".to_string(),
        };
        
        let setup_py_path = format!("benchmark/{}/setup.py", ffi_impl);
        
        match std::fs::write(&setup_py_path, setup_py_content) {
            Ok(_) => format!("Created setup.py at {}", setup_py_path),
            Err(e) => format!("Failed to create setup.py: {}", e),
        }
    }
    
    /// Fix NumPy include directory in setup.py
    fn fix_setup_py_numpy_include(&self, ffi_impl: &str) -> String {
        let setup_py_path = format!("benchmark/{}/setup.py", ffi_impl);
        
        if let Ok(content) = std::fs::read_to_string(&setup_py_path) {
            let fixed_content = if !content.contains("import numpy") {
                format!("import numpy\n{}", content)
            } else {
                content
            };
            
            let fixed_content = if !fixed_content.contains("numpy.get_include()") {
                fixed_content.replace(
                    "include_dirs=[]",
                    "include_dirs=[numpy.get_include()]"
                ).replace(
                    "Extension(",
                    "Extension(\n        include_dirs=[numpy.get_include()],"
                )
            } else {
                fixed_content
            };
            
            match std::fs::write(&setup_py_path, fixed_content) {
                Ok(_) => format!("Fixed NumPy include in {}", setup_py_path),
                Err(e) => format!("Failed to fix setup.py: {}", e),
            }
        } else {
            format!("Could not read setup.py at {}", setup_py_path)
        }
    }
    
    /// Fix C++ language specification in setup.py
    fn fix_setup_py_cpp_language(&self, ffi_impl: &str) -> String {
        let setup_py_path = format!("benchmark/{}/setup.py", ffi_impl);
        
        if let Ok(content) = std::fs::read_to_string(&setup_py_path) {
            let fixed_content = if !content.contains("language='c++'") {
                content.replace(
                    "Extension(",
                    "Extension(\n        language='c++',"
                )
            } else {
                content
            };
            
            match std::fs::write(&setup_py_path, fixed_content) {
                Ok(_) => format!("Added C++ language specification to {}", setup_py_path),
                Err(e) => format!("Failed to fix setup.py: {}", e),
            }
        } else {
            format!("Could not read setup.py at {}", setup_py_path)
        }
    }
    
    /// Fix missing source files
    fn fix_missing_source_files(&self, ffi_impl: &str) -> Vec<String> {
        let mut actions = Vec::new();
        let source_dir = format!("benchmark/{}", ffi_impl);
        
        // Create directory if it doesn't exist
        if let Err(_) = std::fs::create_dir_all(&source_dir) {
            actions.push(format!("Failed to create directory: {}", source_dir));
            return actions;
        }
        
        // Create basic source files
        let source_files = vec!["numeric", "memory", "parallel"];
        let extension = if ffi_impl == "cpp_ext" { "cpp" } else { "c" };
        
        for source_file in source_files {
            let file_path = format!("{}/{}.{}", source_dir, source_file, extension);
            let content = self.generate_source_file_content(source_file, ffi_impl);
            
            match std::fs::write(&file_path, content) {
                Ok(_) => actions.push(format!("Created source file: {}", file_path)),
                Err(e) => actions.push(format!("Failed to create {}: {}", file_path, e)),
            }
        }
        
        actions
    }
    
    /// Generate source file content
    fn generate_source_file_content(&self, module_name: &str, ffi_impl: &str) -> String {
        match (module_name, ffi_impl) {
            ("numeric", "c_ext") => r#"
#include <Python.h>
#include <numpy/arrayobject.h>

static PyObject* numeric_add(PyObject* self, PyObject* args) {
    PyArrayObject *a, *b;
    if (!PyArg_ParseTuple(args, "O!O!", &PyArray_Type, &a, &PyArray_Type, &b)) {
        return NULL;
    }
    
    // Basic implementation - add arrays element-wise
    npy_intp size = PyArray_SIZE(a);
    PyArrayObject* result = (PyArrayObject*)PyArray_SimpleNew(1, &size, NPY_DOUBLE);
    
    double* a_data = (double*)PyArray_DATA(a);
    double* b_data = (double*)PyArray_DATA(b);
    double* result_data = (double*)PyArray_DATA(result);
    
    for (npy_intp i = 0; i < size; i++) {
        result_data[i] = a_data[i] + b_data[i];
    }
    
    return (PyObject*)result;
}

static PyMethodDef NumericMethods[] = {
    {"add", numeric_add, METH_VARARGS, "Add two arrays"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef numericmodule = {
    PyModuleDef_HEAD_INIT,
    "numeric",
    "Numeric operations module",
    -1,
    NumericMethods
};

PyMODINIT_FUNC PyInit_numeric(void) {
    import_array();
    return PyModule_Create(&numericmodule);
}
"#.to_string(),
            ("numeric", "cpp_ext") => r#"
#include <Python.h>
#include <numpy/arrayobject.h>
#include <vector>

extern "C" {

static PyObject* numeric_add(PyObject* self, PyObject* args) {
    PyArrayObject *a, *b;
    if (!PyArg_ParseTuple(args, "O!O!", &PyArray_Type, &a, &PyArray_Type, &b)) {
        return NULL;
    }
    
    try {
        npy_intp size = PyArray_SIZE(a);
        PyArrayObject* result = (PyArrayObject*)PyArray_SimpleNew(1, &size, NPY_DOUBLE);
        
        double* a_data = static_cast<double*>(PyArray_DATA(a));
        double* b_data = static_cast<double*>(PyArray_DATA(b));
        double* result_data = static_cast<double*>(PyArray_DATA(result));
        
        for (npy_intp i = 0; i < size; i++) {
            result_data[i] = a_data[i] + b_data[i];
        }
        
        return reinterpret_cast<PyObject*>(result);
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return NULL;
    }
}

static PyMethodDef NumericMethods[] = {
    {"add", numeric_add, METH_VARARGS, "Add two arrays"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef numericmodule = {
    PyModuleDef_HEAD_INIT,
    "numeric",
    "Numeric operations module",
    -1,
    NumericMethods
};

PyMODINIT_FUNC PyInit_numeric(void) {
    import_array();
    return PyModule_Create(&numericmodule);
}

} // extern "C"
"#.to_string(),
            ("memory", "c_ext") => r#"
#include <Python.h>
#include <numpy/arrayobject.h>
#include <stdlib.h>

static PyObject* memory_allocate(PyObject* self, PyObject* args) {
    int size;
    if (!PyArg_ParseTuple(args, "i", &size)) {
        return NULL;
    }
    
    if (size <= 0) {
        PyErr_SetString(PyExc_ValueError, "Size must be positive");
        return NULL;
    }
    
    npy_intp dims[1] = {size};
    PyArrayObject* result = (PyArrayObject*)PyArray_SimpleNew(1, dims, NPY_DOUBLE);
    
    // Initialize to zero
    double* data = (double*)PyArray_DATA(result);
    for (int i = 0; i < size; i++) {
        data[i] = 0.0;
    }
    
    return (PyObject*)result;
}

static PyMethodDef MemoryMethods[] = {
    {"allocate", memory_allocate, METH_VARARGS, "Allocate array"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef memorymodule = {
    PyModuleDef_HEAD_INIT,
    "memory",
    "Memory operations module",
    -1,
    MemoryMethods
};

PyMODINIT_FUNC PyInit_memory(void) {
    import_array();
    return PyModule_Create(&memorymodule);
}
"#.to_string(),
            ("memory", "cpp_ext") => r#"
#include <Python.h>
#include <numpy/arrayobject.h>
#include <memory>

extern "C" {

static PyObject* memory_allocate(PyObject* self, PyObject* args) {
    int size;
    if (!PyArg_ParseTuple(args, "i", &size)) {
        return NULL;
    }
    
    if (size <= 0) {
        PyErr_SetString(PyExc_ValueError, "Size must be positive");
        return NULL;
    }
    
    try {
        npy_intp dims[1] = {size};
        PyArrayObject* result = (PyArrayObject*)PyArray_SimpleNew(1, dims, NPY_DOUBLE);
        
        double* data = static_cast<double*>(PyArray_DATA(result));
        std::fill(data, data + size, 0.0);
        
        return reinterpret_cast<PyObject*>(result);
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return NULL;
    }
}

static PyMethodDef MemoryMethods[] = {
    {"allocate", memory_allocate, METH_VARARGS, "Allocate array"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef memorymodule = {
    PyModuleDef_HEAD_INIT,
    "memory",
    "Memory operations module",
    -1,
    MemoryMethods
};

PyMODINIT_FUNC PyInit_memory(void) {
    import_array();
    return PyModule_Create(&memorymodule);
}

} // extern "C"
"#.to_string(),
            ("parallel", "c_ext") => r#"
#include <Python.h>
#include <numpy/arrayobject.h>

static PyObject* parallel_compute(PyObject* self, PyObject* args) {
    PyArrayObject *input;
    if (!PyArg_ParseTuple(args, "O!", &PyArray_Type, &input)) {
        return NULL;
    }
    
    npy_intp size = PyArray_SIZE(input);
    PyArrayObject* result = (PyArrayObject*)PyArray_SimpleNew(1, &size, NPY_DOUBLE);
    
    double* input_data = (double*)PyArray_DATA(input);
    double* result_data = (double*)PyArray_DATA(result);
    
    // Simple parallel-like computation (square each element)
    for (npy_intp i = 0; i < size; i++) {
        result_data[i] = input_data[i] * input_data[i];
    }
    
    return (PyObject*)result;
}

static PyMethodDef ParallelMethods[] = {
    {"compute", parallel_compute, METH_VARARGS, "Parallel computation"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef parallelmodule = {
    PyModuleDef_HEAD_INIT,
    "parallel",
    "Parallel operations module",
    -1,
    ParallelMethods
};

PyMODINIT_FUNC PyInit_parallel(void) {
    import_array();
    return PyModule_Create(&parallelmodule);
}
"#.to_string(),
            ("parallel", "cpp_ext") => r#"
#include <Python.h>
#include <numpy/arrayobject.h>
#include <algorithm>

extern "C" {

static PyObject* parallel_compute(PyObject* self, PyObject* args) {
    PyArrayObject *input;
    if (!PyArg_ParseTuple(args, "O!", &PyArray_Type, &input)) {
        return NULL;
    }
    
    try {
        npy_intp size = PyArray_SIZE(input);
        PyArrayObject* result = (PyArrayObject*)PyArray_SimpleNew(1, &size, NPY_DOUBLE);
        
        double* input_data = static_cast<double*>(PyArray_DATA(input));
        double* result_data = static_cast<double*>(PyArray_DATA(result));
        
        std::transform(input_data, input_data + size, result_data,
                      [](double x) { return x * x; });
        
        return reinterpret_cast<PyObject*>(result);
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return NULL;
    }
}

static PyMethodDef ParallelMethods[] = {
    {"compute", parallel_compute, METH_VARARGS, "Parallel computation"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef parallelmodule = {
    PyModuleDef_HEAD_INIT,
    "parallel",
    "Parallel operations module",
    -1,
    ParallelMethods
};

PyMODINIT_FUNC PyInit_parallel(void) {
    import_array();
    return PyModule_Create(&parallelmodule);
}

} // extern "C"
"#.to_string(),
            _ => format!("// Placeholder for {} module\n", module_name),
        }
    }
    
    /// Fix library not built issue
    fn fix_library_not_built(&self, ffi_impl: &str) -> Vec<String> {
        vec![
            format!("Building {} library...", ffi_impl),
            format!("cd benchmark/{}", ffi_impl),
            "python setup.py clean --all".to_string(),
            "python setup.py build_ext --inplace".to_string(),
            "Verifying build output...".to_string(),
        ]
    }
    
    /// Fix architecture mismatch
    fn fix_architecture_mismatch(&self, ffi_impl: &str) -> Vec<String> {
        vec![
            "Fixing architecture mismatch...".to_string(),
            "Setting correct architecture flags...".to_string(),
            format!("cd benchmark/{}", ffi_impl),
            "python setup.py clean --all".to_string(),
            #[cfg(target_pointer_width = "64")]
            "CFLAGS=\"-m64\" LDFLAGS=\"-m64\" python setup.py build_ext --inplace".to_string(),
            #[cfg(target_pointer_width = "32")]
            "CFLAGS=\"-m32\" LDFLAGS=\"-m32\" python setup.py build_ext --inplace".to_string(),
        ]
    }

    /// Fix modern language (Zig/Nim/Julia/Kotlin) specific compilation and linking issues
    pub fn fix_modern_language_issues(&self, ffi_impl: &str, issues: &[DLLIssue]) -> Result<Vec<String>> {
        let mut fix_actions = Vec::new();
        
        for issue in issues {
            match ffi_impl {
                "zig_ext" => {
                    fix_actions.extend(self.fix_zig_specific_issue(issue));
                },
                "nim_ext" => {
                    fix_actions.extend(self.fix_nim_specific_issue(issue));
                },
                "julia_ext" => {
                    fix_actions.extend(self.fix_julia_specific_issue(issue));
                },
                "kotlin_ext" => {
                    fix_actions.extend(self.fix_kotlin_specific_issue(issue));
                },
                _ => {
                    fix_actions.push(format!("Unsupported implementation for modern language fixes: {}", ffi_impl));
                }
            }
        }
        
        Ok(fix_actions)
    }

    /// Fix Zig-specific issues
    fn fix_zig_specific_issue(&self, issue: &DLLIssue) -> Vec<String> {
        let mut actions = Vec::new();
        
        match &issue.issue_type {
            DLLIssueType::DependencyMissing => {
                if issue.description.contains("Zig compiler") {
                    actions.extend(self.fix_zig_compiler_missing());
                }
            },
            DLLIssueType::LoadFailure => {
                if issue.description.contains("build.zig") {
                    actions.extend(self.fix_zig_build_file_missing());
                } else if issue.description.contains("No Zig source files") {
                    actions.extend(self.create_zig_source_files());
                } else if issue.description.contains("build errors") {
                    actions.extend(self.fix_zig_build_errors());
                }
            },
            _ => {
                actions.push(format!("Manual intervention required for Zig issue: {}", issue.description));
            }
        }
        
        actions
    }

    /// Fix Nim-specific issues
    fn fix_nim_specific_issue(&self, issue: &DLLIssue) -> Vec<String> {
        let mut actions = Vec::new();
        
        match &issue.issue_type {
            DLLIssueType::DependencyMissing => {
                if issue.description.contains("Nim compiler") {
                    actions.extend(self.fix_nim_compiler_missing());
                }
            },
            DLLIssueType::LoadFailure => {
                if issue.description.contains("nimble") {
                    actions.extend(self.fix_nim_nimble_file_missing());
                } else if issue.description.contains("No Nim source files") {
                    actions.extend(self.create_nim_source_files());
                } else if issue.description.contains("compilation errors") {
                    actions.extend(self.fix_nim_compilation_errors());
                }
            },
            _ => {
                actions.push(format!("Manual intervention required for Nim issue: {}", issue.description));
            }
        }
        
        actions
    }

    /// Fix Julia-specific issues
    fn fix_julia_specific_issue(&self, issue: &DLLIssue) -> Vec<String> {
        let mut actions = Vec::new();
        
        match &issue.issue_type {
            DLLIssueType::DependencyMissing => {
                if issue.description.contains("Julia not found") {
                    actions.extend(self.fix_julia_missing());
                } else if issue.description.contains("PackageCompiler") {
                    actions.extend(self.fix_julia_package_compiler_missing());
                }
            },
            DLLIssueType::LoadFailure => {
                if issue.description.contains("Project.toml") {
                    actions.extend(self.fix_julia_project_toml_missing());
                } else if issue.description.contains("No Julia source files") {
                    actions.extend(self.create_julia_source_files());
                }
            },
            _ => {
                actions.push(format!("Manual intervention required for Julia issue: {}", issue.description));
            }
        }
        
        actions
    }

    /// Fix Kotlin-specific issues
    fn fix_kotlin_specific_issue(&self, issue: &DLLIssue) -> Vec<String> {
        let mut actions = Vec::new();
        
        match &issue.issue_type {
            DLLIssueType::DependencyMissing => {
                if issue.description.contains("Kotlin/Native") {
                    actions.extend(self.fix_kotlin_native_missing());
                }
            },
            DLLIssueType::LoadFailure => {
                if issue.description.contains("build.gradle.kts") {
                    actions.extend(self.fix_kotlin_build_gradle_missing());
                } else if issue.description.contains("No Kotlin source files") || issue.description.contains("src directory") {
                    actions.extend(self.create_kotlin_source_files());
                } else if issue.description.contains("Gradle wrapper") {
                    actions.extend(self.fix_kotlin_gradle_wrapper_missing());
                } else if issue.description.contains("build errors") {
                    actions.extend(self.fix_kotlin_build_errors());
                }
            },
            _ => {
                actions.push(format!("Manual intervention required for Kotlin issue: {}", issue.description));
            }
        }
        
        actions
    }

    /// Fix missing Zig compiler
    fn fix_zig_compiler_missing(&self) -> Vec<String> {
        vec![
            "Installing Zig compiler...".to_string(),
            "Download from: https://ziglang.org/download/".to_string(),
            "Extract to a directory and add to PATH".to_string(),
            "Verifying Zig installation...".to_string(),
            "zig version".to_string(),
        ]
    }

    /// Fix missing Zig build.zig file
    fn fix_zig_build_file_missing(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let zig_dir = "benchmark/zig_ext";
        let build_zig_path = format!("{}/build.zig", zig_dir);
        
        let build_content = self.generate_zig_build_file();
        match std::fs::write(&build_zig_path, build_content) {
            Ok(_) => actions.push(format!("Created build.zig: {}", build_zig_path)),
            Err(e) => actions.push(format!("Failed to create build.zig: {}", e)),
        }
        
        actions
    }

    /// Create Zig source files
    fn create_zig_source_files(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let zig_dir = "benchmark/zig_ext";
        
        // Create directory if it doesn't exist
        if let Err(_) = std::fs::create_dir_all(zig_dir) {
            actions.push(format!("Failed to create directory: {}", zig_dir));
            return actions;
        }
        
        // Create main Zig source file
        let zig_file_path = format!("{}/zigfunctions.zig", zig_dir);
        let zig_content = self.generate_zig_source_content();
        match std::fs::write(&zig_file_path, zig_content) {
            Ok(_) => actions.push(format!("Created Zig source: {}", zig_file_path)),
            Err(e) => actions.push(format!("Failed to create Zig source: {}", e)),
        }
        
        actions
    }

    /// Fix Zig build errors
    fn fix_zig_build_errors(&self) -> Vec<String> {
        vec![
            "Fixing Zig build errors...".to_string(),
            "cd benchmark/zig_ext".to_string(),
            "zig build".to_string(),
            "Check build.zig configuration if errors persist".to_string(),
        ]
    }

    /// Fix missing Nim compiler
    fn fix_nim_compiler_missing(&self) -> Vec<String> {
        vec![
            "Installing Nim compiler...".to_string(),
            "Download from: https://nim-lang.org/install.html".to_string(),
            "Follow installation instructions for your platform".to_string(),
            "Verifying Nim installation...".to_string(),
            "nim --version".to_string(),
        ]
    }

    /// Fix missing Nim .nimble file
    fn fix_nim_nimble_file_missing(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let nim_dir = "benchmark/nim_ext";
        let nimble_file_path = format!("{}/nimfunctions.nimble", nim_dir);
        
        let nimble_content = self.generate_nim_nimble_file();
        match std::fs::write(&nimble_file_path, nimble_content) {
            Ok(_) => actions.push(format!("Created .nimble file: {}", nimble_file_path)),
            Err(e) => actions.push(format!("Failed to create .nimble file: {}", e)),
        }
        
        actions
    }

    /// Create Nim source files
    fn create_nim_source_files(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let nim_dir = "benchmark/nim_ext";
        
        // Create directory if it doesn't exist
        if let Err(_) = std::fs::create_dir_all(nim_dir) {
            actions.push(format!("Failed to create directory: {}", nim_dir));
            return actions;
        }
        
        // Create main Nim source file
        let nim_file_path = format!("{}/nimfunctions.nim", nim_dir);
        let nim_content = self.generate_nim_source_content();
        match std::fs::write(&nim_file_path, nim_content) {
            Ok(_) => actions.push(format!("Created Nim source: {}", nim_file_path)),
            Err(e) => actions.push(format!("Failed to create Nim source: {}", e)),
        }
        
        actions
    }

    /// Fix Nim compilation errors
    fn fix_nim_compilation_errors(&self) -> Vec<String> {
        vec![
            "Fixing Nim compilation errors...".to_string(),
            "cd benchmark/nim_ext".to_string(),
            "nim c --app:lib --noMain nimfunctions.nim".to_string(),
            "Check exportc pragma usage if errors persist".to_string(),
        ]
    }

    /// Fix missing Julia
    fn fix_julia_missing(&self) -> Vec<String> {
        vec![
            "Installing Julia...".to_string(),
            "Download from: https://julialang.org/downloads/".to_string(),
            "Add Julia to PATH environment variable".to_string(),
            "Verifying Julia installation...".to_string(),
            "julia --version".to_string(),
        ]
    }

    /// Fix missing Julia PackageCompiler
    fn fix_julia_package_compiler_missing(&self) -> Vec<String> {
        vec![
            "Installing PackageCompiler.jl...".to_string(),
            "julia -e 'using Pkg; Pkg.add(\"PackageCompiler\")'".to_string(),
            "Verifying PackageCompiler installation...".to_string(),
            "julia -e 'using PackageCompiler'".to_string(),
        ]
    }

    /// Fix missing Julia Project.toml
    fn fix_julia_project_toml_missing(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let julia_dir = "benchmark/julia_ext";
        let project_toml_path = format!("{}/Project.toml", julia_dir);
        
        let project_content = self.generate_julia_project_toml();
        match std::fs::write(&project_toml_path, project_content) {
            Ok(_) => actions.push(format!("Created Project.toml: {}", project_toml_path)),
            Err(e) => actions.push(format!("Failed to create Project.toml: {}", e)),
        }
        
        actions
    }

    /// Create Julia source files
    fn create_julia_source_files(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let julia_dir = "benchmark/julia_ext";
        
        // Create directory if it doesn't exist
        if let Err(_) = std::fs::create_dir_all(julia_dir) {
            actions.push(format!("Failed to create directory: {}", julia_dir));
            return actions;
        }
        
        // Create main Julia source file
        let julia_file_path = format!("{}/functions.jl", julia_dir);
        let julia_content = self.generate_julia_source_content();
        match std::fs::write(&julia_file_path, julia_content) {
            Ok(_) => actions.push(format!("Created Julia source: {}", julia_file_path)),
            Err(e) => actions.push(format!("Failed to create Julia source: {}", e)),
        }
        
        actions
    }

    /// Fix missing Kotlin/Native
    fn fix_kotlin_native_missing(&self) -> Vec<String> {
        vec![
            "Installing Kotlin/Native...".to_string(),
            "Download from: https://kotlinlang.org/docs/native-overview.html".to_string(),
            "Or install via SDKMAN: sdk install kotlin".to_string(),
            "Verifying Kotlin/Native installation...".to_string(),
            "kotlinc-native -version".to_string(),
        ]
    }

    /// Fix missing Kotlin build.gradle.kts
    fn fix_kotlin_build_gradle_missing(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let kotlin_dir = "benchmark/kotlin_ext";
        let build_gradle_path = format!("{}/build.gradle.kts", kotlin_dir);
        
        let build_content = self.generate_kotlin_build_gradle();
        match std::fs::write(&build_gradle_path, build_content) {
            Ok(_) => actions.push(format!("Created build.gradle.kts: {}", build_gradle_path)),
            Err(e) => actions.push(format!("Failed to create build.gradle.kts: {}", e)),
        }
        
        actions
    }

    /// Create Kotlin source files
    fn create_kotlin_source_files(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let kotlin_dir = "benchmark/kotlin_ext";
        let src_dir = format!("{}/src", kotlin_dir);
        
        // Create directories if they don't exist
        if let Err(_) = std::fs::create_dir_all(&src_dir) {
            actions.push(format!("Failed to create directory: {}", src_dir));
            return actions;
        }
        
        // Create main Kotlin source file
        let kotlin_file_path = format!("{}/Functions.kt", src_dir);
        let kotlin_content = self.generate_kotlin_source_content();
        match std::fs::write(&kotlin_file_path, kotlin_content) {
            Ok(_) => actions.push(format!("Created Kotlin source: {}", kotlin_file_path)),
            Err(e) => actions.push(format!("Failed to create Kotlin source: {}", e)),
        }
        
        actions
    }

    /// Fix missing Kotlin Gradle wrapper
    fn fix_kotlin_gradle_wrapper_missing(&self) -> Vec<String> {
        vec![
            "Creating Gradle wrapper...".to_string(),
            "cd benchmark/kotlin_ext".to_string(),
            "gradle wrapper".to_string(),
            "This creates gradlew.bat for Windows builds".to_string(),
        ]
    }

    /// Fix Kotlin build errors
    fn fix_kotlin_build_errors(&self) -> Vec<String> {
        vec![
            "Fixing Kotlin/Native build errors...".to_string(),
            "cd benchmark/kotlin_ext".to_string(),
            "gradlew.bat build".to_string(),
            "Check build.gradle.kts configuration if errors persist".to_string(),
        ]
    }

    /// Generate Zig build.zig content
    fn generate_zig_build_file(&self) -> String {
        r#"const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const lib = b.addSharedLibrary(.{
        .name = "zigfunctions",
        .root_source_file = .{ .path = "zigfunctions.zig" },
        .target = target,
        .optimize = optimize,
    });

    // Export C ABI functions
    lib.linkLibC();
    
    b.installArtifact(lib);
}
"#.to_string()
    }

    /// Generate Zig source content
    fn generate_zig_source_content(&self) -> String {
        r#"const std = @import("std");

export fn zig_numeric_add(a: f64, b: f64) f64 {
    return a + b;
}

export fn zig_numeric_multiply(a: f64, b: f64) f64 {
    return a * b;
}

export fn zig_memory_allocate(size: usize) ?*f64 {
    if (size == 0) return null;
    
    const allocator = std.heap.page_allocator;
    const memory = allocator.alloc(f64, size) catch return null;
    
    // Initialize to zero
    for (memory) |*item| {
        item.* = 0.0;
    }
    
    return memory.ptr;
}

export fn zig_memory_free(ptr: ?*f64, size: usize) void {
    if (ptr == null or size == 0) return;
    
    const allocator = std.heap.page_allocator;
    const memory = ptr.?[0..size];
    allocator.free(memory);
}

export fn zig_parallel_compute(input: [*]const f64, output: [*]f64, size: usize) void {
    var i: usize = 0;
    while (i < size) : (i += 1) {
        output[i] = input[i] * input[i];
    }
}
"#.to_string()
    }

    /// Generate Nim .nimble file content
    fn generate_nim_nimble_file(&self) -> String {
        r#"# Package

version       = "0.1.0"
author        = "FFI Audit System"
description   = "Nim FFI functions for benchmarking"
license       = "MIT"
srcDir        = "."

# Dependencies

requires "nim >= 1.6.0"
"#.to_string()
    }

    /// Generate Nim source content
    fn generate_nim_source_content(&self) -> String {
        r#"{.compile: "nimfunctions.nim".}

proc nim_numeric_add*(a: cdouble, b: cdouble): cdouble {.exportc.} =
  return a + b

proc nim_numeric_multiply*(a: cdouble, b: cdouble): cdouble {.exportc.} =
  return a * b

proc nim_memory_allocate*(size: csize_t): ptr cdouble {.exportc.} =
  if size == 0:
    return nil
  
  let memory = cast[ptr cdouble](alloc(size * sizeof(cdouble)))
  if memory != nil:
    # Initialize to zero
    for i in 0..<size:
      cast[ptr UncheckedArray[cdouble]](memory)[i] = 0.0
  
  return memory

proc nim_memory_free*(p: ptr cdouble) {.exportc.} =
  if p != nil:
    dealloc(p)

proc nim_parallel_compute*(input: ptr cdouble, output: ptr cdouble, size: csize_t) {.exportc.} =
  if input == nil or output == nil or size == 0:
    return
  
  let inputArray = cast[ptr UncheckedArray[cdouble]](input)
  let outputArray = cast[ptr UncheckedArray[cdouble]](output)
  
  for i in 0..<size:
    outputArray[i] = inputArray[i] * inputArray[i]
"#.to_string()
    }

    /// Generate Julia Project.toml content
    fn generate_julia_project_toml(&self) -> String {
        r#"name = "JuliaFunctions"
uuid = "12345678-1234-5678-9abc-123456789abc"
version = "0.1.0"

[deps]
PackageCompiler = "9b87118b-4619-50d2-8e1e-99f35a4d4d9d"
"#.to_string()
    }

    /// Generate Julia source content
    fn generate_julia_source_content(&self) -> String {
        r#"module JuliaFunctions

using PackageCompiler

@ccallable function julia_numeric_add(a::Cdouble, b::Cdouble)::Cdouble
    return a + b
end

@ccallable function julia_numeric_multiply(a::Cdouble, b::Cdouble)::Cdouble
    return a * b
end

@ccallable function julia_memory_allocate(size::Csize_t)::Ptr{Cdouble}
    if size == 0
        return C_NULL
    end
    
    memory = Vector{Cdouble}(undef, size)
    fill!(memory, 0.0)
    
    # Return pointer to the data
    return pointer(memory)
end

@ccallable function julia_parallel_compute(input::Ptr{Cdouble}, output::Ptr{Cdouble}, size::Csize_t)::Cvoid
    if input == C_NULL || output == C_NULL || size == 0
        return
    end
    
    input_array = unsafe_wrap(Array, input, size)
    output_array = unsafe_wrap(Array, output, size)
    
    for i in 1:size
        output_array[i] = input_array[i] * input_array[i]
    end
    
    return nothing
end

end # module
"#.to_string()
    }

    /// Generate Kotlin build.gradle.kts content
    fn generate_kotlin_build_gradle(&self) -> String {
        r#"plugins {
    kotlin("multiplatform") version "1.9.0"
}

kotlin {
    val hostOs = System.getProperty("os.name")
    val isMingwX64 = hostOs.startsWith("Windows")
    val nativeTarget = when {
        hostOs == "Mac OS X" -> macosX64("native")
        hostOs == "Linux" -> linuxX64("native")
        isMingwX64 -> mingwX64("native")
        else -> throw GradleException("Host OS is not supported in Kotlin/Native.")
    }

    nativeTarget.apply {
        binaries {
            sharedLib {
                baseName = "kotlin_ext"
            }
        }
    }
    
    sourceSets {
        val nativeMain by getting
        val nativeTest by getting
    }
}
"#.to_string()
    }

    /// Generate Kotlin source content
    fn generate_kotlin_source_content(&self) -> String {
        r#"@file:Suppress("unused")

import kotlinx.cinterop.*

@CName("kotlin_numeric_add")
fun numericAdd(a: Double, b: Double): Double {
    return a + b
}

@CName("kotlin_numeric_multiply")
fun numericMultiply(a: Double, b: Double): Double {
    return a * b
}

@CName("kotlin_memory_allocate")
fun memoryAllocate(size: ULong): CPointer<DoubleVar>? {
    if (size == 0UL) return null
    
    return nativeHeap.allocArray<DoubleVar>(size.toInt()).also { ptr ->
        for (i in 0 until size.toInt()) {
            ptr[i] = 0.0
        }
    }
}

@CName("kotlin_memory_free")
fun memoryFree(ptr: CPointer<DoubleVar>?) {
    ptr?.let { nativeHeap.free(it) }
}

@CName("kotlin_parallel_compute")
fun parallelCompute(input: CPointer<DoubleVar>?, output: CPointer<DoubleVar>?, size: ULong) {
    if (input == null || output == null || size == 0UL) return
    
    for (i in 0 until size.toInt()) {
        output[i] = input[i] * input[i]
    }
}
"#.to_string()
    }

    /// Fix Rust/Go specific compilation and linking issues
    pub fn fix_rust_go_issues(&self, ffi_impl: &str, issues: &[DLLIssue]) -> Result<Vec<String>> {
        let mut fix_actions = Vec::new();
        
        for issue in issues {
            match ffi_impl {
                "rust_ext" => {
                    fix_actions.extend(self.fix_rust_specific_issue(issue));
                },
                "go_ext" => {
                    fix_actions.extend(self.fix_go_specific_issue(issue));
                },
                _ => {
                    fix_actions.push(format!("Unsupported implementation for Rust/Go fixes: {}", ffi_impl));
                }
            }
        }
        
        Ok(fix_actions)
    }

    /// Fix Rust-specific issues
    fn fix_rust_specific_issue(&self, issue: &DLLIssue) -> Vec<String> {
        let mut actions = Vec::new();
        
        match &issue.issue_type {
            DLLIssueType::DependencyMissing => {
                if issue.description.contains("Rust toolchain") {
                    actions.extend(self.fix_rust_toolchain_missing());
                } else if issue.description.contains("Cargo") {
                    actions.extend(self.fix_cargo_missing());
                } else if issue.description.contains("Maturin") {
                    actions.extend(self.fix_maturin_missing());
                }
            },
            DLLIssueType::LoadFailure => {
                if issue.description.contains("Cargo.toml") {
                    actions.extend(self.fix_rust_cargo_toml_issues(&issue.affected_library));
                } else if issue.description.contains("No Rust source files") {
                    actions.extend(self.create_rust_source_files());
                } else if issue.description.contains("PyO3") {
                    actions.extend(self.fix_rust_pyo3_issues(&issue.affected_library));
                } else if issue.description.contains("compilation errors") {
                    actions.extend(self.fix_rust_compilation_errors());
                }
            },
            _ => {
                actions.push(format!("Manual intervention required for Rust issue: {}", issue.description));
            }
        }
        
        actions
    }

    /// Fix Go-specific issues
    fn fix_go_specific_issue(&self, issue: &DLLIssue) -> Vec<String> {
        let mut actions = Vec::new();
        
        match &issue.issue_type {
            DLLIssueType::DependencyMissing => {
                if issue.description.contains("Go compiler") {
                    actions.extend(self.fix_go_compiler_missing());
                } else if issue.description.contains("CGO") {
                    actions.extend(self.fix_cgo_missing());
                }
            },
            DLLIssueType::LoadFailure => {
                if issue.description.contains("go.mod") {
                    actions.extend(self.fix_go_mod_missing());
                } else if issue.description.contains("No Go source files") {
                    actions.extend(self.create_go_source_files());
                } else if issue.description.contains("CGO import") {
                    actions.extend(self.fix_go_cgo_imports());
                } else if issue.description.contains("export comments") {
                    actions.extend(self.fix_go_export_comments());
                } else if issue.description.contains("build errors") {
                    actions.extend(self.fix_go_build_errors());
                }
            },
            _ => {
                actions.push(format!("Manual intervention required for Go issue: {}", issue.description));
            }
        }
        
        actions
    }

    /// Fix missing Rust toolchain
    fn fix_rust_toolchain_missing(&self) -> Vec<String> {
        vec![
            "Installing Rust toolchain...".to_string(),
            "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh".to_string(),
            "source ~/.cargo/env".to_string(),
            "Verifying Rust installation...".to_string(),
            "rustc --version".to_string(),
            "cargo --version".to_string(),
        ]
    }

    /// Fix missing Cargo
    fn fix_cargo_missing(&self) -> Vec<String> {
        vec![
            "Cargo comes with Rust, ensuring Rust is properly installed...".to_string(),
            "rustup update".to_string(),
            "Verifying Cargo installation...".to_string(),
            "cargo --version".to_string(),
        ]
    }

    /// Fix missing Maturin
    fn fix_maturin_missing(&self) -> Vec<String> {
        vec![
            "Installing Maturin...".to_string(),
            "pip install maturin".to_string(),
            "Verifying Maturin installation...".to_string(),
            "maturin --version".to_string(),
        ]
    }

    /// Fix Rust Cargo.toml issues
    fn fix_rust_cargo_toml_issues(&self, cargo_toml_path: &str) -> Vec<String> {
        let mut actions = Vec::new();
        
        if !std::path::Path::new(cargo_toml_path).exists() {
            // Create new Cargo.toml
            let cargo_content = self.generate_rust_cargo_toml();
            match std::fs::write(cargo_toml_path, cargo_content) {
                Ok(_) => actions.push(format!("Created Cargo.toml: {}", cargo_toml_path)),
                Err(e) => actions.push(format!("Failed to create Cargo.toml: {}", e)),
            }
        } else {
            // Fix existing Cargo.toml
            if let Ok(content) = std::fs::read_to_string(cargo_toml_path) {
                let mut fixed_content = content;
                
                // Add cdylib crate type if missing
                if !fixed_content.contains("crate-type") || !fixed_content.contains("cdylib") {
                    if !fixed_content.contains("[lib]") {
                        fixed_content.push_str("\n[lib]\ncrate-type = [\"cdylib\"]\n");
                    } else {
                        fixed_content = fixed_content.replace(
                            "[lib]",
                            "[lib]\ncrate-type = [\"cdylib\"]"
                        );
                    }
                }
                
                // Add PyO3 dependency if missing
                if !fixed_content.contains("pyo3") {
                    if !fixed_content.contains("[dependencies]") {
                        fixed_content.push_str("\n[dependencies]\npyo3 = { version = \"0.20\", features = [\"extension-module\"] }\n");
                    } else {
                        fixed_content = fixed_content.replace(
                            "[dependencies]",
                            "[dependencies]\npyo3 = { version = \"0.20\", features = [\"extension-module\"] }"
                        );
                    }
                }
                
                match std::fs::write(cargo_toml_path, fixed_content) {
                    Ok(_) => actions.push(format!("Fixed Cargo.toml: {}", cargo_toml_path)),
                    Err(e) => actions.push(format!("Failed to fix Cargo.toml: {}", e)),
                }
            }
        }
        
        actions
    }

    /// Create Rust source files
    fn create_rust_source_files(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let rust_dir = "benchmark/rust_ext";
        let src_dir = format!("{}/src", rust_dir);
        
        // Create directories if they don't exist
        if let Err(_) = std::fs::create_dir_all(&src_dir) {
            actions.push(format!("Failed to create directory: {}", src_dir));
            return actions;
        }
        
        // Create lib.rs
        let lib_rs_path = format!("{}/lib.rs", src_dir);
        let lib_content = self.generate_rust_lib_content();
        match std::fs::write(&lib_rs_path, lib_content) {
            Ok(_) => actions.push(format!("Created Rust lib.rs: {}", lib_rs_path)),
            Err(e) => actions.push(format!("Failed to create lib.rs: {}", e)),
        }
        
        // Create Cargo.toml
        let cargo_toml_path = format!("{}/Cargo.toml", rust_dir);
        let cargo_content = self.generate_rust_cargo_toml();
        match std::fs::write(&cargo_toml_path, cargo_content) {
            Ok(_) => actions.push(format!("Created Cargo.toml: {}", cargo_toml_path)),
            Err(e) => actions.push(format!("Failed to create Cargo.toml: {}", e)),
        }
        
        actions
    }

    /// Fix Rust PyO3 issues
    fn fix_rust_pyo3_issues(&self, file_path: &str) -> Vec<String> {
        let mut actions = Vec::new();
        
        if let Ok(content) = std::fs::read_to_string(file_path) {
            let mut fixed_content = content;
            
            // Add PyO3 imports if missing
            if !fixed_content.contains("use pyo3::prelude::*") {
                fixed_content = format!("use pyo3::prelude::*;\n{}", fixed_content);
            }
            
            // Add pymodule definition if missing
            if !fixed_content.contains("#[pymodule]") {
                fixed_content.push_str(r#"

#[pymodule]
fn rust_ext(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_numeric_add, m)?)?;
    m.add_function(wrap_pyfunction!(rust_numeric_multiply, m)?)?;
    m.add_function(wrap_pyfunction!(rust_memory_allocate, m)?)?;
    Ok(())
}
"#);
            }
            
            match std::fs::write(file_path, fixed_content) {
                Ok(_) => actions.push(format!("Fixed PyO3 issues in: {}", file_path)),
                Err(e) => actions.push(format!("Failed to fix PyO3 issues in {}: {}", file_path, e)),
            }
        }
        
        actions
    }

    /// Fix Rust compilation errors
    fn fix_rust_compilation_errors(&self) -> Vec<String> {
        vec![
            "Fixing Rust compilation errors...".to_string(),
            "cd benchmark/rust_ext".to_string(),
            "cargo clean".to_string(),
            "cargo check".to_string(),
            "If errors persist, check Rust source code syntax".to_string(),
        ]
    }

    /// Fix missing Go compiler
    fn fix_go_compiler_missing(&self) -> Vec<String> {
        vec![
            "Installing Go compiler...".to_string(),
            "Download from: https://golang.org/dl/".to_string(),
            "Add Go to PATH environment variable".to_string(),
            "Verifying Go installation...".to_string(),
            "go version".to_string(),
        ]
    }

    /// Fix missing CGO
    fn fix_cgo_missing(&self) -> Vec<String> {
        vec![
            "Enabling CGO...".to_string(),
            "set CGO_ENABLED=1".to_string(),
            "Ensuring C compiler is available...".to_string(),
            #[cfg(target_os = "windows")]
            "Install MinGW-w64 or Visual Studio Build Tools".to_string(),
            #[cfg(not(target_os = "windows"))]
            "sudo apt-get install gcc || sudo yum install gcc".to_string(),
            "Verifying CGO...".to_string(),
            "go env CGO_ENABLED".to_string(),
        ]
    }

    /// Fix missing go.mod
    fn fix_go_mod_missing(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let go_dir = "benchmark/go_ext";
        let go_mod_path = format!("{}/go.mod", go_dir);
        
        let go_mod_content = r#"module gofunctions

go 1.19

require ()
"#;
        
        match std::fs::write(&go_mod_path, go_mod_content) {
            Ok(_) => actions.push(format!("Created go.mod: {}", go_mod_path)),
            Err(e) => actions.push(format!("Failed to create go.mod: {}", e)),
        }
        
        actions.extend(vec![
            "cd benchmark/go_ext".to_string(),
            "go mod tidy".to_string(),
        ]);
        
        actions
    }

    /// Create Go source files
    fn create_go_source_files(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let go_dir = "benchmark/go_ext";
        
        // Create directory if it doesn't exist
        if let Err(_) = std::fs::create_dir_all(go_dir) {
            actions.push(format!("Failed to create directory: {}", go_dir));
            return actions;
        }
        
        // Create functions.go
        let functions_go_path = format!("{}/functions.go", go_dir);
        let go_content = self.generate_go_source_content();
        match std::fs::write(&functions_go_path, go_content) {
            Ok(_) => actions.push(format!("Created Go source: {}", functions_go_path)),
            Err(e) => actions.push(format!("Failed to create functions.go: {}", e)),
        }
        
        actions
    }

    /// Fix Go CGO imports
    fn fix_go_cgo_imports(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let go_dir = "benchmark/go_ext";
        
        if let Ok(entries) = std::fs::read_dir(go_dir) {
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "go" {
                        if let Ok(content) = std::fs::read_to_string(entry.path()) {
                            if !content.contains("import \"C\"") {
                                let fixed_content = format!("import \"C\"\n{}", content);
                                match std::fs::write(entry.path(), fixed_content) {
                                    Ok(_) => actions.push(format!("Added CGO import to: {}", entry.path().display())),
                                    Err(e) => actions.push(format!("Failed to fix CGO import in {}: {}", entry.path().display(), e)),
                                }
                            }
                        }
                    }
                }
            }
        }
        
        actions
    }

    /// Fix Go export comments
    fn fix_go_export_comments(&self) -> Vec<String> {
        let mut actions = Vec::new();
        let go_dir = "benchmark/go_ext";
        
        if let Ok(entries) = std::fs::read_dir(go_dir) {
            for entry in entries.flatten() {
                if let Some(ext) = entry.path().extension() {
                    if ext == "go" {
                        if let Ok(content) = std::fs::read_to_string(entry.path()) {
                            let mut fixed_content = content;
                            
                            // Add export comments for common functions
                            if fixed_content.contains("func NumericAdd") && !fixed_content.contains("//export NumericAdd") {
                                fixed_content = fixed_content.replace("func NumericAdd", "//export NumericAdd\nfunc NumericAdd");
                            }
                            if fixed_content.contains("func NumericMultiply") && !fixed_content.contains("//export NumericMultiply") {
                                fixed_content = fixed_content.replace("func NumericMultiply", "//export NumericMultiply\nfunc NumericMultiply");
                            }
                            if fixed_content.contains("func MemoryAllocate") && !fixed_content.contains("//export MemoryAllocate") {
                                fixed_content = fixed_content.replace("func MemoryAllocate", "//export MemoryAllocate\nfunc MemoryAllocate");
                            }
                            
                            match std::fs::write(entry.path(), fixed_content) {
                                Ok(_) => actions.push(format!("Added export comments to: {}", entry.path().display())),
                                Err(e) => actions.push(format!("Failed to fix export comments in {}: {}", entry.path().display(), e)),
                            }
                        }
                    }
                }
            }
        }
        
        actions
    }

    /// Fix Go build errors
    fn fix_go_build_errors(&self) -> Vec<String> {
        vec![
            "Fixing Go build errors...".to_string(),
            "cd benchmark/go_ext".to_string(),
            "go clean".to_string(),
            "set CGO_ENABLED=1".to_string(),
            "go build -buildmode=c-shared -o libgofunctions.dll functions.go".to_string(),
            "If errors persist, check Go source code and CGO configuration".to_string(),
        ]
    }

    /// Generate Rust lib.rs content
    fn generate_rust_lib_content(&self) -> String {
        r#"use pyo3::prelude::*;
use pyo3::types::PyList;

/// Add two numbers
#[pyfunction]
fn rust_numeric_add(a: f64, b: f64) -> f64 {
    a + b
}

/// Multiply two numbers
#[pyfunction]
fn rust_numeric_multiply(a: f64, b: f64) -> f64 {
    a * b
}

/// Allocate a vector of given size
#[pyfunction]
fn rust_memory_allocate(size: usize) -> PyResult<Vec<f64>> {
    if size == 0 {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Size must be positive"));
    }
    Ok(vec![0.0; size])
}

/// Parallel computation (square of numbers)
#[pyfunction]
fn rust_parallel_compute(input: Vec<f64>) -> Vec<f64> {
    input.iter().map(|x| x * x).collect()
}

/// Python module definition
#[pymodule]
fn rust_ext(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_numeric_add, m)?)?;
    m.add_function(wrap_pyfunction!(rust_numeric_multiply, m)?)?;
    m.add_function(wrap_pyfunction!(rust_memory_allocate, m)?)?;
    m.add_function(wrap_pyfunction!(rust_parallel_compute, m)?)?;
    Ok(())
}
"#.to_string()
    }

    /// Generate Go source content
    fn generate_go_source_content(&self) -> String {
        r#"package main

import "C"
import (
    "unsafe"
)

//export NumericAdd
func NumericAdd(a, b C.double) C.double {
    return C.double(float64(a) + float64(b))
}

//export NumericMultiply
func NumericMultiply(a, b C.double) C.double {
    return C.double(float64(a) * float64(b))
}

//export MemoryAllocate
func MemoryAllocate(size C.int) *C.double {
    if size <= 0 {
        return nil
    }
    
    // Allocate memory for array
    arr := make([]C.double, int(size))
    for i := range arr {
        arr[i] = 0.0
    }
    
    return (*C.double)(unsafe.Pointer(&arr[0]))
}

//export ParallelCompute
func ParallelCompute(input *C.double, size C.int, output *C.double) {
    if input == nil || output == nil || size <= 0 {
        return
    }
    
    // Convert C arrays to Go slices
    inputSlice := (*[1 << 30]C.double)(unsafe.Pointer(input))[:size:size]
    outputSlice := (*[1 << 30]C.double)(unsafe.Pointer(output))[:size:size]
    
    // Compute squares
    for i := 0; i < int(size); i++ {
        outputSlice[i] = inputSlice[i] * inputSlice[i]
    }
}

func main() {
    // Required for CGO shared library
}
"#.to_string()
    }

    /// Generate build script to fix issues
    pub fn generate_build_script(&self, ffi_impl: &str, issues: &[DLLIssue]) -> BuildScriptResult {
        let mut script = BuildScript {
            language: ffi_impl.to_string(),
            script_content: String::new(),
            required_tools: vec![],
            environment_variables: std::collections::HashMap::new(),
            build_commands: vec![],
            validation_commands: vec![],
        };

        // Analyze issues and generate appropriate build script
        let mut has_dependency_issues = false;
        let mut has_architecture_issues = false;
        let mut has_path_issues = false;

        for issue in issues {
            match issue.issue_type {
                DLLIssueType::DependencyMissing => has_dependency_issues = true,
                DLLIssueType::ArchitectureMismatch => has_architecture_issues = true,
                DLLIssueType::PathResolutionFailure => has_path_issues = true,
                _ => {}
            }
        }

        // Generate script based on FFI implementation type
        match ffi_impl {
            "c_ext" => self.generate_c_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "cpp_ext" => self.generate_cpp_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "cython_ext" => self.generate_cython_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "numpy_impl" => self.generate_numpy_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "rust_ext" => self.generate_rust_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "go_ext" => self.generate_go_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "fortran_ext" => self.generate_fortran_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "zig_ext" => self.generate_zig_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "nim_ext" => self.generate_nim_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "julia_ext" => self.generate_julia_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            "kotlin_ext" => self.generate_kotlin_build_script(&mut script, has_dependency_issues, has_architecture_issues),
            _ => return Err(crate::error::AuditError::UnsupportedImplementation(ffi_impl.to_string())),
        }

        // Add common validation commands
        script.validation_commands.extend(vec![
            "python -c \"import sys; print(f'Python: {sys.version}')\"".to_string(),
            format!("python -c \"import {}; print('Import successful')\"", self.get_module_name(ffi_impl)),
        ]);

        Ok(script)
    }

    /// Correct library paths
    pub fn correct_library_paths(&self, ffi_impl: &str) -> PathCorrectionResult {
        let mut correction = PathCorrection {
            implementation: ffi_impl.to_string(),
            original_paths: vec![],
            corrected_paths: vec![],
            corrections_applied: vec![],
        };

        // Get expected library paths
        let expected_paths = self.get_expected_library_paths(ffi_impl);
        
        for original_path in expected_paths {
            correction.original_paths.push(original_path.clone());
            
            // Apply various path corrections
            let mut corrected_path = original_path.clone();
            let mut corrections = vec![];

            // Convert to absolute path if relative
            if !std::path::Path::new(&corrected_path).is_absolute() {
                if let Ok(current_dir) = std::env::current_dir() {
                    let absolute_path = current_dir.join(&corrected_path);
                    corrected_path = absolute_path.to_string_lossy().to_string();
                    corrections.push(PathCorrectionEntry {
                        original_path: original_path.clone(),
                        corrected_path: corrected_path.clone(),
                        correction_type: PathCorrectionType::RelativeToAbsolute,
                        description: "Converted relative path to absolute path".to_string(),
                    });
                }
            }

            // Normalize path separators for Windows
            #[cfg(target_os = "windows")]
            {
                let normalized = corrected_path.replace("/", "\\");
                if normalized != corrected_path {
                    corrected_path = normalized;
                    corrections.push(PathCorrectionEntry {
                        original_path: original_path.clone(),
                        corrected_path: corrected_path.clone(),
                        correction_type: PathCorrectionType::DirectorySeparatorFix,
                        description: "Normalized path separators for Windows".to_string(),
                    });
                }
            }

            // Expand environment variables
            if corrected_path.contains("$") || corrected_path.contains("%") {
                let expanded = self.expand_environment_variables(&corrected_path);
                if expanded != corrected_path {
                    corrected_path = expanded;
                    corrections.push(PathCorrectionEntry {
                        original_path: original_path.clone(),
                        corrected_path: corrected_path.clone(),
                        correction_type: PathCorrectionType::EnvironmentVariableExpansion,
                        description: "Expanded environment variables in path".to_string(),
                    });
                }
            }

            correction.corrected_paths.push(corrected_path);
            correction.corrections_applied.extend(corrections);
        }

        Ok(correction)
    }

    /// Validate symbol exports
    pub fn validate_symbol_exports(&self, library_path: &str) -> SymbolExportValidationResult {
        let mut validation = SymbolExportValidation {
            library_path: library_path.to_string(),
            exported_symbols: vec![],
            missing_symbols: vec![],
            validation_successful: false,
            issues: vec![],
        };

        // Check if library file exists
        if !std::path::Path::new(library_path).exists() {
            validation.issues.push(SymbolExportIssue {
                symbol_name: "N/A".to_string(),
                issue_description: "Library file does not exist".to_string(),
                suggested_fix: "Build the library first".to_string(),
            });
            return Ok(validation);
        }

        // Get expected symbols based on library path
        let expected_symbols = self.get_expected_symbols_for_library(library_path);

        // Validate symbols using platform-specific methods
        #[cfg(target_os = "windows")]
        {
            match self.validate_windows_symbols(library_path, &expected_symbols) {
                Ok((found, missing, issues)) => {
                    validation.exported_symbols = found;
                    validation.missing_symbols = missing;
                    validation.issues = issues;
                    validation.validation_successful = validation.missing_symbols.is_empty();
                }
                Err(e) => {
                    validation.issues.push(SymbolExportIssue {
                        symbol_name: "N/A".to_string(),
                        issue_description: format!("Symbol validation failed: {}", e),
                        suggested_fix: "Check library format and architecture".to_string(),
                    });
                }
            }
        }

        #[cfg(not(target_os = "windows"))]
        {
            match self.validate_unix_symbols(library_path, &expected_symbols) {
                Ok((found, missing, issues)) => {
                    validation.exported_symbols = found;
                    validation.missing_symbols = missing;
                    validation.issues = issues;
                    validation.validation_successful = validation.missing_symbols.is_empty();
                }
                Err(e) => {
                    validation.issues.push(SymbolExportIssue {
                        symbol_name: "N/A".to_string(),
                        issue_description: format!("Symbol validation failed: {}", e),
                        suggested_fix: "Check library format and dependencies".to_string(),
                    });
                }
            }
        }

        Ok(validation)
    }

    /// Generate compatibility layer
    pub fn generate_compatibility_layer(&self, ffi_impl: &str) -> CompatibilityLayerResult {
        let mut layer = CompatibilityLayer {
            implementation: ffi_impl.to_string(),
            layer_type: CompatibilityLayerType::ABIWrapper,
            generated_code: String::new(),
            installation_instructions: vec![],
        };

        // Generate compatibility layer based on implementation type
        match ffi_impl {
            "c_ext" => self.generate_c_compatibility_layer(&mut layer),
            "cpp_ext" => self.generate_cpp_compatibility_layer(&mut layer),
            "cython_ext" => self.generate_cython_compatibility_layer(&mut layer),
            "numpy_impl" => self.generate_numpy_compatibility_layer(&mut layer),
            "rust_ext" => self.generate_rust_compatibility_layer(&mut layer),
            "go_ext" => self.generate_go_compatibility_layer(&mut layer),
            "fortran_ext" => self.generate_fortran_compatibility_layer(&mut layer),
            "zig_ext" => self.generate_zig_compatibility_layer(&mut layer),
            "nim_ext" => self.generate_nim_compatibility_layer(&mut layer),
            "julia_ext" => self.generate_julia_compatibility_layer(&mut layer),
            "kotlin_ext" => self.generate_kotlin_compatibility_layer(&mut layer),
            _ => return Err(crate::error::AuditError::UnsupportedImplementation(ffi_impl.to_string())),
        }

        Ok(layer)
    }

    // Helper methods for build script generation

    /// Generate C extension build script
    fn generate_c_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "gcc".to_string(),
            "python3-dev".to_string(),
            "setuptools".to_string(),
        ]);

        if has_dependency_issues {
            script.environment_variables.insert("CC".to_string(), "gcc".to_string());
            script.environment_variables.insert("CXX".to_string(), "g++".to_string());
        }

        if has_architecture_issues {
            #[cfg(target_pointer_width = "64")]
            {
                script.environment_variables.insert("CFLAGS".to_string(), "-m64".to_string());
                script.environment_variables.insert("LDFLAGS".to_string(), "-m64".to_string());
            }
            #[cfg(target_pointer_width = "32")]
            {
                script.environment_variables.insert("CFLAGS".to_string(), "-m32".to_string());
                script.environment_variables.insert("LDFLAGS".to_string(), "-m32".to_string());
            }
        }

        script.build_commands.extend(vec![
            "cd benchmark/c_ext".to_string(),
            "python setup.py clean --all".to_string(),
            "python setup.py build_ext --inplace".to_string(),
        ]);

        script.script_content = self.generate_c_setup_py();
    }

    /// Generate C++ extension build script
    fn generate_cpp_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "g++".to_string(),
            "python3-dev".to_string(),
            "setuptools".to_string(),
        ]);

        if has_dependency_issues {
            script.environment_variables.insert("CXX".to_string(), "g++".to_string());
            script.environment_variables.insert("CXXFLAGS".to_string(), "-std=c++11".to_string());
        }

        if has_architecture_issues {
            #[cfg(target_pointer_width = "64")]
            {
                script.environment_variables.insert("CXXFLAGS".to_string(), "-m64 -std=c++11".to_string());
                script.environment_variables.insert("LDFLAGS".to_string(), "-m64".to_string());
            }
        }

        script.build_commands.extend(vec![
            "cd benchmark/cpp_ext".to_string(),
            "python setup.py clean --all".to_string(),
            "python setup.py build_ext --inplace".to_string(),
        ]);

        script.script_content = self.generate_cpp_setup_py();
    }

    /// Generate NumPy extension build script
    fn generate_numpy_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "gcc".to_string(),
            "python3-dev".to_string(),
            "numpy".to_string(),
            "setuptools".to_string(),
        ]);

        if has_dependency_issues {
            script.environment_variables.insert("CC".to_string(), "gcc".to_string());
            script.environment_variables.insert("CXX".to_string(), "g++".to_string());
        }

        if has_architecture_issues {
            #[cfg(target_pointer_width = "64")]
            {
                script.environment_variables.insert("CFLAGS".to_string(), "-m64".to_string());
                script.environment_variables.insert("LDFLAGS".to_string(), "-m64".to_string());
            }
        }

        script.build_commands.extend(vec![
            "cd benchmark/numpy_impl".to_string(),
            "python setup.py clean --all".to_string(),
            "python setup.py build_ext --inplace".to_string(),
        ]);

        script.script_content = self.generate_numpy_setup_py();
    }

    /// Generate Cython extension build script
    fn generate_cython_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "cython".to_string(),
            "gcc".to_string(),
            "python3-dev".to_string(),
            "setuptools".to_string(),
        ]);

        if has_dependency_issues {
            script.environment_variables.insert("CC".to_string(), "gcc".to_string());
        }

        if has_architecture_issues {
            #[cfg(target_pointer_width = "64")]
            {
                script.environment_variables.insert("CFLAGS".to_string(), "-m64".to_string());
            }
        }

        script.build_commands.extend(vec![
            "cd benchmark/cython_ext".to_string(),
            "cython *.pyx".to_string(),
            "python setup.py clean --all".to_string(),
            "python setup.py build_ext --inplace".to_string(),
        ]);

        script.script_content = self.generate_cython_setup_py();
    }

    /// Generate Rust extension build script
    fn generate_rust_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "cargo".to_string(),
            "rustc".to_string(),
            "maturin".to_string(),
        ]);

        if has_dependency_issues {
            script.environment_variables.insert("RUSTFLAGS".to_string(), "-C target-cpu=native".to_string());
        }

        if has_architecture_issues {
            #[cfg(target_pointer_width = "64")]
            {
                script.environment_variables.insert("CARGO_BUILD_TARGET".to_string(), "x86_64-pc-windows-msvc".to_string());
            }
            #[cfg(target_pointer_width = "32")]
            {
                script.environment_variables.insert("CARGO_BUILD_TARGET".to_string(), "i686-pc-windows-msvc".to_string());
            }
        }

        script.build_commands.extend(vec![
            "cd benchmark/rust_ext".to_string(),
            "cargo clean".to_string(),
            "maturin develop --release".to_string(),
        ]);

        script.script_content = self.generate_rust_cargo_toml();
    }

    /// Generate Go extension build script
    fn generate_go_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "go".to_string(),
            "gcc".to_string(),
        ]);

        if has_dependency_issues {
            script.environment_variables.insert("CGO_ENABLED".to_string(), "1".to_string());
            script.environment_variables.insert("CC".to_string(), "gcc".to_string());
        }

        if has_architecture_issues {
            #[cfg(target_pointer_width = "64")]
            {
                script.environment_variables.insert("GOARCH".to_string(), "amd64".to_string());
            }
            #[cfg(target_pointer_width = "32")]
            {
                script.environment_variables.insert("GOARCH".to_string(), "386".to_string());
            }
        }

        script.build_commands.extend(vec![
            "cd benchmark/go_ext".to_string(),
            "go clean".to_string(),
            "go build -buildmode=c-shared -o libgofunctions.dll functions.go".to_string(),
        ]);

        script.script_content = self.generate_go_module();
    }

    /// Generate Fortran extension build script
    fn generate_fortran_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "gfortran".to_string(),
            "f2py".to_string(),
            "numpy".to_string(),
        ]);

        if has_dependency_issues {
            script.environment_variables.insert("FC".to_string(), "gfortran".to_string());
            script.environment_variables.insert("F90".to_string(), "gfortran".to_string());
        }

        if has_architecture_issues {
            #[cfg(target_pointer_width = "64")]
            {
                script.environment_variables.insert("FFLAGS".to_string(), "-m64".to_string());
            }
        }

        script.build_commands.extend(vec![
            "cd benchmark/fortran_ext".to_string(),
            "f2py -c -m numeric numeric.f90".to_string(),
            "f2py -c -m memory memory.f90".to_string(),
            "f2py -c -m parallel parallel.f90".to_string(),
        ]);

        script.script_content = self.generate_fortran_makefile();
    }

    /// Generate Zig extension build script
    fn generate_zig_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "zig".to_string(),
        ]);

        if has_architecture_issues {
            #[cfg(target_pointer_width = "64")]
            {
                script.environment_variables.insert("ZIG_TARGET".to_string(), "x86_64-windows".to_string());
            }
        }

        script.build_commands.extend(vec![
            "cd benchmark/zig_ext".to_string(),
            "zig build-lib -dynamic -O ReleaseFast functions.zig".to_string(),
        ]);

        script.script_content = self.generate_zig_build();
    }

    /// Generate Nim extension build script
    fn generate_nim_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "nim".to_string(),
            "gcc".to_string(),
        ]);

        if has_dependency_issues {
            script.environment_variables.insert("CC".to_string(), "gcc".to_string());
        }

        script.build_commands.extend(vec![
            "cd benchmark/nim_ext".to_string(),
            "nim c --app:lib --out:libnimfunctions.dll functions.nim".to_string(),
        ]);

        script.script_content = self.generate_nim_config();
    }

    /// Generate Julia extension build script
    fn generate_julia_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "julia".to_string(),
        ]);

        script.build_commands.extend(vec![
            "cd benchmark/julia_ext".to_string(),
            "julia --project=. -e \"using Pkg; Pkg.instantiate()\"".to_string(),
            "julia --project=. -e \"include(\\\"functions.jl\\\")\"".to_string(),
        ]);

        script.script_content = self.generate_julia_project();
    }

    /// Generate Kotlin extension build script
    fn generate_kotlin_build_script(&self, script: &mut BuildScript, has_dependency_issues: bool, has_architecture_issues: bool) {
        script.required_tools.extend(vec![
            "kotlin".to_string(),
            "gradle".to_string(),
        ]);

        script.build_commands.extend(vec![
            "cd benchmark/kotlin_ext".to_string(),
            "gradle clean".to_string(),
            "gradle build".to_string(),
        ]);

        script.script_content = self.generate_kotlin_gradle();
    }

    // Helper methods for path and symbol handling

    /// Get module name for FFI implementation
    fn get_module_name(&self, ffi_impl: &str) -> String {
        match ffi_impl {
            "c_ext" => "c_ext.numeric".to_string(),
            "cpp_ext" => "cpp_ext.numeric".to_string(),
            "cython_ext" => "cython_ext.numeric".to_string(),
            "numpy_impl" => "numpy_impl.numpy_numeric".to_string(),
            "rust_ext" => "rust_ext".to_string(),
            "go_ext" => "go_ext".to_string(),
            "fortran_ext" => "fortran_ext.numeric".to_string(),
            "zig_ext" => "zig_ext".to_string(),
            "nim_ext" => "nim_ext".to_string(),
            "julia_ext" => "julia_ext".to_string(),
            "kotlin_ext" => "kotlin_ext".to_string(),
            _ => ffi_impl.to_string(),
        }
    }

    /// Get expected library paths for FFI implementation
    fn get_expected_library_paths(&self, ffi_impl: &str) -> Vec<String> {
        match ffi_impl {
            "c_ext" => vec![
                "benchmark/c_ext/numeric.pyd".to_string(),
                "benchmark/c_ext/memory.pyd".to_string(),
                "benchmark/c_ext/parallel.pyd".to_string(),
            ],
            "cpp_ext" => vec![
                "benchmark/cpp_ext/numeric.pyd".to_string(),
                "benchmark/cpp_ext/memory.pyd".to_string(),
                "benchmark/cpp_ext/parallel.pyd".to_string(),
            ],
            "cython_ext" => vec![
                "benchmark/cython_ext/numeric.pyd".to_string(),
                "benchmark/cython_ext/memory.pyd".to_string(),
                "benchmark/cython_ext/parallel.pyd".to_string(),
            ],
            "numpy_impl" => vec![
                "benchmark/numpy_impl/numpy_numeric.pyd".to_string(),
                "benchmark/numpy_impl/numpy_memory.pyd".to_string(),
                "benchmark/numpy_impl/numpy_parallel.pyd".to_string(),
            ],
            "rust_ext" => vec![
                "benchmark/rust_ext/target/wheels/rust_ext.pyd".to_string(),
            ],
            "go_ext" => vec![
                "benchmark/go_ext/libgofunctions.dll".to_string(),
            ],
            "fortran_ext" => vec![
                "benchmark/fortran_ext/numeric.pyd".to_string(),
                "benchmark/fortran_ext/memory.pyd".to_string(),
                "benchmark/fortran_ext/parallel.pyd".to_string(),
            ],
            "zig_ext" => vec![
                "benchmark/zig_ext/zigfunctions.dll".to_string(),
            ],
            "nim_ext" => vec![
                "benchmark/nim_ext/libnimfunctions.dll".to_string(),
            ],
            "julia_ext" => vec![
                "benchmark/julia_ext/functions.jl".to_string(),
            ],
            "kotlin_ext" => vec![
                "benchmark/kotlin_ext/build/libs/functions.jar".to_string(),
            ],
            _ => vec![],
        }
    }

    /// Expand environment variables in path
    fn expand_environment_variables(&self, path: &str) -> String {
        let mut expanded = path.to_string();
        
        // Handle Windows-style environment variables (%VAR%)
        if expanded.contains("%") {
            let re = regex::Regex::new(r"%([^%]+)%").unwrap();
            expanded = re.replace_all(&expanded, |caps: &regex::Captures| {
                std::env::var(&caps[1]).unwrap_or_else(|_| caps[0].to_string())
            }).to_string();
        }
        
        // Handle Unix-style environment variables ($VAR)
        if expanded.contains("$") {
            let re = regex::Regex::new(r"\$([A-Za-z_][A-Za-z0-9_]*)").unwrap();
            expanded = re.replace_all(&expanded, |caps: &regex::Captures| {
                std::env::var(&caps[1]).unwrap_or_else(|_| caps[0].to_string())
            }).to_string();
        }
        
        expanded
    }

    /// Get expected symbols for library
    fn get_expected_symbols_for_library(&self, library_path: &str) -> Vec<String> {
        if library_path.contains("numeric") {
            vec![
                "numeric_add".to_string(),
                "numeric_multiply".to_string(),
                "numeric_divide".to_string(),
            ]
        } else if library_path.contains("memory") {
            vec![
                "memory_allocate".to_string(),
                "memory_copy".to_string(),
                "memory_free".to_string(),
            ]
        } else if library_path.contains("parallel") {
            vec![
                "parallel_compute".to_string(),
                "parallel_reduce".to_string(),
            ]
        } else if library_path.contains("rust") {
            vec![
                "rust_numeric_add".to_string(),
                "rust_numeric_multiply".to_string(),
            ]
        } else if library_path.contains("go") {
            vec![
                "GoNumericAdd".to_string(),
                "GoNumericMultiply".to_string(),
            ]
        } else {
            vec!["main".to_string()]
        }
    }

    // Compatibility layer generation methods

    /// Generate C compatibility layer
    fn generate_c_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::ABIWrapper;
        layer.generated_code = r#"
// C FFI Compatibility Layer
#include <Python.h>
#include <numpy/arrayobject.h>

// ABI compatibility wrapper functions
static PyObject* safe_numeric_add(PyObject* self, PyObject* args) {
    // Ensure proper calling convention and error handling
    PyObject* result = NULL;
    
    // Add error checking and type validation
    if (!PyArg_ParseTuple(args, "OO", &arg1, &arg2)) {
        return NULL;
    }
    
    // Call original function with proper error handling
    result = original_numeric_add(self, args);
    
    // Validate result before returning
    if (result == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "C extension function failed");
    }
    
    return result;
}

// Method definitions with proper calling conventions
static PyMethodDef compatibility_methods[] = {
    {"numeric_add", safe_numeric_add, METH_VARARGS, "Safe numeric addition"},
    {NULL, NULL, 0, NULL}
};

// Module definition with proper initialization
static struct PyModuleDef compatibility_module = {
    PyModuleDef_HEAD_INIT,
    "c_ext_compat",
    "C extension compatibility layer",
    -1,
    compatibility_methods
};

PyMODINIT_FUNC PyInit_c_ext_compat(void) {
    import_array();
    return PyModule_Create(&compatibility_module);
}
"#.to_string();

        layer.installation_instructions = vec![
            "Compile with: gcc -shared -fPIC -I$(python -c 'import numpy; print(numpy.get_include())') -o c_ext_compat.so c_ext_compat.c".to_string(),
            "Install in Python path or current directory".to_string(),
            "Import with: import c_ext_compat".to_string(),
        ];
    }

    /// Generate C++ compatibility layer
    fn generate_cpp_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::ABIWrapper;
        layer.generated_code = r#"
// C++ FFI Compatibility Layer
#include <Python.h>
#include <numpy/arrayobject.h>
#include <stdexcept>

extern "C" {
    // C-style wrapper functions for C++ code
    static PyObject* safe_cpp_numeric_add(PyObject* self, PyObject* args) {
        try {
            // C++ exception handling wrapper
            PyObject* result = cpp_numeric_add(self, args);
            if (!result) {
                throw std::runtime_error("C++ function returned NULL");
            }
            return result;
        } catch (const std::exception& e) {
            PyErr_SetString(PyExc_RuntimeError, e.what());
            return NULL;
        } catch (...) {
            PyErr_SetString(PyExc_RuntimeError, "Unknown C++ exception");
            return NULL;
        }
    }

    // Method definitions
    static PyMethodDef cpp_compatibility_methods[] = {
        {"numeric_add", safe_cpp_numeric_add, METH_VARARGS, "Safe C++ numeric addition"},
        {NULL, NULL, 0, NULL}
    };

    // Module definition
    static struct PyModuleDef cpp_compatibility_module = {
        PyModuleDef_HEAD_INIT,
        "cpp_ext_compat",
        "C++ extension compatibility layer",
        -1,
        cpp_compatibility_methods
    };

    PyMODINIT_FUNC PyInit_cpp_ext_compat(void) {
        import_array();
        return PyModule_Create(&cpp_compatibility_module);
    }
}
"#.to_string();

        layer.installation_instructions = vec![
            "Compile with: g++ -shared -fPIC -std=c++11 -I$(python -c 'import numpy; print(numpy.get_include())') -o cpp_ext_compat.so cpp_ext_compat.cpp".to_string(),
            "Ensure C++ runtime is available".to_string(),
            "Import with: import cpp_ext_compat".to_string(),
        ];
    }

    /// Generate NumPy compatibility layer
    fn generate_numpy_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::ABIWrapper;
        layer.generated_code = r#"
// NumPy C API Compatibility Layer
#include <Python.h>
#include <numpy/arrayobject.h>

// Safe NumPy array creation with error checking
static PyObject* safe_numpy_array_new(int nd, npy_intp* dims, int typenum) {
    PyObject* array = PyArray_SimpleNew(nd, dims, typenum);
    if (array == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to create NumPy array");
        return NULL;
    }
    return array;
}

// Safe NumPy array data access with bounds checking
static void* safe_numpy_array_data(PyArrayObject* array, npy_intp index) {
    if (array == NULL) {
        PyErr_SetString(PyExc_ValueError, "Array is NULL");
        return NULL;
    }
    
    if (index < 0 || index >= PyArray_SIZE(array)) {
        PyErr_SetString(PyExc_IndexError, "Array index out of bounds");
        return NULL;
    }
    
    return PyArray_GETPTR1(array, index);
}

// Safe numeric addition with NumPy arrays
static PyObject* safe_numpy_add(PyObject* self, PyObject* args) {
    PyArrayObject *a, *b;
    if (!PyArg_ParseTuple(args, "O!O!", &PyArray_Type, &a, &PyArray_Type, &b)) {
        return NULL;
    }
    
    // Check array compatibility
    if (PyArray_SIZE(a) != PyArray_SIZE(b)) {
        PyErr_SetString(PyExc_ValueError, "Array sizes must match");
        return NULL;
    }
    
    if (PyArray_TYPE(a) != NPY_DOUBLE || PyArray_TYPE(b) != NPY_DOUBLE) {
        PyErr_SetString(PyExc_TypeError, "Arrays must be of type double");
        return NULL;
    }
    
    npy_intp size = PyArray_SIZE(a);
    npy_intp dims[1] = {size};
    PyObject* result = safe_numpy_array_new(1, dims, NPY_DOUBLE);
    if (result == NULL) return NULL;
    
    double* a_data = (double*)PyArray_DATA(a);
    double* b_data = (double*)PyArray_DATA(b);
    double* result_data = (double*)PyArray_DATA((PyArrayObject*)result);
    
    for (npy_intp i = 0; i < size; i++) {
        result_data[i] = a_data[i] + b_data[i];
    }
    
    return result;
}

// Method definitions
static PyMethodDef numpy_compatibility_methods[] = {
    {"safe_add", safe_numpy_add, METH_VARARGS, "Safe NumPy array addition"},
    {NULL, NULL, 0, NULL}
};

// Module definition
static struct PyModuleDef numpy_compatibility_module = {
    PyModuleDef_HEAD_INIT,
    "numpy_compat",
    "NumPy C API compatibility layer",
    -1,
    numpy_compatibility_methods
};

PyMODINIT_FUNC PyInit_numpy_compat(void) {
    import_array();
    return PyModule_Create(&numpy_compatibility_module);
}
"#.to_string();

        layer.installation_instructions = vec![
            "Compile with: gcc -shared -fPIC -I$(python -c 'import numpy; print(numpy.get_include())') -o numpy_compat.so numpy_compat.c".to_string(),
            "Ensure NumPy is installed: pip install numpy".to_string(),
            "Import with: import numpy_compat".to_string(),
        ];
    }

    /// Generate Cython compatibility layer
    fn generate_cython_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::PythonWrapper;
        layer.generated_code = r#"
# Cython FFI Compatibility Layer
# cython_ext_compat.pyx

import numpy as np
cimport numpy as cnp
from libc.stdlib cimport malloc, free

# Safe wrapper functions with proper error handling
def safe_numeric_add(cnp.ndarray[double, ndim=1] a, cnp.ndarray[double, ndim=1] b):
    """Safe Cython numeric addition with error checking"""
    if a.shape[0] != b.shape[0]:
        raise ValueError("Array shapes must match")
    
    cdef int n = a.shape[0]
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(n, dtype=np.float64)
    
    cdef int i
    for i in range(n):
        result[i] = a[i] + b[i]
    
    return result

def safe_memory_allocate(int size):
    """Safe memory allocation with error checking"""
    if size <= 0:
        raise ValueError("Size must be positive")
    
    cdef double* ptr = <double*>malloc(size * sizeof(double))
    if ptr == NULL:
        raise MemoryError("Failed to allocate memory")
    
    # Return as numpy array for safety
    cdef cnp.ndarray[double, ndim=1] result = np.zeros(size, dtype=np.float64)
    free(ptr)
    return result
"#.to_string();

        layer.installation_instructions = vec![
            "Create setup.py with Cython compilation".to_string(),
            "Run: python setup.py build_ext --inplace".to_string(),
            "Import with: import cython_ext_compat".to_string(),
        ];
    }

    /// Generate Rust compatibility layer
    fn generate_rust_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::ABIWrapper;
        layer.generated_code = r#"
// Rust FFI Compatibility Layer
use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use numpy::{PyArray1, PyReadonlyArray1};

/// Safe Rust numeric addition with proper error handling
#[pyfunction]
fn safe_numeric_add(
    py: Python,
    a: PyReadonlyArray1<f64>,
    b: PyReadonlyArray1<f64>,
) -> PyResult<Py<PyArray1<f64>>> {
    let a = a.as_array();
    let b = b.as_array();
    
    if a.len() != b.len() {
        return Err(PyRuntimeError::new_err("Array lengths must match"));
    }
    
    let result: Vec<f64> = a.iter()
        .zip(b.iter())
        .map(|(x, y)| x + y)
        .collect();
    
    Ok(PyArray1::from_vec(py, result).to_owned())
}

/// Safe memory operations with bounds checking
#[pyfunction]
fn safe_memory_allocate(py: Python, size: usize) -> PyResult<Py<PyArray1<f64>>> {
    if size == 0 {
        return Err(PyRuntimeError::new_err("Size must be greater than 0"));
    }
    
    if size > 1_000_000 {
        return Err(PyRuntimeError::new_err("Size too large for safety"));
    }
    
    let data = vec![0.0; size];
    Ok(PyArray1::from_vec(py, data).to_owned())
}

/// Rust compatibility module
#[pymodule]
fn rust_ext_compat(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(safe_numeric_add, m)?)?;
    m.add_function(wrap_pyfunction!(safe_memory_allocate, m)?)?;
    Ok(())
}
"#.to_string();

        layer.installation_instructions = vec![
            "Add to Cargo.toml: pyo3 = { version = \"0.20\", features = [\"extension-module\"] }".to_string(),
            "Build with: maturin develop --release".to_string(),
            "Import with: import rust_ext_compat".to_string(),
        ];
    }

    /// Generate Go compatibility layer
    fn generate_go_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::SharedLibrary;
        layer.generated_code = r#"
// Go FFI Compatibility Layer
package main

import "C"
import (
    "errors"
    "unsafe"
)

//export SafeNumericAdd
func SafeNumericAdd(a *C.double, b *C.double, size C.int, result *C.double) C.int {
    if size <= 0 {
        return -1 // Error: invalid size
    }
    
    if a == nil || b == nil || result == nil {
        return -2 // Error: null pointer
    }
    
    // Convert C arrays to Go slices safely
    aSlice := (*[1 << 30]C.double)(unsafe.Pointer(a))[:size:size]
    bSlice := (*[1 << 30]C.double)(unsafe.Pointer(b))[:size:size]
    resultSlice := (*[1 << 30]C.double)(unsafe.Pointer(result))[:size:size]
    
    // Perform safe addition
    for i := 0; i < int(size); i++ {
        resultSlice[i] = aSlice[i] + bSlice[i]
    }
    
    return 0 // Success
}

//export SafeMemoryAllocate
func SafeMemoryAllocate(size C.int) *C.double {
    if size <= 0 || size > 1000000 {
        return nil // Error: invalid size
    }
    
    // Allocate memory safely
    data := make([]C.double, size)
    return &data[0]
}

//export GetLastError
func GetLastError() *C.char {
    return C.CString("No error")
}

func main() {} // Required for buildmode=c-shared
"#.to_string();

        layer.installation_instructions = vec![
            "Build with: go build -buildmode=c-shared -o libgo_compat.dll go_compat.go".to_string(),
            "Create Python wrapper using ctypes".to_string(),
            "Load with: ctypes.CDLL('./libgo_compat.dll')".to_string(),
        ];
    }

    /// Generate Fortran compatibility layer
    fn generate_fortran_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::F2PyWrapper;
        layer.generated_code = r#"
! Fortran FFI Compatibility Layer
module fortran_compat
    implicit none
    
contains
    
    ! Safe numeric addition with bounds checking
    subroutine safe_numeric_add(a, b, result, n, status)
        implicit none
        integer, intent(in) :: n
        real(8), intent(in) :: a(n), b(n)
        real(8), intent(out) :: result(n)
        integer, intent(out) :: status
        
        integer :: i
        
        ! Input validation
        if (n <= 0) then
            status = -1
            return
        end if
        
        ! Perform safe addition
        do i = 1, n
            result(i) = a(i) + b(i)
        end do
        
        status = 0  ! Success
    end subroutine safe_numeric_add
    
    ! Safe memory operations
    subroutine safe_memory_allocate(size, data, status)
        implicit none
        integer, intent(in) :: size
        real(8), allocatable, intent(out) :: data(:)
        integer, intent(out) :: status
        
        ! Input validation
        if (size <= 0 .or. size > 1000000) then
            status = -1
            return
        end if
        
        ! Allocate memory safely
        allocate(data(size), stat=status)
        if (status == 0) then
            data = 0.0d0  ! Initialize to zero
        end if
    end subroutine safe_memory_allocate
    
end module fortran_compat
"#.to_string();

        layer.installation_instructions = vec![
            "Compile with f2py: f2py -c -m fortran_compat fortran_compat.f90".to_string(),
            "Ensure gfortran is available".to_string(),
            "Import with: import fortran_compat".to_string(),
        ];
    }

    /// Generate Zig compatibility layer
    fn generate_zig_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::SharedLibrary;
        layer.generated_code = r#"
// Zig FFI Compatibility Layer
const std = @import("std");

// Safe numeric addition with error checking
export fn safeNumericAdd(a: [*]const f64, b: [*]const f64, result: [*]f64, size: usize) c_int {
    if (size == 0) return -1; // Error: invalid size
    if (size > 1000000) return -2; // Error: size too large
    
    var i: usize = 0;
    while (i < size) : (i += 1) {
        result[i] = a[i] + b[i];
    }
    
    return 0; // Success
}

// Safe memory allocation
export fn safeMemoryAllocate(size: usize) ?[*]f64 {
    if (size == 0 or size > 1000000) return null;
    
    var allocator = std.heap.page_allocator;
    const memory = allocator.alloc(f64, size) catch return null;
    
    // Initialize to zero
    for (memory) |*item| {
        item.* = 0.0;
    }
    
    return memory.ptr;
}

// Error handling
export fn getLastError() [*:0]const u8 {
    return "No error";
}
"#.to_string();

        layer.installation_instructions = vec![
            "Build with: zig build-lib -dynamic -O ReleaseFast zig_compat.zig".to_string(),
            "Create Python wrapper using ctypes".to_string(),
            "Load with: ctypes.CDLL('./zig_compat.dll')".to_string(),
        ];
    }

    /// Generate Nim compatibility layer
    fn generate_nim_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::SharedLibrary;
        layer.generated_code = r#"
# Nim FFI Compatibility Layer
import math

# Safe numeric addition with bounds checking
proc safeNumericAdd(a: ptr UncheckedArray[float64], b: ptr UncheckedArray[float64], 
                   result: ptr UncheckedArray[float64], size: cint): cint {.exportc, dynlib.} =
  if size <= 0:
    return -1  # Error: invalid size
  
  if size > 1000000:
    return -2  # Error: size too large
  
  for i in 0..<size:
    result[i] = a[i] + b[i]
  
  return 0  # Success

# Safe memory allocation
proc safeMemoryAllocate(size: cint): ptr UncheckedArray[float64] {.exportc, dynlib.} =
  if size <= 0 or size > 1000000:
    return nil
  
  result = cast[ptr UncheckedArray[float64]](alloc(size * sizeof(float64)))
  if result != nil:
    # Initialize to zero
    for i in 0..<size:
      result[i] = 0.0
  
  return result

# Error handling
proc getLastError(): cstring {.exportc, dynlib.} =
  return "No error"
"#.to_string();

        layer.installation_instructions = vec![
            "Compile with: nim c --app:lib --out:nim_compat.dll nim_compat.nim".to_string(),
            "Create Python wrapper using ctypes".to_string(),
            "Load with: ctypes.CDLL('./nim_compat.dll')".to_string(),
        ];
    }

    /// Generate Julia compatibility layer
    fn generate_julia_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::PythonWrapper;
        layer.generated_code = r#"
# Julia FFI Compatibility Layer
module JuliaCompat

using PyCall

# Safe numeric addition with error checking
function safe_numeric_add(a::Vector{Float64}, b::Vector{Float64})::Vector{Float64}
    if length(a) != length(b)
        throw(ArgumentError("Array lengths must match"))
    end
    
    if length(a) == 0
        throw(ArgumentError("Arrays cannot be empty"))
    end
    
    return a .+ b
end

# Safe memory allocation
function safe_memory_allocate(size::Int)::Vector{Float64}
    if size <= 0
        throw(ArgumentError("Size must be positive"))
    end
    
    if size > 1_000_000
        throw(ArgumentError("Size too large for safety"))
    end
    
    return zeros(Float64, size)
end

# Export functions to Python
function __init__()
    # Register functions with PyCall
    @pydef mutable struct JuliaCompatModule
        function numeric_add(self, a, b)
            return safe_numeric_add(a, b)
        end
        
        function memory_allocate(self, size)
            return safe_memory_allocate(size)
        end
    end
end

end # module
"#.to_string();

        layer.installation_instructions = vec![
            "Install PyCall.jl: julia -e 'using Pkg; Pkg.add(\"PyCall\")'".to_string(),
            "Load module in Julia session".to_string(),
            "Access from Python via PyJulia".to_string(),
        ];
    }

    /// Generate Kotlin compatibility layer
    fn generate_kotlin_compatibility_layer(&self, layer: &mut CompatibilityLayer) {
        layer.layer_type = CompatibilityLayerType::JNIWrapper;
        layer.generated_code = r#"
// Kotlin FFI Compatibility Layer
package com.ffi.compat

import java.nio.DoubleBuffer

class KotlinCompat {
    companion object {
        @JvmStatic
        external fun safeNumericAdd(a: DoubleArray, b: DoubleArray): DoubleArray
        
        @JvmStatic
        external fun safeMemoryAllocate(size: Int): DoubleArray
        
        init {
            System.loadLibrary("kotlin_compat")
        }
    }
    
    // Safe wrapper functions with validation
    fun numericAdd(a: DoubleArray, b: DoubleArray): DoubleArray {
        require(a.size == b.size) { "Array sizes must match" }
        require(a.isNotEmpty()) { "Arrays cannot be empty" }
        
        return safeNumericAdd(a, b)
    }
    
    fun memoryAllocate(size: Int): DoubleArray {
        require(size > 0) { "Size must be positive" }
        require(size <= 1_000_000) { "Size too large for safety" }
        
        return safeMemoryAllocate(size)
    }
}

// JNI implementation (C++)
extern "C" {
    JNIEXPORT jdoubleArray JNICALL
    Java_com_ffi_compat_KotlinCompat_safeNumericAdd(JNIEnv *env, jclass clazz, 
                                                    jdoubleArray a, jdoubleArray b) {
        jsize len = env->GetArrayLength(a);
        if (len != env->GetArrayLength(b)) {
            env->ThrowNew(env->FindClass("java/lang/IllegalArgumentException"), 
                         "Array lengths must match");
            return nullptr;
        }
        
        jdouble *a_elements = env->GetDoubleArrayElements(a, nullptr);
        jdouble *b_elements = env->GetDoubleArrayElements(b, nullptr);
        
        jdoubleArray result = env->NewDoubleArray(len);
        jdouble *result_elements = env->GetDoubleArrayElements(result, nullptr);
        
        for (int i = 0; i < len; i++) {
            result_elements[i] = a_elements[i] + b_elements[i];
        }
        
        env->ReleaseDoubleArrayElements(a, a_elements, JNI_ABORT);
        env->ReleaseDoubleArrayElements(b, b_elements, JNI_ABORT);
        env->ReleaseDoubleArrayElements(result, result_elements, 0);
        
        return result;
    }
}
"#.to_string();

        layer.installation_instructions = vec![
            "Compile Kotlin code: kotlinc -cp . -d kotlin_compat.jar KotlinCompat.kt".to_string(),
            "Compile JNI library: g++ -shared -fPIC -I$JAVA_HOME/include -o libkotlin_compat.so kotlin_compat_jni.cpp".to_string(),
            "Access via Jython or Py4J".to_string(),
        ];
    }

    /// Validate symbols on Windows
    #[cfg(target_os = "windows")]
    fn validate_windows_symbols(&self, library_path: &str, expected_symbols: &[String]) -> Result<(Vec<String>, Vec<String>, Vec<SymbolExportIssue>)> {
        use winapi::um::libloaderapi::{LoadLibraryA, GetProcAddress, FreeLibrary};
        use std::ffi::CString;

        let mut found_symbols = Vec::new();
        let mut missing_symbols = Vec::new();
        let mut issues = Vec::new();

        let c_path = CString::new(library_path).map_err(|_| {
            crate::error::AuditError::ValidationFailed("Invalid library path".to_string())
        })?;

        unsafe {
            let handle = LoadLibraryA(c_path.as_ptr());
            if handle.is_null() {
                return Err(crate::error::AuditError::LibraryLoadingFailed(
                    format!("Could not load library: {}", library_path)
                ));
            }

            for symbol in expected_symbols {
                if let Ok(c_symbol) = CString::new(symbol.as_str()) {
                    let proc_addr = GetProcAddress(handle, c_symbol.as_ptr());
                    if proc_addr.is_null() {
                        missing_symbols.push(symbol.clone());
                        issues.push(SymbolExportIssue {
                            symbol_name: symbol.clone(),
                            issue_description: format!("Symbol '{}' not exported", symbol),
                            suggested_fix: "Add symbol to export list or check function name".to_string(),
                        });
                    } else {
                        found_symbols.push(symbol.clone());
                    }
                }
            }

            FreeLibrary(handle);
        }

        Ok((found_symbols, missing_symbols, issues))
    }

    /// Validate symbols on Unix-like systems
    #[cfg(not(target_os = "windows"))]
    fn validate_unix_symbols(&self, library_path: &str, expected_symbols: &[String]) -> Result<(Vec<String>, Vec<String>, Vec<SymbolExportIssue>)> {
        use std::ffi::CString;

        let mut found_symbols = Vec::new();
        let mut missing_symbols = Vec::new();
        let mut issues = Vec::new();

        let c_path = CString::new(library_path).map_err(|_| {
            crate::error::AuditError::ValidationFailed("Invalid library path".to_string())
        })?;

        unsafe {
            let handle = libc::dlopen(c_path.as_ptr(), libc::RTLD_LAZY);
            if handle.is_null() {
                return Err(crate::error::AuditError::LibraryLoadingFailed(
                    format!("Could not load library: {}", library_path)
                ));
            }

            for symbol in expected_symbols {
                if let Ok(c_symbol) = CString::new(symbol.as_str()) {
                    let sym_addr = libc::dlsym(handle, c_symbol.as_ptr());
                    if sym_addr.is_null() {
                        missing_symbols.push(symbol.clone());
                        issues.push(SymbolExportIssue {
                            symbol_name: symbol.clone(),
                            issue_description: format!("Symbol '{}' not exported", symbol),
                            suggested_fix: "Add symbol to export list or check function name".to_string(),
                        });
                    } else {
                        found_symbols.push(symbol.clone());
                    }
                }
            }

            libc::dlclose(handle);
        }

        Ok((found_symbols, missing_symbols, issues))
    }

    // Build script content generators

    /// Generate C setup.py content
    fn generate_c_setup_py(&self) -> String {
        r#"
from setuptools import setup, Extension
import numpy

extensions = [
    Extension('numeric', ['numeric.c'], include_dirs=[numpy.get_include()]),
    Extension('memory', ['memory.c'], include_dirs=[numpy.get_include()]),
    Extension('parallel', ['parallel.c'], include_dirs=[numpy.get_include()]),
]

setup(
    name='c_ext',
    ext_modules=extensions,
    zip_safe=False,
)
"#.to_string()
    }

    /// Generate C++ setup.py content
    fn generate_cpp_setup_py(&self) -> String {
        r#"
from setuptools import setup, Extension
import numpy

extensions = [
    Extension('numeric', ['numeric.cpp'], 
              include_dirs=[numpy.get_include()],
              language='c++',
              extra_compile_args=['-std=c++11']),
    Extension('memory', ['memory.cpp'], 
              include_dirs=[numpy.get_include()],
              language='c++',
              extra_compile_args=['-std=c++11']),
    Extension('parallel', ['parallel.cpp'], 
              include_dirs=[numpy.get_include()],
              language='c++',
              extra_compile_args=['-std=c++11']),
]

setup(
    name='cpp_ext',
    ext_modules=extensions,
    zip_safe=False,
)
"#.to_string()
    }

    /// Generate NumPy setup.py content
    fn generate_numpy_setup_py(&self) -> String {
        r#"
from setuptools import setup, Extension
import numpy

extensions = [
    Extension('numpy_numeric', ['numpy_numeric.c'], 
              include_dirs=[numpy.get_include()]),
    Extension('numpy_memory', ['numpy_memory.c'], 
              include_dirs=[numpy.get_include()]),
    Extension('numpy_parallel', ['numpy_parallel.c'], 
              include_dirs=[numpy.get_include()]),
]

setup(
    name='numpy_impl',
    ext_modules=extensions,
    zip_safe=False,
)
"#.to_string()
    }

    /// Generate Rust Cargo.toml content
    fn generate_rust_cargo_toml(&self) -> String {
        r#"
[package]
name = "rust_ext"
version = "0.1.0"
edition = "2021"

[lib]
name = "rust_ext"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
numpy = "0.20"

[build-dependencies]
pyo3-build-config = "0.20"
"#.to_string()
    }

    /// Generate Go module content
    fn generate_go_module(&self) -> String {
        r#"
module gofunctions

go 1.19

require (
    // Add any required dependencies here
)
"#.to_string()
    }

    /// Generate Fortran Makefile content
    fn generate_fortran_makefile(&self) -> String {
        r#"
FC = gfortran
FFLAGS = -fPIC -O3

all: numeric.so memory.so parallel.so

numeric.so: numeric.f90
	f2py -c -m numeric numeric.f90

memory.so: memory.f90
	f2py -c -m memory memory.f90

parallel.so: parallel.f90
	f2py -c -m parallel parallel.f90

clean:
	rm -f *.so *.o *.mod

.PHONY: all clean
"#.to_string()
    }

    /// Generate Zig build content
    fn generate_zig_build(&self) -> String {
        r#"
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const lib = b.addSharedLibrary(.{
        .name = "zigfunctions",
        .root_source_file = .{ .path = "functions.zig" },
        .target = target,
        .optimize = optimize,
    });

    b.installArtifact(lib);
}
"#.to_string()
    }

    /// Generate Nim config content
    fn generate_nim_config(&self) -> String {
        r#"
# Nim configuration for FFI library
--app:lib
--gc:arc
--opt:speed
--passC:"-fPIC"
--passL:"-shared"
"#.to_string()
    }

    /// Generate Julia project content
    fn generate_julia_project(&self) -> String {
        r#"
[deps]
# Add required Julia packages here

[compat]
julia = "1.6"
"#.to_string()
    }

    /// Generate Kotlin Gradle content
    fn generate_kotlin_gradle(&self) -> String {
        r#"
plugins {
    kotlin("jvm") version "1.8.0"
    `java-library`
}

repositories {
    mavenCentral()
}

dependencies {
    implementation(kotlin("stdlib"))
    // Add other dependencies as needed
}

tasks.jar {
    archiveBaseName.set("functions")
    from(sourceSets.main.get().output)
}
"#.to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::*;

    #[test]
    fn test_ffi_implementation_fixer_creation() {
        let fixer = FFIImplementationFixer::new();
        // Basic creation test
        assert!(true); // Fixer created successfully
    }

    #[test]
    fn test_generate_build_script_c_ext() {
        let fixer = FFIImplementationFixer::new();
        let issues = vec![
            DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Missing dependency".to_string(),
                affected_library: "test.dll".to_string(),
                resolution_steps: vec![],
            }
        ];

        let result = fixer.generate_build_script("c_ext", &issues);
        assert!(result.is_ok());
        
        let script = result.unwrap();
        assert_eq!(script.language, "c_ext");
        assert!(!script.required_tools.is_empty());
        assert!(script.required_tools.contains(&"gcc".to_string()));
        assert!(!script.build_commands.is_empty());
        assert!(!script.script_content.is_empty());
    }

    #[test]
    fn test_generate_build_script_rust_ext() {
        let fixer = FFIImplementationFixer::new();
        let issues = vec![
            DLLIssue {
                issue_type: DLLIssueType::ArchitectureMismatch,
                error_code: None,
                description: "Architecture mismatch".to_string(),
                affected_library: "test.dll".to_string(),
                resolution_steps: vec![],
            }
        ];

        let result = fixer.generate_build_script("rust_ext", &issues);
        assert!(result.is_ok());
        
        let script = result.unwrap();
        assert_eq!(script.language, "rust_ext");
        assert!(script.required_tools.contains(&"cargo".to_string()));
        assert!(script.required_tools.contains(&"rustc".to_string()));
        assert!(!script.build_commands.is_empty());
    }

    #[test]
    fn test_generate_build_script_unsupported() {
        let fixer = FFIImplementationFixer::new();
        let issues = vec![];

        let result = fixer.generate_build_script("unsupported_impl", &issues);
        assert!(result.is_err());
    }

    #[test]
    fn test_correct_library_paths() {
        let fixer = FFIImplementationFixer::new();
        
        let result = fixer.correct_library_paths("c_ext");
        assert!(result.is_ok());
        
        let correction = result.unwrap();
        assert_eq!(correction.implementation, "c_ext");
        assert!(!correction.original_paths.is_empty());
        assert_eq!(correction.original_paths.len(), correction.corrected_paths.len());
    }

    #[test]
    fn test_validate_symbol_exports_nonexistent_library() {
        let fixer = FFIImplementationFixer::new();
        
        let result = fixer.validate_symbol_exports("nonexistent_library.dll");
        assert!(result.is_ok());
        
        let validation = result.unwrap();
        assert_eq!(validation.library_path, "nonexistent_library.dll");
        assert!(!validation.validation_successful);
        assert!(!validation.issues.is_empty());
        assert!(validation.issues[0].issue_description.contains("does not exist"));
    }

    #[test]
    fn test_get_module_name() {
        let fixer = FFIImplementationFixer::new();
        
        assert_eq!(fixer.get_module_name("c_ext"), "c_ext.numeric");
        assert_eq!(fixer.get_module_name("rust_ext"), "rust_ext");
        assert_eq!(fixer.get_module_name("unknown"), "unknown");
    }

    #[test]
    fn test_get_expected_library_paths() {
        let fixer = FFIImplementationFixer::new();
        
        let c_paths = fixer.get_expected_library_paths("c_ext");
        assert!(!c_paths.is_empty());
        assert!(c_paths.iter().any(|p| p.contains("numeric.pyd")));
        
        let rust_paths = fixer.get_expected_library_paths("rust_ext");
        assert!(!rust_paths.is_empty());
        assert!(rust_paths.iter().any(|p| p.contains("rust_ext.pyd")));
        
        let unknown_paths = fixer.get_expected_library_paths("unknown");
        assert!(unknown_paths.is_empty());
    }

    #[test]
    fn test_expand_environment_variables() {
        let fixer = FFIImplementationFixer::new();
        
        // Set a test environment variable
        std::env::set_var("TEST_VAR", "test_value");
        
        // Test Windows-style expansion
        let windows_path = "%TEST_VAR%/path";
        let expanded = fixer.expand_environment_variables(windows_path);
        assert_eq!(expanded, "test_value/path");
        
        // Test Unix-style expansion
        let unix_path = "$TEST_VAR/path";
        let expanded = fixer.expand_environment_variables(unix_path);
        assert_eq!(expanded, "test_value/path");
        
        // Test no expansion needed
        let normal_path = "normal/path";
        let expanded = fixer.expand_environment_variables(normal_path);
        assert_eq!(expanded, "normal/path");
        
        // Clean up
        std::env::remove_var("TEST_VAR");
    }

    #[test]
    fn test_get_expected_symbols_for_library() {
        let fixer = FFIImplementationFixer::new();
        
        let numeric_symbols = fixer.get_expected_symbols_for_library("path/to/numeric.dll");
        assert!(!numeric_symbols.is_empty());
        assert!(numeric_symbols.contains(&"numeric_add".to_string()));
        
        let memory_symbols = fixer.get_expected_symbols_for_library("path/to/memory.dll");
        assert!(!memory_symbols.is_empty());
        assert!(memory_symbols.contains(&"memory_allocate".to_string()));
        
        let rust_symbols = fixer.get_expected_symbols_for_library("path/to/rust_ext.dll");
        assert!(!rust_symbols.is_empty());
        assert!(rust_symbols.contains(&"rust_numeric_add".to_string()));
    }

    #[test]
    fn test_build_script_content_generators() {
        let fixer = FFIImplementationFixer::new();
        
        let c_setup = fixer.generate_c_setup_py();
        assert!(c_setup.contains("Extension"));
        assert!(c_setup.contains("numeric"));
        
        let cpp_setup = fixer.generate_cpp_setup_py();
        assert!(cpp_setup.contains("Extension"));
        assert!(cpp_setup.contains("language='c++'"));
        
        let rust_cargo = fixer.generate_rust_cargo_toml();
        assert!(rust_cargo.contains("[package]"));
        assert!(rust_cargo.contains("pyo3"));
        
        let go_module = fixer.generate_go_module();
        assert!(go_module.contains("module gofunctions"));
        
        let fortran_makefile = fixer.generate_fortran_makefile();
        assert!(fortran_makefile.contains("f2py"));
        assert!(fortran_makefile.contains("gfortran"));
    }

    #[test]
    fn test_generate_compatibility_layer() {
        let fixer = FFIImplementationFixer::new();
        
        // Test C compatibility layer
        let c_result = fixer.generate_compatibility_layer("c_ext");
        assert!(c_result.is_ok());
        let c_layer = c_result.unwrap();
        assert_eq!(c_layer.implementation, "c_ext");
        assert!(!c_layer.generated_code.is_empty());
        assert!(c_layer.generated_code.contains("C FFI Compatibility Layer"));
        assert!(!c_layer.installation_instructions.is_empty());
        
        // Test Rust compatibility layer
        let rust_result = fixer.generate_compatibility_layer("rust_ext");
        assert!(rust_result.is_ok());
        let rust_layer = rust_result.unwrap();
        assert_eq!(rust_layer.implementation, "rust_ext");
        assert!(rust_layer.generated_code.contains("Rust FFI Compatibility Layer"));
        assert!(rust_layer.installation_instructions.iter().any(|i| i.contains("maturin")));
        
        // Test unsupported implementation
        let unsupported_result = fixer.generate_compatibility_layer("unsupported_impl");
        assert!(unsupported_result.is_err());
    }

    #[test]
    fn test_compatibility_layer_types() {
        let fixer = FFIImplementationFixer::new();
        
        // Test different layer types
        let c_layer = fixer.generate_compatibility_layer("c_ext").unwrap();
        assert_eq!(c_layer.layer_type, CompatibilityLayerType::ABIWrapper);
        
        let cython_layer = fixer.generate_compatibility_layer("cython_ext").unwrap();
        assert_eq!(cython_layer.layer_type, CompatibilityLayerType::PythonWrapper);
        
        let go_layer = fixer.generate_compatibility_layer("go_ext").unwrap();
        assert_eq!(go_layer.layer_type, CompatibilityLayerType::SharedLibrary);
        
        let kotlin_layer = fixer.generate_compatibility_layer("kotlin_ext").unwrap();
        assert_eq!(kotlin_layer.layer_type, CompatibilityLayerType::JNIWrapper);
    }

    #[test]
    fn test_rust_go_fix_functionality() {
        let fixer = FFIImplementationFixer::new();
        
        // Test Rust fix functionality
        let rust_issues = vec![
            DLLIssue {
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Rust toolchain not found".to_string(),
                affected_library: "rustc".to_string(),
                resolution_steps: vec![],
            },
            DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: "Cargo.toml not found".to_string(),
                affected_library: "benchmark/rust_ext/Cargo.toml".to_string(),
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
                issue_type: DLLIssueType::DependencyMissing,
                error_code: None,
                description: "Go compiler not found".to_string(),
                affected_library: "go".to_string(),
                resolution_steps: vec![],
            },
            DLLIssue {
                issue_type: DLLIssueType::LoadFailure,
                error_code: None,
                description: "go.mod not found".to_string(),
                affected_library: "benchmark/go_ext/go.mod".to_string(),
                resolution_steps: vec![],
            },
        ];
        
        let go_result = fixer.fix_rust_go_issues("go_ext", &go_issues);
        assert!(go_result.is_ok(), "Go fix should succeed");
        let go_actions = go_result.unwrap();
        assert!(!go_actions.is_empty(), "Go fix should provide actions");
        
        // Test unsupported implementation
        let unsupported_result = fixer.fix_rust_go_issues("unsupported_ext", &[]);
        assert!(unsupported_result.is_ok(), "Unsupported implementation should succeed");
        let unsupported_actions = unsupported_result.unwrap();
        assert_eq!(unsupported_actions.len(), 1, "Should have one unsupported message");
        assert!(unsupported_actions[0].contains("Unsupported implementation"), "Should indicate unsupported");
    }

    // Property-based test for bug fix effectiveness
    // Feature: windows-ffi-audit, Property 3: バグ修正有効性
    #[cfg(feature = "proptest")]
    use proptest::prelude::*;

    #[cfg(feature = "proptest")]
    proptest! {
        #[test]
        fn property_bug_fix_effectiveness(
            ffi_impl in prop::sample::select(vec!["c_ext", "cpp_ext", "cython_ext", "rust_ext", "go_ext", "fortran_ext"]),
            issue_type in prop::sample::select(vec![
                DLLIssueType::DependencyMissing,
                DLLIssueType::ArchitectureMismatch,
                DLLIssueType::PathResolutionFailure,
                DLLIssueType::LoadFailure,
                DLLIssueType::SymbolNotFound
            ])
        ) {
            let fixer = FFIImplementationFixer::new();
            
            // Create a test issue
            let issue = DLLIssue {
                issue_type: issue_type.clone(),
                error_code: Some(126), // Common Windows DLL error
                description: format!("Test issue: {:?}", issue_type),
                affected_library: format!("{}/test.dll", ffi_impl),
                resolution_steps: vec![],
            };
            
            // Generate build script for the issue
            let build_script_result = fixer.generate_build_script(&ffi_impl, &[issue.clone()]);
            prop_assert!(build_script_result.is_ok());
            
            let build_script = build_script_result.unwrap();
            
            // Verify that the build script addresses the specific issue type
            match issue_type {
                DLLIssueType::DependencyMissing => {
                    // Should include required tools and environment variables
                    prop_assert!(!build_script.required_tools.is_empty());
                    prop_assert!(!build_script.environment_variables.is_empty() || !build_script.build_commands.is_empty());
                },
                DLLIssueType::ArchitectureMismatch => {
                    // Should include architecture-specific flags
                    let has_arch_flags = build_script.environment_variables.iter()
                        .any(|(k, v)| k.contains("FLAGS") || v.contains("m64") || v.contains("m32") || v.contains("x86"));
                    prop_assert!(has_arch_flags || build_script.environment_variables.contains_key("GOARCH") || 
                                build_script.environment_variables.contains_key("CARGO_BUILD_TARGET"));
                },
                DLLIssueType::PathResolutionFailure => {
                    // Path correction should be available
                    let path_correction = fixer.correct_library_paths(&ffi_impl);
                    prop_assert!(path_correction.is_ok());
                    let correction = path_correction.unwrap();
                    prop_assert!(!correction.original_paths.is_empty());
                },
                DLLIssueType::LoadFailure => {
                    // Should include build commands to rebuild the library
                    prop_assert!(!build_script.build_commands.is_empty());
                },
                DLLIssueType::SymbolNotFound => {
                    // Should include validation commands
                    prop_assert!(!build_script.validation_commands.is_empty());
                },
                DLLIssueType::CallingConventionMismatch => {
                    // Should include build commands and environment variables
                    prop_assert!(!build_script.build_commands.is_empty() || !build_script.environment_variables.is_empty());
                },
                DLLIssueType::MemoryLayoutMismatch => {
                    // Should include architecture-specific flags or build commands
                    prop_assert!(!build_script.build_commands.is_empty() || !build_script.environment_variables.is_empty());
                }
            }
            
            // Verify build script completeness
            prop_assert_eq!(build_script.language, ffi_impl);
            prop_assert!(!build_script.script_content.is_empty());
            prop_assert!(!build_script.validation_commands.is_empty());
            
            // Test path correction functionality
            let path_correction = fixer.correct_library_paths(&ffi_impl);
            prop_assert!(path_correction.is_ok());
            let correction = path_correction.unwrap();
            prop_assert_eq!(correction.implementation, ffi_impl);
            
            // Verify that corrections are applied when needed
            for (original, corrected) in correction.original_paths.iter().zip(correction.corrected_paths.iter()) {
                // If paths are different, there should be correction entries
                if original != corrected {
                    prop_assert!(!correction.corrections_applied.is_empty());
                }
            }
        }
    }

    #[cfg(feature = "proptest")]
    proptest! {
        #[test]
        fn property_symbol_validation_consistency(
            library_name in prop::sample::select(vec!["numeric", "memory", "parallel", "rust_ext", "go"])
        ) {
            let fixer = FFIImplementationFixer::new();
            let library_path = format!("test/path/{}.dll", library_name);
            
            // Get expected symbols
            let expected_symbols = fixer.get_expected_symbols_for_library(&library_path);
            prop_assert!(!expected_symbols.is_empty());
            
            // Validate symbols (will fail for non-existent library, but should be consistent)
            let validation_result = fixer.validate_symbol_exports(&library_path);
            prop_assert!(validation_result.is_ok());
            
            let validation = validation_result.unwrap();
            prop_assert_eq!(validation.library_path, library_path.clone());
            
            // For non-existent libraries, should report the issue consistently
            if !std::path::Path::new(&library_path).exists() {
                prop_assert!(!validation.validation_successful);
                prop_assert!(!validation.issues.is_empty());
                prop_assert!(validation.issues[0].issue_description.contains("does not exist"));
            }
        }
    }
}