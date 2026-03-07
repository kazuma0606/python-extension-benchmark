"""
FFI Audit Integration Module  (Task 11.2)
==========================================
Python bridge between the windows_ffi_audit Rust extension and the existing
ffi_benchmark_runner.  Works in two modes:

  1. **Native mode** – the compiled windows_ffi_audit.pyd is importable.
     All Rust-backed classes (FallbackPreventionSystem, ComprehensiveAuditReporter,
     …) are used directly.

  2. **Fallback mode** – the extension is not yet built / not on the path.
     A lightweight pure-Python shim provides the same public API so that the
     benchmark runner can always import this module safely.

Requirements covered: 1.1-1.5, 2.1-2.5
"""

from __future__ import annotations

import sys
import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Try to import the compiled Rust extension ─────────────────────────────────
_RUST_AVAILABLE = False
_windows_ffi_audit: Any = None

def _try_load_extension() -> bool:
    """Attempt to import windows_ffi_audit from the audit build directory."""
    global _windows_ffi_audit, _RUST_AVAILABLE

    # Candidate directories where the .pyd / .so may live
    _audit_root = Path(__file__).parent
    candidates = [
        _audit_root / "target" / "debug",
        _audit_root / "target" / "release",
        _audit_root,
    ]
    for path in candidates:
        str_path = str(path)
        if str_path not in sys.path:
            sys.path.insert(0, str_path)

    try:
        import windows_ffi_audit as _ext  # type: ignore
        _windows_ffi_audit = _ext
        _RUST_AVAILABLE = True
        return True
    except ImportError:
        return False

_try_load_extension()


# ── Pure-Python shim (used when Rust extension is absent) ─────────────────────

class _ShimFallbackPreventionSystem:
    """Minimal Python shim for FallbackPreventionSystem."""

    _FALLBACK_THRESHOLD_NS = 10_000_000.0  # 10 ms

    def is_fallback_suspected_py(self, implementation: str, execution_time_ns: float) -> bool:
        name_flag = any(kw in implementation for kw in ("python", "fallback", "pure"))
        return name_flag or execution_time_ns >= self._FALLBACK_THRESHOLD_NS

    def detect_execution_type_py(self, implementation: str) -> int:
        """0=Native, 1=Python, 2=Mixed, 3=Unknown"""
        if any(kw in implementation for kw in ("python", "pure", "fallback")):
            return 1
        if any(kw in implementation for kw in ("_ffi", "_ext", "rust", "c_", "go_", "cython")):
            return 0
        return 3

    def filter_contaminated_results_py(self, results: List[float]) -> List[float]:
        return [r for r in results if r > 0.0 and r < self._FALLBACK_THRESHOLD_NS]

    def compare_with_python_baseline_py(
        self,
        implementation: str,
        ffi_results_ns: List[float],
        python_baseline_ns: List[float],
    ) -> Dict[str, Any]:
        if not ffi_results_ns or not python_baseline_ns:
            return {"error": "empty results"}
        ffi_mean = sum(ffi_results_ns) / len(ffi_results_ns)
        py_mean  = sum(python_baseline_ns) / len(python_baseline_ns)
        ratio    = py_mean / ffi_mean if ffi_mean > 0 else 1.0
        speedup  = (py_mean - ffi_mean) / py_mean * 100.0 if py_mean > 0 else 0.0
        return {
            "implementation": implementation,
            "performance_ratio": ratio,
            "speedup_percentage": speedup,
            "is_significantly_faster": ratio > 1.5,
            "fallback_suspected": ratio < 1.1,
            "p_value": 1.0,
            "t_statistic": 0.0,
            "effect_size": 0.0,
            "degrees_of_freedom": 0.0,
            "flags": ["InsufficientData"] if len(ffi_results_ns) < 3 else [],
            "recommendations": [],
        }


