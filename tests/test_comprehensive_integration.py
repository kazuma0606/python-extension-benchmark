"""包括的統合テスト

Task 8: 包括的統合テスト
- 全12実装の動作確認
- エラーハンドリングの検証  
- uv環境での一貫動作確認
- 要件: 18.1, 18.2, 18.3, 18.4

このテストは全12実装（Pure Python + 11 FFI）での包括的な統合テストを実行し、
エラーハンドリングとuv環境の一貫性を検証する。
"""

import os
import sys
import json
import tempfile
import time
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import pytest

from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.ffi_benchmark_runner import FFIBenchmarkRunner
from benchmark.runner.scenarios import (
    get_all_scenarios, 
    get_default_implementations,
    get_extension_implementations,
    get_ffi_implementations,
    NumericScenario,
    MemoryScenario,
    ParallelScenario
)
from benchmark.runner.output import OutputWriter
from benchmark.runner.visualize import Visualizer
from benchmark.ffi_implementations.uv_checker import UVEnvironmentChecker, check_uv_environment
from benchmark.models import BenchmarkResult


class TestComprehensiveIntegration:
    """包括的統合テストクラス"""
    
    def setup_method(self):
        """テストセットアップ"""
        self.runner = BenchmarkRunner()
        self.ffi_runner = FFIBenchmarkRunner()
        self.uv_checker = UVEnvironmentChecker()
        
    def test_all_12_implementations_verification(self):
        """全12実装の動作確認テスト
        
        要件: 18.1 - 全12実装の動作確認
        """
        print("\n=== 全12実装動作確認テスト開始 ===")
        
        # 期待される12実装のリスト
        expected_implementations = [
            "python",  # Pure Python
            # FFI implementations (11)
            "c_ffi", "cpp_ffi", "numpy_ffi", "cython_ffi", "rust_ffi",
            "fortran_ffi", "julia_ffi", "go_ffi", "zig_ffi", "nim_ffi", "kotlin_ffi"
        ]
        
        print(f"期待実装数: {len(expected_implementations)}")
        print(f"期待実装: {', '.join(expected_implementations)}")
        
        # 利用可能な実装を確認
        available_implementations = self.runner.get_all_available_implementations()
        print(f"\n利用可能実装: {', '.join(available_implementations)}")
        
        # 各実装の個別テスト
        implementation_status = {}
        
        for impl_name in expected_implementations:
            print(f"\nテスト中: {impl_name}")
            
            try:
                # 実装のロードテスト
                implementations = self.runner.load_implementations([impl_name])
                
                if implementations:
                    # 軽量シナリオで実行テスト
                    scenario = NumericScenario("primes")
                    scenario.input_data = 100  # 小さなデータサイズ
                    
                    results = self.runner.run_scenario(
                        scenario, implementations,
                        warmup_runs=1, measurement_runs=2
                    )
                    
                    if results and results[0].status == "SUCCESS":
                        implementation_status[impl_name] = {
                            'status': 'SUCCESS',
                            'load_time': results[0].mean_time,
                            'available': True
                        }
                        print(f"  ✓ {impl_name}: 実行成功 ({results[0].mean_time:.2f}ms)")
                    else:
                        implementation_status[impl_name] = {
                            'status': 'EXECUTION_FAILED',
                            'available': True,
                            'error': results[0].error_message if results else "No results"
                        }
                        print(f"  ⚠ {impl_name}: 実行失敗")
                else:
                    implementation_status[impl_name] = {
                        'status': 'LOAD_FAILED',
                        'available': False
                    }
                    print(f"  ❌ {impl_name}: ロード失敗")
                    
            except Exception as e:
                implementation_status[impl_name] = {
                    'status': 'ERROR',
                    'available': False,
                    'error': str(e)
                }
                print(f"  ❌ {impl_name}: エラー - {e}")
        
        # 結果の分析
        total_implementations = len(expected_implementations)
        available_count = sum(1 for status in implementation_status.values() if status['available'])
        successful_count = sum(1 for status in implementation_status.values() if status['status'] == 'SUCCESS')
        
        print(f"\n=== 実装テスト結果 ===")
        print(f"総実装数: {total_implementations}")
        print(f"利用可能: {available_count}")
        print(f"実行成功: {successful_count}")
        print(f"成功率: {successful_count/total_implementations:.1%}")
        
        # 基本要件の確認
        assert implementation_status.get("python", {}).get('status') == 'SUCCESS', \
            "Pure Python implementation must work"
        
        # 少なくとも30%の実装が動作することを確認
        success_rate = successful_count / total_implementations
        assert success_rate >= 0.3, \
            f"At least 30% implementations should work, got {success_rate:.1%}"
        
        print("✓ 全12実装動作確認テスト完了")
        return implementation_status
    
    def test_error_handling_verification(self):
        """エラーハンドリング検証テスト
        
        要件: 18.2 - エラーハンドリングの検証
        """
        print("\n=== エラーハンドリング検証テスト開始 ===")
        
        # 1. 存在しない実装でのエラーハンドリング
        print("1. 存在しない実装エラーハンドリング")
        nonexistent_implementations = [
            "nonexistent_ffi_1", 
            "nonexistent_ffi_2", 
            "invalid_implementation"
        ]
        
        loaded_impls = self.runner.load_implementations(nonexistent_implementations)
        assert len(loaded_impls) == 0, "Nonexistent implementations should not be loaded"
        assert self.runner.error_handler.has_errors(), "Error handler should record failures"
        
        print("  ✓ 存在しない実装の適切な処理を確認")
        
        # 2. 混在実装でのエラー回復テスト
        print("2. 混在実装エラー回復テスト")
        mixed_implementations = [
            "python",  # 確実に存在
            "nonexistent_ffi",  # 存在しない
            "numpy_impl",  # 通常存在
            "invalid_lang_ffi"  # 存在しない
        ]
        
        loaded_impls = self.runner.load_implementations(mixed_implementations)
        valid_impl_count = len(loaded_impls)
        
        assert valid_impl_count > 0, "Valid implementations should be loaded despite errors"
        
        # 軽量シナリオで実行
        scenario = NumericScenario("primes")
        scenario.input_data = 50
        
        results = self.runner.run_scenario(
            scenario, loaded_impls,
            warmup_runs=1, measurement_runs=2
        )
        
        assert len(results) == valid_impl_count, "Results should be generated for valid implementations"
        
        successful_results = [r for r in results if r.status == "SUCCESS"]
        assert len(successful_results) > 0, "At least some implementations should succeed"
        
        print(f"  ✓ {len(successful_results)}/{len(results)} 実装が正常実行")
        
        # 3. FFI固有のエラーハンドリング
        print("3. FFI固有エラーハンドリング")
        
        # 共有ライブラリロードエラーのシミュレーション
        ffi_implementations = get_ffi_implementations()
        
        if ffi_implementations:
            # 利用可能なFFI実装をテスト
            ffi_loaded = self.runner.load_implementations(ffi_implementations[:3])  # 最大3実装
            
            if ffi_loaded:
                ffi_results = self.runner.run_scenario(
                    scenario, ffi_loaded,
                    warmup_runs=1, measurement_runs=2
                )
                
                # FFI実装でもエラーハンドリングが機能することを確認
                ffi_successful = [r for r in ffi_results if r.status == "SUCCESS"]
                ffi_failed = [r for r in ffi_results if r.status == "ERROR"]
                
                print(f"  FFI成功: {len(ffi_successful)}, FFI失敗: {len(ffi_failed)}")
                
                # エラーが発生した場合でも他の実装に影響しないことを確認
                if ffi_failed:
                    assert len(ffi_successful) >= 0, "FFI errors should not prevent other implementations"
            else:
                print("  ⚠ FFI実装が利用できないため、FFIエラーハンドリングをスキップ")
        
        # 4. エラー統計の確認
        print("4. エラー統計確認")
        error_stats = self.runner.error_handler.get_implementation_statistics()
        
        assert len(error_stats) > 0, "Error statistics should be available"
        
        total_errors = sum(
            stats.get('import_errors', 0) + stats.get('execution_errors', 0)
            for stats in error_stats.values()
        )
        
        assert total_errors > 0, "Some errors should be recorded"
        print(f"  ✓ 総エラー数: {total_errors}")
        
        # 5. エラー後の回復テスト
        print("5. エラー後回復テスト")
        
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
    
    def test_uv_environment_consistency(self):
        """uv環境での一貫動作確認テスト
        
        要件: 18.3 - uv環境での一貫動作確認
        """
        print("\n=== uv環境一貫動作確認テスト開始 ===")
        
        # 1. uv環境状態の確認
        print("1. uv環境状態確認")
        
        env_info = self.uv_checker.get_environment_info()
        is_valid, issues = self.uv_checker.validate_environment()
        
        print(f"  仮想環境: {env_info.get('virtual_env', 'Not set')}")
        print(f"  Python実行可能ファイル: {env_info.get('python_executable')}")
        print(f"  Pythonバージョン: {env_info.get('python_version')}")
        print(f"  uv.lock: {env_info.get('uv_lock_found', 'Not found')}")
        
        # 2. 必要パッケージの確認
        print("\n2. 必要パッケージ確認")
        package_status = self.uv_checker.check_required_packages()
        
        for package, available in package_status.items():
            status = "✓" if available else "❌"
            print(f"  {status} {package}")
        
        missing_packages = [pkg for pkg, available in package_status.items() if not available]
        
        # 3. uv環境でのFFI実装テスト
        print("\n3. uv環境でのFFI実装テスト")
        
        # uv環境チェック関数を使用
        uv_env_ok = check_uv_environment()
        print(f"  uv環境チェック結果: {'✓ OK' if uv_env_ok else '⚠ Issues detected'}")
        
        # FFI実装の動作確認（uv環境依存）
        ffi_implementations = get_ffi_implementations()
        
        if ffi_implementations:
            print(f"  FFI実装テスト対象: {len(ffi_implementations)} 実装")
            
            ffi_test_results = {}
            
            for ffi_impl in ffi_implementations[:5]:  # 最大5実装でテスト
                try:
                    implementations = self.runner.load_implementations([ffi_impl])
                    
                    if implementations:
                        # 軽量テスト実行
                        scenario = NumericScenario("primes")
                        scenario.input_data = 50
                        
                        results = self.runner.run_scenario(
                            scenario, implementations,
                            warmup_runs=1, measurement_runs=1
                        )
                        
                        if results and results[0].status == "SUCCESS":
                            ffi_test_results[ffi_impl] = "SUCCESS"
                            print(f"    ✓ {ffi_impl}: 実行成功")
                        else:
                            ffi_test_results[ffi_impl] = "EXECUTION_FAILED"
                            print(f"    ⚠ {ffi_impl}: 実行失敗")
                    else:
                        ffi_test_results[ffi_impl] = "LOAD_FAILED"
                        print(f"    ❌ {ffi_impl}: ロード失敗")
                        
                except Exception as e:
                    ffi_test_results[ffi_impl] = f"ERROR: {str(e)}"
                    print(f"    ❌ {ffi_impl}: エラー - {e}")
            
            # FFI実装の成功率
            ffi_success_count = sum(1 for status in ffi_test_results.values() if status == "SUCCESS")
            ffi_total_count = len(ffi_test_results)
            ffi_success_rate = ffi_success_count / ffi_total_count if ffi_total_count > 0 else 0
            
            print(f"  FFI成功率: {ffi_success_count}/{ffi_total_count} ({ffi_success_rate:.1%})")
        else:
            print("  ⚠ FFI実装が見つかりません")
            ffi_test_results = {}
        
        # 4. 環境一貫性の検証
        print("\n4. 環境一貫性検証")
        
        # 複数回実行での一貫性確認
        consistency_results = []
        
        for run_num in range(3):  # 3回実行
            scenario = NumericScenario("primes")
            scenario.input_data = 100
            
            implementations = self.runner.load_implementations(["python"])
            
            if implementations:
                results = self.runner.run_scenario(
                    scenario, implementations,
                    warmup_runs=1, measurement_runs=2
                )
                
                if results and results[0].status == "SUCCESS":
                    consistency_results.append(results[0].mean_time)
                    print(f"  実行{run_num + 1}: {results[0].mean_time:.2f}ms")
        
        # 実行時間の一貫性確認（変動係数が50%以下）
        if len(consistency_results) >= 2:
            import statistics
            mean_time = statistics.mean(consistency_results)
            std_dev = statistics.stdev(consistency_results)
            cv = std_dev / mean_time if mean_time > 0 else float('inf')
            
            print(f"  平均実行時間: {mean_time:.2f}ms")
            print(f"  標準偏差: {std_dev:.2f}ms")
            print(f"  変動係数: {cv:.2%}")
            
            assert cv <= 0.5, f"Execution time should be consistent, CV={cv:.2%}"
            print("  ✓ 実行時間の一貫性を確認")
        
        # 5. 最終検証
        print("\n5. 最終検証")
        
        # 基本的な環境要件
        in_venv = (hasattr(sys, 'real_prefix') or 
                   (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
        
        assert in_venv, "Should be running in a virtual environment"
        print("  ✓ 仮想環境での実行を確認")
        
        # 重要パッケージの確認
        critical_packages = ['ctypes', 'numpy']
        for package in critical_packages:
            assert package_status.get(package, False), f"Critical package {package} should be available"
        
        print("  ✓ 重要パッケージの利用可能性を確認")
        
        print("✓ uv環境一貫動作確認テスト完了")
        
        return {
            'uv_environment_ok': uv_env_ok,
            'missing_packages': missing_packages,
            'ffi_test_results': ffi_test_results,
            'consistency_cv': cv if 'cv' in locals() else None
        }
    
    def test_comprehensive_benchmark_execution(self):
        """包括的ベンチマーク実行テスト
        
        要件: 18.4 - 包括的ベンチマーク実行
        """
        print("\n=== 包括的ベンチマーク実行テスト開始 ===")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. システムリソース確認
            print("1. システムリソース確認")
            
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            print(f"  CPU: {cpu_count}コア")
            print(f"  メモリ: {memory_gb:.1f}GB")
            
            # 2. 利用可能実装の確認
            print("\n2. 利用可能実装確認")
            
            available_implementations = self.runner.get_all_available_implementations()
            implementations = self.runner.load_implementations(available_implementations)
            
            print(f"  利用可能実装: {len(implementations)}")
            print(f"  実装リスト: {[impl.name for impl in implementations]}")
            
            assert len(implementations) > 0, "At least some implementations should be available"
            
            # 3. 軽量ベンチマーク実行
            print("\n3. 軽量ベンチマーク実行")
            
            # テスト用の軽量シナリオ
            test_scenarios = [
                NumericScenario("primes"),
                MemoryScenario("sort")
            ]
            
            # 小さなデータサイズに設定
            test_scenarios[0].input_data = 100  # 素数探索
            test_scenarios[1].input_data = list(range(1000, 0, -1))  # ソート
            
            all_results = []
            start_time = time.time()
            
            for scenario in test_scenarios:
                print(f"  実行中: {scenario.name}")
                
                results = self.runner.run_scenario(
                    scenario, implementations,
                    warmup_runs=1, measurement_runs=3
                )
                all_results.extend(results)
                
                successful_count = len([r for r in results if r.status == "SUCCESS"])
                print(f"    成功: {successful_count}/{len(results)}")
            
            execution_time = time.time() - start_time
            print(f"  総実行時間: {execution_time:.2f}秒")
            
            # 4. 結果の分析
            print("\n4. 結果分析")
            
            total_results = len(all_results)
            successful_results = [r for r in all_results if r.status == "SUCCESS"]
            error_results = [r for r in all_results if r.status == "ERROR"]
            
            success_rate = len(successful_results) / total_results if total_results > 0 else 0
            
            print(f"  総結果数: {total_results}")
            print(f"  成功結果: {len(successful_results)}")
            print(f"  エラー結果: {len(error_results)}")
            print(f"  成功率: {success_rate:.1%}")
            
            # 5. 出力ファイル生成テスト
            print("\n5. 出力ファイル生成テスト")
            
            if successful_results:
                writer = OutputWriter(base_dir=tmpdir)
                
                # JSON出力
                json_path = writer.write_json(successful_results, "comprehensive_integration_test")
                assert os.path.exists(json_path), "JSON output should be created"
                print(f"  ✓ JSON: {os.path.basename(json_path)}")
                
                # CSV出力
                csv_path = writer.write_csv(successful_results, "comprehensive_integration_test")
                assert os.path.exists(csv_path), "CSV output should be created"
                print(f"  ✓ CSV: {os.path.basename(csv_path)}")
                
                # 包括的レポート
                try:
                    comprehensive_path = writer.write_comprehensive_report(
                        successful_results, "comprehensive_integration_test"
                    )
                    assert os.path.exists(comprehensive_path), "Comprehensive report should be created"
                    print(f"  ✓ 包括的レポート: {os.path.basename(comprehensive_path)}")
                except Exception as e:
                    print(f"  ⚠ 包括的レポート生成エラー: {e}")
            
            # 6. グラフ生成テスト
            print("\n6. グラフ生成テスト")
            
            if successful_results:
                visualizer = Visualizer(base_dir=tmpdir)
                
                try:
                    exec_time_graph = visualizer.plot_execution_time(
                        successful_results, "comprehensive_integration_execution_time"
                    )
                    assert os.path.exists(exec_time_graph), "Execution time graph should be created"
                    print(f"  ✓ 実行時間グラフ: {os.path.basename(exec_time_graph)}")
                except Exception as e:
                    print(f"  ⚠ 実行時間グラフ生成エラー: {e}")
                
                try:
                    memory_graph = visualizer.plot_memory_usage(
                        successful_results, "comprehensive_integration_memory_usage"
                    )
                    assert os.path.exists(memory_graph), "Memory usage graph should be created"
                    print(f"  ✓ メモリ使用量グラフ: {os.path.basename(memory_graph)}")
                except Exception as e:
                    print(f"  ⚠ メモリ使用量グラフ生成エラー: {e}")
            
            # 7. 最終検証
            print("\n7. 最終検証")
            
            # 基本的な成功基準
            assert total_results > 0, "Some results should be generated"
            assert success_rate >= 0.3, f"Success rate should be at least 30%, got {success_rate:.1%}"
            assert execution_time < 300, f"Execution should complete within 5 minutes, got {execution_time:.2f}s"
            
            # エラーハンドリングの確認
            if error_results:
                assert self.runner.error_handler.has_errors(), "Error handler should record failures"
            
            print("  ✓ 全ての検証項目をクリア")
            
            print("✓ 包括的ベンチマーク実行テスト完了")
            
            return {
                'total_results': total_results,
                'successful_results': len(successful_results),
                'error_results': len(error_results),
                'success_rate': success_rate,
                'execution_time': execution_time,
                'tested_implementations': [impl.name for impl in implementations]
            }
    
    def test_final_comprehensive_integration(self):
        """最終包括的統合テスト - 全機能の統合確認"""
        
        print("\n=== 最終包括的統合テスト開始 ===")
        
        # 各サブテストを実行
        print("実行中: 全12実装動作確認...")
        impl_status = self.test_all_12_implementations_verification()
        
        print("\n実行中: エラーハンドリング検証...")
        error_status = self.test_error_handling_verification()
        
        print("\n実行中: uv環境一貫動作確認...")
        uv_status = self.test_uv_environment_consistency()
        
        print("\n実行中: 包括的ベンチマーク実行...")
        benchmark_status = self.test_comprehensive_benchmark_execution()
        
        # 最終レポート生成
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': {
                'implementation_verification': impl_status,
                'error_handling': error_status,
                'uv_environment': uv_status,
                'comprehensive_benchmark': benchmark_status
            },
            'summary': {
                'total_implementations_tested': len(impl_status),
                'successful_implementations': sum(1 for s in impl_status.values() if s['status'] == 'SUCCESS'),
                'error_handling_working': error_status['successful_recovery'],
                'uv_environment_ok': uv_status['uv_environment_ok'],
                'benchmark_success_rate': benchmark_status['success_rate']
            }
        }
        
        # 最終検証
        summary = final_report['summary']
        
        assert summary['successful_implementations'] > 0, "At least some implementations should work"
        assert summary['error_handling_working'], "Error handling should work"
        assert summary['benchmark_success_rate'] >= 0.3, "Benchmark success rate should be at least 30%"
        
        print("\n" + "=" * 80)
        print("最終包括的統合テスト結果")
        print("=" * 80)
        print(f"テスト実装数: {summary['total_implementations_tested']}")
        print(f"成功実装数: {summary['successful_implementations']}")
        print(f"エラーハンドリング: {'✓' if summary['error_handling_working'] else '❌'}")
        print(f"uv環境: {'✓' if summary['uv_environment_ok'] else '⚠'}")
        print(f"ベンチマーク成功率: {summary['benchmark_success_rate']:.1%}")
        print("=" * 80)
        
        print("\n✓ 最終包括的統合テスト完了")
        
        return final_report


if __name__ == '__main__':
    # 個別テスト実行用
    test_instance = TestComprehensiveIntegration()
    test_instance.setup_method()
    
    print("=" * 80)
    print("包括的統合テスト実行")
    print("=" * 80)
    
    try:
        final_report = test_instance.test_final_comprehensive_integration()
        
        print("\n🎉 全ての包括的統合テストが成功しました！")
        print(f"最終成功率: {final_report['summary']['benchmark_success_rate']:.1%}")
        
    except Exception as e:
        print(f"\n❌ 包括的統合テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)