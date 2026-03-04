"""Property-based tests for scenario execution.

Tests for scenario execution completeness, execution time recording,
memory usage recording, and warmup data exclusion.
"""

import importlib
from typing import List
from hypothesis import given, strategies as st, settings
from benchmark.runner.scenarios import NumericScenario, MemoryScenario, ParallelScenario
from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.models import Implementation


# Strategy for generating implementation lists
@st.composite
def implementation_list_strategy(draw):
    """Generate a list of valid implementations."""
    # Always include at least python and numpy implementations
    impl_names = draw(st.lists(
        st.sampled_from(["python", "numpy_impl"]),
        min_size=1,
        max_size=2,
        unique=True
    ))
    
    implementations = []
    for name in impl_names:
        try:
            module = importlib.import_module(f"benchmark.{name}")
            language = "Python" if name == "python" else "NumPy"
            implementations.append(Implementation(
                name=name,
                module=module,
                language=language
            ))
        except ImportError:
            pass
    
    return implementations


@st.composite
def scenario_strategy(draw):
    """Generate a valid scenario."""
    scenario_type = draw(st.sampled_from([
        ("numeric", "primes"),
        ("numeric", "matrix"),
        ("memory", "sort"),
        ("memory", "filter"),
        ("parallel", 1),
        ("parallel", 2),
    ]))
    
    if scenario_type[0] == "numeric":
        return NumericScenario(scenario_type[1])
    elif scenario_type[0] == "memory":
        return MemoryScenario(scenario_type[1])
    else:  # parallel
        return ParallelScenario(scenario_type[1])


@given(
    scenario=scenario_strategy(),
    implementations=implementation_list_strategy()
)
@settings(deadline=None)
def test_scenario_execution_completeness(scenario, implementations):
    """Feature: python-extension-benchmark, Property 1: シナリオ実行の完全性
    
    任意のシナリオと実装モジュールのリストに対して、シナリオを実行すると、
    全ての実装モジュールが呼び出され、結果が記録されなければならない
    
    Validates: Requirements 1.1, 1.2, 2.1, 2.2, 3.1
    """
    runner = BenchmarkRunner()
    
    # シナリオを実行（テスト用に実行回数を減らす）
    results = runner.run_scenario(
        scenario,
        implementations,
        warmup_runs=1,
        measurement_runs=5
    )
    
    # 全ての実装に対して結果が記録されていることを確認
    assert len(results) == len(implementations), \
        f"Expected {len(implementations)} results, got {len(results)}"
    
    # 各実装の結果が記録されていることを確認
    result_names = {r.implementation_name for r in results}
    impl_names = {impl.name for impl in implementations}
    assert result_names == impl_names, \
        f"Result names {result_names} don't match implementation names {impl_names}"
    
    # 各結果にシナリオ名が記録されていることを確認
    for result in results:
        assert result.scenario_name == scenario.name, \
            f"Expected scenario name '{scenario.name}', got '{result.scenario_name}'"
        
        # 成功した実装は出力値を持つべき
        if result.status == "SUCCESS":
            assert result.output_value is not None, \
                f"Implementation {result.implementation_name} succeeded but has no output"