class _ShimComprehensiveAuditReporter:
    """Minimal Python shim for ComprehensiveAuditReporter."""

    def generate_bug_analysis_report_text(self, implementations: List[str]) -> str:
        lines = [
            "FFI Implementation Bug Analysis Report (shim – Rust extension not available)",
            f"Implementations listed: {', '.join(implementations)}",
            "Build the windows_ffi_audit extension to get full diagnostics.",
        ]
        return "\n".join(lines)

    def generate_performance_validation_report_text(self, results: List[float]) -> str:
        if not results:
            return "No results provided."
        mean = sum(results) / len(results)
        return (
            f"Performance Validation Report (shim)\n"
            f"  Samples: {len(results)}, Mean: {mean:.0f} ns\n"
        )

    def generate_comprehensive_report_text(
        self,
        implementations: List[str],
        performance_results: List[float],
    ) -> str:
        bug_text  = self.generate_bug_analysis_report_text(implementations)
        perf_text = self.generate_performance_validation_report_text(performance_results)
        return f"{bug_text}\n\n{perf_text}"

    def analyze_benchmark_results_py(
        self,
        results: List[Tuple[str, float]],
    ) -> Dict[str, Any]:
        threshold = 10_000_000.0
        suspected = [n for n, t in results if "python" in n or t >= threshold]
        clean     = [n for n, t in results if n not in suspected]
        return {
            "suspected_fallbacks": suspected,
            "clean_implementations": clean,
            "summary": f"Analyzed {len(results)} implementations: "
                       f"{len(suspected)} suspected, {len(clean)} clean.",
        }


def _make_fallback_system() -> Any:
    """Return the Rust FallbackPreventionSystem if all required methods exist,
    otherwise return the pure-Python shim."""
    if _RUST_AVAILABLE:
        obj = _windows_ffi_audit.FallbackPreventionSystem()
        required = (
            "detect_execution_type_py",
            "is_fallback_suspected_py",
            "filter_contaminated_results_py",
            "compare_with_python_baseline_py",
        )
        if all(hasattr(obj, m) for m in required):
            return obj
    return _ShimFallbackPreventionSystem()


def _make_reporter() -> Any:
    """Return the Rust ComprehensiveAuditReporter if all required methods exist,
    otherwise return the pure-Python shim."""
    if _RUST_AVAILABLE:
        obj = _windows_ffi_audit.ComprehensiveAuditReporter()
        required = (
            "generate_bug_analysis_report_text",
            "generate_performance_validation_report_text",
            "generate_comprehensive_report_text",
            "analyze_benchmark_results_py",
        )
        if all(hasattr(obj, m) for m in required):
            return obj
    return _ShimComprehensiveAuditReporter()


# ── Public integration class ──────────────────────────────────────────────────

