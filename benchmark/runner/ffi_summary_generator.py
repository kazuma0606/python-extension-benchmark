#!/usr/bin/env python3
"""
FFI Summary Report Generator

Generates comprehensive benchmark_results_summary_FFI.md report combining
performance analysis, statistical insights, visualizations, and technology recommendations.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from benchmark.models import BenchmarkResult
from benchmark.runner.ffi_visualizer import FFIVisualizer
from benchmark.runner.ffi_statistical_analyzer import FFIStatisticalAnalyzer
from benchmark.runner.ffi_technology_advisor import FFITechnologyAdvisor, UseCase, DevelopmentComplexity


class FFISummaryGenerator:
    """Generates comprehensive FFI benchmark summary reports."""
    
    def __init__(self, output_dir: str = "benchmark/results"):
        """
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize analysis components
        self.visualizer = FFIVisualizer()
        self.statistical_analyzer = FFIStatisticalAnalyzer()
        self.technology_advisor = FFITechnologyAdvisor()
    
    def generate_comprehensive_ffi_summary(
        self,
        results: List[BenchmarkResult],
        filename: str = "benchmark_results_summary_FFI.md"
    ) -> str:
        """Generate comprehensive FFI benchmark summary report.
        
        Args:
            results: Benchmark results
            filename: Output filename
            
        Returns:
            Path to generated report
        """
        print("🔄 Generating comprehensive FFI summary report...")
        
        # Perform analyses
        print("  📊 Running statistical analysis...")
        statistical_report = self.statistical_analyzer.analyze_ffi_performance(results)
        
        print("  🎯 Generating technology recommendations...")
        technology_matrix = self.technology_advisor.generate_technology_matrix(results)
        
        print("  📈 Creating visualizations...")
        speedup_chart = self.visualizer.generate_speedup_comparison_chart(results)
        distribution_chart = self.visualizer.generate_performance_distribution_chart(results)
        characteristics_chart = self.visualizer.generate_language_characteristics_chart(results)
        
        # Generate report content
        print("  📝 Generating report content...")
        report_content = self._generate_report_content(
            results, statistical_report, technology_matrix,
            speedup_chart, distribution_chart, characteristics_chart
        )
        
        # Write report
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ FFI summary report generated: {output_path}")
        return str(output_path)
    
    def _generate_report_content(
        self,
        results: List[BenchmarkResult],
        statistical_report,
        technology_matrix,
        speedup_chart: str,
        distribution_chart: str,
        characteristics_chart: str
    ) -> str:
        """Generate the complete report content."""
        
        # Calculate basic statistics
        python_results = [r for r in results if r.implementation_name == "python" and r.status == "SUCCESS"]
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name) and r.status == "SUCCESS"]
        
        total_scenarios = len(set(r.scenario_name for r in results))
        total_ffi_implementations = len(set(r.implementation_name for r in ffi_results))
        
        # Generate report sections
        report = []
        
        # Header and metadata
        report.append(self._generate_header(results, total_scenarios, total_ffi_implementations))
        
        # Executive summary
        report.append(self._generate_executive_summary(statistical_report, technology_matrix))
        
        # Performance analysis
        report.append(self._generate_performance_analysis(statistical_report, speedup_chart, distribution_chart))
        
        # Language comparison
        report.append(self._generate_language_comparison(statistical_report, characteristics_chart))
        
        # Statistical insights
        report.append(self._generate_statistical_insights(statistical_report))
        
        # Technology selection guide
        report.append(self._generate_technology_selection_guide(technology_matrix))
        
        # Implementation recommendations
        report.append(self._generate_implementation_recommendations(technology_matrix))
        
        # Detailed results
        report.append(self._generate_detailed_results(results, statistical_report))
        
        # Limitations and considerations
        report.append(self._generate_limitations_and_considerations(technology_matrix))
        
        # Appendices
        report.append(self._generate_appendices(results, statistical_report))
        
        return '\n\n'.join(report)
    
    def _generate_header(self, results: List[BenchmarkResult], total_scenarios: int, total_ffi_implementations: int) -> str:
        """Generate report header and metadata."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        environment = results[0].environment if results else None
        
        return f"""# FFI Benchmark Results Summary