@given(
    scenario=scenario_strategy(),
    implementations=implementation_list_strategy()
)
@settings(deadline=None)
def test_execution_time_recording(scenario, implementations):
    """Feature: python-extension-benchmark, Property 2: 実行時間の記録
    
    任意の実装モジュールとシナリオに対して、実行が完了すると、
    実行時間がミリ秒単位で記録され、結果に含まれなければならない
    
    Validates: Requirements 1.3
    """
    runner = BenchmarkRunner()
    
    # シナリオを実行（テスト用に実行回数を減らす）
    results = runner.run_scenario(
        scenario,
        implementations,
        warmup_runs=1,
        measurement_runs=5
    )
    
    for result in results:
        if result.status == "SUCCESS":
            # 実行時間が記録されていることを確認
            assert len(result.execution_times) == 5, \
                f"Expected 5 execution times, got {len(result.execution_times)}"
            
            # 全ての実行時間が正の値であることを確認
            for exec_time in result.execution_times:
                assert exec_time > 0, \
                    f"Execution time must be positive, got {exec_time}"
            
            # 統計値が記録されていることを確認
            assert result.min_time > 0, \
                f"min_time must be positive, got {result.min_time}"
            assert result.median_time > 0, \
                f"median_time must be positive, got {result.median_time}"
            assert result.mean_time > 0, \
                f"mean_time must be positive, got {result.mean_time}"
            assert result.std_dev >= 0, \
                f"std_dev must be non-negative, got {result.std_dev}"
            
            # 統計値が実行時間リストと一致することを確認
            assert result.min_time == min(result.execution_times), \
                f"min_time {result.min_time} doesn't match min of execution_times"



@given(
    scenario=scenario_strategy(),
    implementations=implementation_list_strategy()
)
@settings(deadline=None)
def test_memory_usage_recording(scenario, implementations):
    """Feature: python-extension-benchmark, Property 4: メモリ使用量の記録
    
    任意の実装モジュールとシナリオに対して、実行が完了すると、
    ピークメモリ使用量と平均メモリ使用量がメガバイト単位で記録され、
    結果に含まれなければならない
    
    Validates: Requirements 2.3, 2.4
    """
    runner = BenchmarkRunner()
    
    # シナリオを実行（テスト用に実行回数を減らす）
    results = runner.run_scenario(
        scenario,
        implementations,
        warmup_runs=1,
        measurement_runs=5
    )
    
    for result in results:
        if result.status == "SUCCESS":
            # メモリ使用量が記録されていることを確認
            assert len(result.memory_usage) == 5, \
                f"Expected 5 memory usage measurements, got {len(result.memory_usage)}"
            
            # 全てのメモリ使用量が非負の値であることを確認
            for mem_usage in result.memory_usage:
                assert mem_usage >= 0, \
                    f"Memory usage must be non-negative, got {mem_usage}"
            
            # メモリ使用量がMB単位で記録されていることを確認（妥当な範囲）
            # 最小でも数KB、最大でも数GB程度を想定
            for mem_usage in result.memory_usage:
                assert 0 <= mem_usage < 10000, \
                    f"Memory usage {mem_usage} MB seems unreasonable"



@given(
    scenario=scenario_strategy(),
    implementations=implementation_list_strategy(),
    warmup_runs=st.integers(min_value=1, max_value=5),
    measurement_runs=st.integers(min_value=3, max_value=10)
)
@settings(deadline=None)
def test_warmup_data_exclusion(scenario, implementations, warmup_runs, measurement_runs):
    """Feature: python-extension-benchmark, Property 8: ウォームアップデータの除外
    
    任意のベンチマーク実行に対して、統計計算に使用されるデータは
    ウォームアップ実行の結果を含まず、本計測の結果のみを含まなければならない
    
    Validates: Requirements 4.4
    """
    runner = BenchmarkRunner()
    
    # シナリオを実行
    results = runner.run_scenario(
        scenario,
        implementations,
        warmup_runs=warmup_runs,
        measurement_runs=measurement_runs
    )
    
    for result in results:
        if result.status == "SUCCESS":
            # 記録された実行時間の数が本計測の回数と一致することを確認
            assert len(result.execution_times) == measurement_runs, \
                f"Expected {measurement_runs} execution times (excluding warmup), " \
                f"got {len(result.execution_times)}"
            
            # 記録されたメモリ使用量の数が本計測の回数と一致することを確認
            assert len(result.memory_usage) == measurement_runs, \
                f"Expected {measurement_runs} memory measurements (excluding warmup), " \
                f"got {len(result.memory_usage)}"
            
            # ウォームアップ実行の結果が含まれていないことを確認
            # （記録されたデータ数が本計測の回数と正確に一致していれば、
            #  ウォームアップデータは除外されている）
