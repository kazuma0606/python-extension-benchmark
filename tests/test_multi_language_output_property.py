"""プロパティベーステスト: 多言語拡張結果出力モジュール

多言語拡張ベンチマークシステムの結果出力完全性と性能グラフ生成を検証する。
"""

import json
import csv
import os
import tempfile
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st, settings

from benchmark.runner.output import OutputWriter
from benchmark.runner.visualize import Visualizer
from benchmark.models import BenchmarkResult, EnvironmentInfo, ValidationResult


# Hypothesis strategies for generating multi-language test data
@st.composite
def multi_language_environment_strategy(draw):
    """多言語環境のEnvironmentInfo生成戦略"""
    return EnvironmentInfo(
        os=draw(st.sampled_from(['Linux', 'Windows', 'Darwin'])),
        cpu=draw(st.sampled_from([
            'Intel Core i7-8700K',
            'AMD Ryzen 7 3700X', 
            'Apple M1',
            'Intel Xeon E5-2680'
        ])),
        memory_gb=draw(st.floats(min_value=4.0, max_value=64.0)),
        python_version=draw(st.sampled_from(['3.9.0', '3.10.0', '3.11.0', '3.12.0'])),
        docker=draw(st.booleans())
    )


@st.composite
def multi_language_validation_strategy(draw):
    """多言語ValidationResult生成戦略"""
    # 12実装の言語名
    all_implementations = [
        'python', 'numpy_impl', 'c_ext', 'cpp_ext', 'cython_ext', 'rust_ext', 'fortran_ext',
        'julia_ext', 'go_ext', 'zig_ext', 'nim_ext', 'kotlin_ext'
    ]
    
    mismatches = draw(st.lists(
        st.sampled_from(all_implementations),
        max_size=5
    ))
    
    return ValidationResult(
        is_valid=draw(st.booleans()),
        max_relative_error=draw(st.floats(min_value=0.0, max_value=1.0)),
        mismatches=mismatches
    )