## Report Metadata

- **Generated**: {timestamp}
- **Total Scenarios**: {total_scenarios}
- **FFI Implementations**: {total_ffi_implementations}
- **Pure Python Baseline**: Included
- **Environment**: {environment.os if environment else 'Unknown'} | {environment.cpu if environment else 'Unknown'} | Python {environment.python_version if environment else 'Unknown'}
- **Docker**: {'Yes' if environment and environment.docker else 'No'}

## Overview

This report presents a comprehensive analysis of Foreign Function Interface (FFI) implementations compared to Pure Python performance across multiple programming languages and computational scenarios. The analysis includes statistical significance testing, performance distribution analysis, and practical technology selection guidance."""
    
    def _generate_executive_summary(self, statistical_report, technology_matrix) -> str:
        """Generate executive summary."""
        avg_speedup = statistical_report.overall_speedup_stats.mean
        best_language = technology_matrix.performance_ranking[0] if technology_matrix.performance_ranking else ("Unknown", 0.0)
        most_reliable = technology_matrix.reliability_ranking[0] if technology_matrix.reliability_ranking else ("Unknown", 0.0)
        
        significant_tests = len([t for t in statistical_report.significance_tests if t.is_significant])
        total_tests = len(statistical_report.significance_tests)
        
        return f"""## Executive Summary

### Key Findings

🚀 **Performance Impact**: FFI implementations achieve an average speedup of **{avg_speedup:.1f}x** over Pure Python, with statistical significance confirmed in {significant_tests}/{total_tests} tests.

🏆 **Top Performer**: **{best_language[0]}** leads with an average speedup of **{best_language[1]:.1f}x**, demonstrating exceptional performance gains.

🛡️ **Most Reliable**: **{most_reliable[0]}** shows the highest reliability score, combining performance with consistency.

📊 **Distribution**: Performance improvements follow a {statistical_report.overall_speedup_stats.distribution_type.lower()} distribution, indicating {self._interpret_distribution(statistical_report.overall_speedup_stats.distribution_type)}.

### Strategic Recommendations

1. **For Production Systems**: Consider {best_language[0]} for maximum performance, with careful attention to development complexity
2. **For Rapid Prototyping**: Choose languages with low development complexity while maintaining reasonable performance
3. **For Scientific Computing**: Leverage specialized languages like Fortran or NumPy for domain-specific optimizations
4. **For Cross-Platform**: Prioritize languages with excellent cross-platform support and mature toolchains

### Investment Justification

FFI implementations provide substantial performance improvements that can justify the additional development complexity for:
- Performance-critical applications
- High-throughput data processing
- Real-time systems
- Scientific computing workloads"""
    
    def _generate_performance_analysis(self, statistical_report, speedup_chart: str, distribution_chart: str) -> str:
        """Generate performance analysis section."""
        stats = statistical_report.overall_speedup_stats
        
        performance_categories = {
            'Exceptional (20x+)': 0,
            'Excellent (10-20x)': 0,
            'Very Good (5-10x)': 0,
            'Good (2-5x)': 0,
            'Moderate (1.1-2x)': 0,
            'Similar (0.9-1.1x)': 0,
            'Slower (<0.9x)': 0
        }
        
        # Calculate categories from language comparisons
        for lang_data in statistical_report.language_comparisons.values():
            if 'performance_categories' in lang_data:
                for category, count in lang_data['performance_categories'].items():
                    if category in performance_categories:
                        performance_categories[category] += count
        
        category_table = '\n'.join([
            f"| {category} | {count} |" 
            for category, count in performance_categories.items()
        ])
        
        return f"""## Performance Analysis

### Overall Performance Statistics

| Metric | Value |
|--------|-------|
| **Mean Speedup** | {stats.mean:.2f}x |
| **Median Speedup** | {stats.median:.2f}x |
| **Standard Deviation** | {stats.std_dev:.2f} |
| **95% Confidence Interval** | {stats.confidence_interval_95[0]:.2f}x - {stats.confidence_interval_95[1]:.2f}x |
| **Distribution Type** | {stats.distribution_type} |
| **Skewness** | {stats.skewness:.3f} |

