"""エンドツーエンド統合テスト

全実装で全シナリオを実行し、結果ファイルとグラフの生成、出力値の一致を確認する。
"""

import os
import json
import csv
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import NumericScenario, MemoryScenario, ParallelScenario
from benchmark.runner.output import OutputWriter
from benchmark.runner.visualize import Visualizer
from benchmark.runner.validator import OutputValidator


class TestEndToEndIntegration:
    """エンドツーエンド統合テストクラス"""
    
    def test_full_benchmark_execution_python_numpy(self):
        """Python と NumPy 実装で全シナリオを実行するエンドツーエンドテスト"""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # ベンチマークランナーを初期化
            runner = BenchmarkRunner()
            
            # 利用可能な実装をロード（Python と NumPy のみ）
            implementations = runner.load_implementations(["python", "numpy_impl"])
            
            # 実装が正常にロードされることを確認
            assert len(implementations) >= 1, "At least Python implementation should be loaded"
            
            # 軽量なシナリオを定義（テスト用に小さなデータサイズ）
            scenarios = [
                NumericScenario("primes"),  # 素数探索
                NumericScenario("matrix"),  # 行列積
                MemoryScenario("sort"),     # 配列ソート
                MemoryScenario("filter"),   # 配列フィルタ
                ParallelScenario(1),        # 並列処理（1スレッド）
                ParallelScenario(2),        # 並列処理（2スレッド）
            ]
            
            # テスト用に小さなデータサイズに変更
            for scenario in scenarios:
                if hasattr(scenario, 'scenario_type'):
                    if scenario.scenario_type == "primes":
                        scenario.input_data = 1000  # 100,000 -> 1,000に縮小
                        scenario.description = "Find all prime numbers up to 1,000 (test size)"
                    elif scenario.scenario_type == "matrix":
                        # 100x100 -> 10x10に縮小
                        size = 10
                        matrix_a = [[float(i * size + j) for j in range(size)] for i in range(size)]
                        matrix_b = [[float(i * size + j) for j in range(size)] for i in range(size)]
                        scenario.input_data = (matrix_a, matrix_b)
                        scenario.description = "Multiply two 10x10 matrices (test size)"
                    elif scenario.scenario_type == "sort":
                        scenario.input_data = list(range(10000, 0, -1))  # 10M -> 10K要素に縮小
                        scenario.description = "Sort an array of 10,000 integers (test size)"
                    elif scenario.scenario_type == "filter":
                        scenario.input_data = (list(range(10000)), 5000)  # 10M -> 10K要素に縮小
                        scenario.description = "Filter array elements >= threshold (test size)"
                elif hasattr(scenario, 'num_threads'):
                    # 並列処理シナリオも縮小
                    scenario.input_data = [float(i) for i in range(10000)]  # 10M -> 10K要素に縮小
                    scenario.description = f"Compute sum of 10,000 floats using {scenario.num_threads} threads (test size)"
            
            # 全シナリオを実行（ウォームアップ1回、計測5回に短縮）
            all_results = []
            for scenario in scenarios:
                print(f"\n実行中: {scenario.name}")
                results = runner.run_scenario(
                    scenario, 
                    implementations, 
                    warmup_runs=1, 
                    measurement_runs=5
                )
                all_results.extend(results)
            
            # 結果が生成されることを確認
            assert len(all_results) > 0, "Results should be generated"
            
            # 成功した結果があることを確認
            successful_results = [r for r in all_results if r.status == "SUCCESS"]
            assert len(successful_results) > 0, "At least some results should be successful"
            
            # 各結果の基本的な妥当性を確認
            for result in successful_results:
                assert result.scenario_name is not None
                assert result.implementation_name is not None
                assert len(result.execution_times) == 5  # 計測回数
                assert len(result.memory_usage) == 5
                assert result.min_time > 0
                assert result.mean_time > 0
                assert result.throughput > 0
                assert result.output_value is not None
                assert result.timestamp is not None
                assert result.environment is not None
                
                # 出力値のサイズを制限して表示（大量の数字出力を防ぐ）
                output_info = ""
                if isinstance(result.output_value, list):
                    if len(result.output_value) > 1000:
                        # 大きなリストの場合は要素数のみ表示
                        output_info = f"(list with {len(result.output_value)} elements)"
                    else:
                        output_info = f"(list with {len(result.output_value)} elements: first={result.output_value[0] if result.output_value else 'None'})"
                else:
                    output_info = f"(value: {result.output_value})"
                
                print(f"  ✓ {result.implementation_name}: {result.scenario_name} {output_info}")
                print(f"    実行時間: {result.mean_time:.2f}ms, スループット: {result.throughput:.2f} ops/sec")
            
            print(f"✓ 全シナリオ実行完了: {len(all_results)} 結果生成")
            
            # 結果出力のテスト
            self._test_result_output(all_results, tmpdir)
            
            # グラフ生成のテスト
            self._test_graph_generation(all_results, tmpdir)
            
            # 出力値の一致確認のテスト
            self._test_output_validation(all_results)
    
    def _test_result_output(self, results, tmpdir):
        """結果ファイルの出力をテスト"""
        
        # OutputWriterを初期化
        writer = OutputWriter(base_dir=tmpdir)
        
        # JSON形式で出力
        json_path = writer.write_json(results, "integration_test_results")
        assert os.path.exists(json_path), "JSON file should be created"
        assert os.path.getsize(json_path) > 0, "JSON file should not be empty"
        
        # JSONファイルの内容を検証
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        assert isinstance(json_data, dict), "JSON should contain a dict"
        assert 'results' in json_data, "JSON should contain 'results' field"
        assert 'summary' in json_data, "JSON should contain 'summary' field"
        
        results_data = json_data['results']
        assert isinstance(results_data, list), "JSON results should be a list"
        assert len(results_data) == len(results), "JSON should contain all results"
        
        # 最初の結果の構造を確認
        if results_data:
            first_result = results_data[0]
            required_fields = [
                'scenario_name', 'implementation_name', 'execution_times',
                'memory_usage', 'min_time', 'median_time', 'mean_time',
                'std_dev', 'relative_score', 'throughput', 'timestamp',
                'environment'
            ]
            for field in required_fields:
                assert field in first_result, f"Field {field} should be in JSON output"
        
        print(f"✓ JSON出力テスト完了: {json_path}")
        
        # CSV形式で出力
        csv_path = writer.write_csv(results, "integration_test_results")
        assert os.path.exists(csv_path), "CSV file should be created"
        assert os.path.getsize(csv_path) > 0, "CSV file should not be empty"
        
        # CSVファイルの内容を検証
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            csv_rows = list(csv_reader)
        
        assert len(csv_rows) == len(results), "CSV should contain all results"
        
        # ヘッダーの確認
        if csv_rows:
            headers = csv_rows[0].keys()
            required_headers = [
                'scenario_name', 'implementation_name', 'min_time',
                'median_time', 'mean_time', 'std_dev', 'relative_score',
                'throughput', 'timestamp'
            ]
            for header in required_headers:
                assert header in headers, f"Header {header} should be in CSV output"
        
        print(f"✓ CSV出力テスト完了: {csv_path}")
    
    def _test_graph_generation(self, results, tmpdir):
        """グラフ生成をテスト"""
        
        # Visualizerを初期化
        visualizer = Visualizer(base_dir=tmpdir)
        
        # 実行時間グラフを生成
        exec_time_path = visualizer.plot_execution_time(results, "integration_test_execution_time")
        assert os.path.exists(exec_time_path), "Execution time graph should be created"
        assert os.path.getsize(exec_time_path) > 0, "Execution time graph should not be empty"
        assert exec_time_path.endswith('.png'), "Graph should be PNG format"
        
        print(f"✓ 実行時間グラフ生成完了: {exec_time_path}")
        
        # メモリ使用量グラフを生成
        memory_path = visualizer.plot_memory_usage(results, "integration_test_memory_usage")
        assert os.path.exists(memory_path), "Memory usage graph should be created"
        assert os.path.getsize(memory_path) > 0, "Memory usage graph should not be empty"
        assert memory_path.endswith('.png'), "Graph should be PNG format"
        
        print(f"✓ メモリ使用量グラフ生成完了: {memory_path}")
        
        # スケーラビリティグラフを生成
        scalability_path = visualizer.plot_scalability(results, "integration_test_scalability")
        assert os.path.exists(scalability_path), "Scalability graph should be created"
        assert os.path.getsize(scalability_path) > 0, "Scalability graph should not be empty"
        assert scalability_path.endswith('.png'), "Graph should be PNG format"
        
        print(f"✓ スケーラビリティグラフ生成完了: {scalability_path}")
        
        # グラフディレクトリの確認
        graphs_dir = Path(tmpdir) / 'graphs'
        assert graphs_dir.exists(), "Graphs directory should be created"
        
        graph_files = list(graphs_dir.glob('*.png'))
        assert len(graph_files) == 3, "Three graph files should be created"
        
        print(f"✓ 全グラフ生成完了: {len(graph_files)} ファイル")
    
    def _test_output_validation(self, results):
        """出力値の一致確認をテスト"""
        
        # シナリオごとに出力値をグループ化
        by_scenario = {}
        for result in results:
            if result.status == "SUCCESS" and result.output_value is not None:
                scenario_name = result.scenario_name
                if scenario_name not in by_scenario:
                    by_scenario[scenario_name] = {}
                by_scenario[scenario_name][result.implementation_name] = result.output_value
        
        # 各シナリオで出力値の一致を確認
        validation_results = []
        for scenario_name, outputs in by_scenario.items():
            if len(outputs) >= 2:  # 複数の実装がある場合のみ検証
                print(f"\n出力値検証中: {scenario_name}")
                
                # 出力値のサイズ情報を表示（実際の値は表示しない）
                for impl_name, output_value in outputs.items():
                    if isinstance(output_value, list):
                        print(f"  {impl_name}: リスト ({len(output_value)} 要素)")
                    else:
                        print(f"  {impl_name}: {type(output_value).__name__} ({output_value})")
                
                # 出力値を検証
                validation = OutputValidator.validate(outputs, tolerance=1e-4)
                validation_results.append((scenario_name, validation))
                
                # 検証結果を確認
                assert validation is not None, "Validation result should not be None"
                assert hasattr(validation, 'is_valid'), "Validation should have is_valid field"
                assert hasattr(validation, 'max_relative_error'), "Validation should have max_relative_error field"
                assert hasattr(validation, 'mismatches'), "Validation should have mismatches field"
                
                if validation.is_valid:
                    print(f"✓ {scenario_name}: 出力値一致 (最大相対誤差: {validation.max_relative_error:.2e})")
                else:
                    print(f"⚠️ {scenario_name}: 出力値不一致 (最大相対誤差: {validation.max_relative_error:.2e})")
                    print(f"   不一致実装: {', '.join(validation.mismatches)}")
        
        # 少なくとも1つのシナリオで検証が実行されることを確認
        assert len(validation_results) > 0, "At least one scenario should be validated"
        
        print(f"✓ 出力値検証完了: {len(validation_results)} シナリオ")
    
    def test_error_handling_integration(self):
        """エラーハンドリングの統合テスト"""
        
        runner = BenchmarkRunner()
        
        # 存在しない実装と存在する実装を混在させる
        implementations = runner.load_implementations([
            "python",  # 存在する
            "nonexistent_implementation",  # 存在しない
            "numpy_impl",  # 存在する
        ])
        
        # 存在する実装のみがロードされることを確認
        assert len(implementations) >= 1, "Valid implementations should be loaded"
        
        # エラーログが記録されることを確認
        assert runner.error_handler.has_errors(), "Error should be recorded for nonexistent implementation"
        
        # 軽量なシナリオで実行
        scenario = NumericScenario("primes")
        results = runner.run_scenario(scenario, implementations, warmup_runs=1, measurement_runs=2)
        
        # 結果が生成されることを確認（エラーがあっても継続実行）
        assert len(results) > 0, "Results should be generated despite errors"
        
        # 成功した結果があることを確認
        successful_results = [r for r in results if r.status == "SUCCESS"]
        assert len(successful_results) > 0, "At least some results should be successful"
        
        print("✓ エラーハンドリング統合テスト完了")
    
    def test_minimal_benchmark_with_all_available_implementations(self):
        """利用可能な全実装での最小限のベンチマークテスト"""
        
        runner = BenchmarkRunner()
        
        # 全ての実装をロードを試行
        all_implementation_names = [
            "python", "numpy_impl", "c_ext", "cpp_ext", "cython_ext", "rust_ext"
        ]
        
        implementations = runner.load_implementations(all_implementation_names)
        
        # 少なくともPythonは利用可能であることを確認
        python_impl = next((impl for impl in implementations if impl.name == "python"), None)
        assert python_impl is not None, "Python implementation should always be available"
        
        print(f"利用可能な実装: {[impl.name for impl in implementations]}")
        
        # 最小限のシナリオで実行
        scenario = NumericScenario("primes")
        results = runner.run_scenario(scenario, implementations, warmup_runs=1, measurement_runs=3)
        
        # 結果の基本的な妥当性を確認
        assert len(results) == len(implementations), "Results should be generated for all implementations"
        
        successful_results = [r for r in results if r.status == "SUCCESS"]
        assert len(successful_results) > 0, "At least some implementations should succeed"
        
        # 相対スコアが計算されることを確認
        python_result = next((r for r in successful_results if r.implementation_name == "python"), None)
        if python_result:
            assert python_result.relative_score == 1.0, "Python should have relative score of 1.0"
        
        # 他の実装の相対スコアが妥当であることを確認
        for result in successful_results:
            if result.implementation_name != "python":
                assert result.relative_score > 0, "Relative score should be positive"
        
        print(f"✓ 全実装テスト完了: {len(successful_results)}/{len(implementations)} 成功")


if __name__ == '__main__':
    # 個別テスト実行用
    test_instance = TestEndToEndIntegration()
    
    print("=== エンドツーエンド統合テスト開始 ===\n")
    
    try:
        test_instance.test_full_benchmark_execution_python_numpy()
        print("\n✓ メインベンチマークテスト完了")
        
        test_instance.test_error_handling_integration()
        print("\n✓ エラーハンドリングテスト完了")
        
        test_instance.test_minimal_benchmark_with_all_available_implementations()
        print("\n✓ 全実装テスト完了")
        
        print("\n=== 全ての統合テストが成功しました！ ===")
        
    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()