@st.composite
def multi_language_benchmark_result_strategy(draw):
    """多言語BenchmarkResult生成戦略"""
    # 12実装の言語
    implementations = [
        'python', 'numpy_impl', 'c_ext', 'cpp_ext', 'cython_ext', 'rust_ext', 'fortran_ext',
        'julia_ext', 'go_ext', 'zig_ext', 'nim_ext', 'kotlin_ext'
    ]
    
    # 多言語対応シナリオ
    scenarios = [
        'numeric:find_primes', 'numeric:matrix_multiply',
        'memory:sort_array', 'memory:filter_array', 
        'parallel:parallel_compute_1_thread', 'parallel:parallel_compute_2_threads',
        'parallel:parallel_compute_4_threads', 'parallel:parallel_compute_8_threads'
    ]
    
    num_measurements = draw(st.integers(min_value=5, max_value=20))
    execution_times = draw(st.lists(
        st.floats(min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=num_measurements,
        max_size=num_measurements
    ))
    memory_usage = draw(st.lists(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=num_measurements,
        max_size=num_measurements
    ))
    
    error_msg = draw(st.one_of(
        st.none(),
        st.sampled_from([
            'Julia environment not available',
            'Go compilation failed', 
            'Zig build error',
            'Nim import error',
            'Kotlin/Native runtime error'
        ])
    ))
    
    return BenchmarkResult(
        scenario_name=draw(st.sampled_from(scenarios)),
        implementation_name=draw(st.sampled_from(implementations)),
        execution_times=execution_times,
        memory_usage=memory_usage,
        min_time=min(execution_times),
        median_time=sorted(execution_times)[len(execution_times) // 2],
        mean_time=sum(execution_times) / len(execution_times),
        std_dev=draw(st.floats(min_value=0.0, max_value=10.0)),
        relative_score=draw(st.floats(min_value=0.1, max_value=5.0)),
        throughput=draw(st.floats(min_value=1.0, max_value=1000.0)),
        output_value=draw(st.integers(min_value=0, max_value=10000)),
        timestamp=datetime.now(),
        environment=draw(multi_language_environment_strategy()),
        validation=draw(st.one_of(st.none(), multi_language_validation_strategy())),
        status=draw(st.sampled_from(['SUCCESS', 'ERROR'])),
        error_message=error_msg
    )


@given(st.lists(multi_language_benchmark_result_strategy(), min_size=1, max_size=12))
def test_property_9_multi_language_output_completeness(results):
    """Feature: multi-language-extensions, Property 9: 結果出力の完全性
    
    **検証: 要件 6.2**
    
    すべての成功した多言語実装について、JSON/CSV形式での結果出力が生成される
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(base_dir=tmpdir)
        
        # 成功した結果のみをフィルタ
        successful_results = [r for r in results if r.status == 'SUCCESS']
        
        if not successful_results:
            # 成功した結果がない場合はスキップ
            return
        
        # JSON形式で出力
        json_path = writer.write_json(successful_results, 'multi_language_test')
        
        # ファイルが存在することを確認
        assert os.path.exists(json_path), f"JSON output file not found at {json_path}"
        
        # JSONファイルを読み込み
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # すべての成功した実装の結果が含まれていることを確認
        assert 'results' in json_data
        assert len(json_data['results']) == len(successful_results)
        
        # 各結果に必須フィールドが含まれていることを確認
        for result_dict in json_data['results']:
            # 基本情報
            assert 'scenario_name' in result_dict
            assert 'implementation_name' in result_dict
            assert 'status' in result_dict
            assert result_dict['status'] == 'SUCCESS'
            
            # 実行時間関連
            assert 'min_time' in result_dict
            assert 'median_time' in result_dict
            assert 'mean_time' in result_dict
            assert 'std_dev' in result_dict
            assert 'execution_times' in result_dict
            
            # メモリ使用量
            assert 'memory_usage' in result_dict
            
            # 性能指標
            assert 'throughput' in result_dict
            assert 'relative_score' in result_dict
            
            # 実行日時
            assert 'timestamp' in result_dict
            
            # 環境情報
            assert 'environment' in result_dict
            env = result_dict['environment']
            assert 'os' in env
            assert 'cpu' in env
            assert 'memory_gb' in env
            assert 'python_version' in env
            assert 'docker' in env
        
        # CSV形式で出力
        csv_path = writer.write_csv(successful_results, 'multi_language_test')
        
        # ファイルが存在することを確認
        assert os.path.exists(csv_path), f"CSV output file not found at {csv_path}"
        
        # CSVファイルを読み込み
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # すべての成功した実装の結果が含まれていることを確認
        assert len(rows) == len(successful_results)
        
        # 各行に必須フィールドが含まれていることを確認
        for row in rows:
            # 基本情報
            assert 'scenario_name' in row
            assert 'implementation_name' in row
            assert 'status' in row
            assert row['status'] == 'SUCCESS'
            
            # 実行時間関連
            assert 'min_time' in row
            assert 'median_time' in row
            assert 'mean_time' in row
            assert 'std_dev' in row
            
            # メモリ使用量
            assert 'peak_memory_mb' in row
            assert 'avg_memory_mb' in row
            
            # 性能指標
            assert 'throughput' in row
            assert 'relative_score' in row
            
            # 実行日時
            assert 'timestamp' in row
            
            # 環境情報
            assert 'os' in row
            assert 'cpu' in row
            assert 'memory_gb' in row
            assert 'python_version' in row
            assert 'docker' in row
        
        # 包括的レポートの生成
        comprehensive_path = writer.write_comprehensive_report(successful_results, 'multi_language_test')
        
        # 包括的レポートが存在することを確認
        assert os.path.exists(comprehensive_path), f"Comprehensive report not found at {comprehensive_path}"
        
        # 包括的レポートの内容を確認
        with open(comprehensive_path, 'r', encoding='utf-8') as f:
            comprehensive_data = json.load(f)
        
        # 必須セクションが含まれていることを確認
        assert 'metadata' in comprehensive_data
        assert 'implementation_statistics' in comprehensive_data
        assert 'scenario_statistics' in comprehensive_data
        assert 'detailed_results' in comprehensive_data
        assert 'performance_rankings' in comprehensive_data
        assert 'language_comparison' in comprehensive_data
        
        # メタデータの確認
        metadata = comprehensive_data['metadata']
        assert 'total_results' in metadata
        assert 'total_implementations' in metadata
        assert 'total_scenarios' in metadata
        assert metadata['total_results'] == len(successful_results)


@given(st.lists(multi_language_benchmark_result_strategy(), min_size=1, max_size=12))
@settings(deadline=None)  # グラフ生成は時間がかかるためdeadlineを無効化
def test_property_10_multi_language_graph_generation(results):
    """Feature: multi-language-extensions, Property 10: 性能グラフの生成
    
    **検証: 要件 6.3**
    
    すべての測定結果について、実行時間・メモリ使用量・スケーラビリティのグラフが生成される
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        visualizer = Visualizer(base_dir=tmpdir)
        
        # 成功した結果のみをフィルタ
        successful_results = [r for r in results if r.status == 'SUCCESS']
        
        if not successful_results:
            # 成功した結果がない場合はスキップ
            return
        
        # 1. 実行時間の比較グラフを生成
        execution_time_path = visualizer.plot_execution_time(successful_results, 'multi_language_execution_time')
        
        # ファイルが存在することを確認
        assert os.path.exists(execution_time_path), f"Execution time graph not found at {execution_time_path}"
        
        # PNG形式であることを確認
        assert execution_time_path.endswith('.png'), f"Expected PNG file, got {execution_time_path}"
        
        # 正しいディレクトリに保存されていることを確認
        expected_graphs_dir = Path(tmpdir) / 'graphs'
        assert Path(execution_time_path).parent == expected_graphs_dir
        
        # ファイルサイズが0より大きいことを確認（有効なPNGファイル）
        assert os.path.getsize(execution_time_path) > 0, "Execution time graph file is empty"
        
        # 2. メモリ使用量の比較グラフを生成
        memory_usage_path = visualizer.plot_memory_usage(successful_results, 'multi_language_memory_usage')
        
        # ファイルが存在することを確認
        assert os.path.exists(memory_usage_path), f"Memory usage graph not found at {memory_usage_path}"
        
        # PNG形式であることを確認
        assert memory_usage_path.endswith('.png'), f"Expected PNG file, got {memory_usage_path}"
        
        # 正しいディレクトリに保存されていることを確認
        assert Path(memory_usage_path).parent == expected_graphs_dir
        
        # ファイルサイズが0より大きいことを確認
        assert os.path.getsize(memory_usage_path) > 0, "Memory usage graph file is empty"
        
        # 3. スケーラビリティグラフを生成
        scalability_path = visualizer.plot_scalability(successful_results, 'multi_language_scalability')
        
        # ファイルが存在することを確認
        assert os.path.exists(scalability_path), f"Scalability graph not found at {scalability_path}"
        
        # PNG形式であることを確認
        assert scalability_path.endswith('.png'), f"Expected PNG file, got {scalability_path}"
        
        # 正しいディレクトリに保存されていることを確認
        assert Path(scalability_path).parent == expected_graphs_dir
        
        # ファイルサイズが0より大きいことを確認
        assert os.path.getsize(scalability_path) > 0, "Scalability graph file is empty"
        
        # 4. 包括的比較グラフを生成（12実装対応）
        comprehensive_path = visualizer.plot_comprehensive_comparison(successful_results, 'multi_language_comprehensive')
        
        # ファイルが存在することを確認
        assert os.path.exists(comprehensive_path), f"Comprehensive comparison graph not found at {comprehensive_path}"
        
        # PNG形式であることを確認
        assert comprehensive_path.endswith('.png'), f"Expected PNG file, got {comprehensive_path}"
        
        # 正しいディレクトリに保存されていることを確認
        assert Path(comprehensive_path).parent == expected_graphs_dir
        
        # ファイルサイズが0より大きいことを確認
        assert os.path.getsize(comprehensive_path) > 0, "Comprehensive comparison graph file is empty"
        
        # graphsディレクトリが作成されていることを確認
        assert expected_graphs_dir.exists(), "Graphs directory was not created"
        
        # すべてのグラフファイルが同じディレクトリに保存されていることを確認
        graph_files = list(expected_graphs_dir.glob('*.png'))
        assert len(graph_files) >= 4, f"Expected at least 4 graph files, found {len(graph_files)}"
        
        # 各グラフファイルが有効なサイズを持つことを確認
        for graph_file in graph_files:
            assert graph_file.stat().st_size > 0, f"Graph file {graph_file} is empty"


@given(st.lists(multi_language_benchmark_result_strategy(), min_size=2, max_size=12))
@settings(deadline=None)  # グラフ生成は時間がかかるためdeadlineを無効化
def test_property_multi_language_output_directory_structure(results):
    """Feature: multi-language-extensions, Property: 多言語出力ディレクトリ構造
    
    **検証: 要件 6.2, 6.3**
    
    多言語ベンチマーク結果は適切なディレクトリ構造で出力される
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(base_dir=tmpdir)
        visualizer = Visualizer(base_dir=tmpdir)
        
        # 成功した結果のみをフィルタ
        successful_results = [r for r in results if r.status == 'SUCCESS']
        
        if not successful_results:
            return
        
        # 出力を生成
        json_path = writer.write_json(successful_results, 'multi_language_structure_test')
        csv_path = writer.write_csv(successful_results, 'multi_language_structure_test')
        comprehensive_path = writer.write_comprehensive_report(successful_results, 'multi_language_structure_test')
        
        execution_graph = visualizer.plot_execution_time(successful_results, 'multi_language_structure_execution')
        memory_graph = visualizer.plot_memory_usage(successful_results, 'multi_language_structure_memory')
        
        # ディレクトリ構造を確認
        base_path = Path(tmpdir)
        
        # 必要なディレクトリが作成されていることを確認
        assert (base_path / 'json').exists(), "JSON directory not created"
        assert (base_path / 'csv').exists(), "CSV directory not created"
        assert (base_path / 'graphs').exists(), "Graphs directory not created"
        
        # ファイルが正しいディレクトリに配置されていることを確認
        assert Path(json_path).parent == base_path / 'json'
        assert Path(csv_path).parent == base_path / 'csv'
        assert Path(comprehensive_path).parent == base_path / 'json'
        assert Path(execution_graph).parent == base_path / 'graphs'
        assert Path(memory_graph).parent == base_path / 'graphs'
        
        # ファイル名の形式を確認
        assert Path(json_path).name == 'multi_language_structure_test.json'
        assert Path(csv_path).name == 'multi_language_structure_test.csv'
        assert Path(comprehensive_path).name == 'multi_language_structure_test_comprehensive.json'
        assert Path(execution_graph).name == 'multi_language_structure_execution.png'
        assert Path(memory_graph).name == 'multi_language_structure_memory.png'


@given(st.lists(multi_language_benchmark_result_strategy(), min_size=1, max_size=12))
def test_property_multi_language_error_handling_in_output(results):
    """Feature: multi-language-extensions, Property: エラー処理時の出力継続
    
    **検証: 要件 9.1, 9.2**
    
    一部の言語実装でエラーが発生しても、成功した実装の結果は適切に出力される
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(base_dir=tmpdir)
        
        # 成功とエラーの結果を混在させる
        mixed_results = []
        for result in results:
            # 一部の結果を意図的にエラー状態にする
            if len(mixed_results) % 3 == 0:  # 3つに1つをエラーにする
                error_result = BenchmarkResult(
                    scenario_name=result.scenario_name,
                    implementation_name=result.implementation_name,
                    execution_times=[],
                    memory_usage=[],
                    min_time=0.0,
                    median_time=0.0,
                    mean_time=0.0,
                    std_dev=0.0,
                    relative_score=0.0,
                    throughput=0.0,
                    output_value=0,
                    timestamp=result.timestamp,
                    environment=result.environment,
                    validation=None,
                    status='ERROR',
                    error_message=f'{result.implementation_name} failed to execute'
                )
                mixed_results.append(error_result)
            else:
                mixed_results.append(result)
        
        # 出力を生成
        json_path = writer.write_json(mixed_results, 'multi_language_error_test')
        csv_path = writer.write_csv(mixed_results, 'multi_language_error_test')
        
        # ファイルが生成されることを確認
        assert os.path.exists(json_path), "JSON output not generated despite errors"
        assert os.path.exists(csv_path), "CSV output not generated despite errors"
        
        # JSONの内容を確認
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # すべての結果（成功・エラー両方）が含まれていることを確認
        assert len(json_data['results']) == len(mixed_results)
        
        # エラー結果も適切に記録されていることを確認
        error_results = [r for r in json_data['results'] if r['status'] == 'ERROR']
        success_results = [r for r in json_data['results'] if r['status'] == 'SUCCESS']
        
        # エラー結果にはエラーメッセージが含まれていることを確認
        for error_result in error_results:
            assert 'error_message' in error_result
            # エラーメッセージがNoneでない場合のみチェック
            if error_result['error_message'] is not None:
                assert 'failed to execute' in error_result['error_message']
        
        # 成功結果には適切なデータが含まれていることを確認
        for success_result in success_results:
            assert success_result['execution_times'] is not None
            assert len(success_result['execution_times']) > 0
            assert success_result['mean_time'] > 0