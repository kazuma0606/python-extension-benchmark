"""
Task 11 — Python Integration Tests
====================================
Tests for ffi_audit_integration.py covering:
  - 11.1: PyO3 Python bindings (via the shim when Rust ext is not built)
  - 11.2: Integration with benchmark runner result objects
"""

import sys
import os
from pathlib import Path
from types import SimpleNamespace
from typing import List

# Ensure the audit package root is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from ffi_audit_integration import (
    FFIAuditIntegration,
    create_audit_integration,
    is_rust_extension_available,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_result(name: str, mean_time_s: float, status: str = "SUCCESS") -> SimpleNamespace:
    """Simulate a BenchmarkResult object from the benchmark runner."""
    return SimpleNamespace(
        implementation_name=name,
        mean_time=mean_time_s,
        status=status,
    )


# ── 11.1: PyO3 binding tests ──────────────────────────────────────────────────

class TestPyO3Bindings:
    def test_audit_integration_creates_successfully(self):
        audit = FFIAuditIntegration()
        assert audit is not None

    def test_factory_function(self):
        audit = create_audit_integration()
        assert isinstance(audit, FFIAuditIntegration)

    def test_rust_availability_flag_is_bool(self):
        assert isinstance(is_rust_extension_available(), bool)

    def test_classify_implementation_native(self):
        audit = FFIAuditIntegration()
        for name in ("rust_ffi", "c_ext", "cython_ffi", "go_ffi", "zig_ffi"):
            assert audit.classify_implementation(name) == "native", \
                f"{name} should be classified as native"

    def test_classify_implementation_python(self):
        audit = FFIAuditIntegration()
        for name in ("python", "pure_python", "fallback_impl"):
            assert audit.classify_implementation(name) == "python", \
                f"{name} should be classified as python"

    def test_classify_implementation_unknown(self):
        audit = FFIAuditIntegration()
        result = audit.classify_implementation("some_mystery_impl")
        assert result in ("native", "python", "unknown")

    def test_check_implementation_native(self):
        audit = FFIAuditIntegration()
        info = audit.check_implementation("rust_ffi")
        assert info["implementation"] == "rust_ffi"
        assert "execution_type" in info
        assert "is_native" in info
        assert isinstance(info["recommendations"], list)

    def test_check_implementation_python(self):
        audit = FFIAuditIntegration()
        info = audit.check_implementation("python")
        assert info["fallback_suspected"] is True

    def test_generate_performance_report_structure(self):
        audit = FFIAuditIntegration()
        ffi_data = {
            "rust_ffi": [500.0, 510.0, 495.0],
            "c_ffi":    [450.0, 460.0, 455.0],
        }
        py_baseline = [5000.0, 5100.0, 4950.0]
        report = audit.generate_performance_report(ffi_data, py_baseline)

        assert "comparisons" in report
        assert "passing_implementations" in report
        assert "suspected_fallbacks" in report
        assert "average_speedup_percentage" in report
        assert "report_text" in report
        assert len(report["comparisons"]) == 2

    def test_performance_report_fast_ffi_passes(self):
        audit = FFIAuditIntegration()
        # FFI is 10× faster than Python
        ffi_data = {"fast_ffi": [1000.0] * 10}
        py_baseline = [10_000.0] * 10
        report = audit.generate_performance_report(ffi_data, py_baseline)
        assert "fast_ffi" in report["passing_implementations"], \
            "fast_ffi (10× speedup) should be in passing_implementations"

    def test_performance_report_slow_ffi_is_suspected_fallback(self):
        audit = FFIAuditIntegration()
        # FFI is same speed as Python → fallback suspected
        ffi_data = {"slow_ffi": [10_000.0] * 5}
        py_baseline = [10_000.0] * 5
        report = audit.generate_performance_report(ffi_data, py_baseline)
        assert "slow_ffi" in report["suspected_fallbacks"], \
            "slow_ffi (same speed as Python) should be in suspected_fallbacks"


# ── 11.2: Benchmark runner integration tests ──────────────────────────────────

