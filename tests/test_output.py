"""プロパティベーステスト: 結果出力モジュール

JSON/CSV出力のラウンドトリップ、出力フィールドの完全性、結果出力先の正確性を検証する。
"""

import json
import csv
import os
import tempfile
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st

from benchmark.runner.output import OutputWriter
from benchmark.models import BenchmarkResult, EnvironmentInfo, ValidationResult


# Hypothesis strategies for generating test data
@st.composite
def environment_info_strategy(draw):
    """EnvironmentInfo生成戦略"""
    # 簡素化されたCPU名
    cpu_text = draw(st.sampled_from([
        'Intel Core i7-8700K',
        'AMD Ryzen 7 3700X',
        'Apple M1',
        'Intel Xeon E5-2680'
    ]))
    return EnvironmentInfo(
        os=draw(st.sampled_from(['Linux', 'Windows', 'Darwin'])),
        cpu=cpu_text,
        memory_gb=draw(st.floats(min_value=1.0, max_value=64.0)),
        python_version=draw(st.sampled_from(['3.9.0', '3.10.0', '3.11.0'])),
        docker=draw(st.booleans())
    )


@st.composite
def validation_result_strategy(draw):
    """ValidationResult生成戦略"""
    # 簡素化されたmismatchesリスト
    mismatches = draw(st.lists(
        st.sampled_from(['python', 'numpy', 'cython', 'c_ext', 'rust']),
        max_size=3
    ))
    return ValidationResult(
        is_valid=draw(st.booleans()),
        max_relative_error=draw(st.floats(min_value=0.0, max_value=1.0)),
        mismatches=mismatches
    )


@st.composite
def benchmark_result_strategy(draw):
    """BenchmarkResult生成戦略"""
    # データサイズを小さくして生成を高速化
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
    
    # エラーメッセージを簡素化
    error_msg = draw(st.one_of(
        st.none(),
        st.sampled_from(['Import error', 'Runtime error', 'Memory error'])
    ))
    
    return BenchmarkResult(
        scenario_name=draw(st.sampled_from(['numeric', 'memory', 'parallel'])),
        implementation_name=draw(st.sampled_from(['python', 'numpy', 'cython', 'c_ext'])),
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
        environment=draw(environment_info_strategy()),
        validation=draw(st.one_of(st.none(), validation_result_strategy())),
        status=draw(st.sampled_from(['SUCCESS', 'ERROR'])),
        error_message=error_msg
    )


@given(st.lists(benchmark_result_strategy(), min_size=1, max_size=10))
def test_property_9_json_round_trip(results):
    """Feature: python-extension-benchmark, Property 9: JSON出力のラウンドトリップ
    
    **検証: 要件 5.1**
    
    任意のベンチマーク結果に対して、JSON形式で出力し、再度読み込んだデータは
    元のデータと等価でなければならない
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(base_dir=tmpdir)
        
        # JSON形式で出力
        output_path = writer.write_json(results, 'test_output')
        
        # ファイルが存在することを確認
        assert os.path.exists(output_path)
        
        # JSONファイルを読み込み
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        # 結果を復元
        restored_results = [BenchmarkResult.from_dict(r) for r in loaded_data['results']]
        
        # 元のデータと復元したデータを比較
        assert len(restored_results) == len(results)
        
        for original, restored in zip(results, restored_results):
            assert original.scenario_name == restored.scenario_name
            assert original.implementation_name == restored.implementation_name
            assert original.execution_times == restored.execution_times
            assert original.memory_usage == restored.memory_usage
            assert abs(original.min_time - restored.min_time) < 1e-10
            assert abs(original.median_time - restored.median_time) < 1e-10
            assert abs(original.mean_time - restored.mean_time) < 1e-10
            assert abs(original.std_dev - restored.std_dev) < 1e-10
            assert abs(original.relative_score - restored.relative_score) < 1e-10
            assert abs(original.throughput - restored.throughput) < 1e-10
            assert original.output_value == restored.output_value
            assert original.timestamp == restored.timestamp
            assert original.environment.os == restored.environment.os
            assert original.environment.cpu == restored.environment.cpu
            assert abs(original.environment.memory_gb - restored.environment.memory_gb) < 1e-10
            assert original.environment.python_version == restored.environment.python_version
            assert original.environment.docker == restored.environment.docker
            assert original.status == restored.status
            assert original.error_message == restored.error_message
            
            # Validation結果の比較
            if original.validation is None:
                assert restored.validation is None
            else:
                assert restored.validation is not None
                assert original.validation.is_valid == restored.validation.is_valid
                assert abs(original.validation.max_relative_error - restored.validation.max_relative_error) < 1e-10
                assert original.validation.mismatches == restored.validation.mismatches


@given(st.lists(benchmark_result_strategy(), min_size=1, max_size=3))
def test_property_10_csv_round_trip(results):
    """Feature: python-extension-benchmark, Property 10: CSV出力のラウンドトリップ
    
    **検証: 要件 5.2**
    
    任意のベンチマーク結果に対して、CSV形式で出力し、再度読み込んだデータは
    元のデータと等価でなければならない（数値精度の許容範囲内）
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(base_dir=tmpdir)
        
        # CSV形式で出力
        output_path = writer.write_csv(results, 'test_output')
        
        # ファイルが存在することを確認
        assert os.path.exists(output_path)
        
        # CSVファイルを読み込み
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # 元のデータと復元したデータを比較
        assert len(rows) == len(results)
        
        for original, row in zip(results, rows):
            # 基本情報の検証
            assert original.scenario_name == row['scenario_name']
            assert original.implementation_name == row['implementation_name']
            
            # 数値データの検証（許容誤差あり）
            assert abs(original.min_time - float(row['min_time'])) < 1e-6
            assert abs(original.median_time - float(row['median_time'])) < 1e-6
            assert abs(original.mean_time - float(row['mean_time'])) < 1e-6
            assert abs(original.std_dev - float(row['std_dev'])) < 1e-6
            assert abs(original.relative_score - float(row['relative_score'])) < 1e-6
            assert abs(original.throughput - float(row['throughput'])) < 1e-6
            
            # メモリ使用量の検証
            peak_memory = max(original.memory_usage) if original.memory_usage else 0.0
            avg_memory = sum(original.memory_usage) / len(original.memory_usage) if original.memory_usage else 0.0
            assert abs(peak_memory - float(row['peak_memory_mb'])) < 1e-6
            assert abs(avg_memory - float(row['avg_memory_mb'])) < 1e-6
            
            # タイムスタンプの検証
            assert original.timestamp.isoformat() == row['timestamp']
            
            # 環境情報の検証
            assert original.environment.os == row['os']
            assert original.environment.cpu == row['cpu']
            assert abs(original.environment.memory_gb - float(row['memory_gb'])) < 1e-6
            assert original.environment.python_version == row['python_version']
            assert original.environment.docker == (row['docker'] == 'True')
            
            # ステータスの検証
            assert original.status == row['status']


