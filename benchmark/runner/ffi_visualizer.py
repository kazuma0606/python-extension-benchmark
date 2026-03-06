#!/usr/bin/env python3
"""
FFI Visualization Module

Generates comparison graphs and charts for Pure Python vs FFI performance analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from benchmark.models import BenchmarkResult


class FFIVisualizer:
    """FFI performance visualization generator."""
    
    def __init__(self, output_dir: str = "benchmark/results/graphs"):
        """
        Args:
            output_dir: Directory for graph output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # FFI implementation identification
        self.ffi_implementations = {
            "c_ffi", "cpp_ffi", "numpy_ffi", "cython_ffi", "rust_ffi",
            "fortran_ffi", "julia_ffi", "go_ffi", "zig_ffi", "nim_ffi", "kotlin_ffi"
        }
        
        # Language color mapping for consistency
        self.language_colors = {
            "Python": "#3776ab",
            "C": "#555555", 
            "C++": "#00599c",
            "NumPy": "#013243",
            "Cython": "#fedf00",
            "Rust": "#ce422b",
            "Fortran": "#734f96",
            "Julia": "#9558b2",
            "Go": "#00add8",
            "Zig": "#f7a41d",
            "Nim": "#ffe953",
            "Kotlin": "#7f52ff"
        }
    
    def generate_speedup_comparison_chart(
        self,
        results: List[BenchmarkResult],
        filename: str = "ffi_speedup_comparison"
    ) -> str:
        """Generate Pure Python vs FFI speedup comparison chart.
        
        Args:
            results: Benchmark results
            filename: Output filename (without extension)
            
        Returns:
            Path to generated chart
        """
        # Prepare data
        speedup_data = self._calculate_speedup_data(results)
        
        if not speedup_data:
            print("Warning: No speedup data available for visualization")
            return ""
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        
        # Chart 1: Speedup by scenario
        scenarios = list(speedup_data.keys())
        implementations = set()
        for scenario_data in speedup_data.values():
            implementations.update(scenario_data.keys())
        implementations = sorted(implementations)
        
        # Prepare matrix for heatmap
        speedup_matrix = []
        for scenario in scenarios:
            row = []
            for impl in implementations:
                speedup = speedup_data[scenario].get(impl, 0.0)
                row.append(speedup)
            speedup_matrix.append(row)
        
        # Create heatmap
        im = ax1.imshow(speedup_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=20)
        ax1.set_xticks(range(len(implementations)))
        ax1.set_xticklabels([self._get_language_name(impl) for impl in implementations], rotation=45)
        ax1.set_yticks(range(len(scenarios)))
        ax1.set_yticklabels(scenarios)
        ax1.set_title('FFI Speedup vs Pure Python (Heatmap)', fontsize=14, fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax1)
        cbar.set_label('Speedup Ratio (x times faster)', rotation=270, labelpad=20)
        
        # Add text annotations
        for i in range(len(scenarios)):
            for j in range(len(implementations)):
                speedup = speedup_matrix[i][j]
                if speedup > 0:
                    text_color = 'white' if speedup < 10 else 'black'
                    ax1.text(j, i, f'{speedup:.1f}x', ha='center', va='center', 
                            color=text_color, fontweight='bold')
        
        # Chart 2: Average speedup by language
        lang_speedups = self._calculate_language_average_speedups(results)
        
        languages = list(lang_speedups.keys())
        avg_speedups = [lang_speedups[lang]['avg_speedup'] for lang in languages]
        colors = [self.language_colors.get(lang, '#888888') for lang in languages]
        
        bars = ax2.bar(languages, avg_speedups, color=colors, alpha=0.8, edgecolor='black')
        ax2.set_ylabel('Average Speedup Ratio', fontsize=12)
        ax2.set_title('Average FFI Speedup by Language', fontsize=14, fontweight='bold')
        ax2.set_ylim(0, max(avg_speedups) * 1.1 if avg_speedups else 1)
        
        # Add value labels on bars
        for bar, speedup in zip(bars, avg_speedups):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{speedup:.1f}x', ha='center', va='bottom', fontweight='bold')
        
        # Rotate x-axis labels
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save chart
        output_path = self.output_dir / f"{filename}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def generate_performance_distribution_chart(
        self,
        results: List[BenchmarkResult],
        filename: str = "ffi_performance_distribution"
    ) -> str:
        """Generate performance distribution analysis chart.
        
        Args:
            results: Benchmark results
            filename: Output filename (without extension)
            
        Returns:
            Path to generated chart
        """
        # Prepare data
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name) and r.status == "SUCCESS"]
        python_results = [r for r in results if r.implementation_name == "python" and r.status == "SUCCESS"]
        
        if not ffi_results or not python_results:
            print("Warning: Insufficient data for performance distribution chart")
            return ""
        
        # Calculate speedup ratios
        speedup_ratios = []
        language_speedups = {}
        
        for ffi_result in ffi_results:
            python_result = next((r for r in python_results if r.scenario_name == ffi_result.scenario_name), None)
            if python_result and python_result.mean_time > 0:
                speedup = python_result.mean_time / ffi_result.mean_time
                speedup_ratios.append(speedup)
                
                language = self._get_language_name(ffi_result.implementation_name)
                if language not in language_speedups:
                    language_speedups[language] = []
                language_speedups[language].append(speedup)
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Chart 1: Overall speedup distribution
        ax1.hist(speedup_ratios, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(np.mean(speedup_ratios), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(speedup_ratios):.1f}x')
        ax1.axvline(np.median(speedup_ratios), color='orange', linestyle='--', linewidth=2, label=f'Median: {np.median(speedup_ratios):.1f}x')
        ax1.set_xlabel('Speedup Ratio')
        ax1.set_ylabel('Frequency')
        ax1.set_title('FFI Speedup Distribution', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Box plot by language
        languages = list(language_speedups.keys())
        speedup_lists = [language_speedups[lang] for lang in languages]
        
        box_plot = ax2.boxplot(speedup_lists, labels=languages, patch_artist=True)
        for patch, lang in zip(box_plot['boxes'], languages):
            patch.set_facecolor(self.language_colors.get(lang, '#888888'))
            patch.set_alpha(0.7)
        
        ax2.set_ylabel('Speedup Ratio')
        ax2.set_title('Speedup Distribution by Language', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        # Chart 3: Performance categories
        categories = {
            'Excellent (10x+)': len([s for s in speedup_ratios if s >= 10.0]),
            'Very Good (5-10x)': len([s for s in speedup_ratios if 5.0 <= s < 10.0]),
            'Good (2-5x)': len([s for s in speedup_ratios if 2.0 <= s < 5.0]),
            'Moderate (1.1-2x)': len([s for s in speedup_ratios if 1.1 <= s < 2.0]),
            'Similar (0.9-1.1x)': len([s for s in speedup_ratios if 0.9 <= s < 1.1]),
            'Slower (<0.9x)': len([s for s in speedup_ratios if s < 0.9])
        }
        
        category_names = list(categories.keys())
        category_counts = list(categories.values())
        colors = ['#2ecc71', '#27ae60', '#f39c12', '#e67e22', '#95a5a6', '#e74c3c']
        
        wedges, texts, autotexts = ax3.pie(category_counts, labels=category_names, autopct='%1.1f%%', 
                                          colors=colors, startangle=90)
        ax3.set_title('Performance Category Distribution', fontweight='bold')
        
        # Chart 4: Execution time comparison (log scale)
        execution_times_data = []
        labels = []
        
        # Add Pure Python times
        python_times = [r.mean_time for r in python_results]
        execution_times_data.append(python_times)
        labels.append('Pure Python')
        
        # Add FFI times by language
        for lang in sorted(language_speedups.keys()):
            lang_results = [r for r in ffi_results if self._get_language_name(r.implementation_name) == lang]
            if lang_results:
                lang_times = [r.mean_time for r in lang_results]
                execution_times_data.append(lang_times)
                labels.append(lang)
        
        ax4.boxplot(execution_times_data, labels=labels)
        ax4.set_yscale('log')
        ax4.set_ylabel('Execution Time (ms, log scale)')
        ax4.set_title('Execution Time Comparison', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save chart
        output_path = self.output_dir / f"{filename}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def generate_language_characteristics_chart(
        self,
        results: List[BenchmarkResult],
        filename: str = "ffi_language_characteristics"
    ) -> str:
        """Generate language-specific performance characteristics chart.
        
        Args:
            results: Benchmark results
            filename: Output filename (without extension)
            
        Returns:
            Path to generated chart
        """
        # Analyze language characteristics
        lang_analysis = self._analyze_language_characteristics(results)
        
        if not lang_analysis:
            print("Warning: No language analysis data available")
            return ""
        
        # Create figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Chart 1: Average speedup vs consistency (std dev)
        languages = list(lang_analysis.keys())
        avg_speedups = [lang_analysis[lang]['avg_speedup'] for lang in languages]
        speedup_stds = [lang_analysis[lang]['speedup_std'] for lang in languages]
        colors = [self.language_colors.get(lang, '#888888') for lang in languages]
        
        scatter = ax1.scatter(speedup_stds, avg_speedups, c=colors, s=100, alpha=0.7, edgecolors='black')
        
        for i, lang in enumerate(languages):
            ax1.annotate(lang, (speedup_stds[i], avg_speedups[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=10)
        
        ax1.set_xlabel('Speedup Standard Deviation (consistency)')
        ax1.set_ylabel('Average Speedup Ratio')
        ax1.set_title('Language Performance: Speed vs Consistency', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Success rate vs average speedup
        success_rates = [lang_analysis[lang]['success_rate'] * 100 for lang in languages]
        
        scatter2 = ax2.scatter(success_rates, avg_speedups, c=colors, s=100, alpha=0.7, edgecolors='black')
        
        for i, lang in enumerate(languages):
            ax2.annotate(lang, (success_rates[i], avg_speedups[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=10)
        
        ax2.set_xlabel('Success Rate (%)')
        ax2.set_ylabel('Average Speedup Ratio')
        ax2.set_title('Language Reliability vs Performance', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Scenario coverage
        scenario_counts = [lang_analysis[lang]['scenarios_tested'] for lang in languages]
        
        bars = ax3.bar(languages, scenario_counts, color=colors, alpha=0.8, edgecolor='black')
        ax3.set_ylabel('Scenarios Tested')
        ax3.set_title('Language Implementation Coverage', fontweight='bold')
        
        # Add value labels
        for bar, count in zip(bars, scenario_counts):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
        
        # Chart 4: Best and worst scenarios for each language
        best_scenarios = {}
        worst_scenarios = {}
        
        for lang, analysis in lang_analysis.items():
            if analysis['best_scenario']:
                best_scenarios[lang] = analysis['best_scenario']['speedup']
            if analysis['worst_scenario']:
                worst_scenarios[lang] = analysis['worst_scenario']['speedup']
        
        x_pos = np.arange(len(languages))
        width = 0.35
        
        best_values = [best_scenarios.get(lang, 0) for lang in languages]
        worst_values = [worst_scenarios.get(lang, 0) for lang in languages]
        
        bars1 = ax4.bar(x_pos - width/2, best_values, width, label='Best Scenario', 
                       color='lightgreen', alpha=0.8, edgecolor='black')
        bars2 = ax4.bar(x_pos + width/2, worst_values, width, label='Worst Scenario', 
                       color='lightcoral', alpha=0.8, edgecolor='black')
        
        ax4.set_xlabel('Language')
        ax4.set_ylabel('Speedup Ratio')
        ax4.set_title('Best vs Worst Scenario Performance', fontweight='bold')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(languages, rotation=45, ha='right')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save chart
        output_path = self.output_dir / f"{filename}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(output_path)
    
    def _calculate_speedup_data(self, results: List[BenchmarkResult]) -> Dict[str, Dict[str, float]]:
        """Calculate speedup data for visualization."""
        python_results = {r.scenario_name: r for r in results 
                         if r.implementation_name == "python" and r.status == "SUCCESS"}
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name) and r.status == "SUCCESS"]
        
        speedup_data = {}
        
        for ffi_result in ffi_results:
            scenario = ffi_result.scenario_name
            impl = ffi_result.implementation_name
            
            if scenario not in speedup_data:
                speedup_data[scenario] = {}
            
            if scenario in python_results:
                python_time = python_results[scenario].mean_time
                if python_time > 0:
                    speedup = python_time / ffi_result.mean_time
                    speedup_data[scenario][impl] = speedup
        
        return speedup_data
    
    def _calculate_language_average_speedups(self, results: List[BenchmarkResult]) -> Dict[str, Dict[str, float]]:
        """Calculate average speedups by language."""
        python_results = {r.scenario_name: r for r in results 
                         if r.implementation_name == "python" and r.status == "SUCCESS"}
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name) and r.status == "SUCCESS"]
        
        language_speedups = {}
        
        for ffi_result in ffi_results:
            language = self._get_language_name(ffi_result.implementation_name)
            
            if language not in language_speedups:
                language_speedups[language] = []
            
            if ffi_result.scenario_name in python_results:
                python_time = python_results[ffi_result.scenario_name].mean_time
                if python_time > 0:
                    speedup = python_time / ffi_result.mean_time
                    language_speedups[language].append(speedup)
        
        # Calculate averages
        result = {}
        for language, speedups in language_speedups.items():
            if speedups:
                result[language] = {
                    'avg_speedup': np.mean(speedups),
                    'speedup_count': len(speedups)
                }
        
        return result
    
    def _analyze_language_characteristics(self, results: List[BenchmarkResult]) -> Dict[str, Dict]:
        """Analyze detailed language characteristics."""
        python_results = {r.scenario_name: r for r in results 
                         if r.implementation_name == "python" and r.status == "SUCCESS"}
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name)]
        
        language_analysis = {}
        
        for result in ffi_results:
            language = self._get_language_name(result.implementation_name)
            
            if language not in language_analysis:
                language_analysis[language] = {
                    'speedups': [],
                    'total_tests': 0,
                    'successful_tests': 0,
                    'scenarios_tested': 0,
                    'best_scenario': None,
                    'worst_scenario': None
                }
            
            language_analysis[language]['total_tests'] += 1
            
            if result.status == "SUCCESS":
                language_analysis[language]['successful_tests'] += 1
                language_analysis[language]['scenarios_tested'] += 1
                
                # Calculate speedup if Python baseline exists
                if result.scenario_name in python_results:
                    python_time = python_results[result.scenario_name].mean_time
                    if python_time > 0:
                        speedup = python_time / result.mean_time
                        language_analysis[language]['speedups'].append(speedup)
                        
                        # Track best and worst scenarios
                        if (language_analysis[language]['best_scenario'] is None or 
                            speedup > language_analysis[language]['best_scenario']['speedup']):
                            language_analysis[language]['best_scenario'] = {
                                'scenario': result.scenario_name,
                                'speedup': speedup
                            }
                        
                        if (language_analysis[language]['worst_scenario'] is None or 
                            speedup < language_analysis[language]['worst_scenario']['speedup']):
                            language_analysis[language]['worst_scenario'] = {
                                'scenario': result.scenario_name,
                                'speedup': speedup
                            }
        
        # Calculate final statistics
        for language, analysis in language_analysis.items():
            if analysis['speedups']:
                analysis['avg_speedup'] = np.mean(analysis['speedups'])
                analysis['speedup_std'] = np.std(analysis['speedups'])
            else:
                analysis['avg_speedup'] = 0.0
                analysis['speedup_std'] = 0.0
            
            analysis['success_rate'] = analysis['successful_tests'] / analysis['total_tests'] if analysis['total_tests'] > 0 else 0.0
        
        return language_analysis
    
    def _is_ffi_implementation(self, impl_name: str) -> bool:
        """Check if implementation is FFI-based."""
        return impl_name in self.ffi_implementations
    
    def _get_language_name(self, impl_name: str) -> str:
        """Get language name from implementation name."""
        language_map = {
            "python": "Python",
            "numpy_impl": "NumPy",
            "c_ext": "C",
            "cpp_ext": "C++", 
            "cython_ext": "Cython",
            "rust_ext": "Rust",
            "fortran_ext": "Fortran",
            "julia_ext": "Julia",
            "go_ext": "Go",
            "zig_ext": "Zig",
            "nim_ext": "Nim",
            "kotlin_ext": "Kotlin",
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
            "kotlin_ffi": "Kotlin"
        }
        return language_map.get(impl_name, "Unknown")


def main():
    """Test visualization functionality."""
    # This would be used for testing with actual benchmark results
    print("FFI Visualizer module loaded successfully")


if __name__ == "__main__":
    main()