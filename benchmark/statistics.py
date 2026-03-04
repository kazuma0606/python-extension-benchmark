"""統計計算モジュール

ベンチマーク計測データから統計値を計算する。
"""

import statistics
from typing import List
from benchmark.models import StatResult


class Statistics:
    """統計計算クラス"""

    @staticmethod
    def calculate(measurements: List[float]) -> StatResult:
        """計測データから統計値を計算
        
        Args:
            measurements: 計測データのリスト
            
        Returns:
            StatResult: 最小値、中央値、平均値、標準偏差
        """
        if not measurements:
            raise ValueError("measurements must not be empty")
        
        return StatResult(
            min=min(measurements),
            median=statistics.median(measurements),
            mean=statistics.mean(measurements),
            std_dev=statistics.stdev(measurements) if len(measurements) > 1 else 0.0
        )

    @staticmethod
    def calculate_relative_score(target_time: float, baseline_time: float) -> float:
        """ベースライン（Pure Python）に対する相対スコアを計算
        
        Args:
            target_time: 対象実装の実行時間
            baseline_time: ベースライン実装の実行時間
            
        Returns:
            float: 相対スコア（baseline_time / target_time）
                  値が大きいほど高速（1.0がベースライン）
        """
        if baseline_time <= 0:
            raise ValueError("baseline_time must be positive")
        if target_time <= 0:
            raise ValueError("target_time must be positive")
        
        return baseline_time / target_time

    @staticmethod
    def calculate_scalability(
        single_thread_throughput: float,
        multi_thread_throughput: float
    ) -> float:
        """スケーラビリティを計算（シングルスレッドに対する倍率）
        
        Args:
            single_thread_throughput: シングルスレッドのスループット
            multi_thread_throughput: マルチスレッドのスループット
            
        Returns:
            float: スケーラビリティ（multi_thread_throughput / single_thread_throughput）
        """
        if single_thread_throughput <= 0:
            raise ValueError("single_thread_throughput must be positive")
        if multi_thread_throughput <= 0:
            raise ValueError("multi_thread_throughput must be positive")
        
        return multi_thread_throughput / single_thread_throughput

    @staticmethod
    def calculate_relative_error(a: float, b: float) -> float:
        """2つの数値の相対誤差を計算
        
        Args:
            a: 数値1
            b: 数値2
            
        Returns:
            float: 相対誤差 |a - b| / max(|a|, |b|)
        """
        max_abs = max(abs(a), abs(b))
        if max_abs == 0:
            return 0.0
        return abs(a - b) / max_abs
