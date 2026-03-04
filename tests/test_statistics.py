"""プロパティベーステスト: 統計計算モジュール

統計計算の正確性、相対スコア計算、相対誤差計算を検証する。
"""

import pytest
import statistics
from hypothesis import given, strategies as st

from benchmark.statistics import Statistics


@given(st.lists(st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False), min_size=10, max_size=100))
def test_property_7_statistics_calculation(measurements):
    """Feature: python-extension-benchmark, Property 7: 統計計算の正確性
    
    **検証: 要件 4.3**
    
    任意の計測データのリストに対して、計算された最小値、中央値、平均値、標準偏差は、
    標準的な統計関数の結果と一致しなければならない
    """
    result = Statistics.calculate(measurements)
    
    # 最小値の検証
    assert result.min == min(measurements)
    
    # 中央値の検証
    assert result.median == statistics.median(measurements)
    
    # 平均値の検証
    assert abs(result.mean - statistics.mean(measurements)) < 1e-10
    
    # 標準偏差の検証
    if len(measurements) > 1:
        expected_std = statistics.stdev(measurements)
        assert abs(result.std_dev - expected_std) < 1e-10
    else:
        assert result.std_dev == 0.0


@given(
    st.lists(st.floats(min_value=0.001, max_value=1000.0, allow_nan=False, allow_infinity=False), min_size=2, max_size=10)
)
def test_property_3_relative_score_calculation(execution_times):
    """Feature: python-extension-benchmark, Property 3: 相対スコアの計算正確性
    
    **検証: 要件 1.4**
    
    任意の実行時間のセットに対して、Pure Python実装の実行時間をベースラインとした
    相対スコアは、各実装の実行時間をPure Pythonの実行時間で割った値と等しくなければならない
    """
    baseline = execution_times[0]
    
    for time in execution_times:
        expected = baseline / time
        actual = Statistics.calculate_relative_score(time, baseline)
        assert abs(expected - actual) < 1e-10


@given(
    st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
)
def test_property_16_relative_error_calculation(a, b):
    """Feature: python-extension-benchmark, Property 16: 相対誤差の検証正確性
    
    **検証: 要件 9.2**
    
    任意の2つの数値に対して、相対誤差の計算は |a - b| / max(|a|, |b|) として
    正しく計算され、0.0001未満かどうかの判定が正確でなければならない
    """
    # 両方がゼロの場合はスキップ
    if a == 0 and b == 0:
        actual = Statistics.calculate_relative_error(a, b)
        assert actual == 0.0
        return
    
    # 期待値を計算
    max_abs = max(abs(a), abs(b))
    expected = abs(a - b) / max_abs
    
    # 実際の値を計算
    actual = Statistics.calculate_relative_error(a, b)
    
    # 検証
    assert abs(expected - actual) < 1e-10
    
    # 0.0001未満かどうかの判定が正確であることを確認
    threshold = 0.0001
    if expected < threshold:
        assert actual < threshold
    else:
        assert actual >= threshold or abs(actual - threshold) < 1e-10
