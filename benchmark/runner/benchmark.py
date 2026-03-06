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
from benchmark.runner.error_handler import ErrorHandler
from benchmark.ffi_implementations.uv_checker import UVEnvironmentChecker, check_uv_environment


class BenchmarkRunner:
    """ベンチマーク実行クラス"""
    
    def __init__(self):
        """初期化"""
        self.environment = self._get_environment_info()
        self.error_handler = ErrorHandler()
        self.uv_checker = UVEnvironmentChecker()
        
        # FFI実装の識別
        self.ffi_implementations = {
            "c_ffi", "cpp_ffi", "numpy_ffi", "cython_ffi", "rust_ffi",
            "fortran_ffi", "julia_ffi", "go_ffi", "zig_ffi", "nim_ffi", "kotlin_ffi"
        }
    
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
                error_log = self.error_handler.handle_execution_error(
                    implementation.name,
                    scenario.name,
                    e
                )
                
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
                    error_message=error_log.error_message,
                    thread_count=getattr(scenario, 'num_threads', None)
                )
                results.append(error_result)
        
        # Pure Python実装をベースラインとして相対スコアを計算
        self._calculate_relative_scores(results)
        
        # 並列処理シナリオの場合、スケーラビリティを計算
        self._calculate_scalability(results)
        
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
        
        # 並列処理シナリオの場合、スレッド数を記録
        thread_count = None
        if hasattr(scenario, 'num_threads'):
            thread_count = scenario.num_threads
        
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
            environment=self.environment,
            thread_count=thread_count
        )
    
    def _calculate_scalability(self, results: List[BenchmarkResult]) -> None:
        """並列処理結果のスケーラビリティを計算
        
        Args:
            results: 計測結果のリスト（in-placeで更新）
        """
        # 実装ごとにグループ化
        by_implementation = {}
        for result in results:
            if result.thread_count is not None and result.status == "SUCCESS":
                if result.implementation_name not in by_implementation:
                    by_implementation[result.implementation_name] = {}
                by_implementation[result.implementation_name][result.thread_count] = result
        
        # 各実装のスケーラビリティを計算
        for impl_name, thread_results in by_implementation.items():
            # シングルスレッド（thread_count=1）の結果を取得
            single_thread_result = thread_results.get(1)
            if single_thread_result is None:
                continue
            
            single_thread_throughput = single_thread_result.throughput
            if single_thread_throughput <= 0:
                continue
            
            # 各スレッド数のスケーラビリティを計算
            for thread_count, result in thread_results.items():
                if result.throughput > 0:
                    result.scalability = Statistics.calculate_scalability(
                        single_thread_throughput,
                        result.throughput
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
            from benchmark.runner.scenarios import get_all_scenarios
            scenarios = get_all_scenarios()
        
        all_results = []
        for scenario in scenarios:
            print(f"\nRunning scenario: {scenario.name}")
            results = self.run_scenario(scenario, implementations)
            all_results.extend(results)
        
        # 全結果に対してスケーラビリティを計算
        self._calculate_scalability(all_results)
        
        # エラーサマリーを出力
        if self.error_handler.has_errors():
            self.error_handler.print_error_summary()
        
        return all_results
    
    def get_all_available_implementations(self) -> List[str]:
        """利用可能な全実装名を取得（FFI実装含む）
        
        Returns:
            List[str]: 利用可能な実装名のリスト
        """
        # 拡張版実装（Pure Python + 拡張）
        extension_implementations = [
            "python", "numpy_impl", "c_ext", "cpp_ext", "cython_ext", 
            "rust_ext", "fortran_ext", "julia_ext", "go_ext", 
            "zig_ext", "nim_ext", "kotlin_ext"
        ]
        
        # FFI実装
        ffi_implementations = [
            "c_ffi", "cpp_ffi", "numpy_ffi", "cython_ffi", "rust_ffi",
            "fortran_ffi", "julia_ffi", "go_ffi", "zig_ffi", "nim_ffi", "kotlin_ffi"
        ]
        
        all_implementations = extension_implementations + ffi_implementations
        available = []
        
        for impl_name in all_implementations:
            if impl_name.endswith('_ffi'):
                # FFI実装の場合
                try:
                    module_name = f"benchmark.ffi_implementations.{impl_name}"
                    __import__(module_name)
                    available.append(impl_name)
                except ImportError:
                    # FFI実装が利用できない場合はスキップ
                    continue
            else:
                # 拡張版実装の場合
                module_name = f"benchmark.{impl_name}"
                try:
                    __import__(module_name)
                    available.append(impl_name)
                except ImportError:
                    # 実装が利用できない場合はスキップ
                    continue
        
        return available

    def load_implementations(
        self,
        implementation_names: List[str]
    ) -> List[Implementation]:
        """実装モジュールを安全にロード（FFI実装対応）
        
        Args:
            implementation_names: ロードする実装名のリスト
                例: ["python", "numpy_impl", "c_ext", "c_ffi", "cpp_ffi"]
        
        Returns:
            List[Implementation]: 正常にロードされた実装のリスト
        """
        implementations = []
        
        language_map = {
            # 拡張版実装
            "python": "Python",
            "numpy_impl": "NumPy",
            "c_ext": "C Extension",
            "cpp_ext": "C++ Extension",
            "cython_ext": "Cython Extension",
            "rust_ext": "Rust Extension",
            "fortran_ext": "Fortran Extension",
            "julia_ext": "Julia Extension",
            "go_ext": "Go Extension",
            "zig_ext": "Zig Extension",
            "nim_ext": "Nim Extension",
            "kotlin_ext": "Kotlin Extension",
            # FFI実装
            "c_ffi": "C FFI",
            "cpp_ffi": "C++ FFI",
            "numpy_ffi": "NumPy FFI",
            "cython_ffi": "Cython FFI",
            "rust_ffi": "Rust FFI",
            "fortran_ffi": "Fortran FFI",
            "julia_ffi": "Julia FFI",
            "go_ffi": "Go FFI",
            "zig_ffi": "Zig FFI",
            "nim_ffi": "Nim FFI",
            "kotlin_ffi": "Kotlin FFI",
        }
        
        for name in implementation_names:
            if name.endswith('_ffi'):
                # FFI実装の場合
                module_name = f"benchmark.ffi_implementations.{name}"
            else:
                # 拡張版実装の場合
                module_name = f"benchmark.{name}"
            
            module = self.error_handler.safe_import_module(module_name, name)
            
            if module is not None:
                language = language_map.get(name, "Unknown")
                implementations.append(Implementation(
                    name=name,
                    module=module,
                    language=language
                ))
        
        if not implementations:
            print("⚠️  Warning: No implementations were successfully loaded!")
        else:
            print(f"✓ Successfully loaded {len(implementations)} implementation(s): "
                  f"{', '.join(impl.name for impl in implementations)}\n")
        
        return implementations
    
    def run_comprehensive_benchmark(
        self,
        scenarios: Optional[List[Scenario]] = None,
        implementation_filter: Optional[List[str]] = None,
        check_uv_env: bool = True
    ) -> List[BenchmarkResult]:
        """包括的ベンチマークを実行（全12実装対応 + FFI実装）
        
        Args:
            scenarios: 実行するシナリオのリスト（Noneの場合はデフォルト）
            implementation_filter: 実行する実装のフィルタ（Noneの場合は全て）
            check_uv_env: uv環境確認を行うかどうか
            
        Returns:
            List[BenchmarkResult]: 全シナリオの計測結果
        """
        # uv環境確認（FFI実装を含む場合）
        if check_uv_env and implementation_filter:
            has_ffi = any(impl.endswith('_ffi') for impl in implementation_filter)
            if has_ffi:
                print("🔍 Checking uv environment for FFI implementations...")
                if not check_uv_environment():
                    print("⚠️  Warning: uv environment issues detected. FFI implementations may not work correctly.")
                    print("   Continuing with available implementations...\n")
        
        from benchmark.runner.scenarios import get_default_implementations
        
        # 実装リストを決定
        if implementation_filter is None:
            target_implementations = get_default_implementations()
        else:
            target_implementations = implementation_filter
        
        # 利用可能な実装をロード
        available_implementations = self.get_all_available_implementations()
        filtered_implementations = [
            impl for impl in target_implementations 
            if impl in available_implementations
        ]
        
        print(f"🚀 Starting comprehensive benchmark with {len(filtered_implementations)} implementations:")
        print(f"   Target: {', '.join(target_implementations)}")
        print(f"   Available: {', '.join(filtered_implementations)}")
        
        if len(filtered_implementations) != len(target_implementations):
            missing = set(target_implementations) - set(filtered_implementations)
            print(f"   Missing: {', '.join(missing)}")
        print()
        
        # 実装をロード
        implementations = self.load_implementations(filtered_implementations)
        
        if not implementations:
            print("❌ No implementations could be loaded. Aborting benchmark.")
            return []
        
        # ベンチマーク実行
        results = self.run_all_scenarios(implementations, scenarios)
        
        # 結果サマリーを出力
        self._print_benchmark_summary(results, implementations)
        
        return results
    
    def _print_benchmark_summary(
        self,
        results: List[BenchmarkResult],
        implementations: List[Implementation]
    ) -> None:
        """ベンチマーク結果のサマリーを出力
        
        Args:
            results: ベンチマーク結果
            implementations: 実行された実装
        """
        print(f"\n{'='*80}")
        print(f"BENCHMARK SUMMARY")
        print(f"{'='*80}")
        
        # 実装別の成功/失敗統計
        impl_stats = {}
        for result in results:
            impl = result.implementation_name
            if impl not in impl_stats:
                impl_stats[impl] = {'success': 0, 'error': 0}
            
            if result.status == "SUCCESS":
                impl_stats[impl]['success'] += 1
            else:
                impl_stats[impl]['error'] += 1
        
        print(f"\nImplementation Statistics:")
        print(f"{'Implementation':<15} {'Language':<10} {'Success':<8} {'Errors':<8} {'Status'}")
        print(f"{'-'*60}")
        
        language_map = {
            # 拡張版実装
            "python": "Python", "numpy_impl": "NumPy", "c_ext": "C Extension",
            "cpp_ext": "C++ Extension", "cython_ext": "Cython Extension", "rust_ext": "Rust Extension",
            "fortran_ext": "Fortran Extension", "julia_ext": "Julia Extension", "go_ext": "Go Extension",
            "zig_ext": "Zig Extension", "nim_ext": "Nim Extension", "kotlin_ext": "Kotlin Extension",
            # FFI実装
            "c_ffi": "C FFI", "cpp_ffi": "C++ FFI", "numpy_ffi": "NumPy FFI",
            "cython_ffi": "Cython FFI", "rust_ffi": "Rust FFI", "fortran_ffi": "Fortran FFI",
            "julia_ffi": "Julia FFI", "go_ffi": "Go FFI", "zig_ffi": "Zig FFI",
            "nim_ffi": "Nim FFI", "kotlin_ffi": "Kotlin FFI"
        }
        
        for impl in implementations:
            stats = impl_stats.get(impl.name, {'success': 0, 'error': 0})
            language = language_map.get(impl.name, "Unknown")
            status = "✓ OK" if stats['error'] == 0 else "⚠ ERRORS"
            
            print(f"{impl.name:<15} {language:<10} {stats['success']:<8} {stats['error']:<8} {status}")
        
        # エラー統計
        if self.error_handler.has_errors():
            error_stats = self.error_handler.get_implementation_statistics()
            print(f"\nError Details:")
            for impl, stats in error_stats.items():
                print(f"  {impl}: {stats['import_errors']} import, {stats['execution_errors']} runtime")
        
        print(f"\nTotal Results: {len(results)} benchmark runs completed")
        print(f"{'='*80}\n")
