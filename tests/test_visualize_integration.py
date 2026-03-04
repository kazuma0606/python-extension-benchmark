"""統合テスト: グラフ生成モジュール

実際のベンチマーク結果を使用してグラフ生成をテストする。
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from benchmark.runner.visualize import Visualizer
from benchmark.models import BenchmarkResult, EnvironmentInfo


def test_visualizer_with_realistic_data():
    """実際のベンチマーク結果を使用してグラフ生成をテスト"""
    
    # テスト用の環境情報
    env = EnvironmentInfo(
        os='Linux',
        cpu='Intel Core i7-9700K',
        memory_gb=16.0,
        python_version='3.11.0',
        docker=False
    )
    
    # テスト用のベンチマーク結果を作成
    results = [
        # Numeric scenario - Python
        BenchmarkResult(
            scenario_name='numeric',
            implementation_name='python',
            execution_times=[100.0] * 100,
            memory_usage=[50.0] * 100,
            min_time=95.0,
            median_time=100.0,
            mean_time=100.0,
            std_dev=5.0,
            relative_score=1.0,
            throughput=10.0,
            output_value=12345,
            timestamp=datetime.now(),
            environment=env,
            status='SUCCESS'
        ),
        # Numeric scenario - NumPy
        BenchmarkResult(
            scenario_name='numeric',
            implementation_name='numpy',
            execution_times=[10.0] * 100,
            memory_usage=[60.0] * 100,
            min_time=9.5,
            median_time=10.0,
            mean_time=10.0,
            std_dev=0.5,
            relative_score=0.1,
            throughput=100.0,
            output_value=12345,
            timestamp=datetime.now(),
            environment=env,
            status='SUCCESS'
        ),
        # Memory scenario - Python
        BenchmarkResult(
            scenario_name='memory',
            implementation_name='python',
            execution_times=[200.0] * 100,
            memory_usage=[100.0] * 100,
            min_time=195.0,
            median_time=200.0,
            mean_time=200.0,
            std_dev=10.0,
            relative_score=1.0,
            throughput=5.0,
            output_value=67890,
            timestamp=datetime.now(),
            environment=env,
            status='SUCCESS'
        ),
        # Memory scenario - NumPy
        BenchmarkResult(
            scenario_name='memory',
            implementation_name='numpy',
            execution_times=[50.0] * 100,
            memory_usage=[80.0] * 100,
            min_time=48.0,
            median_time=50.0,
            mean_time=50.0,
            std_dev=2.0,
            relative_score=0.25,
            throughput=20.0,
            output_value=67890,
            timestamp=datetime.now(),
            environment=env,
            status='SUCCESS'
        ),
        # Parallel scenario - 1 thread
        BenchmarkResult(
            scenario_name='parallel_1_thread',
            implementation_name='python',
            execution_times=[150.0] * 100,
            memory_usage=[70.0] * 100,
            min_time=145.0,
            median_time=150.0,
            mean_time=150.0,
            std_dev=5.0,
            relative_score=1.0,
            throughput=6.67,
            output_value=11111,
            timestamp=datetime.now(),
            environment=env,
            status='SUCCESS'
        ),
        # Parallel scenario - 2 threads
        BenchmarkResult(
            scenario_name='parallel_2_threads',
            implementation_name='python',
            execution_times=[80.0] * 100,
            memory_usage=[75.0] * 100,
            min_time=78.0,
            median_time=80.0,
            mean_time=80.0,
            std_dev=3.0,
            relative_score=0.53,
            throughput=12.5,
            output_value=11111,
            timestamp=datetime.now(),
            environment=env,
            status='SUCCESS'
        ),
        # Parallel scenario - 4 threads
        BenchmarkResult(
            scenario_name='parallel_4_threads',
            implementation_name='python',
            execution_times=[45.0] * 100,
            memory_usage=[80.0] * 100,
            min_time=43.0,
            median_time=45.0,
            mean_time=45.0,
            std_dev=2.0,
            relative_score=0.3,
            throughput=22.22,
            output_value=11111,
            timestamp=datetime.now(),
            environment=env,
            status='SUCCESS'
        ),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        visualizer = Visualizer(base_dir=tmpdir)
        
        # 実行時間グラフを生成
        exec_time_path = visualizer.plot_execution_time(results, 'integration_test_execution_time')
        assert os.path.exists(exec_time_path)
        assert os.path.getsize(exec_time_path) > 0
        print(f"✓ Execution time graph created: {exec_time_path}")
        
        # メモリ使用量グラフを生成
        memory_path = visualizer.plot_memory_usage(results, 'integration_test_memory_usage')
        assert os.path.exists(memory_path)
        assert os.path.getsize(memory_path) > 0
        print(f"✓ Memory usage graph created: {memory_path}")
        
        # スケーラビリティグラフを生成
        scalability_path = visualizer.plot_scalability(results, 'integration_test_scalability')
        assert os.path.exists(scalability_path)
        assert os.path.getsize(scalability_path) > 0
        print(f"✓ Scalability graph created: {scalability_path}")
        
        # すべてのグラフが正しいディレクトリに保存されていることを確認
        graphs_dir = Path(tmpdir) / 'graphs'
        assert graphs_dir.exists()
        graph_files = list(graphs_dir.glob('*.png'))
        assert len(graph_files) == 3
        print(f"✓ All 3 graphs created in {graphs_dir}")


def test_visualizer_with_empty_data():
    """空のデータでもエラーなくグラフを生成できることをテスト"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        visualizer = Visualizer(base_dir=tmpdir)
        
        # 空のリストでグラフを生成
        exec_time_path = visualizer.plot_execution_time([], 'empty_execution_time')
        assert os.path.exists(exec_time_path)
        
        memory_path = visualizer.plot_memory_usage([], 'empty_memory_usage')
        assert os.path.exists(memory_path)
        
        scalability_path = visualizer.plot_scalability([], 'empty_scalability')
        assert os.path.exists(scalability_path)
        
        print("✓ Empty data handled gracefully")


if __name__ == '__main__':
    test_visualizer_with_realistic_data()
    test_visualizer_with_empty_data()
    print("\n✓ All integration tests passed!")