class TestBenchmarkRunnerIntegration:
    """Simulate what ffi_benchmark_runner would do when calling the audit system."""

    def _make_mixed_results(self) -> list:
        return [
            _make_result("python",      mean_time_s=0.010),   # 10 ms baseline
            _make_result("rust_ffi",    mean_time_s=0.001),   # 1 ms — clearly faster
            _make_result("c_ffi",       mean_time_s=0.0008),  # 0.8 ms — clearly faster
            _make_result("slow_ffi",    mean_time_s=0.012),   # 12 ms — likely fallback
            _make_result("broken_ffi",  mean_time_s=0.0,  status="ERROR"),
        ]

    def test_audit_benchmark_results_returns_expected_keys(self):
        audit = FFIAuditIntegration()
        results = self._make_mixed_results()
        report = audit.audit_benchmark_results(results)

        for key in ("suspected_fallbacks", "clean_implementations",
                    "python_baseline_ns", "comparisons",
                    "clean_ffi_times_ns", "report_text", "summary"):
            assert key in report, f"Missing key: {key}"

    def test_audit_ignores_error_status_results(self):
        audit = FFIAuditIntegration()
        results = [
            _make_result("python",  0.010),
            _make_result("bad_ffi", 0.001, status="ERROR"),
        ]
        report = audit.audit_benchmark_results(results)
        # broken_ffi was an ERROR, so it should not appear in clean_implementations
        assert "bad_ffi" not in report["clean_implementations"]

    def test_slow_ffi_detected_as_suspected_fallback(self):
        audit = FFIAuditIntegration()
        # slow_ffi reports 12 ms — above the 10 ms threshold
        results = [
            _make_result("python",   0.010),
            _make_result("slow_ffi", 0.012),
        ]
        report = audit.audit_benchmark_results(results)
        assert "slow_ffi" in report["suspected_fallbacks"], \
            "slow_ffi (12 ms) should be suspected as a fallback"

    def test_fast_ffi_is_clean(self):
        audit = FFIAuditIntegration()
        results = [
            _make_result("python",   0.010),
            _make_result("rust_ffi", 0.001),
        ]
        report = audit.audit_benchmark_results(results)
        assert "rust_ffi" in report["clean_implementations"]

    def test_python_baseline_collected(self):
        audit = FFIAuditIntegration()
        results = [_make_result("python", 0.010), _make_result("rust_ffi", 0.001)]
        report = audit.audit_benchmark_results(results)
        # Python baseline should be ~ 10_000_000 ns
        assert len(report["python_baseline_ns"]) == 1
        assert abs(report["python_baseline_ns"][0] - 10_000_000.0) < 1.0

    def test_comparisons_generated_when_baseline_available(self):
        audit = FFIAuditIntegration()
        results = [
            _make_result("python",   0.010),
            _make_result("rust_ffi", 0.001),
            _make_result("c_ffi",    0.0008),
        ]
        report = audit.audit_benchmark_results(results)
        assert len(report["comparisons"]) == 2, \
            "Should have one comparison per non-Python implementation"

    def test_report_text_is_non_empty_string(self):
        audit = FFIAuditIntegration()
        results = [_make_result("python", 0.010), _make_result("rust_ffi", 0.001)]
        report = audit.audit_benchmark_results(results)
        assert isinstance(report["report_text"], str)
        assert len(report["report_text"]) > 0

    def test_contaminated_results_filtered(self):
        audit = FFIAuditIntegration()
        # Include a clearly contaminated result (negative / zero)
        # filter_contaminated_results_py removes <= 0 and >= 10ms
        results = [
            _make_result("python",   0.010),
            _make_result("rust_ffi", 0.001),
            _make_result("bad_ffi",  0.015),   # > 10 ms → contaminated
        ]
        report = audit.audit_benchmark_results(results)
        # clean_ffi_times_ns should not contain the 15 ms result
        threshold = FFIAuditIntegration.FALLBACK_THRESHOLD_NS
        for t in report["clean_ffi_times_ns"]:
            assert t < threshold, f"Contaminated time {t} ns leaked into clean results"


# ── Standalone runner (pytest not required) ────────────────────────────────────

if __name__ == "__main__":
    import traceback

    test_classes = [TestPyO3Bindings, TestBenchmarkRunnerIntegration]
    passed = failed = 0

    for cls in test_classes:
        instance = cls()
        for attr in dir(cls):
            if not attr.startswith("test_"):
                continue
            method = getattr(instance, attr)
            try:
                method()
                print(f"  PASS  {cls.__name__}.{attr}")
                passed += 1
            except Exception as exc:
                print(f"  FAIL  {cls.__name__}.{attr}")
                traceback.print_exc()
                failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
