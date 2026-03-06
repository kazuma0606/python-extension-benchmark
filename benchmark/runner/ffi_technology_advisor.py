#!/usr/bin/env python3
"""
FFI Technology Selection Advisor

Provides technology selection guidance based on performance analysis,
development cost considerations, and use case requirements.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from benchmark.models import BenchmarkResult
from benchmark.runner.ffi_statistical_analyzer import FFIStatisticalAnalyzer, FFIStatisticalReport


class DevelopmentComplexity(Enum):
    """Development complexity levels."""
    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


class UseCase(Enum):
    """Common use cases for FFI implementations."""
    PROTOTYPING = "Prototyping"
    PRODUCTION_PERFORMANCE = "Production Performance"
    EXISTING_LIBRARY_INTEGRATION = "Existing Library Integration"
    SCIENTIFIC_COMPUTING = "Scientific Computing"
    REAL_TIME_PROCESSING = "Real-time Processing"
    CROSS_PLATFORM_DEPLOYMENT = "Cross-platform Deployment"
    MAINTENANCE_OPTIMIZATION = "Maintenance Optimization"


@dataclass
class TechnologyProfile:
    """Technology profile for FFI implementation."""
    language: str
    implementation_name: str
    
    # Performance characteristics
    avg_speedup: float
    speedup_consistency: float  # Coefficient of variation
    success_rate: float
    
    # Development characteristics
    development_complexity: DevelopmentComplexity
    setup_time_hours: float
    maintenance_effort: DevelopmentComplexity
    
    # Ecosystem characteristics
    library_ecosystem: str  # Rich, Moderate, Limited
    community_support: str  # Excellent, Good, Limited
    documentation_quality: str  # Excellent, Good, Fair, Poor
    
    # Technical characteristics
    memory_safety: bool
    cross_platform_support: str  # Excellent, Good, Limited
    debugging_difficulty: DevelopmentComplexity
    
    # Limitations and considerations
    limitations: List[str]
    best_use_cases: List[UseCase]
    avoid_for: List[UseCase]


@dataclass
class TechnologyRecommendation:
    """Technology recommendation with rationale."""
    use_case: UseCase
    primary_recommendation: str
    alternative_options: List[str]
    rationale: str
    performance_expectation: str
    development_effort: str
    risk_assessment: str
    implementation_notes: List[str]


@dataclass
class FFITechnologyMatrix:
    """Comprehensive FFI technology selection matrix."""
    timestamp: datetime
    analysis_summary: str
    
    # Technology profiles
    technology_profiles: Dict[str, TechnologyProfile]
    
    # Use case recommendations
    use_case_recommendations: Dict[UseCase, TechnologyRecommendation]
    
    # Comparative analysis
    performance_ranking: List[Tuple[str, float]]  # (language, avg_speedup)
    ease_of_use_ranking: List[Tuple[str, DevelopmentComplexity]]
    reliability_ranking: List[Tuple[str, float]]  # (language, success_rate)
    
    # Decision framework
    decision_framework: Dict[str, Any]
    
    # Warnings and considerations
    general_considerations: List[str]
    platform_specific_notes: Dict[str, List[str]]


class FFITechnologyAdvisor:
    """FFI technology selection advisor."""
    
    def __init__(self):
        """Initialize the technology advisor."""
        self.statistical_analyzer = FFIStatisticalAnalyzer()
        
        # Predefined technology characteristics (based on general knowledge)
        self.technology_characteristics = {
            "C": {
                "development_complexity": DevelopmentComplexity.HIGH,
                "setup_time_hours": 4.0,
                "maintenance_effort": DevelopmentComplexity.HIGH,
                "library_ecosystem": "Rich",
                "community_support": "Excellent",
                "documentation_quality": "Good",
                "memory_safety": False,
                "cross_platform_support": "Excellent",
                "debugging_difficulty": DevelopmentComplexity.HIGH,
                "limitations": [
                    "Manual memory management required",
                    "No built-in safety features",
                    "Verbose syntax for complex operations",
                    "Requires careful pointer handling"
                ],
                "best_use_cases": [UseCase.PRODUCTION_PERFORMANCE, UseCase.REAL_TIME_PROCESSING, UseCase.EXISTING_LIBRARY_INTEGRATION],
                "avoid_for": [UseCase.PROTOTYPING]
            },
            "C++": {
                "development_complexity": DevelopmentComplexity.HIGH,
                "setup_time_hours": 5.0,
                "maintenance_effort": DevelopmentComplexity.HIGH,
                "library_ecosystem": "Rich",
                "community_support": "Excellent",
                "documentation_quality": "Good",
                "memory_safety": False,
                "cross_platform_support": "Excellent",
                "debugging_difficulty": DevelopmentComplexity.HIGH,
                "limitations": [
                    "Complex language with many features",
                    "Manual memory management",
                    "Long compilation times",
                    "ABI compatibility issues"
                ],
                "best_use_cases": [UseCase.PRODUCTION_PERFORMANCE, UseCase.EXISTING_LIBRARY_INTEGRATION, UseCase.SCIENTIFIC_COMPUTING],
                "avoid_for": [UseCase.PROTOTYPING]
            },
            "NumPy": {
                "development_complexity": DevelopmentComplexity.LOW,
                "setup_time_hours": 1.0,
                "maintenance_effort": DevelopmentComplexity.LOW,
                "library_ecosystem": "Rich",
                "community_support": "Excellent",
                "documentation_quality": "Excellent",
                "memory_safety": True,
                "cross_platform_support": "Excellent",
                "debugging_difficulty": DevelopmentComplexity.LOW,
                "limitations": [
                    "Limited to numerical operations",
                    "Requires Cython for FFI",
                    "Array-focused operations only"
                ],
                "best_use_cases": [UseCase.SCIENTIFIC_COMPUTING, UseCase.PROTOTYPING, UseCase.MAINTENANCE_OPTIMIZATION],
                "avoid_for": [UseCase.REAL_TIME_PROCESSING]
            },
            "Cython": {
                "development_complexity": DevelopmentComplexity.MEDIUM,
                "setup_time_hours": 2.0,
                "maintenance_effort": DevelopmentComplexity.MEDIUM,
                "library_ecosystem": "Moderate",
                "community_support": "Good",
                "documentation_quality": "Good",
                "memory_safety": True,
                "cross_platform_support": "Good",
                "debugging_difficulty": DevelopmentComplexity.MEDIUM,
                "limitations": [
                    "Python-like syntax with C performance",
                    "Compilation step required",
                    "Limited debugging support"
                ],
                "best_use_cases": [UseCase.PROTOTYPING, UseCase.PRODUCTION_PERFORMANCE, UseCase.SCIENTIFIC_COMPUTING],
                "avoid_for": []
            },
            "Rust": {
                "development_complexity": DevelopmentComplexity.HIGH,
                "setup_time_hours": 6.0,
                "maintenance_effort": DevelopmentComplexity.MEDIUM,
                "library_ecosystem": "Moderate",
                "community_support": "Good",
                "documentation_quality": "Excellent",
                "memory_safety": True,
                "cross_platform_support": "Excellent",
                "debugging_difficulty": DevelopmentComplexity.MEDIUM,
                "limitations": [
                    "Steep learning curve",
                    "Strict borrow checker",
                    "Longer development time initially"
                ],
                "best_use_cases": [UseCase.PRODUCTION_PERFORMANCE, UseCase.CROSS_PLATFORM_DEPLOYMENT, UseCase.REAL_TIME_PROCESSING],
                "avoid_for": [UseCase.PROTOTYPING]
            },
            "Fortran": {
                "development_complexity": DevelopmentComplexity.MEDIUM,
                "setup_time_hours": 3.0,
                "maintenance_effort": DevelopmentComplexity.MEDIUM,
                "library_ecosystem": "Limited",
                "community_support": "Limited",
                "documentation_quality": "Fair",
                "memory_safety": False,
                "cross_platform_support": "Good",
                "debugging_difficulty": DevelopmentComplexity.MEDIUM,
                "limitations": [
                    "Specialized for numerical computing",
                    "Limited general-purpose libraries",
                    "Older language paradigms"
                ],
                "best_use_cases": [UseCase.SCIENTIFIC_COMPUTING, UseCase.EXISTING_LIBRARY_INTEGRATION],
                "avoid_for": [UseCase.PROTOTYPING, UseCase.CROSS_PLATFORM_DEPLOYMENT]
            },
            "Julia": {
                "development_complexity": DevelopmentComplexity.MEDIUM,
                "setup_time_hours": 3.0,
                "maintenance_effort": DevelopmentComplexity.MEDIUM,
                "library_ecosystem": "Moderate",
                "community_support": "Good",
                "documentation_quality": "Good",
                "memory_safety": True,
                "cross_platform_support": "Good",
                "debugging_difficulty": DevelopmentComplexity.MEDIUM,
                "limitations": [
                    "JIT compilation overhead",
                    "Large runtime dependency",
                    "Compilation complexity for FFI"
                ],
                "best_use_cases": [UseCase.SCIENTIFIC_COMPUTING, UseCase.PRODUCTION_PERFORMANCE],
                "avoid_for": [UseCase.REAL_TIME_PROCESSING, UseCase.PROTOTYPING]
            },
            "Go": {
                "development_complexity": DevelopmentComplexity.MEDIUM,
                "setup_time_hours": 2.5,
                "maintenance_effort": DevelopmentComplexity.LOW,
                "library_ecosystem": "Moderate",
                "community_support": "Good",
                "documentation_quality": "Good",
                "memory_safety": True,
                "cross_platform_support": "Excellent",
                "debugging_difficulty": DevelopmentComplexity.LOW,
                "limitations": [
                    "Garbage collection overhead",
                    "Limited control over memory layout",
                    "CGO performance overhead"
                ],
                "best_use_cases": [UseCase.CROSS_PLATFORM_DEPLOYMENT, UseCase.MAINTENANCE_OPTIMIZATION],
                "avoid_for": [UseCase.REAL_TIME_PROCESSING]
            },
            "Zig": {
                "development_complexity": DevelopmentComplexity.HIGH,
                "setup_time_hours": 4.0,
                "maintenance_effort": DevelopmentComplexity.MEDIUM,
                "library_ecosystem": "Limited",
                "community_support": "Limited",
                "documentation_quality": "Fair",
                "memory_safety": True,
                "cross_platform_support": "Excellent",
                "debugging_difficulty": DevelopmentComplexity.MEDIUM,
                "limitations": [
                    "Young language with evolving ecosystem",
                    "Limited libraries and tooling",
                    "Steep learning curve"
                ],
                "best_use_cases": [UseCase.PRODUCTION_PERFORMANCE, UseCase.REAL_TIME_PROCESSING],
                "avoid_for": [UseCase.PROTOTYPING, UseCase.EXISTING_LIBRARY_INTEGRATION]
            },
            "Nim": {
                "development_complexity": DevelopmentComplexity.MEDIUM,
                "setup_time_hours": 2.5,
                "maintenance_effort": DevelopmentComplexity.MEDIUM,
                "library_ecosystem": "Limited",
                "community_support": "Limited",
                "documentation_quality": "Fair",
                "memory_safety": True,
                "cross_platform_support": "Good",
                "debugging_difficulty": DevelopmentComplexity.MEDIUM,
                "limitations": [
                    "Small ecosystem",
                    "Limited community support",
                    "Compilation complexity"
                ],
                "best_use_cases": [UseCase.PROTOTYPING, UseCase.PRODUCTION_PERFORMANCE],
                "avoid_for": [UseCase.EXISTING_LIBRARY_INTEGRATION]
            },
            "Kotlin": {
                "development_complexity": DevelopmentComplexity.MEDIUM,
                "setup_time_hours": 3.0,
                "maintenance_effort": DevelopmentComplexity.MEDIUM,
                "library_ecosystem": "Moderate",
                "community_support": "Good",
                "documentation_quality": "Good",
                "memory_safety": True,
                "cross_platform_support": "Good",
                "debugging_difficulty": DevelopmentComplexity.MEDIUM,
                "limitations": [
                    "Large runtime overhead",
                    "JVM ecosystem dependency",
                    "Complex build system"
                ],
                "best_use_cases": [UseCase.EXISTING_LIBRARY_INTEGRATION, UseCase.CROSS_PLATFORM_DEPLOYMENT],
                "avoid_for": [UseCase.REAL_TIME_PROCESSING, UseCase.PROTOTYPING]
            }
        }
    
    def generate_technology_matrix(self, results: List[BenchmarkResult]) -> FFITechnologyMatrix:
        """Generate comprehensive FFI technology selection matrix.
        
        Args:
            results: Benchmark results
            
        Returns:
            Comprehensive technology selection matrix
        """
        # Perform statistical analysis
        statistical_report = self.statistical_analyzer.analyze_ffi_performance(results)
        
        # Generate technology profiles
        technology_profiles = self._generate_technology_profiles(statistical_report)
        
        # Generate use case recommendations
        use_case_recommendations = self._generate_use_case_recommendations(technology_profiles)
        
        # Generate rankings
        performance_ranking = self._generate_performance_ranking(technology_profiles)
        ease_of_use_ranking = self._generate_ease_of_use_ranking(technology_profiles)
        reliability_ranking = self._generate_reliability_ranking(technology_profiles)
        
        # Generate decision framework
        decision_framework = self._generate_decision_framework(technology_profiles)
        
        # Generate considerations and notes
        general_considerations = self._generate_general_considerations(statistical_report)
        platform_notes = self._generate_platform_specific_notes()
        
        return FFITechnologyMatrix(
            timestamp=datetime.now(),
            analysis_summary=self._generate_analysis_summary(statistical_report),
            technology_profiles=technology_profiles,
            use_case_recommendations=use_case_recommendations,
            performance_ranking=performance_ranking,
            ease_of_use_ranking=ease_of_use_ranking,
            reliability_ranking=reliability_ranking,
            decision_framework=decision_framework,
            general_considerations=general_considerations,
            platform_specific_notes=platform_notes
        )
    
    def _generate_technology_profiles(self, statistical_report: FFIStatisticalReport) -> Dict[str, TechnologyProfile]:
        """Generate detailed technology profiles."""
        profiles = {}
        
        for language, analysis in statistical_report.language_comparisons.items():
            if language in self.technology_characteristics:
                char = self.technology_characteristics[language]
                
                # Extract performance data
                dist_analysis = analysis['distribution_analysis']
                
                profiles[language] = TechnologyProfile(
                    language=language,
                    implementation_name=f"{language.lower()}_ffi",
                    avg_speedup=dist_analysis.mean,
                    speedup_consistency=analysis['coefficient_of_variation'],
                    success_rate=1.0,  # Assume success if in analysis
                    development_complexity=char["development_complexity"],
                    setup_time_hours=char["setup_time_hours"],
                    maintenance_effort=char["maintenance_effort"],
                    library_ecosystem=char["library_ecosystem"],
                    community_support=char["community_support"],
                    documentation_quality=char["documentation_quality"],
                    memory_safety=char["memory_safety"],
                    cross_platform_support=char["cross_platform_support"],
                    debugging_difficulty=char["debugging_difficulty"],
                    limitations=char["limitations"],
                    best_use_cases=char["best_use_cases"],
                    avoid_for=char["avoid_for"]
                )
        
        return profiles
    
    def _generate_use_case_recommendations(self, profiles: Dict[str, TechnologyProfile]) -> Dict[UseCase, TechnologyRecommendation]:
        """Generate recommendations for each use case."""
        recommendations = {}
        
        # Prototyping
        prototyping_candidates = [
            (lang, profile) for lang, profile in profiles.items()
            if UseCase.PROTOTYPING in profile.best_use_cases or UseCase.PROTOTYPING not in profile.avoid_for
        ]
        prototyping_candidates.sort(key=lambda x: (x[1].development_complexity.value, -x[1].avg_speedup))
        
        if prototyping_candidates:
            primary = prototyping_candidates[0][0]
            alternatives = [candidate[0] for candidate in prototyping_candidates[1:3]]
            
            recommendations[UseCase.PROTOTYPING] = TechnologyRecommendation(
                use_case=UseCase.PROTOTYPING,
                primary_recommendation=primary,
                alternative_options=alternatives,
                rationale=f"{primary} offers the best balance of ease of use and performance for rapid prototyping",
                performance_expectation=f"Expected speedup: {profiles[primary].avg_speedup:.1f}x",
                development_effort=f"Setup time: {profiles[primary].setup_time_hours:.1f} hours",
                risk_assessment="Low risk - quick to implement and test",
                implementation_notes=[
                    "Focus on core functionality first",
                    "Consider migration path to production implementation",
                    "Validate performance assumptions early"
                ]
            )
        
        # Production Performance
        production_candidates = [
            (lang, profile) for lang, profile in profiles.items()
            if UseCase.PRODUCTION_PERFORMANCE in profile.best_use_cases
        ]
        production_candidates.sort(key=lambda x: -x[1].avg_speedup)
        
        if production_candidates:
            primary = production_candidates[0][0]
            alternatives = [candidate[0] for candidate in production_candidates[1:3]]
            
            recommendations[UseCase.PRODUCTION_PERFORMANCE] = TechnologyRecommendation(
                use_case=UseCase.PRODUCTION_PERFORMANCE,
                primary_recommendation=primary,
                alternative_options=alternatives,
                rationale=f"{primary} provides the highest performance with acceptable development complexity",
                performance_expectation=f"Expected speedup: {profiles[primary].avg_speedup:.1f}x",
                development_effort=f"Development complexity: {profiles[primary].development_complexity.value}",
                risk_assessment="Medium risk - requires careful implementation and testing",
                implementation_notes=[
                    "Invest in comprehensive testing",
                    "Plan for maintenance and updates",
                    "Consider performance monitoring"
                ]
            )
        
        # Scientific Computing
        scientific_candidates = [
            (lang, profile) for lang, profile in profiles.items()
            if UseCase.SCIENTIFIC_COMPUTING in profile.best_use_cases
        ]
        scientific_candidates.sort(key=lambda x: (-x[1].avg_speedup, x[1].development_complexity.value))
        
        if scientific_candidates:
            primary = scientific_candidates[0][0]
            alternatives = [candidate[0] for candidate in scientific_candidates[1:3]]
            
            recommendations[UseCase.SCIENTIFIC_COMPUTING] = TechnologyRecommendation(
                use_case=UseCase.SCIENTIFIC_COMPUTING,
                primary_recommendation=primary,
                alternative_options=alternatives,
                rationale=f"{primary} is optimized for numerical computing with good ecosystem support",
                performance_expectation=f"Expected speedup: {profiles[primary].avg_speedup:.1f}x",
                development_effort=f"Moderate effort with specialized libraries",
                risk_assessment="Low-Medium risk - well-established in scientific community",
                implementation_notes=[
                    "Leverage existing scientific libraries",
                    "Validate numerical accuracy",
                    "Consider parallel processing capabilities"
                ]
            )
        
        # Add more use case recommendations...
        self._add_remaining_use_case_recommendations(recommendations, profiles)
        
        return recommendations
    
    def _add_remaining_use_case_recommendations(self, recommendations: Dict[UseCase, TechnologyRecommendation], profiles: Dict[str, TechnologyProfile]):
        """Add recommendations for remaining use cases."""
        
        # Real-time Processing
        realtime_candidates = [
            (lang, profile) for lang, profile in profiles.items()
            if UseCase.REAL_TIME_PROCESSING in profile.best_use_cases
        ]
        realtime_candidates.sort(key=lambda x: (-x[1].avg_speedup, x[1].speedup_consistency))
        
        if realtime_candidates:
            primary = realtime_candidates[0][0]
            alternatives = [candidate[0] for candidate in realtime_candidates[1:2]]
            
            recommendations[UseCase.REAL_TIME_PROCESSING] = TechnologyRecommendation(
                use_case=UseCase.REAL_TIME_PROCESSING,
                primary_recommendation=primary,
                alternative_options=alternatives,
                rationale=f"{primary} provides consistent low-latency performance",
                performance_expectation=f"Expected speedup: {profiles[primary].avg_speedup:.1f}x with low variance",
                development_effort="High - requires careful optimization",
                risk_assessment="High risk - strict timing requirements",
                implementation_notes=[
                    "Profile for worst-case performance",
                    "Avoid garbage collection languages",
                    "Test under load conditions"
                ]
            )
        
        # Cross-platform Deployment
        crossplatform_candidates = [
            (lang, profile) for lang, profile in profiles.items()
            if UseCase.CROSS_PLATFORM_DEPLOYMENT in profile.best_use_cases
        ]
        crossplatform_candidates.sort(key=lambda x: (x[1].cross_platform_support == "Excellent", -x[1].avg_speedup))
        
        if crossplatform_candidates:
            primary = crossplatform_candidates[0][0]
            alternatives = [candidate[0] for candidate in crossplatform_candidates[1:3]]
            
            recommendations[UseCase.CROSS_PLATFORM_DEPLOYMENT] = TechnologyRecommendation(
                use_case=UseCase.CROSS_PLATFORM_DEPLOYMENT,
                primary_recommendation=primary,
                alternative_options=alternatives,
                rationale=f"{primary} offers excellent cross-platform support with good performance",
                performance_expectation=f"Expected speedup: {profiles[primary].avg_speedup:.1f}x across platforms",
                development_effort="Medium - platform testing required",
                risk_assessment="Medium risk - platform-specific issues possible",
                implementation_notes=[
                    "Test on all target platforms",
                    "Use platform-agnostic build systems",
                    "Plan for platform-specific optimizations"
                ]
            )
    
    def _generate_performance_ranking(self, profiles: Dict[str, TechnologyProfile]) -> List[Tuple[str, float]]:
        """Generate performance ranking."""
        ranking = [(lang, profile.avg_speedup) for lang, profile in profiles.items()]
        ranking.sort(key=lambda x: -x[1])
        return ranking
    
    def _generate_ease_of_use_ranking(self, profiles: Dict[str, TechnologyProfile]) -> List[Tuple[str, DevelopmentComplexity]]:
        """Generate ease of use ranking."""
        complexity_order = {
            DevelopmentComplexity.VERY_LOW: 1,
            DevelopmentComplexity.LOW: 2,
            DevelopmentComplexity.MEDIUM: 3,
            DevelopmentComplexity.HIGH: 4,
            DevelopmentComplexity.VERY_HIGH: 5
        }
        
        ranking = [(lang, profile.development_complexity) for lang, profile in profiles.items()]
        ranking.sort(key=lambda x: complexity_order[x[1]])
        return ranking
    
    def _generate_reliability_ranking(self, profiles: Dict[str, TechnologyProfile]) -> List[Tuple[str, float]]:
        """Generate reliability ranking based on success rate and consistency."""
        ranking = []
        for lang, profile in profiles.items():
            # Combine success rate and consistency (lower CV is better)
            reliability_score = profile.success_rate * (1.0 / (1.0 + profile.speedup_consistency))
            ranking.append((lang, reliability_score))
        
        ranking.sort(key=lambda x: -x[1])
        return ranking
    
    def _generate_decision_framework(self, profiles: Dict[str, TechnologyProfile]) -> Dict[str, Any]:
        """Generate decision framework for technology selection."""
        return {
            "selection_criteria": {
                "performance_priority": {
                    "description": "When performance is the top priority",
                    "recommended_approach": "Choose highest speedup with acceptable development cost",
                    "key_metrics": ["avg_speedup", "speedup_consistency"]
                },
                "development_speed_priority": {
                    "description": "When fast development is crucial",
                    "recommended_approach": "Choose lowest development complexity",
                    "key_metrics": ["development_complexity", "setup_time_hours"]
                },
                "maintenance_priority": {
                    "description": "When long-term maintenance is important",
                    "recommended_approach": "Balance performance with maintainability",
                    "key_metrics": ["maintenance_effort", "community_support", "documentation_quality"]
                },
                "risk_minimization": {
                    "description": "When minimizing project risk is essential",
                    "recommended_approach": "Choose mature, well-supported technologies",
                    "key_metrics": ["community_support", "success_rate", "memory_safety"]
                }
            },
            "decision_tree": {
                "step_1": "Identify primary use case and constraints",
                "step_2": "Filter technologies by use case suitability",
                "step_3": "Rank by priority criteria (performance, ease, maintenance, risk)",
                "step_4": "Consider team expertise and project timeline",
                "step_5": "Validate choice with prototype or pilot implementation"
            },
            "red_flags": [
                "Choosing high-complexity language for prototyping",
                "Ignoring memory safety for production systems",
                "Selecting immature ecosystem for critical applications",
                "Overlooking cross-platform requirements",
                "Underestimating maintenance effort"
            ]
        }
    
    def _generate_analysis_summary(self, statistical_report: FFIStatisticalReport) -> str:
        """Generate analysis summary."""
        total_languages = len(statistical_report.languages_analyzed)
        avg_speedup = statistical_report.overall_speedup_stats.mean
        
        return (f"Analysis of {total_languages} FFI languages across "
                f"{len(statistical_report.scenarios_analyzed)} scenarios. "
                f"Average speedup: {avg_speedup:.1f}x over Pure Python. "
                f"Statistical significance confirmed in "
                f"{len([t for t in statistical_report.significance_tests if t.is_significant])}"
                f"/{len(statistical_report.significance_tests)} tests.")
    
    def _generate_general_considerations(self, statistical_report: FFIStatisticalReport) -> List[str]:
        """Generate general considerations for FFI adoption."""
        considerations = [
            "FFI implementations require additional build complexity and dependencies",
            "Performance gains vary significantly by use case and data size",
            "Memory management becomes critical in non-garbage-collected languages",
            "Cross-platform deployment requires testing on all target platforms",
            "Debugging FFI code can be more challenging than pure Python",
            "Consider the total cost of ownership including development and maintenance"
        ]
        
        # Add data-driven considerations
        if statistical_report.outlier_analysis.outlier_percentage > 10:
            considerations.append(f"High performance variability detected ({statistical_report.outlier_analysis.outlier_percentage:.1f}% outliers) - thorough testing recommended")
        
        if statistical_report.overall_speedup_stats.distribution_type.startswith("Right-skewed"):
            considerations.append("Performance distribution is right-skewed - some implementations show exceptional results while others are modest")
        
        return considerations
    
    def _generate_platform_specific_notes(self) -> Dict[str, List[str]]:
        """Generate platform-specific implementation notes."""
        return {
            "Windows": [
                "Use Visual Studio Build Tools for C/C++ compilation",
                "Consider Windows-specific library paths and DLL loading",
                "Test with both 32-bit and 64-bit Python installations",
                "Be aware of Windows-specific path separators and file handling"
            ],
            "Linux": [
                "Ensure development packages are installed (build-essential, etc.)",
                "Consider different Linux distributions and package managers",
                "Test shared library loading with different glibc versions",
                "Use appropriate compiler flags for optimization"
            ],
            "macOS": [
                "Install Xcode Command Line Tools for compilation",
                "Consider both Intel and Apple Silicon architectures",
                "Test with different macOS versions for compatibility",
                "Be aware of macOS security restrictions on unsigned libraries"
            ],
            "Docker": [
                "Use multi-stage builds to minimize image size",
                "Install all necessary build dependencies in the image",
                "Consider using Alpine Linux for smaller images",
                "Test shared library loading in containerized environments"
            ]
        }


def main():
    """Test technology advisor functionality."""
    print("FFI Technology Advisor module loaded successfully")


if __name__ == "__main__":
    main()