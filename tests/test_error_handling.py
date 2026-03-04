"""Property-based tests for error handling.

Tests for error continuation when implementations fail.
"""

from types import ModuleType
from typing import List
from hypothesis import given, strategies as st, settings
from benchmark.runner.scenarios import NumericScenario
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.models import Implementation


class MockModule:
    """モックモジュール（エラーを発生させる/させない）"""
    
    def __init__(self, should_error: bool = False, error_type: str = "runtime"):
        self.should_error = should_error
        self.error_type = error_type
    
    def find_primes(self, n: int) -> List[int]:
        """素数探索（モック実装）"""
        if self.should_error:
            if self.error_type == "runtime":
                raise RuntimeError("Mock runtime error in find_primes")
            elif self.error_type == "value":
                raise ValueError("Mock value error in find_primes")
            elif self.error_type == "type":
                raise TypeError("Mock type error in find_primes")
        
        # 簡単な実装（正確性は不要）
        return [2, 3, 5, 7, 11]
    
    def matrix_multiply(self, a, b):
        """行列積（モック実装）"""
        if self.should_error:
            raise RuntimeError("Mock error in matrix_multiply")
        return [[0.0]]
    
    def sort_array(self, arr):
        """配列ソート（モック実装）"""
        if self.should_error:
            raise RuntimeError("Mock error in sort_array")
        return sorted(arr)
    
    def filter_array(self, arr, threshold):
        """配列フィルタ（モック実装）"""
        if self.should_error:
            raise RuntimeError("Mock error in filter_array")
        return [x for x in arr if x >= threshold]
    
    def parallel_compute(self, data, num_threads):
        """並列計算（モック実装）"""
        if self.should_error:
            raise RuntimeError("Mock error in parallel_compute")
        return sum(data)


def create_mock_implementation(name: str, should_error: bool) -> Implementation:
    """モック実装を作成
    
    Args:
        name: 実装名
        should_error: エラーを発生させるかどうか
        
    Returns:
        Implementation: モック実装
    """
    mock_module = MockModule(should_error=should_error)
    return Implementation(
        name=name,
        module=mock_module,
        language="Mock"
    )


@st.composite
def error_flag_list_strategy(draw):
    """エラーフラグのリストを生成
    
    少なくとも1つは成功する実装を含む
    """
    # 3-10個の実装を生成
    size = draw(st.integers(min_value=3, max_value=10))
    
    # 少なくとも1つは成功する実装を含む
    error_flags = draw(st.lists(
        st.booleans(),
        min_size=size,
        max_size=size
    ))
    
    # 全てがエラーの場合、少なくとも1つを成功に変更
    if all(error_flags):
        error_flags[0] = False
    
    return error_flags


@given(error_flags=error_flag_list_strategy())
@settings(deadline=None, max_examples=100)
def test_error_continuation(error_flags):
    """Feature: python-extension-benchmark, Property 14: エラー時の継続実行
    
    任意の実装モジュールのリストに対して、1つの実装がエラーを発生させても、
    他の実装モジュールの実行は継続され、エラー情報が記録されなければならない
    
    Validates: Requirements 8.3
    """
    # モック実装を作成
    implementations = [
        create_mock_implementation(f"mock_{i}", should_error)
        for i, should_error in enumerate(error_flags)
    ]
    
    # シナリオを作成
    scenario = NumericScenario("primes")
    
    # ベンチマークランナーを作成
    runner = BenchmarkRunner()
    
    # シナリオを実行（テスト用に実行回数を減らす）
    results = runner.run_scenario(
        scenario,
        implementations,
        warmup_runs=1,
        measurement_runs=3
    )
    
    # 全ての実装に対して結果が記録されていることを確認
    assert len(results) == len(implementations), \
        f"Expected {len(implementations)} results, got {len(results)}"
    
    # エラーが発生した実装の数を確認
    error_count = sum(1 for r in results if r.status == "ERROR")
    expected_error_count = sum(error_flags)
    assert error_count == expected_error_count, \
        f"Expected {expected_error_count} errors, got {error_count}"
    
    # 成功した実装の数を確認
    success_count = sum(1 for r in results if r.status == "SUCCESS")
    expected_success_count = len(error_flags) - sum(error_flags)
    assert success_count == expected_success_count, \
        f"Expected {expected_success_count} successes, got {success_count}"
    
    # エラーが発生した実装はエラーメッセージを持つべき
    for i, result in enumerate(results):
        if error_flags[i]:
            assert result.status == "ERROR", \
                f"Implementation {i} should have ERROR status"
            assert result.error_message is not None, \
                f"Implementation {i} should have error message"
            assert len(result.execution_times) == 0, \
                f"Implementation {i} should have no execution times"
        else:
            assert result.status == "SUCCESS", \
                f"Implementation {i} should have SUCCESS status"
            assert result.error_message is None, \
                f"Implementation {i} should not have error message"
            assert len(result.execution_times) == 3, \
                f"Implementation {i} should have 3 execution times"
    
    # エラーハンドラーにエラーが記録されていることを確認
    assert len(runner.error_handler.error_logs) == expected_error_count, \
        f"Expected {expected_error_count} error logs, " \
        f"got {len(runner.error_handler.error_logs)}"


