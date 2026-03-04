"""統合テスト: OutputValidatorとBenchmarkResultの統合

OutputValidatorがBenchmarkResultと正しく統合されることを検証する。
"""

import pytest
from datetime import datetime

from benchmark.runner.validator import OutputValidator
from benchmark.models import BenchmarkResult, EnvironmentInfo, ValidationResult


def test_validator_with_benchmark_results():
    """BenchmarkResultにValidationResultを含めることができる"""
    # 環境情報を作成
    env = EnvironmentInfo(
        os="Windows",
        cpu="Intel Core i7",
        memory_gb=16.0,
        python_version="3.12.0",
        docker=False
    )
    
    # 複数の実装の出力値を作成
    outputs = {
        "python": 42.0,
        "numpy": 42.0,
        "cython": 42.00005,  # 許容範囲内の誤差
    }
    
    # 検証を実行
    validation = OutputValidator.validate(outputs, tolerance=1e-4)
    
    # BenchmarkResultを作成
    result = BenchmarkResult(
        scenario_name="test_scenario",
        implementation_name="python",
        execution_times=[1.0, 1.1, 1.2],
        memory_usage=[10.0, 10.5, 11.0],
        min_time=1.0,
        median_time=1.1,
        mean_time=1.1,
        std_dev=0.1,
        relative_score=1.0,
        throughput=909.09,
        output_value=42.0,
        timestamp=datetime.now(),
        environment=env,
        validation=validation
    )
    
    # ValidationResultが正しく含まれていることを確認
    assert result.validation is not None
    assert result.validation.is_valid == True
    assert result.validation.max_relative_error < 1e-4
    assert len(result.validation.mismatches) == 0


def test_validator_with_mismatched_results():
    """不一致がある場合のBenchmarkResultとの統合"""
    env = EnvironmentInfo(
        os="Windows",
        cpu="Intel Core i7",
        memory_gb=16.0,
        python_version="3.12.0",
        docker=False
    )
    
    # 不一致のある出力値を作成
    outputs = {
        "python": 100.0,
        "numpy": 100.0,
        "cython": 105.0,  # 5%の誤差（許容範囲外）
    }
    
    # 検証を実行（警告出力を抑制）
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        validation = OutputValidator.validate(outputs, tolerance=1e-4)
    finally:
        sys.stdout = old_stdout
    
    # BenchmarkResultを作成
    result = BenchmarkResult(
        scenario_name="test_scenario",
        implementation_name="python",
        execution_times=[1.0, 1.1, 1.2],
        memory_usage=[10.0, 10.5, 11.0],
        min_time=1.0,
        median_time=1.1,
        mean_time=1.1,
        std_dev=0.1,
        relative_score=1.0,
        throughput=909.09,
        output_value=100.0,
        timestamp=datetime.now(),
        environment=env,
        validation=validation
    )
    
    # ValidationResultが不一致を記録していることを確認
    assert result.validation is not None
    assert result.validation.is_valid == False
    assert result.validation.max_relative_error > 1e-4
    assert "cython" in result.validation.mismatches


def test_benchmark_result_to_dict_with_validation():
    """ValidationResultを含むBenchmarkResultのシリアライゼーション"""
    env = EnvironmentInfo(
        os="Windows",
        cpu="Intel Core i7",
        memory_gb=16.0,
        python_version="3.12.0",
        docker=False
    )
    
    validation = ValidationResult(
        is_valid=True,
        max_relative_error=1e-6,
        mismatches=[]
    )
    
    result = BenchmarkResult(
        scenario_name="test_scenario",
        implementation_name="python",
        execution_times=[1.0, 1.1, 1.2],
        memory_usage=[10.0, 10.5, 11.0],
        min_time=1.0,
        median_time=1.1,
        mean_time=1.1,
        std_dev=0.1,
        relative_score=1.0,
        throughput=909.09,
        output_value=42.0,
        timestamp=datetime.now(),
        environment=env,
        validation=validation
    )
    
    # 辞書に変換
    result_dict = result.to_dict()
    
    # validationフィールドが含まれていることを確認
    assert 'validation' in result_dict
    assert result_dict['validation'] is not None
    assert result_dict['validation']['is_valid'] == True
    assert result_dict['validation']['max_relative_error'] == 1e-6
    assert result_dict['validation']['mismatches'] == []
    
    # 辞書から復元
    restored = BenchmarkResult.from_dict(result_dict)
    
    # ValidationResultが正しく復元されることを確認
    assert restored.validation is not None
    assert restored.validation.is_valid == True
    assert restored.validation.max_relative_error == 1e-6
    assert restored.validation.mismatches == []
