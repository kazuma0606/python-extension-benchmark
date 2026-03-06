"""結果出力モジュール

ベンチマーク結果をJSON/CSV形式で出力する。
"""

import json
import csv
import os
from pathlib import Path
from typing import List, Dict
from benchmark.models import BenchmarkResult


class OutputWriter:
    """ベンチマーク結果の出力を担当するクラス"""
    
    def __init__(self, base_dir: str = "benchmark/results"):
        """
        Args:
            base_dir: 結果出力のベースディレクトリ
        """
        self.base_dir = Path(base_dir)
        self.json_dir = self.base_dir / "json"
        self.csv_dir = self.base_dir / "csv"
        
        # ディレクトリが存在しない場合は作成
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        
        # FFI実装の識別
        self.ffi_implementations = {
            "c_ffi", "cpp_ffi", "numpy_ffi", "cython_ffi", "rust_ffi",
            "fortran_ffi", "julia_ffi", "go_ffi", "zig_ffi", "nim_ffi", "kotlin_ffi"
        }
    
    def write_json(self, results: List[BenchmarkResult], filename: str) -> str:
        """JSON形式で結果を出力
        
        Args:
            results: ベンチマーク結果のリスト
            filename: 出力ファイル名（拡張子なし）
            
        Returns:
            出力されたファイルのパス
        """
        output_path = self.json_dir / f"{filename}.json"
        
        # BenchmarkResultをJSON形式に変換
        data = {
            'results': [result.to_dict() for result in results],
            'summary': {
                'total_scenarios': len(set(r.scenario_name for r in results)),
                'total_implementations': len(set(r.implementation_name for r in results)),
                'total_measurements': len(results),
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def write_csv(self, results: List[BenchmarkResult], filename: str) -> str:
        """CSV形式で結果を出力
        
        Args:
            results: ベンチマーク結果のリスト
            filename: 出力ファイル名（拡張子なし）
            
        Returns:
            出力されたファイルのパス
        """
        output_path = self.csv_dir / f"{filename}.csv"
        
        # CSVのヘッダー定義
        fieldnames = [
            'scenario_name',
            'implementation_name',
            'min_time',
            'median_time',
            'mean_time',
            'std_dev',
            'relative_score',
            'throughput',
            'peak_memory_mb',
            'avg_memory_mb',
            'thread_count',
            'scalability',
            'timestamp',
            'os',
            'cpu',
            'memory_gb',
            'python_version',
            'docker',
            'validation_is_valid',
            'validation_max_error',
            'status',
            'error_message',
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                # メモリ使用量の統計を計算
                peak_memory = max(result.memory_usage) if result.memory_usage else 0.0
                avg_memory = sum(result.memory_usage) / len(result.memory_usage) if result.memory_usage else 0.0
                
                row = {
                    'scenario_name': result.scenario_name,
                    'implementation_name': result.implementation_name,
                    'min_time': result.min_time,
                    'median_time': result.median_time,
                    'mean_time': result.mean_time,
                    'std_dev': result.std_dev,
                    'relative_score': result.relative_score,
                    'throughput': result.throughput,
                    'peak_memory_mb': peak_memory,
                    'avg_memory_mb': avg_memory,
                    'thread_count': result.thread_count or '',
                    'scalability': result.scalability or '',
                    'timestamp': result.timestamp.isoformat(),
                    'os': result.environment.os,
                    'cpu': result.environment.cpu,
                    'memory_gb': result.environment.memory_gb,
                    'python_version': result.environment.python_version,
                    'docker': result.environment.docker,
                    'validation_is_valid': result.validation.is_valid if result.validation else '',
                    'validation_max_error': result.validation.max_relative_error if result.validation else '',
                    'status': result.status,
                    'error_message': result.error_message or '',
                }
                writer.writerow(row)
        
        return str(output_path)
    
    def write_comprehensive_report(
        self,
        results: List[BenchmarkResult],
        filename: str
    ) -> str:
        """包括的なレポートをJSON形式で出力（12実装対応）
        
        Args:
            results: ベンチマーク結果のリスト
            filename: 出力ファイル名（拡張子なし）
            
        Returns:
            出力されたファイルのパス
        """
        output_path = self.json_dir / f"{filename}_comprehensive.json"
        
        # 実装別統計
        impl_stats = {}
        scenario_stats = {}
        
        for result in results:
            # 実装別統計
            impl = result.implementation_name
            if impl not in impl_stats:
                impl_stats[impl] = {
                    'total_scenarios': 0,
                    'successful_scenarios': 0,
                    'failed_scenarios': 0,
                    'avg_execution_time': 0.0,
                    'avg_memory_usage': 0.0,
                    'avg_relative_score': 0.0,
                    'language': self._get_language_name(impl)
                }
            
            impl_stats[impl]['total_scenarios'] += 1
            
            if result.status == "SUCCESS":
                impl_stats[impl]['successful_scenarios'] += 1
                impl_stats[impl]['avg_execution_time'] += result.mean_time
                if result.memory_usage:
                    impl_stats[impl]['avg_memory_usage'] += max(result.memory_usage)
                impl_stats[impl]['avg_relative_score'] += result.relative_score
            else:
                impl_stats[impl]['failed_scenarios'] += 1
            
            # シナリオ別統計
            scenario = result.scenario_name
            if scenario not in scenario_stats:
                scenario_stats[scenario] = {
                    'total_implementations': 0,
                    'successful_implementations': 0,
                    'failed_implementations': 0,
                    'best_performance': None,
                    'worst_performance': None
                }
            
            scenario_stats[scenario]['total_implementations'] += 1
            
            if result.status == "SUCCESS":
                scenario_stats[scenario]['successful_implementations'] += 1
                
                # 最高・最低性能の更新
                if (scenario_stats[scenario]['best_performance'] is None or 
                    result.mean_time < scenario_stats[scenario]['best_performance']['time']):
                    scenario_stats[scenario]['best_performance'] = {
                        'implementation': impl,
                        'time': result.mean_time,
                        'relative_score': result.relative_score
                    }
                
                if (scenario_stats[scenario]['worst_performance'] is None or 
                    result.mean_time > scenario_stats[scenario]['worst_performance']['time']):
                    scenario_stats[scenario]['worst_performance'] = {
                        'implementation': impl,
                        'time': result.mean_time,
                        'relative_score': result.relative_score
                    }
            else:
                scenario_stats[scenario]['failed_implementations'] += 1
        
        # 平均値を計算
        for impl, stats in impl_stats.items():
            if stats['successful_scenarios'] > 0:
                stats['avg_execution_time'] /= stats['successful_scenarios']
                stats['avg_memory_usage'] /= stats['successful_scenarios']
                stats['avg_relative_score'] /= stats['successful_scenarios']
                stats['success_rate'] = stats['successful_scenarios'] / stats['total_scenarios']
            else:
                stats['success_rate'] = 0.0
        
        # 包括的なデータ構造
        comprehensive_data = {
            'metadata': {
                'total_results': len(results),
                'total_implementations': len(impl_stats),
                'total_scenarios': len(scenario_stats),
                'generation_timestamp': results[0].timestamp.isoformat() if results else None,
                'environment': {
                    'os': results[0].environment.os,
                    'cpu': results[0].environment.cpu,
                    'memory_gb': results[0].environment.memory_gb,
                    'python_version': results[0].environment.python_version,
                    'docker': results[0].environment.docker,
                } if results else None
            },
            'implementation_statistics': impl_stats,
            'scenario_statistics': scenario_stats,
            'detailed_results': [result.to_dict() for result in results],
            'performance_rankings': self._calculate_performance_rankings(results),
            'language_comparison': self._calculate_language_comparison(results)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _get_language_name(self, impl_name: str) -> str:
        """実装名から言語名を取得"""
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
        }
        return language_map.get(impl_name, "Unknown")
    
    def _calculate_performance_rankings(self, results: List[BenchmarkResult]) -> Dict:
        """性能ランキングを計算"""
        successful_results = [r for r in results if r.status == "SUCCESS"]
        
        if not successful_results:
            return {}
        
        # シナリオ別ランキング
        scenario_rankings = {}
        scenarios = set(r.scenario_name for r in successful_results)
        
        for scenario in scenarios:
            scenario_results = [r for r in successful_results if r.scenario_name == scenario]
            scenario_results.sort(key=lambda x: x.mean_time)  # 実行時間でソート
            
            scenario_rankings[scenario] = [
                {
                    'rank': i + 1,
                    'implementation': r.implementation_name,
                    'language': self._get_language_name(r.implementation_name),
                    'execution_time': r.mean_time,
                    'relative_score': r.relative_score
                }
                for i, r in enumerate(scenario_results)
            ]
        
        # 総合ランキング（平均相対スコア）
        impl_scores = {}
        for result in successful_results:
            impl = result.implementation_name
            if impl not in impl_scores:
                impl_scores[impl] = []
            impl_scores[impl].append(result.relative_score)
        
        overall_ranking = []
        for impl, scores in impl_scores.items():
            avg_score = sum(scores) / len(scores)
            overall_ranking.append({
                'implementation': impl,
                'language': self._get_language_name(impl),
                'average_relative_score': avg_score,
                'scenarios_completed': len(scores)
            })
        
        overall_ranking.sort(key=lambda x: x['average_relative_score'], reverse=True)
        for i, item in enumerate(overall_ranking):
            item['rank'] = i + 1
        
        return {
            'by_scenario': scenario_rankings,
            'overall': overall_ranking
        }
    
    def _calculate_language_comparison(self, results: List[BenchmarkResult]) -> Dict:
        """言語別比較分析を計算"""
        successful_results = [r for r in results if r.status == "SUCCESS"]
        
        if not successful_results:
            return {}
        
        language_stats = {}
        
        for result in successful_results:
            lang = self._get_language_name(result.implementation_name)
            
            if lang not in language_stats:
                language_stats[lang] = {
                    'implementations': [],
                    'total_scenarios': 0,
                    'avg_execution_time': 0.0,
                    'avg_relative_score': 0.0,
                    'best_scenario': None,
                    'worst_scenario': None
                }
            
            if result.implementation_name not in language_stats[lang]['implementations']:
                language_stats[lang]['implementations'].append(result.implementation_name)
            
            language_stats[lang]['total_scenarios'] += 1
            language_stats[lang]['avg_execution_time'] += result.mean_time
            language_stats[lang]['avg_relative_score'] += result.relative_score
            
            # 最高・最低シナリオの更新
            if (language_stats[lang]['best_scenario'] is None or 
                result.relative_score > language_stats[lang]['best_scenario']['relative_score']):
                language_stats[lang]['best_scenario'] = {
                    'scenario': result.scenario_name,
                    'implementation': result.implementation_name,
                    'relative_score': result.relative_score,
                    'execution_time': result.mean_time
                }
            
            if (language_stats[lang]['worst_scenario'] is None or 
                result.relative_score < language_stats[lang]['worst_scenario']['relative_score']):
                language_stats[lang]['worst_scenario'] = {
                    'scenario': result.scenario_name,
                    'implementation': result.implementation_name,
                    'relative_score': result.relative_score,
                    'execution_time': result.mean_time
                }
        
        # 平均値を計算
        for lang, stats in language_stats.items():
            if stats['total_scenarios'] > 0:
                stats['avg_execution_time'] /= stats['total_scenarios']
                stats['avg_relative_score'] /= stats['total_scenarios']
        
    def write_ffi_comparison_report(
        self,
        results: List[BenchmarkResult],
        filename: str
    ) -> str:
        """FFI vs Pure Python比較レポートを出力
        
        Args:
            results: ベンチマーク結果のリスト
            filename: 出力ファイル名（拡張子なし）
            
        Returns:
            出力されたファイルのパス
        """
        output_path = self.json_dir / f"{filename}_ffi_comparison.json"
        
        # Pure PythonとFFI実装を分離
        pure_python_results = [r for r in results if r.implementation_name == "python"]
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name)]
        
        # シナリオ別比較データを構築
        scenario_comparisons = {}
        
        for scenario in set(r.scenario_name for r in results):
            scenario_comparisons[scenario] = {
                'pure_python': None,
                'ffi_implementations': {},
                'speedup_analysis': {}
            }
            
            # Pure Python結果を取得
            python_result = next((r for r in pure_python_results if r.scenario_name == scenario), None)
            if python_result and python_result.status == "SUCCESS":
                scenario_comparisons[scenario]['pure_python'] = {
                    'execution_time_ms': python_result.mean_time,
                    'memory_usage_mb': max(python_result.memory_usage) if python_result.memory_usage else 0,
                    'throughput': python_result.throughput
                }
            
            # FFI実装結果を取得
            ffi_scenario_results = [r for r in ffi_results if r.scenario_name == scenario]
            
            for ffi_result in ffi_scenario_results:
                if ffi_result.status == "SUCCESS":
                    impl_name = ffi_result.implementation_name
                    language = self._get_language_name(impl_name)
                    
                    # 高速化倍率を計算
                    speedup_ratio = 1.0
                    if python_result and python_result.mean_time > 0:
                        speedup_ratio = python_result.mean_time / ffi_result.mean_time
                    
                    scenario_comparisons[scenario]['ffi_implementations'][impl_name] = {
                        'language': language,
                        'execution_time_ms': ffi_result.mean_time,
                        'memory_usage_mb': max(ffi_result.memory_usage) if ffi_result.memory_usage else 0,
                        'throughput': ffi_result.throughput,
                        'speedup_ratio': speedup_ratio,
                        'relative_score': ffi_result.relative_score
                    }
                    
                    scenario_comparisons[scenario]['speedup_analysis'][impl_name] = {
                        'language': language,
                        'speedup_ratio': speedup_ratio,
                        'performance_category': self._categorize_performance(speedup_ratio)
                    }
        
        # 総合統計を計算
        overall_statistics = self._calculate_ffi_overall_statistics(results)
        
        # レポートデータを構築
        comparison_report = {
            'metadata': {
                'report_type': 'FFI_vs_Pure_Python_Comparison',
                'generation_timestamp': results[0].timestamp.isoformat() if results else None,
                'total_scenarios': len(scenario_comparisons),
                'total_ffi_implementations': len(set(r.implementation_name for r in ffi_results)),
                'environment': results[0].environment.to_dict() if results else None
            },
            'scenario_comparisons': scenario_comparisons,
            'overall_statistics': overall_statistics,
            'performance_rankings': self._calculate_ffi_performance_rankings(results),
            'language_effectiveness': self._analyze_language_effectiveness(results)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def write_ffi_csv_comparison(
        self,
        results: List[BenchmarkResult],
        filename: str
    ) -> str:
        """FFI比較結果をCSV形式で出力
        
        Args:
            results: ベンチマーク結果のリスト
            filename: 出力ファイル名（拡張子なし）
            
        Returns:
            出力されたファイルのパス
        """
        output_path = self.csv_dir / f"{filename}_ffi_comparison.csv"
        
        # CSVのヘッダー定義（FFI比較用）
        fieldnames = [
            'scenario_name',
            'implementation_name',
            'language',
            'implementation_type',  # 'pure_python' or 'ffi'
            'execution_time_ms',
            'memory_usage_mb',
            'throughput',
            'relative_score',
            'speedup_vs_python',
            'performance_category',
            'status',
            'error_message',
            'timestamp'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Pure Python結果を取得（比較基準用）
            python_results = {r.scenario_name: r for r in results 
                            if r.implementation_name == "python" and r.status == "SUCCESS"}
            
            for result in results:
                # 実装タイプを判定
                impl_type = "pure_python" if result.implementation_name == "python" else "ffi"
                
                # 高速化倍率を計算
                speedup_ratio = 1.0
                if (result.implementation_name != "python" and 
                    result.scenario_name in python_results and 
                    result.status == "SUCCESS"):
                    python_time = python_results[result.scenario_name].mean_time
                    if python_time > 0:
                        speedup_ratio = python_time / result.mean_time
                
                # メモリ使用量を計算
                memory_usage = max(result.memory_usage) if result.memory_usage else 0.0
                
                row = {
                    'scenario_name': result.scenario_name,
                    'implementation_name': result.implementation_name,
                    'language': self._get_language_name(result.implementation_name),
                    'implementation_type': impl_type,
                    'execution_time_ms': result.mean_time,
                    'memory_usage_mb': memory_usage,
                    'throughput': result.throughput,
                    'relative_score': result.relative_score,
                    'speedup_vs_python': speedup_ratio,
                    'performance_category': self._categorize_performance(speedup_ratio),
                    'status': result.status,
                    'error_message': result.error_message or '',
                    'timestamp': result.timestamp.isoformat()
                }
                writer.writerow(row)
        
        return str(output_path)
    
    def _is_ffi_implementation(self, impl_name: str) -> bool:
        """実装がFFI実装かどうかを判定"""
        return impl_name in self.ffi_implementations
    
    def _categorize_performance(self, speedup_ratio: float) -> str:
        """高速化倍率をカテゴリに分類"""
        if speedup_ratio >= 10.0:
            return "Excellent (10x+)"
        elif speedup_ratio >= 5.0:
            return "Very Good (5-10x)"
        elif speedup_ratio >= 2.0:
            return "Good (2-5x)"
        elif speedup_ratio >= 1.1:
            return "Moderate (1.1-2x)"
        elif speedup_ratio >= 0.9:
            return "Similar (0.9-1.1x)"
        else:
            return "Slower (<0.9x)"
    
    def _calculate_ffi_overall_statistics(self, results: List[BenchmarkResult]) -> Dict:
        """FFI実装の総合統計を計算"""
        pure_python_results = [r for r in results if r.implementation_name == "python" and r.status == "SUCCESS"]
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name) and r.status == "SUCCESS"]
        
        if not pure_python_results or not ffi_results:
            return {}
        
        # 高速化倍率の統計
        speedup_ratios = []
        for ffi_result in ffi_results:
            python_result = next((r for r in pure_python_results if r.scenario_name == ffi_result.scenario_name), None)
            if python_result and python_result.mean_time > 0:
                speedup = python_result.mean_time / ffi_result.mean_time
                speedup_ratios.append(speedup)
        
        if not speedup_ratios:
            return {}
        
        return {
            'total_ffi_implementations': len(set(r.implementation_name for r in ffi_results)),
            'total_scenarios_tested': len(set(r.scenario_name for r in ffi_results)),
            'average_speedup': sum(speedup_ratios) / len(speedup_ratios),
            'max_speedup': max(speedup_ratios),
            'min_speedup': min(speedup_ratios),
            'speedup_distribution': {
                'excellent_10x_plus': len([s for s in speedup_ratios if s >= 10.0]),
                'very_good_5_10x': len([s for s in speedup_ratios if 5.0 <= s < 10.0]),
                'good_2_5x': len([s for s in speedup_ratios if 2.0 <= s < 5.0]),
                'moderate_1_1_2x': len([s for s in speedup_ratios if 1.1 <= s < 2.0]),
                'similar_0_9_1_1x': len([s for s in speedup_ratios if 0.9 <= s < 1.1]),
                'slower_below_0_9x': len([s for s in speedup_ratios if s < 0.9])
            }
        }
    
    def _calculate_ffi_performance_rankings(self, results: List[BenchmarkResult]) -> Dict:
        """FFI実装の性能ランキングを計算"""
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name) and r.status == "SUCCESS"]
        
        if not ffi_results:
            return {}
        
        # 実装別の平均性能を計算
        impl_performance = {}
        for result in ffi_results:
            impl = result.implementation_name
            if impl not in impl_performance:
                impl_performance[impl] = {
                    'language': self._get_language_name(impl),
                    'total_scenarios': 0,
                    'total_relative_score': 0.0,
                    'total_execution_time': 0.0
                }
            
            impl_performance[impl]['total_scenarios'] += 1
            impl_performance[impl]['total_relative_score'] += result.relative_score
            impl_performance[impl]['total_execution_time'] += result.mean_time
        
        # 平均値を計算してランキング作成
        ranking = []
        for impl, perf in impl_performance.items():
            avg_relative_score = perf['total_relative_score'] / perf['total_scenarios']
            avg_execution_time = perf['total_execution_time'] / perf['total_scenarios']
            
            ranking.append({
                'implementation': impl,
                'language': perf['language'],
                'average_relative_score': avg_relative_score,
                'average_execution_time_ms': avg_execution_time,
                'scenarios_completed': perf['total_scenarios']
            })
        
        # 相対スコアでソート（高い方が良い）
        ranking.sort(key=lambda x: x['average_relative_score'], reverse=True)
        
        # ランク付け
        for i, item in enumerate(ranking):
            item['rank'] = i + 1
        
        return {
            'by_relative_score': ranking,
            'by_execution_time': sorted(ranking, key=lambda x: x['average_execution_time_ms'])
        }
    
    def _analyze_language_effectiveness(self, results: List[BenchmarkResult]) -> Dict:
        """言語別のFFI効果を分析"""
        pure_python_results = {r.scenario_name: r for r in results 
                             if r.implementation_name == "python" and r.status == "SUCCESS"}
        ffi_results = [r for r in results if self._is_ffi_implementation(r.implementation_name) and r.status == "SUCCESS"]
        
        language_analysis = {}
        
        for result in ffi_results:
            language = self._get_language_name(result.implementation_name)
            
            if language not in language_analysis:
                language_analysis[language] = {
                    'implementations': [],
                    'scenarios_tested': 0,
                    'total_speedup': 0.0,
                    'speedup_ratios': [],
                    'best_scenario': None,
                    'worst_scenario': None
                }
            
            if result.implementation_name not in language_analysis[language]['implementations']:
                language_analysis[language]['implementations'].append(result.implementation_name)
            
            # 高速化倍率を計算
            if result.scenario_name in pure_python_results:
                python_time = pure_python_results[result.scenario_name].mean_time
                if python_time > 0:
                    speedup = python_time / result.mean_time
                    language_analysis[language]['speedup_ratios'].append(speedup)
                    language_analysis[language]['total_speedup'] += speedup
                    language_analysis[language]['scenarios_tested'] += 1
                    
                    # 最高・最低シナリオの更新
                    if (language_analysis[language]['best_scenario'] is None or 
                        speedup > language_analysis[language]['best_scenario']['speedup']):
                        language_analysis[language]['best_scenario'] = {
                            'scenario': result.scenario_name,
                            'implementation': result.implementation_name,
                            'speedup': speedup,
                            'execution_time_ms': result.mean_time
                        }
                    
                    if (language_analysis[language]['worst_scenario'] is None or 
                        speedup < language_analysis[language]['worst_scenario']['speedup']):
                        language_analysis[language]['worst_scenario'] = {
                            'scenario': result.scenario_name,
                            'implementation': result.implementation_name,
                            'speedup': speedup,
                            'execution_time_ms': result.mean_time
                        }
        
        # 統計値を計算
        for language, analysis in language_analysis.items():
            if analysis['scenarios_tested'] > 0:
                analysis['average_speedup'] = analysis['total_speedup'] / analysis['scenarios_tested']
                analysis['max_speedup'] = max(analysis['speedup_ratios'])
                analysis['min_speedup'] = min(analysis['speedup_ratios'])
                analysis['effectiveness_rating'] = self._rate_language_effectiveness(analysis['average_speedup'])
            else:
                analysis['average_speedup'] = 0.0
                analysis['max_speedup'] = 0.0
                analysis['min_speedup'] = 0.0
                analysis['effectiveness_rating'] = "No Data"
        
        return language_analysis
    
    def _rate_language_effectiveness(self, avg_speedup: float) -> str:
        """言語の効果度を評価"""
        if avg_speedup >= 20.0:
            return "Exceptional"
        elif avg_speedup >= 10.0:
            return "Excellent"
        elif avg_speedup >= 5.0:
            return "Very Good"
        elif avg_speedup >= 2.0:
            return "Good"
        elif avg_speedup >= 1.1:
            return "Moderate"
        else:
            return "Limited"

