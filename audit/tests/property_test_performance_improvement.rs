// Feature: windows-ffi-audit, Property 13: 性能向上実現
// Validates: Requirements 6.1-6.5

use windows_ffi_audit::FallbackPreventionSystem;
use proptest::prelude::*;

proptest! {
    #![proptest_config(ProptestConfig::with_cases(100))]

    // Property 13-A: FFI implementations faster than Python are detected as such
    #[test]
    fn property_ffi_faster_than_python_detected(
        // FFI results: clearly faster (lower ns values)
        ffi_results in prop::collection::vec(500.0f64..1500.0f64, 5..15),
        // Python baseline: clearly slower
        python_speedup in 3.0f64..10.0f64,
        python_n in 5usize..15usize,
    ) {
        let system = FallbackPreventionSystem::new();

        // Build Python baseline as ffi_mean * speedup ± small noise
        let ffi_mean: f64 = ffi_results.iter().sum::<f64>() / ffi_results.len() as f64;
        let py_base = ffi_mean * python_speedup;
        let python_baseline: Vec<f64> = (0..python_n)
            .map(|i| py_base * (1.0 + (i as f64 % 5.0 - 2.0) * 0.05))
            .collect();

        let result = system.compare_with_python_baseline("fast_ffi", &ffi_results, &python_baseline).unwrap();

        // Performance ratio should be well above 1 (FFI is faster)
        prop_assert!(result.performance_ratio > 1.5,
            "FFI clearly faster than Python should yield ratio > 1.5, got {:.2}",
            result.performance_ratio);

        // Speedup percentage should be positive
        prop_assert!(result.speedup_percentage > 0.0,
            "Speedup percentage should be positive when FFI is faster: {:.1}%",
            result.speedup_percentage);

        // Should be marked as significantly faster
        prop_assert!(result.is_significantly_faster,
            "FFI with {}× speedup should be detected as significantly faster",
            python_speedup);

        // Fallback should not be suspected when FFI is clearly faster
        prop_assert!(!result.fallback_suspected,
            "Fallback should not be suspected when FFI is {}× faster than Python",
            python_speedup);
    }

    // Property 13-B: Implementations with Python-like speed are flagged as potential fallbacks
    #[test]
    fn property_python_speed_flagged_as_fallback(
        // FFI results suspiciously similar to Python
        base_time in 1_000_000.0f64..5_000_000.0f64,
        n_ffi in 5usize..12usize,
        n_py in 5usize..12usize,
    ) {
        let system = FallbackPreventionSystem::new();

        // FFI results ≈ Python baseline (ratio near 1.0)
        let ffi_results: Vec<f64> = (0..n_ffi)
            .map(|i| base_time * (1.0 + (i as f64 % 3.0 - 1.0) * 0.02))
            .collect();
        let python_baseline: Vec<f64> = (0..n_py)
            .map(|i| base_time * (1.0 + (i as f64 % 3.0 - 1.0) * 0.02))
            .collect();

        let result = system.compare_with_python_baseline("suspect_ffi", &ffi_results, &python_baseline).unwrap();

        // Should NOT be confirmed as significantly faster
        prop_assert!(!result.is_significantly_faster,
            "FFI with same speed as Python should not be confirmed as faster: ratio={:.2}",
            result.performance_ratio);

        // Fallback should be suspected
        prop_assert!(result.fallback_suspected,
            "Fallback should be suspected when FFI speed ≈ Python speed: ratio={:.2}",
            result.performance_ratio);
    }

    // Property 13-C: Performance ratio is monotonically related to actual speedup
    #[test]
    fn property_performance_ratio_monotonic(
        base_ffi in 500.0f64..2000.0f64,
        small_speedup in 1.5f64..3.0f64,
        large_speedup in 5.0f64..15.0f64,
        n in 5usize..10usize,
    ) {
        let system = FallbackPreventionSystem::new();

        let ffi: Vec<f64> = (0..n).map(|_| base_ffi).collect();
        let py_slow: Vec<f64>  = (0..n).map(|_| base_ffi * large_speedup).collect();
        let py_medium: Vec<f64> = (0..n).map(|_| base_ffi * small_speedup).collect();

        let result_slow   = system.compare_with_python_baseline("ffi", &ffi, &py_slow).unwrap();
        let result_medium = system.compare_with_python_baseline("ffi", &ffi, &py_medium).unwrap();

        // Larger Python time → higher performance ratio
        prop_assert!(result_slow.performance_ratio > result_medium.performance_ratio,
            "Slower Python baseline should yield higher performance ratio: \
             slow={:.2} medium={:.2}",
            result_slow.performance_ratio, result_medium.performance_ratio);
    }

    // Property 13-D: Aggregate report correctly classifies passing vs failing implementations
    #[test]
    fn property_report_classifies_implementations(
        ffi_fast in prop::collection::vec(300.0f64..800.0f64, 8..12),
        ffi_slow in prop::collection::vec(5_000_000.0f64..15_000_000.0f64, 8..12),
        python_base in prop::collection::vec(3_000_000.0f64..8_000_000.0f64, 8..12),
    ) {
        let system = FallbackPreventionSystem::new();

        let fast_result = system.compare_with_python_baseline(
            "fast_impl", &ffi_fast, &python_base).unwrap();
        let slow_result = system.compare_with_python_baseline(
            "slow_impl", &ffi_slow, &python_base).unwrap();

        let report = system.generate_performance_report(
            &[fast_result.clone(), slow_result.clone()]).unwrap();

        // Report totals should match comparisons
        prop_assert_eq!(report.comparisons.len(), 2,
            "Report should contain all 2 comparisons");

        let total_classified = report.passing_implementations.len()
            + report.failing_implementations.len();
        prop_assert_eq!(total_classified, 2,
            "Every implementation must be in exactly one category");

        // The fast FFI should pass
        if fast_result.is_significantly_faster {
            prop_assert!(report.passing_implementations.contains(&"fast_impl".to_string()),
                "fast_impl should be in passing implementations");
        }

        // The slow FFI (slower than Python) should fail
        if slow_result.fallback_suspected || !slow_result.is_significantly_faster {
            prop_assert!(report.failing_implementations.contains(&"slow_impl".to_string()),
                "slow_impl should be in failing implementations");
        }
    }

    // Property 13-E: Statistical significance is detected when sample sizes are adequate
    #[test]
    fn property_significance_detected_with_adequate_samples(
        ffi_results in prop::collection::vec(100.0f64..500.0f64, 8..15),
        speedup_factor in 5.0f64..20.0f64,
        n_py in 8usize..15usize,
    ) {
        let system = FallbackPreventionSystem::new();

        let ffi_mean: f64 = ffi_results.iter().sum::<f64>() / ffi_results.len() as f64;
        // Python baseline: ffi_mean × speedup (clearly different)
        let python_baseline: Vec<f64> = (0..n_py)
            .map(|i| ffi_mean * speedup_factor * (1.0 + (i as f64 % 4.0 - 1.5) * 0.01))
            .collect();

        let result = system.compare_with_python_baseline("impl", &ffi_results, &python_baseline).unwrap();

        // With a clear speedup and ≥8 samples, the test should reach significance
        prop_assert!(result.statistical_significance.is_significant,
            "Welch's t-test should detect significance for {}× speedup with {} samples",
            speedup_factor, ffi_results.len());

        prop_assert!(result.statistical_significance.p_value < 0.05,
            "p-value should be < 0.05 for clear speedup: got {:.4}",
            result.statistical_significance.p_value);
    }

    // Property 13-F: Effect size (Cohen's d) is positive when FFI is faster
    #[test]
    fn property_effect_size_positive_when_ffi_faster(
        ffi_results in prop::collection::vec(200.0f64..600.0f64, 5..12),
        py_multiplier in 2.0f64..8.0f64,
        n_py in 5usize..12usize,
    ) {
        let system = FallbackPreventionSystem::new();

        let ffi_mean: f64 = ffi_results.iter().sum::<f64>() / ffi_results.len() as f64;
        let python_baseline: Vec<f64> = (0..n_py)
            .map(|_| ffi_mean * py_multiplier)
            .collect();

        let result = system.compare_with_python_baseline("impl", &ffi_results, &python_baseline).unwrap();

        // Cohen's d should be positive (positive = FFI mean is lower, i.e., faster)
        prop_assert!(result.statistical_significance.effect_size > 0.0,
            "Effect size should be positive when FFI is faster: d={:.2}",
            result.statistical_significance.effect_size);

        // Effect size should grow with speedup factor
        prop_assert!(result.statistical_significance.effect_size > 0.5,
            "Large speedup ({:.1}×) should yield large effect size, got d={:.2}",
            py_multiplier, result.statistical_significance.effect_size);
    }
}
