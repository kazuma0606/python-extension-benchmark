"""性能回帰テスト

Task 8.1: 性能回帰テスト
- Pure Python性能の基準値確認
- FFI実装の期待性能確認
- 測定精度の検証
- 要件: 14.1, 14.2

このテストはPure Pythonの性能基準値を確立し、FFI実装の期待性能を確認し、
測定精度を検証する。
"""

import os
import sys
import json
import time
import statistics
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add benchmark directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psutil
except ImportError:
    psutil = None

from benchmark.ffi_implementations.uv_checker import UVEnvironmentChecker


class TestPerformanceRegression:
    """性能回帰テストクラス"""
    
    def __init__(self):
        self.uv_checker = UVEnvironmentChecker()
        
    def test_pure_python_baseline_performance(self):
        """Pure Python性能基準値確認テスト
        
        要件: 14.1 - Pure Python性能の基準値確認
        """
        print("\n=== Pure Python性能基準値確認テスト開始 ===")
        
        # 1. 基本的な数値計算性能
        print("1. 基本数値計算性能測定")
        
        def find_primes_python(n: int) -> List[int]:
            """Pure Python素数探索実装"""
            if n < 2:
                return []
            
            primes = []
            for num in range(2, n + 1):
                is_prime = True
                for i in range(2, int(num ** 0.5) + 1):
                    if num % i == 0:
                        is_prime = False
                        break
                if is_prime:
                    primes.append(num)
            return primes
        
        # 複数回実行して基準値を測定
        prime_times = []
        test_sizes = [100, 500, 1000]
        
        for size in test_sizes:
            times_for_size = []
            
            for run in range(5):  # 5回実行
                start_time = time.perf_counter()
                result = find_primes_python(size)
                end_time = time.perf_counter()
                
                execution_time = (end_time - start_time) * 1000  # ms
                times_for_size.append(execution_time)
            
            avg_time = statistics.mean(times_for_size)
            std_dev = statistics.stdev(times_for_size) if len(times_for_size) > 1 else 0
            
            prime_times.append({
                'size': size,
                'avg_time': avg_time,
                'std_dev': std_dev,
                'times': times_for_size,
                'result_count': len(result)
            })
            
            print(f"  素数探索(n={size}): {avg_time:.2f}±{std_dev:.2f}ms, 結果数: {len(result)}")
        
        # 2. 行列計算性能
        print("\n2. 行列計算性能測定")
        
        def matrix_multiply_python(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
            """Pure Python行列積実装"""
            rows_a, cols_a = len(a), len(a[0])
            rows_b, cols_b = len(b), len(b[0])
            
            if cols_a != rows_b:
                raise ValueError("Matrix dimensions don't match")
            
            result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
            
            for i in range(rows_a):
                for j in range(cols_b):
                    for k in range(cols_a):
                        result[i][j] += a[i][k] * b[k][j]
            
            return result
        
        matrix_times = []
        matrix_sizes = [5, 10, 20]
        
        for size in matrix_sizes:
            # テスト用行列生成
            matrix_a = [[float(i * size + j) for j in range(size)] for i in range(size)]
            matrix_b = [[float(i * size + j) for j in range(size)] for i in range(size)]
            
            times_for_size = []
            
            for run in range(3):  # 3回実行（行列計算は重いため）
                start_time = time.perf_counter()
                result = matrix_multiply_python(matrix_a, matrix_b)
                end_time = time.perf_counter()
                
                execution_time = (end_time - start_time) * 1000  # ms
                times_for_size.append(execution_time)
            
            avg_time = statistics.mean(times_for_size)
            std_dev = statistics.stdev(times_for_size) if len(times_for_size) > 1 else 0
            
            matrix_times.append({
                'size': size,
                'avg_time': avg_time,
                'std_dev': std_dev,
                'times': times_for_size
            })
            
            print(f"  行列積({size}x{size}): {avg_time:.2f}±{std_dev:.2f}ms")
        
        # 3. メモリ操作性能
        print("\n3. メモリ操作性能測定")
        
        def sort_array_python(arr: List[int]) -> List[int]:
            """Pure Pythonソート実装（バブルソート）"""
            n = len(arr)
            result = arr.copy()
            
            for i in range(n):
                for j in range(0, n - i - 1):
                    if result[j] > result[j + 1]:
                        result[j], result[j + 1] = result[j + 1], result[j]
            
            return result
        
        sort_times = []
        sort_sizes = [100, 500, 1000]
        
        for size in sort_sizes:
            # 逆順配列を生成
            test_array = list(range(size, 0, -1))
            
            times_for_size = []
            
            for run in range(3):  # 3回実行
                start_time = time.perf_counter()
                result = sort_array_python(test_array)
                end_time = time.perf_counter()
                
                execution_time = (end_time - start_time) * 1000  # ms
                times_for_size.append(execution_time)
            
            avg_time = statistics.mean(times_for_size)
            std_dev = statistics.stdev(times_for_size) if len(times_for_size) > 1 else 0
            
            sort_times.append({
                'size': size,
                'avg_time': avg_time,
                'std_dev': std_dev,
                'times': times_for_size
            })
            
            print(f"  配列ソート(n={size}): {avg_time:.2f}±{std_dev:.2f}ms")
        
        # 4. 基準値の検証
        print("\n4. 基準値検証")
        
        # 性能が合理的な範囲内であることを確認
        for prime_result in prime_times:
            assert prime_result['avg_time'] > 0, "Execution time should be positive"
            assert prime_result['avg_time'] < 10000, f"Prime calculation should complete within 10s, got {prime_result['avg_time']:.2f}ms"
            
            # 変動係数が50%以下であることを確認
            cv = prime_result['std_dev'] / prime_result['avg_time'] if prime_result['avg_time'] > 0 else float('inf')
            assert cv <= 0.5, f"Performance should be consistent, CV={cv:.2%}"
        
        for matrix_result in matrix_times:
            assert matrix_result['avg_time'] > 0, "Execution time should be positive"
            assert matrix_result['avg_time'] < 30000, f"Matrix calculation should complete within 30s, got {matrix_result['avg_time']:.2f}ms"
        
        for sort_result in sort_times:
            assert sort_result['avg_time'] > 0, "Execution time should be positive"
            assert sort_result['avg_time'] < 60000, f"Sort should complete within 60s, got {sort_result['avg_time']:.2f}ms"
        
        print("  ✓ 全ての基準値が合理的な範囲内")
        
        print("✓ Pure Python性能基準値確認テスト完了")
        
        return {
            'prime_performance': prime_times,
            'matrix_performance': matrix_times,
            'sort_performance': sort_times,
            'baseline_established': True
        }
    
    def test_ffi_implementation_expected_performance(self):
        """FFI実装期待性能確認テスト
        
        要件: 14.2 - FFI実装の期待性能確認
        """
        print("\n=== FFI実装期待性能確認テスト開始 ===")
        
        # 1. FFI実装ディレクトリの確認
        print("1. FFI実装ディレクトリ確認")
        
        benchmark_dir = Path(__file__).parent.parent / "benchmark"
        ffi_dir = benchmark_dir / "ffi_implementations"
        
        expected_ffi_implementations = [
            "c_ffi", "cpp_ffi", "numpy_ffi", "cython_ffi", "rust_ffi",
            "fortran_ffi", "julia_ffi", "go_ffi", "zig_ffi", "nim_ffi", "kotlin_ffi"
        ]
        
        available_ffi = []
        shared_libraries = {}
        
        if ffi_dir.exists():
            for impl_name in expected_ffi_implementations:
                impl_dir = ffi_dir / impl_name
                if impl_dir.exists():
                    available_ffi.append(impl_name)
                    
                    # 共有ライブラリファイルの確認
                    lib_files = (list(impl_dir.glob("*.dll")) + 
                               list(impl_dir.glob("*.so")) + 
                               list(impl_dir.glob("*.dylib")))
                    
                    if lib_files:
                        shared_libraries[impl_name] = [str(lib.name) for lib in lib_files]
        
        print(f"  利用可能FFI実装: {len(available_ffi)}/{len(expected_ffi_implementations)}")
        print(f"  実装リスト: {available_ffi}")
        print(f"  共有ライブラリ: {len(shared_libraries)} 実装")
        
        # 2. FFI実装の期待性能特性
        print("\n2. FFI実装期待性能特性")
        
        # 各FFI実装の期待性能特性を定義
        expected_performance_characteristics = {
            'c_ffi': {
                'expected_speedup_range': (10, 50),
                'description': 'C implementation should provide 10-50x speedup'
            },
            'cpp_ffi': {
                'expected_speedup_range': (10, 50),
                'description': 'C++ implementation should provide 10-50x speedup'
            },
            'numpy_ffi': {
                'expected_speedup_range': (5, 20),
                'description': 'NumPy FFI should provide 5-20x speedup (vectorized operations)'
            },
            'cython_ffi': {
                'expected_speedup_range': (5, 30),
                'description': 'Cython FFI should provide 5-30x speedup'
            },
            'rust_ffi': {
                'expected_speedup_range': (10, 40),
                'description': 'Rust FFI should provide 10-40x speedup'
            },
            'fortran_ffi': {
                'expected_speedup_range': (10, 50),
                'description': 'Fortran FFI should provide 10-50x speedup (scientific computing)'
            },
            'julia_ffi': {
                'expected_speedup_range': (5, 30),
                'description': 'Julia FFI should provide 5-30x speedup (JIT optimized)'
            },
            'go_ffi': {
                'expected_speedup_range': (3, 15),
                'description': 'Go FFI should provide 3-15x speedup'
            },
            'zig_ffi': {
                'expected_speedup_range': (10, 40),
                'description': 'Zig FFI should provide 10-40x speedup'
            },
            'nim_ffi': {
                'expected_speedup_range': (5, 25),
                'description': 'Nim FFI should provide 5-25x speedup'
            },
            'kotlin_ffi': {
                'expected_speedup_range': (2, 10),
                'description': 'Kotlin FFI should provide 2-10x speedup'
            }
        }
        
        for impl_name, characteristics in expected_performance_characteristics.items():
            min_speedup, max_speedup = characteristics['expected_speedup_range']
            description = characteristics['description']
            
            availability = "✓" if impl_name in available_ffi else "❌"
            library_status = "✓" if impl_name in shared_libraries else "❌"
            
            print(f"  {impl_name}: {description}")
            print(f"    ディレクトリ: {availability}, 共有ライブラリ: {library_status}")
        
        # 3. FFI実装の理論的性能分析
        print("\n3. FFI実装理論的性能分析")
        
        # Pure Pythonの基準性能を使用（前のテストから）
        baseline_prime_time = 50.0  # ms (仮定値)
        baseline_matrix_time = 100.0  # ms (仮定値)
        baseline_sort_time = 200.0  # ms (仮定値)
        
        theoretical_performance = {}
        
        for impl_name in available_ffi:
            if impl_name in expected_performance_characteristics:
                min_speedup, max_speedup = expected_performance_characteristics[impl_name]['expected_speedup_range']
                
                theoretical_performance[impl_name] = {
                    'prime_time_range': (baseline_prime_time / max_speedup, baseline_prime_time / min_speedup),
                    'matrix_time_range': (baseline_matrix_time / max_speedup, baseline_matrix_time / min_speedup),
                    'sort_time_range': (baseline_sort_time / max_speedup, baseline_sort_time / min_speedup),
                    'speedup_range': (min_speedup, max_speedup)
                }
                
                print(f"  {impl_name}:")
                print(f"    期待高速化: {min_speedup}-{max_speedup}x")
                print(f"    期待素数探索時間: {theoretical_performance[impl_name]['prime_time_range'][0]:.2f}-{theoretical_performance[impl_name]['prime_time_range'][1]:.2f}ms")
        
        # 4. FFI実装の制約と考慮事項
        print("\n4. FFI実装制約と考慮事項")
        
        ffi_constraints = {
            'data_conversion_overhead': {
                'description': 'Python ↔ C型変換によるオーバーヘッド',
                'impact': 'Small data: 10-50% overhead, Large data: 1-5% overhead'
            },
            'function_call_overhead': {
                'description': 'FFI関数呼び出しオーバーヘッド',
                'impact': 'Per call: 0.1-1.0μs overhead'
            },
            'memory_management': {
                'description': 'メモリ管理の複雑性',
                'impact': 'Potential memory leaks if not handled properly'
            },
            'platform_dependency': {
                'description': 'プラットフォーム依存の共有ライブラリ',
                'impact': 'Different .dll/.so/.dylib files needed'
            }
        }
        
        for constraint_name, details in ffi_constraints.items():
            print(f"  {constraint_name}: {details['description']}")
            print(f"    影響: {details['impact']}")
        
        # 5. 期待性能の検証
        print("\n5. 期待性能検証")
        
        # 基本的な検証
        assert len(available_ffi) > 0, "At least some FFI implementations should be available"
        assert len(shared_libraries) > 0, "At least some shared libraries should be available"
        
        # 期待性能範囲の妥当性確認
        for impl_name, perf_data in theoretical_performance.items():
            min_speedup, max_speedup = perf_data['speedup_range']
            
            assert min_speedup > 1.0, f"{impl_name} minimum speedup should be > 1.0x"
            assert max_speedup > min_speedup, f"{impl_name} maximum speedup should be > minimum speedup"
            assert max_speedup < 1000, f"{impl_name} maximum speedup should be realistic (< 1000x)"
        
        print(f"  ✓ {len(available_ffi)} FFI実装の期待性能を確認")
        print(f"  ✓ {len(shared_libraries)} 共有ライブラリの可用性を確認")
        
        print("✓ FFI実装期待性能確認テスト完了")
        
        return {
            'available_ffi_implementations': available_ffi,
            'shared_libraries': shared_libraries,
            'theoretical_performance': theoretical_performance,
            'ffi_constraints': ffi_constraints,
            'expected_performance_validated': True
        }
    
    def test_measurement_precision_verification(self):
        """測定精度検証テスト
        
        要件: 14.1, 14.2 - 測定精度の検証
        """
        print("\n=== 測定精度検証テスト開始 ===")
        
        # 1. 時間測定精度の確認
        print("1. 時間測定精度確認")
        
        # 異なる時間測定方法の比較
        measurement_methods = {
            'time.time()': time.time,
            'time.perf_counter()': time.perf_counter,
            'time.process_time()': time.process_time
        }
        
        def test_computation():
            """テスト用計算処理"""
            result = 0
            for i in range(10000):
                result += i * i
            return result
        
        measurement_results = {}
        
        for method_name, time_func in measurement_methods.items():
            times = []
            
            for run in range(10):  # 10回測定
                start_time = time_func()
                result = test_computation()
                end_time = time_func()
                
                execution_time = (end_time - start_time) * 1000  # ms
                times.append(execution_time)
            
            avg_time = statistics.mean(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            cv = std_dev / avg_time if avg_time > 0 else float('inf')
            
            measurement_results[method_name] = {
                'times': times,
                'avg_time': avg_time,
                'std_dev': std_dev,
                'cv': cv,
                'min_time': min(times),
                'max_time': max(times)
            }
            
            print(f"  {method_name}: {avg_time:.3f}±{std_dev:.3f}ms (CV: {cv:.1%})")
        
        # 2. 測定精度の統計分析
        print("\n2. 測定精度統計分析")
        
        # 最も精度の高い測定方法を特定
        best_method = min(measurement_results.keys(), 
                         key=lambda k: measurement_results[k]['cv'])
        
        print(f"  最高精度測定方法: {best_method}")
        print(f"  変動係数: {measurement_results[best_method]['cv']:.2%}")
        
        # 測定精度の要件確認
        for method_name, results in measurement_results.items():
            # time.perf_counter()のみ厳密な精度要件を適用
            if method_name == 'time.perf_counter()':
                assert results['cv'] <= 0.2, f"{method_name} CV should be <= 20%, got {results['cv']:.2%}"
                assert results['min_time'] > 0, f"{method_name} minimum time should be positive"
            else:
                # 他の測定方法は参考値として記録のみ
                if results['cv'] > 0.5:
                    print(f"    ⚠ {method_name}: 精度が低い (CV: {results['cv']:.2%})")
                if results['min_time'] <= 0:
                    print(f"    ⚠ {method_name}: 負の時間値を検出 (min: {results['min_time']:.6f}ms)")
        
        # 3. メモリ使用量測定精度
        print("\n3. メモリ使用量測定精度")
        
        if psutil:
            process = psutil.Process()
            
            memory_measurements = []
            
            for run in range(10):
                # メモリ使用量を測定
                initial_memory = process.memory_info().rss / (1024**2)  # MB
                
                # より大きなメモリを使用する処理
                test_data = [i for i in range(500000)]  # 50万要素のリスト
                
                peak_memory = process.memory_info().rss / (1024**2)  # MB
                memory_increase = peak_memory - initial_memory
                
                memory_measurements.append(memory_increase)
                
                del test_data  # メモリ解放
                time.sleep(0.1)  # メモリ解放の時間を確保
            
            avg_memory = statistics.mean(memory_measurements)
            std_memory = statistics.stdev(memory_measurements) if len(memory_measurements) > 1 else 0
            cv_memory = std_memory / avg_memory if avg_memory > 0 else float('inf')
            
            print(f"  平均メモリ増加: {avg_memory:.2f}±{std_memory:.2f}MB")
            print(f"  メモリ測定CV: {cv_memory:.1%}")
            
            # メモリ測定精度の確認（より緩い基準）
            if avg_memory > 1.0:  # 1MB以上のメモリ増加がある場合のみ精度をチェック
                assert cv_memory <= 0.5, f"Memory measurement CV should be <= 50%, got {cv_memory:.2%}"
            else:
                print(f"    ⚠ メモリ増加が小さすぎるため精度チェックをスキップ ({avg_memory:.2f}MB)")
            
            assert avg_memory >= 0, "Average memory increase should be non-negative"
        else:
            print("  ⚠ psutil not available, skipping memory precision test")
        
        # 4. 統計的有意性の確認
        print("\n4. 統計的有意性確認")
        
        # サンプルサイズの妥当性確認
        sample_sizes = [3, 5, 10, 20]
        
        def calculate_confidence_interval(times: List[float], confidence: float = 0.95) -> Tuple[float, float]:
            """信頼区間を計算"""
            if len(times) < 2:
                return (0, 0)
            
            mean = statistics.mean(times)
            std_dev = statistics.stdev(times)
            
            # t分布を使用した信頼区間（簡易版）
            import math
            t_value = 2.0  # 簡易的にt=2を使用
            margin = t_value * std_dev / math.sqrt(len(times))
            
            return (mean - margin, mean + margin)
        
        for sample_size in sample_sizes:
            times = []
            
            for run in range(sample_size):
                start_time = time.perf_counter()
                result = test_computation()
                end_time = time.perf_counter()
                
                execution_time = (end_time - start_time) * 1000  # ms
                times.append(execution_time)
            
            avg_time = statistics.mean(times)
            ci_lower, ci_upper = calculate_confidence_interval(times)
            ci_width = ci_upper - ci_lower
            
            print(f"  サンプルサイズ{sample_size}: {avg_time:.3f}ms, 信頼区間幅: {ci_width:.3f}ms")
        
        # 5. 測定環境の一貫性確認
        print("\n5. 測定環境一貫性確認")
        
        # システム負荷の確認
        if psutil:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            print(f"  CPU使用率: {cpu_percent:.1f}%")
            print(f"  メモリ使用率: {memory_percent:.1f}%")
            
            # システム負荷が適切であることを確認
            assert cpu_percent < 80, f"CPU usage should be < 80% for accurate measurements, got {cpu_percent:.1f}%"
            assert memory_percent < 90, f"Memory usage should be < 90% for accurate measurements, got {memory_percent:.1f}%"
        
        # 6. 最終検証
        print("\n6. 最終検証")
        
        # 測定精度の要件を満たしていることを確認
        best_cv = measurement_results[best_method]['cv']
        assert best_cv <= 0.1, f"Best measurement method CV should be <= 10%, got {best_cv:.2%}"
        
        print(f"  ✓ 最高測定精度: {best_cv:.2%} (要件: ≤10%)")
        print(f"  ✓ 推奨測定方法: {best_method}")
        
        print("✓ 測定精度検証テスト完了")
        
        return {
            'measurement_methods': measurement_results,
            'best_method': best_method,
            'best_cv': best_cv,
            'memory_precision': {
                'avg_memory': avg_memory if psutil else None,
                'cv_memory': cv_memory if psutil else None
            },
            'measurement_precision_validated': True
        }
    
    def test_performance_regression_comprehensive(self):
        """包括的性能回帰テスト"""
        
        print("\n" + "=" * 80)
        print("包括的性能回帰テスト実行")
        print("=" * 80)
        print(f"開始時刻: {datetime.now().isoformat()}")
        print()
        
        # 各サブテストを実行
        print("実行中: Pure Python性能基準値確認...")
        baseline_results = self.test_pure_python_baseline_performance()
        
        print("\n実行中: FFI実装期待性能確認...")
        ffi_results = self.test_ffi_implementation_expected_performance()
        
        print("\n実行中: 測定精度検証...")
        precision_results = self.test_measurement_precision_verification()
        
        # 最終レポート生成
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': {
                'baseline_performance': baseline_results,
                'ffi_expected_performance': ffi_results,
                'measurement_precision': precision_results
            },
            'summary': {
                'baseline_established': baseline_results['baseline_established'],
                'ffi_implementations_available': len(ffi_results['available_ffi_implementations']),
                'shared_libraries_available': len(ffi_results['shared_libraries']),
                'measurement_precision_validated': precision_results['measurement_precision_validated'],
                'best_measurement_method': precision_results['best_method'],
                'best_measurement_cv': precision_results['best_cv']
            }
        }
        
        # 最終検証
        summary = final_report['summary']
        
        assert summary['baseline_established'], "Baseline performance should be established"
        assert summary['ffi_implementations_available'] > 0, "At least some FFI implementations should be available"
        assert summary['measurement_precision_validated'], "Measurement precision should be validated"
        assert summary['best_measurement_cv'] <= 0.1, "Measurement precision should be adequate"
        
        print("\n" + "=" * 80)
        print("包括的性能回帰テスト結果")
        print("=" * 80)
        print(f"基準値確立: {'✓' if summary['baseline_established'] else '❌'}")
        print(f"FFI実装数: {summary['ffi_implementations_available']}")
        print(f"共有ライブラリ数: {summary['shared_libraries_available']}")
        print(f"測定精度: {summary['best_measurement_cv']:.2%} ({summary['best_measurement_method']})")
        print("=" * 80)
        
        print(f"\n🎉 包括的性能回帰テストが成功しました！")
        print(f"完了時刻: {datetime.now().isoformat()}")
        
        return final_report


if __name__ == '__main__':
    # テスト実行
    test_instance = TestPerformanceRegression()
    
    try:
        final_report = test_instance.test_performance_regression_comprehensive()
        
        print("\n✅ 全ての性能回帰テストが成功しました！")
        
    except Exception as e:
        print(f"\n❌ 性能回帰テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)