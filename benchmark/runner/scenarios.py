"""ベンチマークシナリオ定義

各ベンチマークシナリオ（数値計算、メモリ操作、並列処理）を定義する。
"""

import time
import tracemalloc
from typing import Any, Tuple, List
from benchmark.models import Scenario, Implementation


class NumericScenario(Scenario):
    """数値計算シナリオ（素数探索、行列積）"""
    
    def __init__(self, scenario_type: str = "primes"):
        """
        Args:
            scenario_type: "primes" または "matrix"
        """
        self.scenario_type = scenario_type
        
        if scenario_type == "primes":
            name = "Numeric: Prime Search"
            description = "Find all prime numbers up to 100,000 using Sieve of Eratosthenes"
            input_data = 100000
            expected_output_type = list
        elif scenario_type == "matrix":
            name = "Numeric: Matrix Multiplication"
            description = "Multiply two 100x100 matrices"
            # Create 100x100 matrices
            size = 100
            matrix_a = [[float(i * size + j) for j in range(size)] for i in range(size)]
            matrix_b = [[float(i * size + j) for j in range(size)] for i in range(size)]
            input_data = (matrix_a, matrix_b)
            expected_output_type = list
        else:
            raise ValueError(f"Unknown scenario_type: {scenario_type}")
        
        super().__init__(
            name=name,
            description=description,
            input_data=input_data,
            expected_output_type=expected_output_type
        )
    
    def execute(self, implementation: Implementation) -> Tuple[Any, float, float]:
        """実装を実行し、(出力, 実行時間, メモリ使用量)を返す
        
        Args:
            implementation: 実行する実装モジュール
            
        Returns:
            Tuple[Any, float, float]: (出力値, 実行時間(ms), メモリ使用量(MB))
        """
        # メモリ計測開始
        tracemalloc.start()
        
        # 実行時間計測
        start_time = time.perf_counter()
        
        if self.scenario_type == "primes":
            output = implementation.module.find_primes(self.input_data)
        elif self.scenario_type == "matrix":
            matrix_a, matrix_b = self.input_data
            output = implementation.module.matrix_multiply(matrix_a, matrix_b)
        else:
            raise ValueError(f"Unknown scenario_type: {self.scenario_type}")
        
        end_time = time.perf_counter()
        
        # メモリ使用量取得
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 実行時間をミリ秒に変換
        execution_time_ms = (end_time - start_time) * 1000
        
        # メモリ使用量をMBに変換
        memory_usage_mb = peak / (1024 * 1024)
        
        return output, execution_time_ms, memory_usage_mb


class MemoryScenario(Scenario):
    """メモリ操作シナリオ（配列ソート、フィルタ）"""
    
    def __init__(self, scenario_type: str = "sort"):
        """
        Args:
            scenario_type: "sort" または "filter"
        """
        self.scenario_type = scenario_type
        
        if scenario_type == "sort":
            name = "Memory: Array Sort"
            description = "Sort an array of 10 million integers"
            # 10,000,000要素の配列を生成（逆順）
            input_data = list(range(10000000, 0, -1))
            expected_output_type = list
        elif scenario_type == "filter":
            name = "Memory: Array Filter"
            description = "Filter array elements >= threshold"
            # 10,000,000要素の配列と閾値
            input_data = (list(range(10000000)), 5000000)
            expected_output_type = list
        else:
            raise ValueError(f"Unknown scenario_type: {scenario_type}")
        
        super().__init__(
            name=name,
            description=description,
            input_data=input_data,
            expected_output_type=expected_output_type
        )
    
    def execute(self, implementation: Implementation) -> Tuple[Any, float, float]:
        """実装を実行し、(出力, 実行時間, メモリ使用量)を返す
        
        Args:
            implementation: 実行する実装モジュール
            
        Returns:
            Tuple[Any, float, float]: (出力値, 実行時間(ms), メモリ使用量(MB))
        """
        # メモリ計測開始
        tracemalloc.start()
        
        # 実行時間計測
        start_time = time.perf_counter()
        
        if self.scenario_type == "sort":
            output = implementation.module.sort_array(self.input_data)
        elif self.scenario_type == "filter":
            arr, threshold = self.input_data
            output = implementation.module.filter_array(arr, threshold)
        else:
            raise ValueError(f"Unknown scenario_type: {self.scenario_type}")
        
        end_time = time.perf_counter()
        
        # メモリ使用量取得
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 実行時間をミリ秒に変換
        execution_time_ms = (end_time - start_time) * 1000
        
        # メモリ使用量をMBに変換
        memory_usage_mb = peak / (1024 * 1024)
        
        return output, execution_time_ms, memory_usage_mb


