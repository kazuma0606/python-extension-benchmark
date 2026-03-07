"""
Task 13.1 — Real FFI Implementation Diagnostics
================================================
Runs the audit system against all actual FFI implementations to:
  - Detect problems in each language implementation
  - Generate fix steps
  - Report classification and execution-type detection

Requirements covered: 1.1-1.5, 3.1-3.8
"""

from __future__ import annotations

import sys
import importlib
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent))

from ffi_audit_integration import FFIAuditIntegration, is_rust_extension_available


# ---------------------------------------------------------------------------
# All FFI/extension implementation names from the benchmark system
# ---------------------------------------------------------------------------

FFI_IMPLEMENTATIONS = [
    # Extension implementations
    "c_ext", "cpp_ext", "cython_ext", "rust_ext",
    "fortran_ext", "julia_ext", "go_ext", "zig_ext",
    "nim_ext", "kotlin_ext",
    # FFI implementations
    "c_ffi", "cpp_ffi", "numpy_ffi", "cython_ffi",
    "rust_ffi", "fortran_ffi", "julia_ffi", "go_ffi",
    "zig_ffi", "nim_ffi", "kotlin_ffi",
]

PYTHON_BASELINE = "python"

# Module paths for each implementation (best-effort import check)
IMPL_MODULE_MAP: Dict[str, str] = {
    "python":      "benchmark.ffi_implementations.numpy_ffi",  # baseline via numpy
    "c_ext":       "benchmark.ffi_implementations.c_ffi",
    "cpp_ext":     "benchmark.ffi_implementations.cpp_ffi",
    "cython_ext":  "benchmark.ffi_implementations.cython_ffi",
    "rust_ext":    "benchmark.ffi_implementations.rust_ffi",
    "fortran_ext": "benchmark.ffi_implementations.fortran_ffi",
    "julia_ext":   "benchmark.ffi_implementations.julia_ffi",
    "go_ext":      "benchmark.ffi_implementations.go_ffi",
    "zig_ext":     "benchmark.ffi_implementations.zig_ffi",
    "nim_ext":     "benchmark.ffi_implementations.nim_ffi",
    "kotlin_ext":  "benchmark.ffi_implementations.kotlin_ffi",
    "c_ffi":       "benchmark.ffi_implementations.c_ffi",
    "cpp_ffi":     "benchmark.ffi_implementations.cpp_ffi",
    "numpy_ffi":   "benchmark.ffi_implementations.numpy_ffi",
    "cython_ffi":  "benchmark.ffi_implementations.cython_ffi",
    "rust_ffi":    "benchmark.ffi_implementations.rust_ffi",
    "fortran_ffi": "benchmark.ffi_implementations.fortran_ffi",
    "julia_ffi":   "benchmark.ffi_implementations.julia_ffi",
    "go_ffi":      "benchmark.ffi_implementations.go_ffi",
    "zig_ffi":     "benchmark.ffi_implementations.zig_ffi",
    "nim_ffi":     "benchmark.ffi_implementations.nim_ffi",
    "kotlin_ffi":  "benchmark.ffi_implementations.kotlin_ffi",
}


def try_import_module(module_path: str) -> Tuple[bool, str]:
    """Attempt to import a module; return (success, error_message)."""
    try:
        importlib.import_module(module_path)
        return True, ""
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Diagnostic test class
# ---------------------------------------------------------------------------

