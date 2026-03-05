"""エラーハンドリングのデモンストレーション

このスクリプトは、エラーハンドリング機能を実演します。
"""

import sys
import os
from pathlib import Path

# Add benchmark directory to path (adjust for new location)
benchmark_path = Path(__file__).parent.parent.parent / 'benchmark'
sys.path.insert(0, str(benchmark_path))

from benchmark.runner.benchmark import BenchmarkRunner
from benchmark.runner.scenarios import NumericScenario


def main():
    print("=" * 70)
    print("エラーハンドリングのデモンストレーション")
    print("=" * 70)
    print()
    
    # ベンチマークランナーを作成
    runner = BenchmarkRunner()
    
    # 実装をロード（存在しないモジュールを含む）
    print("1. 実装モジュールのロード（存在しないモジュールを含む）")
    print("-" * 70)
    implementation_names = [
        "python",           # 存在する
        "numpy_impl",       # 存在する
        "invalid_module",   # 存在しない
        "c_ext",           # 存在しない（まだ実装されていない）
    ]
    
    implementations = runner.load_implementations(implementation_names)
    print()
    
    # シナリオを実行
    print("2. ベンチマークシナリオの実行")
    print("-" * 70)
    scenario = NumericScenario("primes")
    
    results = runner.run_scenario(
        scenario,
        implementations,
        warmup_runs=1,
        measurement_runs=3
    )
    
    print()
    print("3. 結果サマリー")
    print("-" * 70)
    for result in results:
        status_icon = "✓" if result.status == "SUCCESS" else "✗"
        print(f"{status_icon} {result.implementation_name}: {result.status}")
        if result.status == "SUCCESS":
            print(f"  平均実行時間: {result.mean_time:.2f} ms")
        else:
            print(f"  エラー: {result.error_message}")
    
    print()
    
    # エラーサマリーを表示
    if runner.error_handler.has_errors():
        runner.error_handler.print_error_summary()
    
    print("=" * 70)
    print("デモンストレーション完了")
    print("=" * 70)


if __name__ == "__main__":
    main()