def get_all_scenarios() -> List[Scenario]:
    """全ベンチマークシナリオを取得
    
    Returns:
        List[Scenario]: 全シナリオのリスト
    """
    scenarios = [
        # 数値計算シナリオ
        NumericScenario("primes"),
        NumericScenario("matrix"),
        
        # メモリ操作シナリオ
        MemoryScenario("sort"),
        MemoryScenario("filter"),
        
        # 並列処理シナリオ: スレッド数1、2、4、8、16で計測
        ParallelScenario(1),
        ParallelScenario(2),
        ParallelScenario(4),
        ParallelScenario(8),
        ParallelScenario(16),
    ]
    
    return scenarios


def get_default_implementations() -> List[str]:
    """デフォルトの実装リストを取得（拡張版 + FFI版）
    
    Returns:
        List[str]: 24の実装名（12拡張版 + 12FFI版）
    """
    extension_implementations = [
        "python",      # Pure Python
        "numpy_impl",  # NumPy
        "c_ext",       # C Extension
        "cpp_ext",     # C++ Extension
        "cython_ext",  # Cython Extension
        "rust_ext",    # Rust Extension
        "fortran_ext", # Fortran Extension
        "julia_ext",   # Julia Extension
        "go_ext",      # Go Extension
        "zig_ext",     # Zig Extension
        "nim_ext",     # Nim Extension
        "kotlin_ext",  # Kotlin Extension
    ]
    
    ffi_implementations = [
        "c_ffi",       # C FFI
        "cpp_ffi",     # C++ FFI
        "numpy_ffi",   # NumPy FFI
        "cython_ffi",  # Cython FFI
        "rust_ffi",    # Rust FFI
        "fortran_ffi", # Fortran FFI
        "julia_ffi",   # Julia FFI
        "go_ffi",      # Go FFI
        "zig_ffi",     # Zig FFI
        "nim_ffi",     # Nim FFI
        "kotlin_ffi",  # Kotlin FFI
    ]
    
    return extension_implementations + ffi_implementations


def get_extension_implementations() -> List[str]:
    """拡張版実装のみを取得
    
    Returns:
        List[str]: 12の拡張版実装名
    """
    return [
        "python",      # Pure Python
        "numpy_impl",  # NumPy
        "c_ext",       # C Extension
        "cpp_ext",     # C++ Extension
        "cython_ext",  # Cython Extension
        "rust_ext",    # Rust Extension
        "fortran_ext", # Fortran Extension
        "julia_ext",   # Julia Extension
        "go_ext",      # Go Extension
        "zig_ext",     # Zig Extension
        "nim_ext",     # Nim Extension
        "kotlin_ext",  # Kotlin Extension
    ]


def get_ffi_implementations() -> List[str]:
    """FFI実装のみを取得
    
    Returns:
        List[str]: 11のFFI実装名（Pure Pythonは除く）
    """
    return [
        "c_ffi",       # C FFI
        "cpp_ffi",     # C++ FFI
        "numpy_ffi",   # NumPy FFI
        "cython_ffi",  # Cython FFI
        "rust_ffi",    # Rust FFI
        "fortran_ffi", # Fortran FFI
        "julia_ffi",   # Julia FFI
        "go_ffi",      # Go FFI
        "zig_ffi",     # Zig FFI
        "nim_ffi",     # Nim FFI
        "kotlin_ffi",  # Kotlin FFI
    ]


class ParallelScenario(Scenario):
    """並列処理シナリオ（マルチスレッド分散計算）"""
    
    def __init__(self, num_threads: int = 1):
        """
        Args:
            num_threads: 使用するスレッド数
        """
        self.num_threads = num_threads
        
        name = f"Parallel: Multi-threaded Computation ({num_threads} threads)"
        description = f"Compute sum of 10 million floats using {num_threads} threads"
        # 10,000,000要素の浮動小数点配列
        input_data = [float(i) for i in range(10000000)]
        expected_output_type = float
        
        super().__init__(
            name=name,
            description=description,
            input_data=input_data,
            expected_output_type=expected_output_type
        )
    
    def execute(self, implementation: Implementation) -> Tuple[Any, float, float]:
        """実装を実行し、(出力, 実行時間, メモリ使用量)を返す
        
        Args:
            implementation: 実行する実装モジュール
            
        Returns:
            Tuple[Any, float, float]: (出力値, 実行時間(ms), メモリ使用量(MB))
        """
        # メモリ計測開始
        tracemalloc.start()
        
        # 実行時間計測
        start_time = time.perf_counter()
        
        output = implementation.module.parallel_compute(self.input_data, self.num_threads)
        
        end_time = time.perf_counter()
        
        # メモリ使用量取得
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # 実行時間をミリ秒に変換
        execution_time_ms = (end_time - start_time) * 1000
        
        # メモリ使用量をMBに変換
        memory_usage_mb = peak / (1024 * 1024)
        
        return output, execution_time_ms, memory_usage_mb