@given(st.lists(benchmark_result_strategy(), min_size=1, max_size=3))
def test_property_11_output_field_completeness(results):
    """Feature: python-extension-benchmark, Property 11: 出力フィールドの完全性
    
    **検証: 要件 5.3, 5.4**
    
    任意のベンチマーク結果の出力に対して、実行時間、メモリ使用量、スループット、
    相対スコア、実行日時、環境情報（OS、CPU、メモリ）が含まれなければならない
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(base_dir=tmpdir)
        
        # JSON形式で出力
        json_path = writer.write_json(results, 'test_output')
        
        # JSONファイルを読み込み
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # 各結果に必須フィールドが含まれていることを確認
        for result_dict in json_data['results']:
            # 実行時間関連
            assert 'min_time' in result_dict
            assert 'median_time' in result_dict
            assert 'mean_time' in result_dict
            assert 'std_dev' in result_dict
            assert 'execution_times' in result_dict
            
            # メモリ使用量
            assert 'memory_usage' in result_dict
            
            # スループット
            assert 'throughput' in result_dict
            
            # 相対スコア
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
        csv_path = writer.write_csv(results, 'test_output')
        
        # CSVファイルを読み込み
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # 各行に必須フィールドが含まれていることを確認
        for row in rows:
            # 実行時間関連
            assert 'min_time' in row
            assert 'median_time' in row
            assert 'mean_time' in row
            assert 'std_dev' in row
            
            # メモリ使用量
            assert 'peak_memory_mb' in row
            assert 'avg_memory_mb' in row
            
            # スループット
            assert 'throughput' in row
            
            # 相対スコア
            assert 'relative_score' in row
            
            # 実行日時
            assert 'timestamp' in row
            
            # 環境情報
            assert 'os' in row
            assert 'cpu' in row
            assert 'memory_gb' in row
            assert 'python_version' in row
            assert 'docker' in row


@given(st.lists(benchmark_result_strategy(), min_size=1, max_size=10))
def test_property_19_output_directory_correctness(results):
    """Feature: python-extension-benchmark, Property 19: 結果出力先の正確性
    
    **検証: 要件 10.3**
    
    任意のベンチマーク実行に対して、計測結果は指定された専用ディレクトリ
    （results/json、results/csv、results/graphs）に出力されなければならない
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(base_dir=tmpdir)
        
        # JSON形式で出力
        json_path = writer.write_json(results, 'test_output')
        
        # JSONファイルが正しいディレクトリに出力されていることを確認
        expected_json_dir = Path(tmpdir) / 'json'
        assert Path(json_path).parent == expected_json_dir
        assert os.path.exists(json_path)
        
        # CSV形式で出力
        csv_path = writer.write_csv(results, 'test_output')
        
        # CSVファイルが正しいディレクトリに出力されていることを確認
        expected_csv_dir = Path(tmpdir) / 'csv'
        assert Path(csv_path).parent == expected_csv_dir
        assert os.path.exists(csv_path)
        
        # ディレクトリが作成されていることを確認
        assert expected_json_dir.exists()
        assert expected_csv_dir.exists()