### Performance Categories

| Category | Count |
|----------|-------|
{category_table}

### Visualization

![FFI Speedup Comparison]({os.path.basename(speedup_chart) if speedup_chart else 'chart_not_available.png'})

![Performance Distribution Analysis]({os.path.basename(distribution_chart) if distribution_chart else 'chart_not_available.png'})

### Performance Insights

- **{self._get_performance_insight(stats.mean)}**
- **Distribution**: {self._interpret_distribution(stats.distribution_type)}
- **Consistency**: {self._interpret_consistency(stats.std_dev, stats.mean)}
- **Reliability**: {self._interpret_confidence_interval(stats.confidence_interval_95)}"""
    
    def _generate_language_comparison(self, statistical_report, characteristics_chart: str) -> str:
        """Generate language comparison section."""
        
        # Create language comparison table
        language_rows = []
        for lang, analysis in statistical_report.language_comparisons.items():
            dist = analysis['distribution_analysis']
            cv = analysis['coefficient_of_variation']
            scenarios = analysis['scenarios_tested']
            
            language_rows.append(
                f"| {lang} | {dist.mean:.2f}x | {cv:.3f} | {scenarios} | {self._rate_consistency_simple(cv)} |"
            )
        
        language_table = '\n'.join(language_rows)
        
        return f"""## Language-Specific Analysis

### Performance Comparison by Language

| Language | Avg Speedup | Consistency (CV) | Scenarios | Rating |
|----------|-------------|------------------|-----------|---------|
{language_table}

### Language Characteristics

![Language Performance Characteristics]({os.path.basename(characteristics_chart) if characteristics_chart else 'chart_not_available.png'})

### Language Insights

{self._generate_language_insights(statistical_report.language_comparisons)}"""
    
    def _generate_statistical_insights(self, statistical_report) -> str:
        """Generate statistical insights section."""
        
        # Significance test results
        test_results = []
        for test in statistical_report.significance_tests:
            significance = "✅ Significant" if test.is_significant else "❌ Not Significant"
            test_results.append(f"- **{test.test_name}**: {significance} (p = {test.p_value:.4f})")
        
        test_results_text = '\n'.join(test_results)
        
        # Outlier analysis
        outlier_info = statistical_report.outlier_analysis
        
        return f"""## Statistical Analysis

### Significance Testing

{test_results_text}

### Outlier Analysis

- **Method**: {outlier_info.method}
- **Outliers Detected**: {len(outlier_info.outlier_indices)} ({outlier_info.outlier_percentage:.1f}%)
- **Threshold Range**: {outlier_info.threshold_lower:.2f}x - {outlier_info.threshold_upper:.2f}x

{self._interpret_outliers(outlier_info)}

### Statistical Recommendations

{chr(10).join([f"- {rec}" for rec in statistical_report.statistical_recommendations])}

### Normality Assessment

- **Test**: {statistical_report.overall_speedup_stats.normality_test.test_name}
- **Result**: {statistical_report.overall_speedup_stats.normality_test.interpretation}
- **P-value**: {statistical_report.overall_speedup_stats.normality_test.p_value:.4f}"""
    
    def _generate_technology_selection_guide(self, technology_matrix) -> str:
        """Generate technology selection guide."""
        
        # Performance ranking
        perf_ranking = []
        for i, (lang, speedup) in enumerate(technology_matrix.performance_ranking[:5], 1):
            perf_ranking.append(f"{i}. **{lang}** ({speedup:.1f}x)")
        
        # Ease of use ranking
        ease_ranking = []
        for i, (lang, complexity) in enumerate(technology_matrix.ease_of_use_ranking[:5], 1):
            ease_ranking.append(f"{i}. **{lang}** ({complexity.value})")
        
        # Use case recommendations
        use_case_recs = []
        for use_case, rec in technology_matrix.use_case_recommendations.items():
            use_case_recs.append(f"""
