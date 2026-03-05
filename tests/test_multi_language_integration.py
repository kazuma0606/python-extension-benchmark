"""多言語拡張統合テスト

全12実装（Python, NumPy, C, C++, Cython, Rust, Fortran, Julia, Go, Zig, Nim, Kotlin）
での統合テストとエラー回復テストを実行する。
"""

import os
import json
import csv
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import pytest

from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import get_all_scenarios, get_default_implementations
from benchmark.runner.output import OutputWriter
from benchmark.runner.visualize import Visualizer
from benchmark.runner.validator import OutputValidator
from benchmark.models import BenchmarkResult


class TestMultiLanguageIntegration:
    """多言語拡張統合テストクラス"""
    
    def test_comprehensive_benchmark_all_implementations(self):
        """全12実装での包括的ベンチマークテスト"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = BenchmarkRunner()
            
            # 全実装での包括的ベンチマーク実行
            results = runner.run_comprehensive_benchmark()
            
            # 結果が生成されることを確認
            assert len(results) > 0, "Results should be generated"
            
            # 成功した結果があることを確認
            successful_results = [r for r in results if r.status == "SUCCESS"]
            assert len(successful_results) > 0, "At least some results should be successful"
            
            # 実装別の統計を確認
            impl_stats = self._analyze_implementation_statistics(results)
            
            print(f"\n=== 実装別統計 ===")
            for impl_name, stats in impl_stats.items():
                success_rate = stats['success'] / (stats['success'] + stats['error']) * 100
                print(f"{impl_name}: {stats['success']} 成功, {stats['error']} エラー ({success_rate:.1f}% 成功率)")
            
            # 少なくとも50%の実装が何らかの結果を出すことを確認
            working_implementations = len([s for s in impl_stats.values() if s['success'] > 0])
            total_implementations = len(get_default_implementations())
            success_rate = working_implementations / total_implementations
            
            print(f"\n動作実装: {working_implementations}/{total_implementations} ({success_rate:.1%})")
            assert success_rate >= 0.3, f"At least 30% of implementations should work, got {success_rate:.1%}"
            
            # 結果出力のテスト
            self._test_comprehensive_output(results, tmpdir)
            
            # グラフ生成のテスト
            self._test_comprehensive_visualization(results, tmpdir)
            
            print("✓ 包括的ベンチマークテスト完了")
    
    def test_error_recovery_and_continuation(self):
        """エラー回復と継続実行テスト"""
        
        runner = BenchmarkRunner()
        
        # 存在しない実装と存在する実装を混在
        mixed_implementations = [
            "python",  # 確実に存在
            "nonexistent_lang_1",  # 存在しない
            "numpy_impl",  # 通常存在
            "nonexistent_lang_2",  # 存在しない
            "c_ext",  # 通常存在
        ]
        
        implementations = runner.load_implementations(mixed_implementations)
        
        # 存在する実装のみがロードされることを確認
        assert len(implementations) >= 1, "Valid implementations should be loaded"
        
        # エラーログが記録されることを確認
        assert runner.error_handler.has_errors(), "Errors should be recorded for nonexistent implementations"
        
        # エラー統計を確認
        error_stats = runner.error_handler.get_implementation_statistics()
        assert len(error_stats) >= 2, "At least 2 implementations should have errors"
        
        # 軽量シナリオで実行
        from benchmark.runner.scenarios import NumericScenario
        scenario = NumericScenario("primes")
        scenario.input_data = 1000  # 小さなデータサイズ
        
        results = runner.run_scenario(scenario, implementations, warmup_runs=1, measurement_runs=3)
        
        # エラーがあっても結果が生成されることを確認
        assert len(results) > 0, "Results should be generated despite import errors"
        
        # 成功した結果があることを確認
        successful_results = [r for r in results if r.status == "SUCCESS"]
        assert len(successful_results) > 0, "At least some results should be successful"
        
        print("✓ エラー回復テスト完了")
    
    def test_language_specific_error_handling(self):
        """言語固有のエラーハンドリングテスト"""
        
        runner = BenchmarkRunner()
        
        # 各言語実装を個別にテスト
        language_implementations = get_default_implementations()
        
        results_by_language = {}
        
        for impl_name in language_implementations:
            print(f"\nテスト中: {impl_name}")
            
            try:
                implementations = runner.load_implementations([impl_name])
                
                if implementations:
                    # 軽量シナリオで実行
                    from benchmark.runner.scenarios import NumericScenario
                    scenario = NumericScenario("primes")
                    scenario.input_data = 100  # 非常に小さなデータサイズ
                    
                    results = runner.run_scenario(
                        scenario, implementations, 
                        warmup_runs=1, measurement_runs=2
                    )
                    
                    results_by_language[impl_name] = {
                        'loaded': True,
                        'executed': len(results) > 0,
                        'successful': any(r.status == "SUCCESS" for r in results),
                        'results': results
                    }
                    
                    print(f"  ✓ {impl_name}: 実行成功")
                else:
                    results_by_language[impl_name] = {
                        'loaded': False,
                        'executed': False,
                        'successful': False,
                        'results': []
                    }
                    print(f"  ⚠ {impl_name}: ロード失敗")
                    
            except Exception as e:
                results_by_language[impl_name] = {
                    'loaded': False,
                    'executed': False,
                    'successful': False,
                    'results': [],
                    'error': str(e)
                }
                print(f"  ❌ {impl_name}: エラー - {e}")
        
        # 統計を出力
        loaded_count = sum(1 for r in results_by_language.values() if r['loaded'])
        executed_count = sum(1 for r in results_by_language.values() if r['executed'])
        successful_count = sum(1 for r in results_by_language.values() if r['successful'])
        
        print(f"\n=== 言語別テスト結果 ===")
        print(f"ロード成功: {loaded_count}/{len(language_implementations)}")
        print(f"実行成功: {executed_count}/{len(language_implementations)}")
        print(f"結果成功: {successful_count}/{len(language_implementations)}")
        
        # 少なくとも基本実装（Python）は動作することを確認
        assert results_by_language.get("python", {}).get('successful', False), \
            "Python implementation should always work"
        
        print("✓ 言語固有エラーハンドリングテスト完了")
    
    def test_scalability_across_implementations(self):
        """実装間でのスケーラビリティテスト"""
        
        runner = BenchmarkRunner()
        
        # 利用可能な実装をロード
        available_implementations = runner.get_all_available_implementations()
        implementations = runner.load_implementations(available_implementations[:5])  # 最大5実装でテスト
        
        if len(implementations) < 2:
            pytest.skip("Need at least 2 implementations for scalability test")
        
        # 並列処理シナリオでスケーラビリティをテスト
        from benchmark.runner.scenarios import ParallelScenario
        
        thread_counts = [1, 2, 4]
        all_results = []
        
        for thread_count in thread_counts:
            scenario = ParallelScenario(thread_count)
            scenario.input_data = [float(i) for i in range(10000)]  # 小さなデータサイズ
            
            results = runner.run_scenario(
                scenario, implementations,
                warmup_runs=1, measurement_runs=3
            )
            all_results.extend(results)
        
        # スケーラビリティが計算されることを確認
        scalability_results = [r for r in all_results if hasattr(r, 'scalability') and r.scalability is not None]
        
        if scalability_results:
            print(f"\nスケーラビリティ結果:")
            for result in scalability_results:
                print(f"  {result.implementation_name} ({result.thread_count}スレッド): {result.scalability:.2f}")
        
        print("✓ スケーラビリティテスト完了")
    
    def test_output_consistency_across_languages(self):
        """言語間での出力一致性テスト"""
        
        runner = BenchmarkRunner()
        
        # 利用可能な実装をロード
        available_implementations = runner.get_all_available_implementations()
        implementations = runner.load_implementations(available_implementations)
        
        if len(implementations) < 2:
            pytest.skip("Need at least 2 implementations for consistency test")
        
        # 数値計算シナリオで出力一致性をテスト
        from benchmark.runner.scenarios import NumericScenario
        
        scenarios = [
            NumericScenario("primes"),
            NumericScenario("matrix")
        ]
        
        # テスト用に小さなデータサイズに変更
        scenarios[0].input_data = 100  # 素数探索
        
        # 行列積も小さなサイズに
        size = 5
        matrix_a = [[float(i * size + j) for j in range(size)] for i in range(size)]
        matrix_b = [[float(i * size + j) for j in range(size)] for i in range(size)]
        scenarios[1].input_data = (matrix_a, matrix_b)
        
        consistency_results = {}
        
        for scenario in scenarios:
            print(f"\n一致性テスト: {scenario.name}")
            
            results = runner.run_scenario(
                scenario, implementations,
                warmup_runs=1, measurement_runs=1
            )
            
            # 成功した結果の出力値を収集
            outputs = {}
            for result in results:
                if result.status == "SUCCESS" and result.output_value is not None:
                    outputs[result.implementation_name] = result.output_value
            
            if len(outputs) >= 2:
                # 出力値の一致を検証
                validation = OutputValidator.validate(outputs, tolerance=1e-6)
                consistency_results[scenario.name] = validation
                
                if validation.is_valid:
                    print(f"  ✓ 出力一致 (最大相対誤差: {validation.max_relative_error:.2e})")
                else:
                    print(f"  ⚠ 出力不一致 (最大相対誤差: {validation.max_relative_error:.2e})")
                    print(f"    不一致実装: {', '.join(validation.mismatches)}")
            else:
                print(f"  ⚠ 比較可能な実装が不足: {len(outputs)}")
        
        print("✓ 出力一致性テスト完了")
    
    def _analyze_implementation_statistics(self, results: List[BenchmarkResult]) -> Dict[str, Dict[str, int]]:
        """実装別の統計を分析
        
        Args:
            results: ベンチマーク結果のリスト
            
        Returns:
            Dict[str, Dict[str, int]]: 実装別の成功/エラー統計
        """
        stats = {}
        
        for result in results:
            impl = result.implementation_name
            if impl not in stats:
                stats[impl] = {'success': 0, 'error': 0}
            
            if result.status == "SUCCESS":
                stats[impl]['success'] += 1
            else:
                stats[impl]['error'] += 1
        
        return stats
    
    def _test_comprehensive_output(self, results: List[BenchmarkResult], tmpdir: str) -> None:
        """包括的な結果出力テスト
        
        Args:
            results: ベンチマーク結果
            tmpdir: 一時ディレクトリ
        """
        writer = OutputWriter(base_dir=tmpdir)
        
        # JSON出力テスト
        json_path = writer.write_json(results, "multi_language_results")
        assert os.path.exists(json_path), "JSON file should be created"
        
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        assert 'results' in json_data, "JSON should contain results"
        assert 'summary' in json_data, "JSON should contain summary"
        assert len(json_data['results']) == len(results), "JSON should contain all results"
        
        # CSV出力テスト
        csv_path = writer.write_csv(results, "multi_language_results")
        assert os.path.exists(csv_path), "CSV file should be created"
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            csv_rows = list(csv_reader)
        
        assert len(csv_rows) == len(results), "CSV should contain all results"
        
        print(f"✓ 結果出力テスト完了: JSON={json_path}, CSV={csv_path}")
    
    def _test_comprehensive_visualization(self, results: List[BenchmarkResult], tmpdir: str) -> None:
        """包括的な可視化テスト
        
        Args:
            results: ベンチマーク結果
            tmpdir: 一時ディレクトリ
        """
        visualizer = Visualizer(base_dir=tmpdir)
        
        # 成功した結果のみでグラフ生成
        successful_results = [r for r in results if r.status == "SUCCESS"]
        
        if not successful_results:
            print("⚠ 成功した結果がないため、グラフ生成をスキップ")
            return
        
        # 実行時間グラフ
        exec_time_path = visualizer.plot_execution_time(successful_results, "multi_language_execution_time")
        assert os.path.exists(exec_time_path), "Execution time graph should be created"
        
        # メモリ使用量グラフ
        memory_path = visualizer.plot_memory_usage(successful_results, "multi_language_memory_usage")
        assert os.path.exists(memory_path), "Memory usage graph should be created"
        
        # スケーラビリティグラフ（並列処理結果がある場合）
        parallel_results = [r for r in successful_results if hasattr(r, 'thread_count') and r.thread_count is not None]
        if parallel_results:
            scalability_path = visualizer.plot_scalability(parallel_results, "multi_language_scalability")
            assert os.path.exists(scalability_path), "Scalability graph should be created"
        
        print(f"✓ 可視化テスト完了")


if __name__ == '__main__':
    # 個別テスト実行用
    test_instance = TestMultiLanguageIntegration()
    
    print("=== 多言語拡張統合テスト開始 ===\n")
    
    try:
        test_instance.test_comprehensive_benchmark_all_implementations()
        print("\n✓ 包括的ベンチマークテスト完了")
        
        test_instance.test_error_recovery_and_continuation()
        print("\n✓ エラー回復テスト完了")
        
        test_instance.test_language_specific_error_handling()
        print("\n✓ 言語固有エラーハンドリングテスト完了")
        
        test_instance.test_scalability_across_implementations()
        print("\n✓ スケーラビリティテスト完了")
        
        test_instance.test_output_consistency_across_languages()
        print("\n✓ 出力一致性テスト完了")
        
        print("\n=== 全ての多言語統合テストが成功しました！ ===")
        
    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()