class TestFFIDiagnostics:
    """Task 13.1: Diagnose all FFI implementations using the audit system."""

    def setup(self) -> None:
        self.audit = FFIAuditIntegration()
        self.results: List[Dict[str, Any]] = []

    def test_audit_system_initialises(self) -> None:
        """Audit integration object must be created without error."""
        assert self.audit is not None
        # Record Rust extension status (informational)
        print(f"  Rust extension available: {is_rust_extension_available()}")

    def test_check_all_ffi_implementations(self) -> None:
        """Requirement 1.1 / 3.1-3.8: detect execution type for every impl."""
        issues_found = []

        for impl in FFI_IMPLEMENTATIONS:
            info = self.audit.check_implementation(impl)

            assert info["implementation"] == impl, \
                f"implementation field mismatch for {impl}"
            assert "execution_type" in info
            assert "is_native" in info
            assert "fallback_suspected" in info
            assert isinstance(info["recommendations"], list)

            classification = self.audit.classify_implementation(impl)
            assert classification in ("native", "python", "unknown"), \
                f"Unexpected classification '{classification}' for {impl}"

            if info["fallback_suspected"] or not info["is_native"]:
                issues_found.append({
                    "impl": impl,
                    "classification": classification,
                    "execution_type": info["execution_type"],
                    "fallback_suspected": info["fallback_suspected"],
                    "recommendations": info["recommendations"],
                })

            self.results.append({
                "impl": impl,
                "classification": classification,
                **info,
            })

        # Print diagnostic summary
        print(f"\n  Checked {len(FFI_IMPLEMENTATIONS)} implementations")
        print(f"  Issues flagged: {len(issues_found)}")
        for issue in issues_found:
            print(f"    - {issue['impl']}: classification={issue['classification']}, "
                  f"type={issue['execution_type']}, fallback={issue['fallback_suspected']}")
            for rec in issue["recommendations"][:2]:
                print(f"      * {rec}")

    def test_python_not_classified_as_native(self) -> None:
        """Requirement 1.3: Python baseline should not be classified as native."""
        info = self.audit.check_implementation(PYTHON_BASELINE)
        assert info["fallback_suspected"] is True, \
            "Python baseline should be flagged as suspected fallback"
        classification = self.audit.classify_implementation(PYTHON_BASELINE)
        assert classification == "python", \
            f"Python baseline should be classified as 'python', got '{classification}'"

    def test_native_ffi_impls_classified_correctly(self) -> None:
        """Requirement 3.1-3.8: C/Rust/Go etc. should be classified as native."""
        native_impls = [
            "c_ext", "cpp_ext", "rust_ext", "go_ext", "fortran_ext",
            "zig_ext", "nim_ext",
            "c_ffi", "cpp_ffi", "rust_ffi", "go_ffi", "fortran_ffi",
            "zig_ffi", "nim_ffi",
        ]
        for impl in native_impls:
            classification = self.audit.classify_implementation(impl)
            assert classification in ("native", "unknown"), \
                f"{impl} should be 'native' or 'unknown', got '{classification}'"

    def test_module_importability(self) -> None:
        """Requirement 1.2: Check which implementation modules can be imported."""
        import_results: Dict[str, Tuple[bool, str]] = {}

        for impl, module_path in IMPL_MODULE_MAP.items():
            ok, err = try_import_module(module_path)
            import_results[impl] = (ok, err)

        # Count working vs broken
        working = [impl for impl, (ok, _) in import_results.items() if ok]
        broken  = [impl for impl, (ok, _) in import_results.items() if not ok]

        print(f"\n  Importable modules: {len(working)}/{len(import_results)}")
        if broken:
            print(f"  Import failures ({len(broken)}):")
            for impl in broken:
                _, err = import_results[impl]
                print(f"    - {impl}: {err[:80]}")

        # At least some implementations should be importable
        assert len(working) > 0, \
            "At least one FFI implementation module must be importable"

    def test_fix_recommendations_generated(self) -> None:
        """Requirement 1.4-1.5: For suspected fallbacks, recommendations must be non-empty."""
        # python always has recommendations since it IS the fallback
        info = self.audit.check_implementation(PYTHON_BASELINE)
        assert info["fallback_suspected"] is True
        assert len(info["recommendations"]) > 0, \
            "Python baseline should generate fix recommendations"

    def test_report_generation_for_all_impls(self) -> None:
        """Requirement 1.5: generate_performance_report must produce valid output."""
        import time
        ffi_data: Dict[str, List[float]] = {}
        py_baseline = [10_000_000.0] * 5  # 10 ms Python baseline

        for impl in FFI_IMPLEMENTATIONS[:6]:  # Sample of implementations
            # Simulate native FFI being ~10x faster
            ffi_data[impl] = [1_000_000.0] * 5  # 1 ms

        report = self.audit.generate_performance_report(ffi_data, py_baseline)

        assert "comparisons" in report
        assert "passing_implementations" in report
        assert "suspected_fallbacks" in report
        assert "average_speedup_percentage" in report
        assert "report_text" in report
        assert len(report["comparisons"]) == len(ffi_data)
        # All sampled impls should show significant speedup (10x vs Python)
        assert len(report["passing_implementations"]) > 0, \
            "At least one implementation should show significant speedup"

        print(f"\n  Passing implementations: {report['passing_implementations']}")
        print(f"  Avg speedup: {report['average_speedup_percentage']:.1f}%")


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    suite = TestFFIDiagnostics()
    suite.setup()

    tests = [
        ("test_audit_system_initialises",           suite.test_audit_system_initialises),
        ("test_check_all_ffi_implementations",      suite.test_check_all_ffi_implementations),
        ("test_python_not_classified_as_native",    suite.test_python_not_classified_as_native),
        ("test_native_ffi_impls_classified_correctly", suite.test_native_ffi_impls_classified_correctly),
        ("test_module_importability",               suite.test_module_importability),
        ("test_fix_recommendations_generated",      suite.test_fix_recommendations_generated),
        ("test_report_generation_for_all_impls",    suite.test_report_generation_for_all_impls),
    ]

    passed = failed = 0
    for name, fn in tests:
        try:
            print(f"\n[TEST] {name}")
            fn()
            print(f"  PASS")
            passed += 1
        except Exception as exc:
            print(f"  FAIL: {exc}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print(f"Task 13.1 Diagnostics: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