#### {use_case.value}

- **Primary Recommendation**: {rec.primary_recommendation}
- **Alternatives**: {', '.join(rec.alternative_options) if rec.alternative_options else 'None'}
- **Rationale**: {rec.rationale}
- **Expected Performance**: {rec.performance_expectation}
- **Development Effort**: {rec.development_effort}
- **Risk Assessment**: {rec.risk_assessment}""")
        
        return f"""## Technology Selection Guide

### Performance Rankings

{chr(10).join(perf_ranking)}

### Ease of Use Rankings

{chr(10).join(ease_ranking)}

### Use Case Recommendations

{''.join(use_case_recs)}

### Decision Framework

{self._format_decision_framework(technology_matrix.decision_framework)}"""
    
    def _generate_implementation_recommendations(self, technology_matrix) -> str:
        """Generate implementation recommendations."""
        
        # Technology profiles summary
        profile_summaries = []
        for lang, profile in technology_matrix.technology_profiles.items():
            profile_summaries.append(f"""
### {lang}

- **Performance**: {profile.avg_speedup:.1f}x average speedup
- **Consistency**: {self._rate_consistency_simple(profile.speedup_consistency)}
- **Development Complexity**: {profile.development_complexity.value}
- **Setup Time**: {profile.setup_time_hours:.1f} hours
- **Memory Safety**: {'✅' if profile.memory_safety else '❌'}
- **Cross-Platform**: {profile.cross_platform_support}

**Best For**: {', '.join([uc.value for uc in profile.best_use_cases])}

**Avoid For**: {', '.join([uc.value for uc in profile.avoid_for]) if profile.avoid_for else 'None'}

**Key Limitations**:
{chr(10).join([f"- {limitation}" for limitation in profile.limitations])}""")
        
        return f"""## Implementation Recommendations

### Technology Profiles

{''.join(profile_summaries)}

### General Considerations

{chr(10).join([f"- {consideration}" for consideration in technology_matrix.general_considerations])}

### Platform-Specific Notes

{self._format_platform_notes(technology_matrix.platform_specific_notes)}"""
    
    def _generate_detailed_results(self, results: List[BenchmarkResult], statistical_report) -> str:
        """Generate detailed results section."""
        
        # Scenario-wise breakdown
        scenario_breakdown = []
        for scenario, analysis in statistical_report.scenario_comparisons.items():
            best_lang = analysis['best_language']
            worst_lang = analysis['worst_language']
            
            scenario_breakdown.append(f"""
#### {scenario}

- **Languages Tested**: {analysis['languages_tested']}
- **Best Performance**: {best_lang['language']} ({best_lang['speedup']:.1f}x)
- **Worst Performance**: {worst_lang['language']} ({worst_lang['speedup']:.1f}x)
- **Performance Range**: {analysis['speedup_range']:.1f}x
- **Average**: {analysis['distribution_analysis'].mean:.1f}x""")
        
        return f"""## Detailed Results

### Scenario-wise Performance Breakdown

{''.join(scenario_breakdown)}

### Raw Data Summary

- **Total Benchmark Runs**: {len(results)}
- **Successful Runs**: {len([r for r in results if r.status == "SUCCESS"])}
- **Failed Runs**: {len([r for r in results if r.status != "SUCCESS"])}
- **Scenarios Covered**: {len(set(r.scenario_name for r in results))}
- **Implementations Tested**: {len(set(r.implementation_name for r in results))}"""
    
    def _generate_limitations_and_considerations(self, technology_matrix) -> str:
        """Generate limitations and considerations section."""
        
        return f"""## Limitations and Considerations

### Benchmark Limitations

- **Environment Dependency**: Results are specific to the test environment and may vary on different hardware/software configurations
- **Workload Specificity**: Performance characteristics may differ significantly for other types of computational workloads
- **Implementation Quality**: FFI implementations are proof-of-concept and may not represent optimally tuned production code
- **Measurement Overhead**: FFI call overhead and data conversion costs are included in measurements

### FFI Implementation Considerations