class FFIAuditIntegration:
    """
    High-level integration layer between the windows_ffi_audit Rust extension
    and the existing ffi_benchmark_runner.

    Usage
    -----
    >>> audit = FFIAuditIntegration()
    >>> report = audit.audit_benchmark_results(results)
    >>> print(report["summary"])
    """

    # Execution-time threshold above which a result is treated as a Python fallback
    FALLBACK_THRESHOLD_NS: float = 10_000_000.0  # 10 ms

    def __init__(self) -> None:
        self._prevention = _make_fallback_system()
        self._reporter   = _make_reporter()
        self.rust_available = _RUST_AVAILABLE

    # ── Requirement 2.1: detect fallback in benchmark results ─────────────────

    def audit_benchmark_results(
        self,
        results: List[Any],
        python_impl_name: str = "python",
    ) -> Dict[str, Any]:
        """
        Analyse a list of BenchmarkResult objects from the benchmark runner.

        Parameters
        ----------
        results:
            List of BenchmarkResult objects (must have ``implementation_name``,
            ``mean_time``, and ``status`` attributes).
        python_impl_name:
            Name of the pure-Python baseline implementation.

        Returns
        -------
        dict with keys:
            suspected_fallbacks, clean_implementations,
            python_baseline_ns, comparisons, report_text, summary
        """
        # Collect (name, mean_ns) pairs from successful results
        pairs: List[Tuple[str, float]] = []
        for r in results:
            if getattr(r, "status", "ERROR") == "SUCCESS":
                name    = getattr(r, "implementation_name", "unknown")
                mean_s  = getattr(r, "mean_time", 0.0)          # seconds
                mean_ns = mean_s * 1e9
                pairs.append((name, mean_ns))

        # Separate Python baseline from FFI implementations
        py_pairs  = [(n, t) for n, t in pairs if n == python_impl_name]
        ffi_pairs = [(n, t) for n, t in pairs if n != python_impl_name]

        py_times = [t for _, t in py_pairs]

        # Requirement 2.1: detect fallback for each FFI impl
        analysis = self._reporter.analyze_benchmark_results_py(ffi_pairs)

        # Requirement 2.3: per-implementation comparison if Python baseline available
        comparisons: List[Dict[str, Any]] = []
        if py_times:
            for name, ffi_time in ffi_pairs:
                cmp = self._prevention.compare_with_python_baseline_py(
                    name, [ffi_time], py_times
                )
                comparisons.append(cmp)

        # Requirement 2.2: list implementations that should be stopped / investigated
        suspected = analysis.get("suspected_fallbacks", [])

        # Requirement 2.5: filter contaminated results
        all_ffi_times = [t for _, t in ffi_pairs]
        clean_times = self._prevention.filter_contaminated_results_py(all_ffi_times)

        # Build report text (Requirement 1.5)
        impl_names = [n for n, _ in pairs]
        perf_values = [t for _, t in ffi_pairs]
        report_text = self._reporter.generate_comprehensive_report_text(
            impl_names, perf_values
        )

        return {
            "suspected_fallbacks": suspected,
            "clean_implementations": analysis.get("clean_implementations", []),
            "python_baseline_ns": py_times,
            "comparisons": comparisons,
            "clean_ffi_times_ns": clean_times,
            "report_text": report_text,
            "summary": analysis.get("summary", ""),
            "rust_extension_used": self.rust_available,
        }

    # ── Requirement 1.1-1.5: per-implementation audit ─────────────────────────

    def check_implementation(self, impl_name: str) -> Dict[str, Any]:
        """
        Run a quick audit check on a single FFI implementation.

        Returns
        -------
        dict with keys:
            implementation, execution_type, is_native, fallback_suspected,
            recommendations
        """
        exec_type = self._prevention.detect_execution_type_py(impl_name)
        is_native = (exec_type == 0)  # 0 = NativeOnly
        fallback  = self._prevention.is_fallback_suspected_py(impl_name, 0.0)

        recommendations: List[str] = []
        if not is_native:
            recommendations.append(
                f"{impl_name}: not detected as native — check library loading."
            )
        if fallback:
            recommendations.append(
                f"{impl_name}: implementation name suggests Python fallback."
            )

        return {
            "implementation": impl_name,
            "execution_type": exec_type,  # 0=Native,1=Python,2=Mixed,3=Unknown
            "is_native": is_native,
            "fallback_suspected": fallback,
            "recommendations": recommendations,
        }

    # ── Requirement 6.1-6.5: performance report generation ────────────────────

    def generate_performance_report(
        self,
        ffi_results_ns: Dict[str, List[float]],
        python_baseline_ns: List[float],
    ) -> Dict[str, Any]:
        """
        Generate a performance report comparing multiple FFI implementations
        against a shared Python baseline.

        Parameters
        ----------
        ffi_results_ns:
            Dict mapping implementation name → list of timing samples in ns.
        python_baseline_ns:
            List of Python baseline timing samples in ns.

        Returns
        -------
        dict with comparisons list and summary text.
        """
        comparisons = []
        for name, samples in ffi_results_ns.items():
            cmp = self._prevention.compare_with_python_baseline_py(
                name, samples, python_baseline_ns
            )
            comparisons.append(cmp)

        passing   = [c["implementation"] for c in comparisons if c.get("is_significantly_faster")]
        fallbacks = [c["implementation"] for c in comparisons if c.get("fallback_suspected")]
        avg_speedup = (
            sum(c["speedup_percentage"] for c in comparisons if c.get("is_significantly_faster"))
            / max(len(passing), 1)
        )

        report_text = self._reporter.generate_performance_validation_report_text(
            [s for samples in ffi_results_ns.values() for s in samples]
        )

        return {
            "comparisons": comparisons,
            "passing_implementations": passing,
            "suspected_fallbacks": fallbacks,
            "average_speedup_percentage": avg_speedup,
            "report_text": report_text,
        }

    # ── Utility ───────────────────────────────────────────────────────────────

    def classify_implementation(self, name: str) -> str:
        """Return 'native', 'python', or 'unknown' based on the implementation name."""
        if _RUST_AVAILABLE and hasattr(_windows_ffi_audit, "classify_implementation"):
            return _windows_ffi_audit.classify_implementation(name)
        # Pure-Python fallback
        if any(kw in name for kw in ("python", "pure", "fallback")):
            return "python"
        if any(kw in name for kw in ("_ffi", "_ext", "rust", "c_", "cython", "go_", "zig", "nim", "julia", "kotlin", "fortran")):
            return "native"
        return "unknown"


# ── Module-level convenience ──────────────────────────────────────────────────

def create_audit_integration() -> FFIAuditIntegration:
    """Factory function — preferred entry point."""
    return FFIAuditIntegration()


def is_rust_extension_available() -> bool:
    """True if the compiled windows_ffi_audit extension is loaded."""
    return _RUST_AVAILABLE
