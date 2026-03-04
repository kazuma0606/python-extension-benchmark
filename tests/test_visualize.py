"""プロパティベーステスト: グラフ生成モジュール

グラフファイルの生成を検証する。
"""

import os
import tempfile
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st, settings

from benchmark.runner.visualize import Visualizer
from benchmark.models import BenchmarkResult, EnvironmentInfo, ValidationResult


# Hypothesis strategies for generating test data
@st.composite
def environment_info_strategy(draw):
    """EnvironmentInfo生成戦略"""
    return EnvironmentInfo(
        os=draw(st.sampled_from(['Linux', 'Windows', 'Darwin'])),
        cpu=draw(st.text(min_size=1, max_size=50)),
        memory_gb=draw(st.floats(min_value=1.0, max_value=128.0)),
        python_version=draw(st.sampled_from(['3.9.0', '3.10.0', '3.11.0'])),
        docker=draw(st.booleans())
    )


@st.composite
def benchmark_result_strategy(draw):
    """BenchmarkResult生成戦略"""
    num_measurements = draw(st.integers(min_value=10, max_value=100))
    execution_times = draw(st.lists(
        st.floats(min_value=0.001, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=num_measurements,
        max_size=num_measurements
    ))
    memory_usage = draw(st.lists(
        st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        min_size=num_measurements,
        max_size=num_measurements
    ))
    
    return BenchmarkResult(
        scenario_name=draw(st.sampled_from(['numeric', 'memory', 'parallel_1_thread', 'parallel_2_threads', 'parallel_4_threads'])),
        implementation_name=draw(st.sampled_from(['python', 'numpy', 'cython', 'c_ext'])),
        execution_times=execution_times,
        memory_usage=memory_usage,
        min_time=min(execution_times),
        median_time=sorted(execution_times)[len(execution_times) // 2],
        mean_time=sum(execution_times) / len(execution_times),
        std_dev=draw(st.floats(min_value=0.0, max_value=100.0)),
        relative_score=draw(st.floats(min_value=0.1, max_value=10.0)),
        throughput=draw(st.floats(min_value=1.0, max_value=10000.0)),
        output_value=draw(st.integers(min_value=0, max_value=1000000)),
        timestamp=datetime.now(),
        environment=draw(environment_info_strategy()),
        validation=None,
        status='SUCCESS'
    )


@given(st.lists(benchmark_result_strategy(), min_size=1, max_size=10))
@settings(deadline=None)  # グラフ生成は時間がかかるためdeadlineを無効化
def test_property_12_graph_file_generation(results):
    """Feature: python-extension-benchmark, Property 12: グラフファイルの生成
    
    **検証: 要件 6.1, 6.2, 6.3, 6.4**
    
    任意のベンチマーク結果に対して、実行時間、メモリ使用量、スケーラビリティの
    グラフがPNG形式で生成され、指定されたパスに保存されなければならない
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        visualizer = Visualizer(base_dir=tmpdir)
        
        # 実行時間の比較グラフを生成
        execution_time_path = visualizer.plot_execution_time(results, 'test_execution_time')
        
        # ファイルが存在することを確認
        assert os.path.exists(execution_time_path), f"Execution time graph not found at {execution_time_path}"
        
        # PNG形式であることを確認
        assert execution_time_path.endswith('.png'), f"Expected PNG file, got {execution_time_path}"
        
        # 正しいディレクトリに保存されていることを確認
        expected_graphs_dir = Path(tmpdir) / 'graphs'
        assert Path(execution_time_path).parent == expected_graphs_dir
        
        # ファイルサイズが0より大きいことを確認（有効なPNGファイル）
        assert os.path.getsize(execution_time_path) > 0
        
        # メモリ使用量の比較グラフを生成
        memory_usage_path = visualizer.plot_memory_usage(results, 'test_memory_usage')
        
        # ファイルが存在することを確認
        assert os.path.exists(memory_usage_path), f"Memory usage graph not found at {memory_usage_path}"
        
        # PNG形式であることを確認
        assert memory_usage_path.endswith('.png'), f"Expected PNG file, got {memory_usage_path}"
        
        # 正しいディレクトリに保存されていることを確認
        assert Path(memory_usage_path).parent == expected_graphs_dir
        
        # ファイルサイズが0より大きいことを確認
        assert os.path.getsize(memory_usage_path) > 0
        
        # スケーラビリティグラフを生成
        scalability_path = visualizer.plot_scalability(results, 'test_scalability')
        
        # ファイルが存在することを確認
        assert os.path.exists(scalability_path), f"Scalability graph not found at {scalability_path}"
        
        # PNG形式であることを確認
        assert scalability_path.endswith('.png'), f"Expected PNG file, got {scalability_path}"
        
        # 正しいディレクトリに保存されていることを確認
        assert Path(scalability_path).parent == expected_graphs_dir
        
        # ファイルサイズが0より大きいことを確認
        assert os.path.getsize(scalability_path) > 0
        
        # graphsディレクトリが作成されていることを確認
        assert expected_graphs_dir.exists()