- **Development Complexity**: FFI implementations require additional build infrastructure and cross-platform considerations
- **Maintenance Burden**: Multiple language implementations increase maintenance complexity and testing requirements
- **Debugging Challenges**: Debugging across language boundaries can be more difficult than pure Python debugging
- **Dependency Management**: Each FFI implementation introduces additional runtime and build-time dependencies

### Production Deployment Considerations

- **Build Complexity**: FFI implementations require compilation steps and platform-specific build configurations
- **Distribution Challenges**: Shared libraries must be distributed and loaded correctly across target platforms
- **Version Compatibility**: Language runtime versions and ABI compatibility must be managed carefully
- **Security Implications**: FFI implementations may introduce additional attack surfaces and security considerations

### Recommendations for Production Use

1. **Prototype First**: Start with Pure Python and identify actual performance bottlenecks before implementing FFI solutions
2. **Measure Carefully**: Validate that FFI overhead doesn't negate performance gains for your specific use case
3. **Plan for Maintenance**: Consider the long-term maintenance cost of multiple language implementations
4. **Test Thoroughly**: Implement comprehensive testing across all target platforms and configurations
5. **Document Dependencies**: Clearly document all build and runtime dependencies for each FFI implementation"""
    
    def _generate_appendices(self, results: List[BenchmarkResult], statistical_report) -> str:
        """Generate appendices section."""
        
        # Environment details
        env = results[0].environment if results else None
        env_details = f"""
- **Operating System**: {env.os if env else 'Unknown'}
- **CPU**: {env.cpu if env else 'Unknown'}
- **Memory**: {env.memory_gb if env else 'Unknown'} GB
- **Python Version**: {env.python_version if env else 'Unknown'}
- **Docker Environment**: {'Yes' if env and env.docker else 'No'}""" if env else "Environment information not available"
        
        # Methodology
        methodology = """
1. **Baseline Establishment**: Pure Python implementations serve as the performance baseline (1.0x)
2. **FFI Implementation**: Each language provides equivalent functionality through shared library FFI calls
3. **Measurement Protocol**: 100 iterations per scenario with statistical analysis of execution times
4. **Data Validation**: Output correctness verified against Pure Python baseline for all implementations
5. **Statistical Analysis**: Significance testing, distribution analysis, and outlier detection performed
6. **Environment Control**: All measurements performed in controlled environment with consistent resource allocation"""
        
        return f"""## Appendices

### Appendix A: Test Environment

{env_details}

### Appendix B: Methodology

{methodology}

### Appendix C: Statistical Methods

- **Significance Testing**: One-sample t-test and Wilcoxon signed-rank test for performance improvement validation
- **Distribution Analysis**: Shapiro-Wilk normality test, skewness and kurtosis analysis
- **Outlier Detection**: Interquartile Range (IQR) method with 1.5×IQR threshold
- **Confidence Intervals**: 95% confidence intervals using t-distribution
- **Language Comparison**: One-way ANOVA for multi-group comparison when applicable

### Appendix D: Implementation Notes

- **FFI Interface**: All implementations use ctypes for Python-to-native library integration
- **Memory Management**: Automatic memory cleanup implemented for all FFI calls
- **Error Handling**: Comprehensive error handling with graceful degradation for failed implementations
- **Build Systems**: Language-appropriate build systems (Make, Cargo, etc.) with unified build scripts

---

