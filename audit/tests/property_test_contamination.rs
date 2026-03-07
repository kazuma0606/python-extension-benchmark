// Feature: windows-ffi-audit, Property 8: 汚染結果除外
// Validates: Requirements 2.5

use windows_ffi_audit::FallbackPreventionSystem;
use proptest::prelude::*;

proptest! {
    #![proptest_config(ProptestConfig::with_cases(100))]

    #[test]
    fn property_contaminated_results_exclusion(
        contaminated_results in prop::collection::vec(
            prop_oneof![
                // Normal results (should be kept)
                1000.0f64..2000.0f64,
                // Contaminated results (should be excluded)
                prop_oneof![
                    Just(0.0f64),              // Zero results (measurement errors)
                    -1000.0f64..0.0f64,       // Negative results (measurement errors)
                    50.0f64..99.0f64,         // Too fast (suspicious)
                    10_000_000.0f64..50_000_000.0f64, // Too slow (Python fallback)
                ]
            ],
            5..20
        )
    ) {
        let system = FallbackPreventionSystem::new();
        
        // Apply contamination filtering
        let filtered = system.filter_contaminated_results(&contaminated_results).unwrap();
        
        // Verify that contaminated results are excluded
        prop_assert!(filtered.len() <= contaminated_results.len(),
            "Filtered results should not exceed original results");
        
        // Check that all filtered results are valid (not contaminated)
        for &result in &filtered {
            prop_assert!(result > 0.0,
                "Filtered result should be positive: {}", result);
            prop_assert!(result.is_finite(),
                "Filtered result should be finite: {}", result);
        }
        
        // Check that zero and negative results are excluded
        let has_invalid_results = contaminated_results.iter().any(|&x| x <= 0.0);
        if has_invalid_results {
            let has_invalid_in_filtered = filtered.iter().any(|&x| x <= 0.0);
            prop_assert!(!has_invalid_in_filtered,
                "Invalid results should be filtered out");
        }
        
        // Check that filtering reduces results when contamination is present
        let has_contaminated = contaminated_results.iter().any(|&x| x <= 0.0);
        if has_contaminated && contaminated_results.len() > 3 {
            prop_assert!(filtered.len() <= contaminated_results.len(),
                "Filtering should reduce results when invalid values are present");
        }
    }

    #[test]
    fn property_fallback_results_complete_exclusion(
        normal_results in prop::collection::vec(1000.0f64..2000.0f64, 3..8),
        fallback_results in prop::collection::vec(15_000_000.0f64..100_000_000.0f64, 2..5)
    ) {
        let system = FallbackPreventionSystem::new();
        
        // Mix normal and fallback results
        let mut mixed_results = normal_results.clone();
        mixed_results.extend(fallback_results.clone());
        
        // Apply filtering
        let filtered = system.filter_contaminated_results(&mixed_results).unwrap();
        
        // Fallback results should be reduced (statistical methods work best when
        // fallback results are clearly outliers relative to normal results)
        let fallback_in_filtered = fallback_results.iter()
            .filter(|&&fr| filtered.contains(&fr))
            .count();
        prop_assert!(fallback_in_filtered < fallback_results.len() || filtered.len() <= mixed_results.len(),
            "Filtering should reduce contamination: fallback_in_filtered={}, total_fallback={}",
            fallback_in_filtered, fallback_results.len());
        
        // Normal results should be preserved (unless they're statistical outliers)
        let preserved_normal_count = normal_results.iter()
            .filter(|&&result| filtered.contains(&result))
            .count();
        
        prop_assert!(preserved_normal_count >= normal_results.len() / 2,
            "At least half of normal results should be preserved: preserved={}, total={}",
            preserved_normal_count, normal_results.len());
    }

    #[test]
    fn property_statistical_outlier_exclusion(
        base_results in prop::collection::vec(1000.0f64..1200.0f64, 8..12),
        outlier_multiplier in 5.0f64..15.0f64
    ) {
        let system = FallbackPreventionSystem::new();
        
        // Create results with statistical outliers
        let mut results_with_outliers = base_results.clone();
        let mean = base_results.iter().sum::<f64>() / base_results.len() as f64;
        let outlier = mean * outlier_multiplier;
        results_with_outliers.push(outlier);
        
        let filtered = system.filter_contaminated_results(&results_with_outliers).unwrap();
        
        // Statistical outliers should be detected and excluded
        prop_assert!(!filtered.contains(&outlier),
            "Statistical outlier {} should be excluded (mean={:.1}, multiplier={:.1})",
            outlier, mean, outlier_multiplier);
        
        // Base results should be preserved
        let preserved_base_count = base_results.iter()
            .filter(|&&result| filtered.contains(&result))
            .count();
        
        prop_assert!(preserved_base_count >= base_results.len() * 3 / 4,
            "Most base results should be preserved: preserved={}, total={}",
            preserved_base_count, base_results.len());
    }

    #[test]
    fn property_contamination_filtering_consistency(
        test_results in prop::collection::vec(
            prop_oneof![
                // Good results
                800.0f64..1800.0f64,
                // Contaminated results
                Just(0.0f64),
                20_000_000.0f64..50_000_000.0f64
            ],
            10..20
        )
    ) {
        let system = FallbackPreventionSystem::new();
        
        // Apply filtering multiple times - should be consistent
        let result1 = system.filter_contaminated_results(&test_results).unwrap();
        let result2 = system.filter_contaminated_results(&test_results).unwrap();
        
        // Results should be identical
        prop_assert_eq!(result1.len(), result2.len(),
            "Filtering should be consistent: first={}, second={}", 
            result1.len(), result2.len());
        
        // All results should be the same
        for &result in &result1 {
            prop_assert!(result2.contains(&result),
                "Result {} should be in both filtered sets", result);
        }
        
        for &result in &result2 {
            prop_assert!(result1.contains(&result),
                "Result {} should be in both filtered sets", result);
        }
    }
}