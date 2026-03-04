"""Integration tests for error handling.

Tests for import errors and real-world error scenarios.
"""

from benchmark.runner.benchmark import BenchmarkRunner


def test_load_implementations_with_invalid_module():
    """インポートエラーが発生した場合のテスト"""
    runner = BenchmarkRunner()
    
    # 存在しないモジュールと存在するモジュールを混在させる
    implementation_names = [
        "python",  # 存在する
        "invalid_module_that_does_not_exist",  # 存在しない
        "numpy_impl",  # 存在する
    ]
    
    # 実装をロード
    implementations = runner.load_implementations(implementation_names)
    
    # 存在するモジュールのみがロードされることを確認
    assert len(implementations) == 2
    assert implementations[0].name == "python"
    assert implementations[1].name == "numpy_impl"
    
    # エラーログが記録されていることを確認
    assert len(runner.error_handler.error_logs) == 1
    assert runner.error_handler.error_logs[0].implementation_name == "invalid_module_that_does_not_exist"
    assert runner.error_handler.error_logs[0].error_type == "ImportError"


def test_load_implementations_all_invalid():
    """全てのモジュールが存在しない場合のテスト"""
    runner = BenchmarkRunner()
    
    # 全て存在しないモジュール
    implementation_names = [
        "invalid_module_1",
        "invalid_module_2",
        "invalid_module_3",
    ]
    
    # 実装をロード
    implementations = runner.load_implementations(implementation_names)
    
    # 何もロードされないことを確認
    assert len(implementations) == 0
    
    # エラーログが記録されていることを確認
    assert len(runner.error_handler.error_logs) == 3


def test_load_implementations_all_valid():
    """全てのモジュールが存在する場合のテスト"""
    runner = BenchmarkRunner()
    
    # 全て存在するモジュール
    implementation_names = [
        "python",
        "numpy_impl",
    ]
    
    # 実装をロード
    implementations = runner.load_implementations(implementation_names)
    
    # 全てロードされることを確認
    assert len(implementations) == 2
    assert implementations[0].name == "python"
    assert implementations[1].name == "numpy_impl"
    
    # エラーログが記録されていないことを確認
    assert len(runner.error_handler.error_logs) == 0


def test_error_summary():
    """エラーサマリーのテスト"""
    runner = BenchmarkRunner()
    
    # エラーがない場合
    summary = runner.error_handler.get_error_summary()
    assert "No errors occurred" in summary
    
    # エラーを発生させる
    runner.load_implementations(["invalid_module"])
    
    # エラーサマリーを取得
    summary = runner.error_handler.get_error_summary()
    assert "Error Summary" in summary
    assert "1 error(s) occurred" in summary
    assert "invalid_module" in summary