*Report generated by FFI Benchmark Analysis System*
*For questions or issues, please refer to the project documentation*"""
    
    # Helper methods for formatting and interpretation
    
    def _interpret_distribution(self, distribution_type: str) -> str:
        """Interpret distribution type."""
        if "Right-skewed" in distribution_type:
            return "some implementations achieve exceptional performance while most show moderate improvements"
        elif "Left-skewed" in distribution_type:
            return "most implementations perform well with few underperformers"
        else:
            return "performance improvements are relatively evenly distributed"
    
    def _interpret_consistency(self, std_dev: float, mean: float) -> str:
        """Interpret performance consistency."""
        cv = std_dev / mean if mean > 0 else float('inf')
        if cv < 0.2:
            return "Performance is highly consistent across implementations"
        elif cv < 0.5:
            return "Performance shows moderate variability"
        else:
            return "Performance is highly variable - careful selection recommended"
    
    def _interpret_confidence_interval(self, ci: tuple) -> str:
        """Interpret confidence interval."""
        width = ci[1] - ci[0]
        if width < 1.0:
            return f"Narrow confidence interval ({ci[0]:.2f}x - {ci[1]:.2f}x) indicates reliable performance estimates"
        else:
            return f"Wide confidence interval ({ci[0]:.2f}x - {ci[1]:.2f}x) suggests high variability"
    
    def _interpret_outliers(self, outlier_analysis) -> str:
        """Interpret outlier analysis."""
        if outlier_analysis.outlier_percentage > 15:
            return "**High outlier rate suggests investigating extreme cases for optimization opportunities or implementation issues.**"
        elif outlier_analysis.outlier_percentage > 5:
            return "**Moderate outlier rate is normal but worth investigating for insights.**"
        else:
            return "**Low outlier rate indicates consistent performance across implementations.**"
    
    def _get_performance_insight(self, mean_speedup: float) -> str:
        """Get performance insight based on mean speedup."""
        if mean_speedup >= 10:
            return "Exceptional performance gains justify FFI implementation for most use cases"
        elif mean_speedup >= 5:
            return "Excellent performance gains make FFI attractive for performance-critical applications"
        elif mean_speedup >= 2:
            return "Good performance improvements can justify FFI for bottleneck scenarios"
        else:
            return "Moderate performance gains require careful cost-benefit analysis"
    
    def _rate_consistency_simple(self, cv: float) -> str:
        """Simple consistency rating."""
        if cv <= 0.1:
            return "Excellent"
        elif cv <= 0.2:
            return "Good"
        elif cv <= 0.3:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_language_insights(self, language_comparisons: Dict) -> str:
        """Generate language-specific insights."""
        insights = []
        
        for lang, analysis in language_comparisons.items():
            dist = analysis['distribution_analysis']
            cv = analysis['coefficient_of_variation']
            
            if dist.mean >= 10:
                insights.append(f"- **{lang}**: Exceptional performer with {dist.mean:.1f}x average speedup")
            elif cv <= 0.1:
                insights.append(f"- **{lang}**: Highly consistent performance (CV: {cv:.3f})")
            elif dist.mean >= 5:
                insights.append(f"- **{lang}**: Strong performer with {dist.mean:.1f}x speedup")
        
        return '\n'.join(insights) if insights else "- No specific language insights available"
    
    def _format_decision_framework(self, framework: Dict) -> str:
        """Format decision framework."""
        criteria_text = []
        for criterion, details in framework['selection_criteria'].items():
            criteria_text.append(f"""
**{criterion.replace('_', ' ').title()}**
- {details['description']}
- Approach: {details['recommended_approach']}
- Key Metrics: {', '.join(details['key_metrics'])}""")
        
        return f"""
#### Selection Criteria

{''.join(criteria_text)}

#### Decision Process

{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(framework['decision_tree'].values())])}

#### Red Flags

{chr(10).join([f"- {flag}" for flag in framework['red_flags']])}"""
    
    def _format_platform_notes(self, platform_notes: Dict) -> str:
        """Format platform-specific notes."""
        formatted_notes = []
        for platform, notes in platform_notes.items():
            formatted_notes.append(f"""
#### {platform}

{chr(10).join([f"- {note}" for note in notes])}""")
        
        return ''.join(formatted_notes)
    
    def _is_ffi_implementation(self, impl_name: str) -> bool:
        """Check if implementation is FFI-based."""
        ffi_implementations = {
            "c_ffi", "cpp_ffi", "numpy_ffi", "cython_ffi", "rust_ffi",
            "fortran_ffi", "julia_ffi", "go_ffi", "zig_ffi", "nim_ffi", "kotlin_ffi"
        }
        return impl_name in ffi_implementations


def main():
    """Test FFI summary generator."""
    print("FFI Summary Generator module loaded successfully")


if __name__ == "__main__":
    main()