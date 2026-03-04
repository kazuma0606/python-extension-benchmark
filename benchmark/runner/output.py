"""結果出力モジュール

ベンチマーク結果をJSON/CSV形式で出力する。
"""

import json
import csv
import os
from pathlib import Path
from typing import List
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

