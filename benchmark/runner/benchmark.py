"""ベンチマークランナー

ベンチマーク実行の中核コンポーネント。
シナリオを実行し、計測結果を収集する。
"""

import platform
import sys
from datetime import datetime
from typing import List, Optional
from benchmark.models import (
    BenchmarkResult,
    EnvironmentInfo,
    Implementation,
    Scenario
)
from benchmark.statistics import Statistics


class BenchmarkRunner:
    """ベンチマーク実行クラス"""
    
    def __init__(self):
        """初期化"""
        self.environment = self._get_environment_info()
    
    def _get_environment_info(self) -> EnvironmentInfo:
        """実行環境情報を取得
        
        Returns:
            EnvironmentInfo: 環境情報
        """
        import psutil
        
        return EnvironmentInfo(
            os=platform.system(),
            cpu=platform.processor() or platform.machine(),
            memory_gb=psutil.virtual_memory().total / (1024 ** 3),
            python_version=sys.version.split()[0],
            docker=False  # TODO: Docker環境の検出
        )
    
    def run_scenario(
        self,
        scenario: Scenario,
        implementations: List[Implementation],
        warmup_runs: int = 10,
        measurement_runs: int = 100
    ) -> List[BenchmarkResult]:
        """シナリオを実行し、計測結果を返す
        
        Args:
            scenario: 実行するシナリオ
            implementations: 実行する実装モジュールのリスト
            warmup_runs: ウォームアップ実行回数（デフォルト: 10）
            measurement_runs: 本計測実行回数（デフォルト: 100）
            
        Returns:
            List[BenchmarkResult]: 各実装の計測結果
        """
        results = []
        
        for implementation in implementations:
            try:
                result = self._run_single_implementation(
                    scenario,
                    implementation,
                    warmup_runs,
                    measurement_runs
                )
                results.append(result)
            except Exception as e:
                # エラーが発生しても他の実装は継続
                error_result = BenchmarkResult(
                    scenario_name=scenario.name,
                    implementation_name=implementation.name,
                    execution_times=[],
                    memory_usage=[],
                    min_time=0.0,
                    median_time=0.0,
                    mean_time=0.0,
                    std_dev=0.0,
                    relative_score=0.0,
                    throughput=0.0,
                    output_value=None,
                    timestamp=datetime.now(),
                    environment=self.environment,
                    status="ERROR",
                    error_message=str(e)
                )
                results.append(error_result)
                print(f"Error in {implementation.name}: {e}")
        
        # Pure Python実装をベースラインとして相対スコアを計算
        self._calculate_relative_scores(results)
        
        return results
    
    def _run_single_implementation(
        self,
        scenario: Scenario,
        implementation: Implementation,
        warmup_runs: int,
        measurement_runs: int
    ) -> BenchmarkResult:
        """単一実装のベンチマークを実行
        
        Args:
            scenario: 実行するシナリオ
            implementation: 実行する実装モジュール
            warmup_runs: ウォームアップ実行回数
            measurement_runs: 本計測実行回数
            
        Returns:
            BenchmarkResult: 計測結果
        """
        # ウォームアップ実行（結果は破棄）
        for _ in range(warmup_runs):
            scenario.execute(implementation)
        
        # 本計測実行
        execution_times = []
        memory_usages = []
        output_value = None
        
        for i in range(measurement_runs):
            output, exec_time, mem_usage = scenario.execute(implementation)
            execution_times.append(exec_time)
            memory_usages.append(mem_usage)
            
            # 最初の実行の出力値を保存（検証用）
            if i == 0:
                output_value = output
        
        # 統計値を計算
        time_stats = Statistics.calculate(execution_times)
        
        # スループットを計算（ops/sec）
        throughput = 1000.0 / time_stats.mean if time_stats.mean > 0 else 0.0
        
        return BenchmarkResult(
            scenario_name=scenario.name,
            implementation_name=implementation.name,
            execution_times=execution_times,
            memory_usage=memory_usages,
            min_time=time_stats.min,
            median_time=time_stats.median,
            mean_time=time_stats.mean,
            std_dev=time_stats.std_dev,
            relative_score=1.0,  # 後で計算
            throughput=throughput,
            output_value=output_value,
            timestamp=datetime.now(),
            environment=self.environment
        )
    
    def _calculate_relative_scores(self, results: List[BenchmarkResult]) -> None:
        """相対スコアを計算（Pure Pythonをベースライン）
        
        Args:
            results: 計測結果のリスト（in-placeで更新）
        """
        # Pure Python実装の平均実行時間を取得
        baseline_time = None
        for result in results:
            if result.implementation_name == "python" and result.status == "SUCCESS":
                baseline_time = result.mean_time
                break
        
        if baseline_time is None or baseline_time <= 0:
            # ベースラインが見つからない場合は全て1.0
            return
        
        # 各実装の相対スコアを計算
        for result in results:
            if result.status == "SUCCESS" and result.mean_time > 0:
                result.relative_score = Statistics.calculate_relative_score(
                    result.mean_time,
                    baseline_time
                )
    
    def run_all_scenarios(
        self,
        implementations: List[Implementation],
        scenarios: Optional[List[Scenario]] = None
    ) -> List[BenchmarkResult]:
        """全シナリオを実行
        
        Args:
            implementations: 実行する実装モジュールのリスト
            scenarios: 実行するシナリオのリスト（Noneの場合はデフォルトシナリオ）
            
        Returns:
            List[BenchmarkResult]: 全シナリオの計測結果
        """
        if scenarios is None:
            # デフォルトシナリオを使用
            from benchmark.runner.scenarios import (
                NumericScenario,
                MemoryScenario,
                ParallelScenario
            )
            scenarios = [
                NumericScenario("primes"),
                NumericScenario("matrix"),
                MemoryScenario("sort"),
                MemoryScenario("filter"),
                ParallelScenario(1),
                ParallelScenario(2),
                ParallelScenario(4),
            ]
        
        all_results = []
        for scenario in scenarios:
            print(f"\nRunning scenario: {scenario.name}")
            results = self.run_scenario(scenario, implementations)
            all_results.extend(results)
        
        return all_results
