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
        
        return language_stats

