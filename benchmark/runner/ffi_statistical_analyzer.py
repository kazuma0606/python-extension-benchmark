#!/usr/bin/env python3
"""
FFI Statistical Analysis Module

Performs statistical analysis on FFI vs Pure Python performance data including
significance testing, performance distribution analysis, and outlier detection.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from benchmark.models import BenchmarkResult


@dataclass
class StatisticalTestResult:
    """Statistical test result."""
    test_name: str
    statistic: float
    p_value: float
    is_significant: bool
    confidence_level: float
    interpretation: str


@dataclass
class OutlierAnalysis:
    """Outlier detection analysis result."""
    method: str
    outlier_indices: List[int]
    outlier_values: List[float]
    threshold_lower: Optional[float]
    threshold_upper: Optional[float]
    outlier_percentage: float


@dataclass
class PerformanceDistributionAnalysis:
    """Performance distribution analysis result."""
    mean: float
    median: float
    std_dev: float
    skewness: float
    kurtosis: float
    normality_test: StatisticalTestResult
    distribution_type: str
    confidence_interval_95: Tuple[float, float]


@dataclass
class FFIStatisticalReport:
    """Comprehensive FFI statistical analysis report."""
    timestamp: datetime
    total_comparisons: int
    languages_analyzed: List[str]
    scenarios_analyzed: List[str]
    
    # Overall statistics
    overall_speedup_stats: PerformanceDistributionAnalysis
    significance_tests: List[StatisticalTestResult]
    outlier_analysis: OutlierAnalysis
    
    # Language-specific analysis
    language_comparisons: Dict[str, Dict[str, Any]]
    scenario_comparisons: Dict[str, Dict[str, Any]]
    
    # Recommendations
    statistical_recommendations: List[str]


class FFIStatisticalAnalyzer:
    """Statistical analyzer for FFI performance data."""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Args:
            confidence_level: Confidence level for statistical tests (default: 0.95)
        """
        self.confidence_level = confidence_level
        self.alpha = 1.0 - confidence_level
    
    def analyze_ffi_performance(self, results: List[BenchmarkResult]) -> FFIStatisticalReport:
        """Perform comprehensive statistical analysis of FFI performance.
        
        Args:
            results: Benchmark results
            
        Returns:
            Comprehensive statistical analysis report
        """
        # Separate Pure Python and FFI results
        python_results = {r.scenario_name: r for r in results 
                         if r.implementation_name == "python" and r.status == "SUCCESS"}
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name) and r.status == "SUCCESS"]
        
        if not python_results or not ffi_results:
            raise ValueError("Insufficient data for statistical analysis")
        
        # Calculate speedup ratios
        speedup_data = self._calculate_speedup_ratios(python_results, ffi_results)
        
        # Overall distribution analysis
        all_speedups = [item['speedup'] for item in speedup_data]
        overall_stats = self._analyze_distribution(all_speedups, "Overall FFI Speedup")
        
        # Significance testing
        significance_tests = self._perform_significance_tests(speedup_data, python_results, ffi_results)
        
        # Outlier detection
        outlier_analysis = self._detect_outliers(all_speedups)
        
        # Language-specific analysis
        language_comparisons = self._analyze_by_language(speedup_data)
        
        # Scenario-specific analysis
        scenario_comparisons = self._analyze_by_scenario(speedup_data)
        
        # Generate recommendations
        recommendations = self._generate_statistical_recommendations(
            overall_stats, significance_tests, outlier_analysis, language_comparisons
        )
        
        return FFIStatisticalReport(
            timestamp=datetime.now(),
            total_comparisons=len(speedup_data),
            languages_analyzed=list(language_comparisons.keys()),
            scenarios_analyzed=list(scenario_comparisons.keys()),
            overall_speedup_stats=overall_stats,
            significance_tests=significance_tests,
            outlier_analysis=outlier_analysis,
            language_comparisons=language_comparisons,
            scenario_comparisons=scenario_comparisons,
            statistical_recommendations=recommendations
        )
    
    def _calculate_speedup_ratios(
        self, 
        python_results: Dict[str, BenchmarkResult], 
        ffi_results: List[BenchmarkResult]
    ) -> List[Dict[str, Any]]:
        """Calculate speedup ratios with metadata."""
        speedup_data = []
        
        for ffi_result in ffi_results:
            if ffi_result.scenario_name in python_results:
                python_result = python_results[ffi_result.scenario_name]
                
                if python_result.mean_time > 0:
                    speedup = python_result.mean_time / ffi_result.mean_time
                    
                    speedup_data.append({
                        'scenario': ffi_result.scenario_name,
                        'implementation': ffi_result.implementation_name,
                        'language': self._get_language_name(ffi_result.implementation_name),
                        'speedup': speedup,
                        'python_time': python_result.mean_time,
                        'ffi_time': ffi_result.mean_time,
                        'python_std': python_result.std_dev,
                        'ffi_std': ffi_result.std_dev
                    })
        
        return speedup_data
    
    def _analyze_distribution(self, data: List[float], name: str) -> PerformanceDistributionAnalysis:
        """Analyze the distribution of performance data."""
        if not data:
            raise ValueError("Empty data for distribution analysis")
        
        data_array = np.array(data)
        
        # Basic statistics
        mean_val = np.mean(data_array)
        median_val = np.median(data_array)
        std_val = np.std(data_array, ddof=1)
        skewness = stats.skew(data_array)
        kurtosis_val = stats.kurtosis(data_array)
        
        # Confidence interval
        sem = stats.sem(data_array)
        ci_95 = stats.t.interval(self.confidence_level, len(data_array)-1, loc=mean_val, scale=sem)
        
        # Normality test
        if len(data_array) >= 8:  # Minimum sample size for Shapiro-Wilk
            shapiro_stat, shapiro_p = stats.shapiro(data_array)
            normality_test = StatisticalTestResult(
                test_name="Shapiro-Wilk Normality Test",
                statistic=shapiro_stat,
                p_value=shapiro_p,
                is_significant=shapiro_p < self.alpha,
                confidence_level=self.confidence_level,
                interpretation="Data is NOT normally distributed" if shapiro_p < self.alpha else "Data appears normally distributed"
            )
        else:
            normality_test = StatisticalTestResult(
                test_name="Shapiro-Wilk Normality Test",
                statistic=0.0,
                p_value=1.0,
                is_significant=False,
                confidence_level=self.confidence_level,
                interpretation="Insufficient data for normality test"
            )
        
        # Determine distribution type
        if abs(skewness) < 0.5:
            dist_type = "Approximately Normal"
        elif skewness > 0.5:
            dist_type = "Right-skewed (Positive skew)"
        else:
            dist_type = "Left-skewed (Negative skew)"
        
        return PerformanceDistributionAnalysis(
            mean=mean_val,
            median=median_val,
            std_dev=std_val,
            skewness=skewness,
            kurtosis=kurtosis_val,
            normality_test=normality_test,
            distribution_type=dist_type,
            confidence_interval_95=ci_95
        )
    
    def _perform_significance_tests(
        self, 
        speedup_data: List[Dict[str, Any]], 
        python_results: Dict[str, BenchmarkResult], 
        ffi_results: List[BenchmarkResult]
    ) -> List[StatisticalTestResult]:
        """Perform various significance tests."""
        tests = []
        
        # Test 1: One-sample t-test (H0: mean speedup = 1.0, no improvement)
        speedups = [item['speedup'] for item in speedup_data]
        
        if len(speedups) >= 2:
            t_stat, t_p = stats.ttest_1samp(speedups, 1.0)
            tests.append(StatisticalTestResult(
                test_name="One-sample t-test (H0: speedup = 1.0)",
                statistic=t_stat,
                p_value=t_p,
                is_significant=t_p < self.alpha,
                confidence_level=self.confidence_level,
                interpretation=f"FFI implementations are {'significantly' if t_p < self.alpha else 'not significantly'} faster than Pure Python"
            ))
        
        # Test 2: Wilcoxon signed-rank test (non-parametric alternative)
        if len(speedups) >= 6:  # Minimum for meaningful Wilcoxon test
            # Compare against baseline of 1.0 (no improvement)
            differences = np.array(speedups) - 1.0
            wilcoxon_stat, wilcoxon_p = stats.wilcoxon(differences, alternative='greater')
            tests.append(StatisticalTestResult(
                test_name="Wilcoxon Signed-Rank Test (H0: median speedup = 1.0)",
                statistic=wilcoxon_stat,
                p_value=wilcoxon_p,
                is_significant=wilcoxon_p < self.alpha,
                confidence_level=self.confidence_level,
                interpretation=f"FFI median speedup is {'significantly' if wilcoxon_p < self.alpha else 'not significantly'} greater than 1.0"
            ))
        
        # Test 3: Language comparison (ANOVA if multiple languages)
        languages = list(set(item['language'] for item in speedup_data))
        if len(languages) >= 2:
            language_groups = []
            for lang in languages:
                lang_speedups = [item['speedup'] for item in speedup_data if item['language'] == lang]
                if len(lang_speedups) >= 2:  # Need at least 2 samples per group
                    language_groups.append(lang_speedups)
            
            if len(language_groups) >= 2:
                try:
                    f_stat, f_p = stats.f_oneway(*language_groups)
                    tests.append(StatisticalTestResult(
                        test_name="One-way ANOVA (Language Comparison)",
                        statistic=f_stat,
                        p_value=f_p,
                        is_significant=f_p < self.alpha,
                        confidence_level=self.confidence_level,
                        interpretation=f"Languages show {'significant' if f_p < self.alpha else 'no significant'} differences in speedup performance"
                    ))
                except Exception as e:
                    # ANOVA failed, possibly due to insufficient variance
                    tests.append(StatisticalTestResult(
                        test_name="One-way ANOVA (Language Comparison)",
                        statistic=0.0,
                        p_value=1.0,
                        is_significant=False,
                        confidence_level=self.confidence_level,
                        interpretation=f"ANOVA test failed: {str(e)}"
                    ))
        
        return tests
    
    def _detect_outliers(self, data: List[float]) -> OutlierAnalysis:
        """Detect outliers using multiple methods."""
        if not data:
            return OutlierAnalysis("No data", [], [], None, None, 0.0)
        
        data_array = np.array(data)
        
        # Method 1: IQR method
        q1 = np.percentile(data_array, 25)
        q3 = np.percentile(data_array, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outlier_mask = (data_array < lower_bound) | (data_array > upper_bound)
        outlier_indices = np.where(outlier_mask)[0].tolist()
        outlier_values = data_array[outlier_mask].tolist()
        
        outlier_percentage = len(outlier_indices) / len(data_array) * 100
        
        return OutlierAnalysis(
            method="Interquartile Range (IQR)",
            outlier_indices=outlier_indices,
            outlier_values=outlier_values,
            threshold_lower=lower_bound,
            threshold_upper=upper_bound,
            outlier_percentage=outlier_percentage
        )
    
    def _analyze_by_language(self, speedup_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by language."""
        language_analysis = {}
        
        # Group by language
        language_groups = {}
        for item in speedup_data:
            lang = item['language']
            if lang not in language_groups:
                language_groups[lang] = []
            language_groups[lang].append(item)
        
        # Analyze each language
        for lang, items in language_groups.items():
            speedups = [item['speedup'] for item in items]
            
            if len(speedups) >= 2:
                # Distribution analysis
                dist_analysis = self._analyze_distribution(speedups, f"{lang} Speedup")
                
                # Consistency analysis (coefficient of variation)
                cv = dist_analysis.std_dev / dist_analysis.mean if dist_analysis.mean > 0 else float('inf')
                
                # Performance categories
                categories = self._categorize_performance(speedups)
                
                language_analysis[lang] = {
                    'sample_size': len(speedups),
                    'distribution_analysis': dist_analysis,
                    'coefficient_of_variation': cv,
                    'consistency_rating': self._rate_consistency(cv),
                    'performance_categories': categories,
                    'best_scenario': max(items, key=lambda x: x['speedup']),
                    'worst_scenario': min(items, key=lambda x: x['speedup']),
                    'scenarios_tested': list(set(item['scenario'] for item in items))
                }
        
        return language_analysis
    
    def _analyze_by_scenario(self, speedup_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by scenario."""
        scenario_analysis = {}
        
        # Group by scenario
        scenario_groups = {}
        for item in speedup_data:
            scenario = item['scenario']
            if scenario not in scenario_groups:
                scenario_groups[scenario] = []
            scenario_groups[scenario].append(item)
        
        # Analyze each scenario
        for scenario, items in scenario_groups.items():
            speedups = [item['speedup'] for item in items]
            
            if len(speedups) >= 2:
                # Distribution analysis
                dist_analysis = self._analyze_distribution(speedups, f"{scenario} Speedup")
                
                # Language effectiveness for this scenario
                lang_effectiveness = {}
                for item in items:
                    lang_effectiveness[item['language']] = item['speedup']
                
                # Best and worst languages for this scenario
                best_lang = max(items, key=lambda x: x['speedup'])
                worst_lang = min(items, key=lambda x: x['speedup'])
                
                scenario_analysis[scenario] = {
                    'languages_tested': len(items),
                    'distribution_analysis': dist_analysis,
                    'language_effectiveness': lang_effectiveness,
                    'best_language': {
                        'language': best_lang['language'],
                        'implementation': best_lang['implementation'],
                        'speedup': best_lang['speedup']
                    },
                    'worst_language': {
                        'language': worst_lang['language'],
                        'implementation': worst_lang['implementation'],
                        'speedup': worst_lang['speedup']
                    },
                    'speedup_range': max(speedups) - min(speedups)
                }
        
        return scenario_analysis
    
    def _categorize_performance(self, speedups: List[float]) -> Dict[str, int]:
        """Categorize performance levels."""
        categories = {
            'Exceptional (20x+)': len([s for s in speedups if s >= 20.0]),
            'Excellent (10-20x)': len([s for s in speedups if 10.0 <= s < 20.0]),
            'Very Good (5-10x)': len([s for s in speedups if 5.0 <= s < 10.0]),
            'Good (2-5x)': len([s for s in speedups if 2.0 <= s < 5.0]),
            'Moderate (1.1-2x)': len([s for s in speedups if 1.1 <= s < 2.0]),
            'Similar (0.9-1.1x)': len([s for s in speedups if 0.9 <= s < 1.1]),
            'Slower (<0.9x)': len([s for s in speedups if s < 0.9])
        }
        return categories
    
    def _rate_consistency(self, coefficient_of_variation: float) -> str:
        """Rate consistency based on coefficient of variation."""
        if coefficient_of_variation <= 0.1:
            return "Excellent (Very Consistent)"
        elif coefficient_of_variation <= 0.2:
            return "Good (Consistent)"
        elif coefficient_of_variation <= 0.3:
            return "Moderate (Somewhat Variable)"
        elif coefficient_of_variation <= 0.5:
            return "Poor (Variable)"
        else:
            return "Very Poor (Highly Variable)"
    
    def _generate_statistical_recommendations(
        self,
        overall_stats: PerformanceDistributionAnalysis,
        significance_tests: List[StatisticalTestResult],
        outlier_analysis: OutlierAnalysis,
        language_comparisons: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate statistical recommendations based on analysis."""
        recommendations = []
        
        # Overall performance recommendation
        if overall_stats.mean > 5.0:
            recommendations.append(f"FFI implementations show excellent performance with mean speedup of {overall_stats.mean:.1f}x")
        elif overall_stats.mean > 2.0:
            recommendations.append(f"FFI implementations show good performance with mean speedup of {overall_stats.mean:.1f}x")
        else:
            recommendations.append(f"FFI implementations show moderate performance with mean speedup of {overall_stats.mean:.1f}x")
        
        # Statistical significance recommendation
        significant_tests = [t for t in significance_tests if t.is_significant]
        if significant_tests:
            recommendations.append(f"Performance improvements are statistically significant ({len(significant_tests)}/{len(significance_tests)} tests)")
        else:
            recommendations.append("Performance improvements may not be statistically significant - consider larger sample sizes")
        
        # Distribution recommendation
        if overall_stats.distribution_type == "Right-skewed (Positive skew)":
            recommendations.append("Performance distribution is right-skewed - some implementations show exceptional performance")
        elif overall_stats.distribution_type == "Left-skewed (Negative skew)":
            recommendations.append("Performance distribution is left-skewed - most implementations perform well with few underperformers")
        
        # Outlier recommendation
        if outlier_analysis.outlier_percentage > 10:
            recommendations.append(f"High outlier rate ({outlier_analysis.outlier_percentage:.1f}%) - investigate extreme performance cases")
        elif outlier_analysis.outlier_percentage > 5:
            recommendations.append(f"Moderate outlier rate ({outlier_analysis.outlier_percentage:.1f}%) - some implementations show unusual performance")
        
        # Language-specific recommendations
        if language_comparisons:
            # Find most consistent language
            most_consistent = min(language_comparisons.items(), 
                                key=lambda x: x[1]['coefficient_of_variation'] if x[1]['coefficient_of_variation'] != float('inf') else 1000)
            recommendations.append(f"Most consistent language: {most_consistent[0]} (CV: {most_consistent[1]['coefficient_of_variation']:.3f})")
            
            # Find best performing language
            best_performing = max(language_comparisons.items(), 
                                key=lambda x: x[1]['distribution_analysis'].mean)
            recommendations.append(f"Best performing language: {best_performing[0]} (mean: {best_performing[1]['distribution_analysis'].mean:.1f}x)")
        
        return recommendations
    
    def _is_ffi_implementation(self, impl_name: str) -> bool:
        """Check if implementation is FFI-based or extension-based (treated as equivalent)."""
        ffi_implementations = {
            "c_ffi", "cpp_ffi", "numpy_ffi", "cython_ffi", "rust_ffi",
            "fortran_ffi", "julia_ffi", "go_ffi", "zig_ffi", "nim_ffi", "kotlin_ffi"
        }
        extension_implementations = {
            "c_ext", "cpp_ext", "numpy_impl", "cython_ext", "rust_ext",
            "fortran_ext", "julia_ext", "go_ext", "zig_ext", "nim_ext", "kotlin_ext"
        }
        return impl_name in ffi_implementations or impl_name in extension_implementations
    
    def _get_language_name(self, impl_name: str) -> str:
        """Get language name from implementation name."""
        language_map = {
            # FFI implementations
            "c_ffi": "C",
            "cpp_ffi": "C++",
            "numpy_ffi": "NumPy",
            "cython_ffi": "Cython",
            "rust_ffi": "Rust",
            "fortran_ffi": "Fortran",
            "julia_ffi": "Julia",
            "go_ffi": "Go",
            "zig_ffi": "Zig",
            "nim_ffi": "Nim",
            "kotlin_ffi": "Kotlin",
            # Extension implementations
            "c_ext": "C",
            "cpp_ext": "C++",
            "numpy_impl": "NumPy",
            "cython_ext": "Cython",
            "rust_ext": "Rust",
            "fortran_ext": "Fortran",
            "julia_ext": "Julia",
            "go_ext": "Go",
            "zig_ext": "Zig",
            "nim_ext": "Nim",
            "kotlin_ext": "Kotlin"
        }
        return language_map.get(impl_name, "Unknown")


def main():
    """Test statistical analysis functionality."""
    print("FFI Statistical Analyzer module loaded successfully")


if __name__ == "__main__":
    main()