@given(
    num_implementations=st.integers(min_value=2, max_value=5),
    error_position=st.integers(min_value=0, max_value=4)
)
@settings(deadline=None, max_examples=50)
def test_error_at_specific_position(num_implementations, error_position):
    """特定の位置でエラーが発生した場合のテスト
    
    エラーが発生した位置に関わらず、全ての実装が実行されることを確認
    """
    # エラー位置が実装数を超える場合は調整
    if error_position >= num_implementations:
        error_position = num_implementations - 1
    
    # エラーフラグを作成
    error_flags = [i == error_position for i in range(num_implementations)]
    
    # モック実装を作成
    implementations = [
        create_mock_implementation(f"mock_{i}", should_error)
        for i, should_error in enumerate(error_flags)
    ]
    
    # シナリオを作成
    scenario = NumericScenario("primes")
    
    # ベンチマークランナーを作成
    runner = BenchmarkRunner()
    
    # シナリオを実行
    results = runner.run_scenario(
        scenario,
        implementations,
        warmup_runs=1,
        measurement_runs=2
    )
    
    # 全ての実装が実行されたことを確認
    assert len(results) == num_implementations
    
    # エラー位置の実装だけがエラーステータスを持つことを確認
    for i, result in enumerate(results):
        if i == error_position:
            assert result.status == "ERROR"
        else:
            assert result.status == "SUCCESS"


def test_multiple_error_types():
    """異なるタイプのエラーが発生した場合のテスト"""
    # 異なるエラータイプのモック実装を作成
    implementations = [
        create_mock_implementation("mock_success", should_error=False),
        Implementation(
            name="mock_runtime_error",
            module=MockModule(should_error=True, error_type="runtime"),
            language="Mock"
        ),
        Implementation(
            name="mock_value_error",
            module=MockModule(should_error=True, error_type="value"),
            language="Mock"
        ),
        Implementation(
            name="mock_type_error",
            module=MockModule(should_error=True, error_type="type"),
            language="Mock"
        ),
    ]
    
    # シナリオを作成
    scenario = NumericScenario("primes")
    
    # ベンチマークランナーを作成
    runner = BenchmarkRunner()
    
    # シナリオを実行
    results = runner.run_scenario(
        scenario,
        implementations,
        warmup_runs=1,
        measurement_runs=2
    )
    
    # 全ての実装が実行されたことを確認
    assert len(results) == 4
    
    # 最初の実装は成功
    assert results[0].status == "SUCCESS"
    assert results[0].implementation_name == "mock_success"
    
    # 残りの実装はエラー
    for i in range(1, 4):
        assert results[i].status == "ERROR"
        assert results[i].error_message is not None
        assert "Mock" in results[i].error_message
    
    # エラーログが記録されていることを確認
    assert len(runner.error_handler.error_logs) == 3
