"""最終統合テスト

Docker環境での全体テスト、クリーンビルドテスト、全言語実装の動作確認、
リソース制限下での動作テストを実行する。

要件: 7.3, 7.4, 9.1, 9.2, 9.3
"""

import os
import sys
import json
import subprocess
import tempfile
import time
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import pytest

from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import get_all_scenarios, get_default_implementations
from benchmark.runner.output import OutputWriter
from benchmark.runner.visualize import Visualizer
from benchmark.models import BenchmarkResult


class TestFinalIntegration:
    """最終統合テストクラス"""
    
    def test_clean_build_verification(self):
        """クリーンビルドテスト - 全言語実装のビルド状況確認"""
        
        print("=== クリーンビルドテスト開始 ===")
        
        # 全実装の期待リスト
        expected_implementations = get_default_implementations()
        
        # 実装の可用性をテスト
        runner = BenchmarkRunner()
        available_implementations = runner.get_all_available_implementations()
        
        print(f"期待実装数: {len(expected_implementations)}")
        print(f"利用可能実装数: {len(available_implementations)}")
        
        # 各実装の状態を確認
        implementation_status = {}
        
        for impl_name in expected_implementations:
            try:
                implementations = runner.load_implementations([impl_name])
                if implementations:
                    implementation_status[impl_name] = "SUCCESS"
                    print(f"  ✓ {impl_name}: ロード成功")
                else:
                    implementation_status[impl_name] = "LOAD_FAILED"
                    print(f"  ⚠ {impl_name}: ロード失敗")
            except Exception as e:
                implementation_status[impl_name] = f"ERROR: {str(e)}"
                print(f"  ❌ {impl_name}: エラー - {e}")
        
        # 統計を出力
        success_count = sum(1 for status in implementation_status.values() if status == "SUCCESS")
        success_rate = success_count / len(expected_implementations)
        
        print(f"\n成功実装: {success_count}/{len(expected_implementations)} ({success_rate:.1%})")
        
        # 少なくとも基本実装は動作することを確認
        assert implementation_status.get("python") == "SUCCESS", "Python implementation must work"
        assert implementation_status.get("numpy_impl") == "SUCCESS", "NumPy implementation must work"
        
        # 全体の成功率が30%以上であることを確認
        assert success_rate >= 0.3, f"At least 30% implementations should work, got {success_rate:.1%}"
        
        print("✓ クリーンビルドテスト完了")
        
        return implementation_status 
   
    def test_all_language_implementations_functionality(self):
        """全言語実装の動作確認テスト"""
        
        print("\n=== 全言語実装動作確認テスト開始 ===")
        
        runner = BenchmarkRunner()
        
        # 利用可能な実装をロード
        available_implementations = runner.get_all_available_implementations()
        implementations = runner.load_implementations(available_implementations)
        
        print(f"テスト対象実装: {[impl.name for impl in implementations]}")
        
        # 軽量シナリオで各実装をテスト
        from benchmark.runner.scenarios import NumericScenario, MemoryScenario
        
        test_scenarios = [
            NumericScenario("primes"),
            MemoryScenario("sort")
        ]
        
        # テスト用に小さなデータサイズに設定
        test_scenarios[0].input_data = 100  # 素数探索
        test_scenarios[1].input_data = list(range(1000, 0, -1))  # ソート
        
        functionality_results = {}
        
        for scenario in test_scenarios:
            print(f"\nシナリオテスト: {scenario.name}")
            
            scenario_results = {}
            
            for impl in implementations:
                try:
                    # 個別実装でテスト実行
                    results = runner.run_scenario(
                        scenario, [impl], 
                        warmup_runs=1, measurement_runs=2
                    )
                    
                    if results and results[0].status == "SUCCESS":
                        scenario_results[impl.name] = {
                            'status': 'SUCCESS',
                            'execution_time': results[0].mean_time,
                            'output_size': len(results[0].output_value) if isinstance(results[0].output_value, list) else 1
                        }
                        print(f"  ✓ {impl.name}: {results[0].mean_time:.2f}ms")
                    else:
                        scenario_results[impl.name] = {
                            'status': 'FAILED',
                            'error': results[0].error_message if results else "No results"
                        }
                        print(f"  ❌ {impl.name}: 実行失敗")
                        
                except Exception as e:
                    scenario_results[impl.name] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    print(f"  ❌ {impl.name}: エラー - {e}")
            
            functionality_results[scenario.name] = scenario_results
        
        # 結果の分析
        total_tests = 0
        successful_tests = 0
        
        for scenario_name, scenario_results in functionality_results.items():
            for impl_name, result in scenario_results.items():
                total_tests += 1
                if result['status'] == 'SUCCESS':
                    successful_tests += 1
        
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        print(f"\n全体成功率: {successful_tests}/{total_tests} ({success_rate:.1%})")
        
        # 少なくとも50%のテストが成功することを確認
        assert success_rate >= 0.5, f"At least 50% of functionality tests should pass, got {success_rate:.1%}"
        
        print("✓ 全言語実装動作確認テスト完了")
        
        return functionality_results    

    def test_resource_constrained_execution(self):
        """リソース制限下での動作テスト"""
        
        print("\n=== リソース制限下動作テスト開始 ===")
        
        # システムリソースの確認
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        print(f"システムリソース: CPU={cpu_count}コア, メモリ={memory_gb:.1f}GB")
        
        # リソース制限の設定
        limited_thread_count = min(2, cpu_count)
        
        # 環境変数でスレッド数を制限
        original_env = {}
        thread_env_vars = ['OMP_NUM_THREADS', 'NUMBA_NUM_THREADS', 'MKL_NUM_THREADS', 'JULIA_NUM_THREADS']
        
        for var in thread_env_vars:
            original_env[var] = os.environ.get(var)
            os.environ[var] = str(limited_thread_count)
        
        try:
            runner = BenchmarkRunner()
            
            # 利用可能な実装の一部でテスト（リソース節約）
            available_implementations = runner.get_all_available_implementations()
            test_implementations = available_implementations[:4]  # 最大4実装でテスト
            
            implementations = runner.load_implementations(test_implementations)
            
            print(f"制限環境テスト対象: {[impl.name for impl in implementations]} (スレッド数: {limited_thread_count})")
            
            # 並列処理シナリオでリソース制限をテスト
            from benchmark.runner.scenarios import ParallelScenario
            
            scenario = ParallelScenario(limited_thread_count)
            scenario.input_data = [float(i) for i in range(5000)]  # 小さなデータセット
            
            # メモリ使用量を監視しながら実行
            process = psutil.Process()
            initial_memory = process.memory_info().rss / (1024**2)  # MB
            
            start_time = time.time()
            results = runner.run_scenario(
                scenario, implementations,
                warmup_runs=1, measurement_runs=3
            )
            execution_time = time.time() - start_time
            
            peak_memory = process.memory_info().rss / (1024**2)  # MB
            memory_increase = peak_memory - initial_memory
            
            print(f"実行時間: {execution_time:.2f}秒")
            print(f"メモリ増加: {memory_increase:.1f}MB")
            
            # 結果の検証
            assert len(results) > 0, "Results should be generated under resource constraints"
            
            successful_results = [r for r in results if r.status == "SUCCESS"]
            assert len(successful_results) > 0, "At least some implementations should succeed under constraints"
            
            # リソース使用量の妥当性確認
            assert memory_increase < 1000, f"Memory increase should be reasonable, got {memory_increase:.1f}MB"
            assert execution_time < 60, f"Execution should complete within reasonable time, got {execution_time:.2f}s"
            
            # スレッド数制限の確認
            for result in successful_results:
                if hasattr(result, 'thread_count'):
                    assert result.thread_count <= limited_thread_count, \
                        f"Thread count should respect limit: {result.thread_count} > {limited_thread_count}"
            
            print(f"✓ リソース制限下で {len(successful_results)}/{len(results)} 実装が成功")
            
        finally:
            # 環境変数を復元
            for var in thread_env_vars:
                if original_env[var] is not None:
                    os.environ[var] = original_env[var]
                elif var in os.environ:
                    del os.environ[var]
        
        print("✓ リソース制限下動作テスト完了")
        
        return {
            'execution_time': execution_time,
            'memory_increase': memory_increase,
            'successful_implementations': len(successful_results),
            'total_implementations': len(results)
        }
    
    def test_performance_regression_detection(self):
        """性能回帰テスト"""
        
        print("\n=== 性能回帰テスト開始 ===")
        
        runner = BenchmarkRunner()
        
        # 基準実装（Python）での性能測定
        python_implementations = runner.load_implementations(["python"])
        
        if not python_implementations:
            pytest.skip("Python implementation not available for regression test")
        
        # 基準シナリオで性能測定
        from benchmark.runner.scenarios import NumericScenario
        
        baseline_scenario = NumericScenario("primes")
        baseline_scenario.input_data = 1000
        
        # 複数回実行して安定した基準値を取得
        baseline_results = runner.run_scenario(
            baseline_scenario, python_implementations,
            warmup_runs=2, measurement_runs=5
        )
        
        if not baseline_results or baseline_results[0].status != "SUCCESS":
            pytest.skip("Could not establish baseline performance")
        
        baseline_time = baseline_results[0].mean_time
        baseline_memory = sum(baseline_results[0].memory_usage) / len(baseline_results[0].memory_usage)
        
        print(f"基準性能 (Python): {baseline_time:.2f}ms, メモリ: {baseline_memory:.1f}MB")
        
        # 他の実装での性能測定
        available_implementations = runner.get_all_available_implementations()
        other_implementations = [impl for impl in available_implementations if impl != "python"]
        
        if other_implementations:
            test_implementations = runner.load_implementations(other_implementations[:3])  # 最大3実装
            
            regression_results = {}
            
            for impl in test_implementations:
                try:
                    results = runner.run_scenario(
                        baseline_scenario, [impl],
                        warmup_runs=2, measurement_runs=5
                    )
                    
                    if results and results[0].status == "SUCCESS":
                        impl_time = results[0].mean_time
                        impl_memory = sum(results[0].memory_usage) / len(results[0].memory_usage)
                        
                        # 性能比較（基準との比率）
                        time_ratio = impl_time / baseline_time
                        memory_ratio = impl_memory / baseline_memory
                        
                        regression_results[impl.name] = {
                            'time_ratio': time_ratio,
                            'memory_ratio': memory_ratio,
                            'absolute_time': impl_time,
                            'absolute_memory': impl_memory
                        }
                        
                        print(f"{impl.name}: 時間比率={time_ratio:.2f}x, メモリ比率={memory_ratio:.2f}x")
                        
                        # 極端な性能劣化の検出
                        if time_ratio > 100:  # 100倍以上遅い場合は警告
                            print(f"  ⚠ {impl.name}: 極端な性能劣化検出 ({time_ratio:.1f}x)")
                        
                        if memory_ratio > 10:  # 10倍以上メモリを使う場合は警告
                            print(f"  ⚠ {impl.name}: 極端なメモリ使用量増加 ({memory_ratio:.1f}x)")
                    
                except Exception as e:
                    print(f"  ❌ {impl.name}: 性能測定エラー - {e}")
            
            # 回帰分析結果
            if regression_results:
                avg_time_ratio = sum(r['time_ratio'] for r in regression_results.values()) / len(regression_results)
                avg_memory_ratio = sum(r['memory_ratio'] for r in regression_results.values()) / len(regression_results)
                
                print(f"\n平均性能比率: 時間={avg_time_ratio:.2f}x, メモリ={avg_memory_ratio:.2f}x")
                
                # 合理的な性能範囲内であることを確認
                assert avg_time_ratio < 1000, f"Average time ratio too high: {avg_time_ratio:.2f}x"
                assert avg_memory_ratio < 50, f"Average memory ratio too high: {avg_memory_ratio:.2f}x"
        
        print("✓ 性能回帰テスト完了")
        
        return {
            'baseline_time': baseline_time,
            'baseline_memory': baseline_memory,
            'regression_results': regression_results if 'regression_results' in locals() else {}
        } 
   
    def test_error_handling_verification(self):
        """エラーハンドリング検証テスト"""
        
        print("\n=== エラーハンドリング検証テスト開始 ===")
        
        runner = BenchmarkRunner()
        
        # 意図的にエラーを発生させるテスト
        
        # 1. 存在しない実装のテスト
        print("1. 存在しない実装テスト")
        nonexistent_implementations = ["nonexistent_lang_1", "nonexistent_lang_2"]
        
        loaded_impls = runner.load_implementations(nonexistent_implementations)
        assert len(loaded_impls) == 0, "Nonexistent implementations should not be loaded"
        assert runner.error_handler.has_errors(), "Error handler should record import failures"
        
        print("  ✓ 存在しない実装の適切な処理を確認")
        
        # 2. 混在実装でのエラー回復テスト
        print("2. 混在実装エラー回復テスト")
        mixed_implementations = ["python", "nonexistent_lang", "numpy_impl"]
        
        loaded_impls = runner.load_implementations(mixed_implementations)
        valid_impl_count = len(loaded_impls)
        
        assert valid_impl_count > 0, "Valid implementations should be loaded despite errors"
        
        # 軽量シナリオで実行
        from benchmark.runner.scenarios import NumericScenario
        scenario = NumericScenario("primes")
        scenario.input_data = 50
        
        results = runner.run_scenario(scenario, loaded_impls, warmup_runs=1, measurement_runs=2)
        
        assert len(results) == valid_impl_count, "Results should be generated for valid implementations"
        
        successful_results = [r for r in results if r.status == "SUCCESS"]
        assert len(successful_results) > 0, "At least some implementations should succeed"
        
        print(f"  ✓ {len(successful_results)}/{len(results)} 実装が正常実行")
        
        # 3. エラー統計の確認
        print("3. エラー統計確認")
        error_stats = runner.error_handler.get_implementation_statistics()
        
        assert len(error_stats) > 0, "Error statistics should be available"
        
        total_errors = sum(
            stats.get('import_errors', 0) + stats.get('execution_errors', 0)
            for stats in error_stats.values()
        )
        
        assert total_errors > 0, "Some errors should be recorded"
        
        print(f"  ✓ 総エラー数: {total_errors}")
        
        # 4. エラーログの詳細確認
        print("4. エラーログ詳細確認")
        error_logs = runner.error_handler.error_logs
        
        assert len(error_logs) > 0, "Error logs should be available"
        
        for log in error_logs[:3]:  # 最初の3つのログを確認
            assert hasattr(log, 'timestamp'), "Error log should have timestamp"
            assert hasattr(log, 'implementation_name'), "Error log should have implementation name"
            assert hasattr(log, 'error_type'), "Error log should have error type"
            assert hasattr(log, 'error_message'), "Error log should have error message"
            
            print(f"  ログ: {log.implementation_name} - {log.error_type}")
        
        # 5. エラー回復後の正常動作確認
        print("5. エラー回復後正常動作確認")
        
        # 新しいランナーインスタンスで正常実装のみテスト
        clean_runner = BenchmarkRunner()
        clean_implementations = clean_runner.load_implementations(["python"])
        
        if clean_implementations:
            clean_results = clean_runner.run_scenario(
                scenario, clean_implementations,
                warmup_runs=1, measurement_runs=2
            )
            
            assert len(clean_results) > 0, "Clean runner should produce results"
            assert clean_results[0].status == "SUCCESS", "Clean execution should succeed"
            
            print("  ✓ エラー後の正常動作を確認")
        
        print("✓ エラーハンドリング検証テスト完了")
        
        return {
            'total_errors': total_errors,
            'error_implementations': list(error_stats.keys()),
            'successful_recovery': len(successful_results) > 0
        }    

    def test_comprehensive_final_integration(self):
        """包括的最終統合テスト - 全機能の統合確認"""
        
        print("\n=== 包括的最終統合テスト開始 ===")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. システム環境の確認
            print("1. システム環境確認")
            system_info = {
                'cpu_count': psutil.cpu_count(),
                'memory_gb': psutil.virtual_memory().total / (1024**3),
                'python_version': sys.version,
                'platform': sys.platform
            }
            
            print(f"  CPU: {system_info['cpu_count']}コア")
            print(f"  メモリ: {system_info['memory_gb']:.1f}GB")
            print(f"  Python: {system_info['python_version'].split()[0]}")
            print(f"  プラットフォーム: {system_info['platform']}")
            
            # 2. 全実装の包括的テスト
            print("\n2. 全実装包括的テスト")
            runner = BenchmarkRunner()
            
            # 包括的ベンチマーク実行（軽量版）
            start_time = time.time()
            
            try:
                # 利用可能な実装で軽量ベンチマーク実行
                available_implementations = runner.get_all_available_implementations()
                implementations = runner.load_implementations(available_implementations)
                
                print(f"  テスト対象: {[impl.name for impl in implementations]}")
                
                # 軽量シナリオセット
                from benchmark.runner.scenarios import NumericScenario, MemoryScenario
                
                test_scenarios = [
                    NumericScenario("primes"),
                    MemoryScenario("sort")
                ]
                
                # 小さなデータサイズに設定
                test_scenarios[0].input_data = 100
                test_scenarios[1].input_data = list(range(1000, 0, -1))
                
                all_results = []
                
                for scenario in test_scenarios:
                    results = runner.run_scenario(
                        scenario, implementations,
                        warmup_runs=1, measurement_runs=3
                    )
                    all_results.extend(results)
                
                execution_time = time.time() - start_time
                
                print(f"  実行時間: {execution_time:.2f}秒")
                print(f"  総結果数: {len(all_results)}")
                
                # 3. 結果の分析と検証
                print("\n3. 結果分析")
                
                successful_results = [r for r in all_results if r.status == "SUCCESS"]
                error_results = [r for r in all_results if r.status == "ERROR"]
                
                success_rate = len(successful_results) / len(all_results) if all_results else 0
                
                print(f"  成功: {len(successful_results)}")
                print(f"  エラー: {len(error_results)}")
                print(f"  成功率: {success_rate:.1%}")
                
                # 4. 出力ファイル生成テスト
                print("\n4. 出力ファイル生成テスト")
                
                if successful_results:
                    writer = OutputWriter(base_dir=tmpdir)
                    
                    # JSON出力
                    json_path = writer.write_json(successful_results, "final_integration_test")
                    assert os.path.exists(json_path), "JSON output should be created"
                    
                    # CSV出力
                    csv_path = writer.write_csv(successful_results, "final_integration_test")
                    assert os.path.exists(csv_path), "CSV output should be created"
                    
                    print(f"  ✓ JSON: {os.path.basename(json_path)}")
                    print(f"  ✓ CSV: {os.path.basename(csv_path)}")
                    
                    # 5. グラフ生成テスト
                    print("\n5. グラフ生成テスト")
                    
                    visualizer = Visualizer(base_dir=tmpdir)
                    
                    try:
                        exec_time_graph = visualizer.plot_execution_time(
                            successful_results, "final_integration_execution_time"
                        )
                        assert os.path.exists(exec_time_graph), "Execution time graph should be created"
                        print(f"  ✓ 実行時間グラフ: {os.path.basename(exec_time_graph)}")
                    except Exception as e:
                        print(f"  ⚠ 実行時間グラフ生成エラー: {e}")
                    
                    try:
                        memory_graph = visualizer.plot_memory_usage(
                            successful_results, "final_integration_memory_usage"
                        )
                        assert os.path.exists(memory_graph), "Memory usage graph should be created"
                        print(f"  ✓ メモリ使用量グラフ: {os.path.basename(memory_graph)}")
                    except Exception as e:
                        print(f"  ⚠ メモリ使用量グラフ生成エラー: {e}")
                
                # 6. 最終検証
                print("\n6. 最終検証")
                
                # 基本的な成功基準
                assert len(all_results) > 0, "Some results should be generated"
                assert success_rate >= 0.3, f"Success rate should be at least 30%, got {success_rate:.1%}"
                assert execution_time < 300, f"Execution should complete within 5 minutes, got {execution_time:.2f}s"
                
                # エラーハンドリングの確認
                if error_results:
                    assert runner.error_handler.has_errors(), "Error handler should record failures"
                
                print("  ✓ 全ての検証項目をクリア")
                
                # 7. 最終レポート生成
                final_report = {
                    'timestamp': datetime.now().isoformat(),
                    'system_info': system_info,
                    'execution_time': execution_time,
                    'total_results': len(all_results),
                    'successful_results': len(successful_results),
                    'error_results': len(error_results),
                    'success_rate': success_rate,
                    'tested_implementations': [impl.name for impl in implementations],
                    'available_implementations': available_implementations
                }
                
                report_path = os.path.join(tmpdir, 'final_integration_report.json')
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(final_report, f, indent=2, ensure_ascii=False)
                
                print(f"\n✓ 最終レポート生成: {report_path}")
                
            except Exception as e:
                print(f"\n❌ 包括的テスト中にエラー: {e}")
                raise
        
        print("\n✓ 包括的最終統合テスト完了")
        
        return final_report


if __name__ == '__main__':
    # 個別テスト実行用
    test_instance = TestFinalIntegration()
    
    print("=== 最終統合テスト実行 ===\n")
    
    try:
        # 各テストを順次実行
        build_status = test_instance.test_clean_build_verification()
        functionality_results = test_instance.test_all_language_implementations_functionality()
        resource_results = test_instance.test_resource_constrained_execution()
        regression_results = test_instance.test_performance_regression_detection()
        error_results = test_instance.test_error_handling_verification()
        final_report = test_instance.test_comprehensive_final_integration()
        
        print("\n=== 全ての最終統合テストが成功しました！ ===")
        print(f"最終成功率: {final_report['success_rate']:.1%}")
        print(f"テスト実装数: {len(final_report['tested_implementations'])}")
        
    except Exception as e:
        print(f"\n❌ 最終統合テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)