# FFI Benchmark Tutorial

## はじめに

このチュートリアルでは、Python Benchmark TestシステムのFFI実装を使用して、Pure PythonとFFI版の性能比較を行う方法を学習します。

## 前提条件

- Python 3.8以上
- uv（Python パッケージマネージャー）
- 基本的なPythonプログラミング知識

## ステップ1: 環境セットアップ

### 1.1 uvのインストール

```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1.2 プロジェクトセットアップ

```bash
# プロジェクトディレクトリに移動
cd py_benchmark_test

# uv環境の同期
uv sync

# 仮想環境のアクティベーション
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows
```

### 1.3 環境確認

```python
from benchmark.ffi_implementations.uv_checker import UVEnvironmentChecker

checker = UVEnvironmentChecker()
checker.print_environment_status()
```

## ステップ2: 基本的なベンチマーク実行

### 2.1 環境チェック

```python
from benchmark.runner.ffi_benchmark_runner import FFIBenchmarkRunner

runner = FFIBenchmarkRunner()
runner.check_environment()
```

### 2.2 シンプルなベンチマーク

```python
# FFI比較ベンチマークの実行
runner.run_ffi_comparison_benchmark(
    include_extensions=True,
    include_ffi=True,
    output_prefix="tutorial_benchmark"
)
```

## ステップ3: カスタムシナリオの作成

### 3.1 数値計算シナリオ

```python
from benchmark.runner.scenarios import NumericScenario

# 素数探索シナリオ
prime_scenario = NumericScenario("primes")
prime_scenario.input_data = 1000  # 1000以下の素数を探索

# 行列積シナリオ
matrix_scenario = NumericScenario("matrix")
size = 10
matrix_a = [[float(i * size + j) for j in range(size)] for i in range(size)]
matrix_b = [[float(i * size + j) for j in range(size)] for i in range(size)]
matrix_scenario.input_data = (matrix_a, matrix_b)
```

### 3.2 メモリ操作シナリオ

```python
from benchmark.runner.scenarios import MemoryScenario

# ソートシナリオ
sort_scenario = MemoryScenario("sort")
sort_scenario.input_data = list(range(5000, 0, -1))  # 逆順配列

# フィルタシナリオ
filter_scenario = MemoryScenario("filter")
filter_scenario.input_data = (list(range(10000)), 5000)  # 閾値5000でフィルタ
```

## ステップ4: 結果の分析

### 4.1 結果ファイルの確認

```python
import json
from pathlib import Path

# 最新の結果ファイルを読み込み
results_dir = Path("benchmark/results/json")
json_files = list(results_dir.glob("*.json"))
latest_file = max(json_files, key=lambda p: p.stat().st_mtime)

with open(latest_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['results']
summary = data['summary']
```

### 4.2 性能分析

```python
# 実装別の平均実行時間
by_implementation = {}
for result in results:
    impl_name = result['implementation_name']
    if impl_name not in by_implementation:
        by_implementation[impl_name] = []
    by_implementation[impl_name].append(result['mean_time'])

for impl_name, times in by_implementation.items():
    avg_time = sum(times) / len(times)
    print(f"{impl_name}: {avg_time:.2f} ms")
```

### 4.3 高速化倍率の計算

```python
# Pure Pythonを基準とした高速化倍率
python_results = [r for r in results if r['implementation_name'] == 'python']
ffi_results = [r for r in results if r['implementation_name'].endswith('_ffi')]

if python_results and ffi_results:
    python_avg = sum(r['mean_time'] for r in python_results) / len(python_results)
    
    for ffi_result in ffi_results:
        speedup = python_avg / ffi_result['mean_time']
        print(f"{ffi_result['implementation_name']}: {speedup:.2f}x speedup")
```

## ステップ5: 可視化

### 5.1 グラフ生成

```python
from benchmark.runner.visualize import Visualizer

visualizer = Visualizer()

# 実行時間グラフ
exec_time_graph = visualizer.plot_execution_time(results, "tutorial_execution_time")

# メモリ使用量グラフ
memory_graph = visualizer.plot_memory_usage(results, "tutorial_memory_usage")

print(f"Graphs saved: {exec_time_graph}, {memory_graph}")
```

## ステップ6: トラブルシューティング

### 6.1 よくある問題

#### FFI実装が見つからない
```python
# 利用可能な実装の確認
available = runner.get_all_available_implementations()
print(f"Available implementations: {available}")
```

#### 共有ライブラリのエラー
```bash
# ライブラリの存在確認
ls benchmark/ffi_implementations/*/lib*

# 依存関係の確認（Linux）
ldd benchmark/ffi_implementations/c_ffi/libcfunctions.so
```

### 6.2 デバッグ手法

```python
import logging

# ログレベルの設定
logging.basicConfig(level=logging.DEBUG)

# 詳細なエラー情報の取得
try:
    runner.run_ffi_comparison_benchmark()
except Exception as e:
    import traceback
    traceback.print_exc()
```

## まとめ

このチュートリアルでは以下を学習しました：

1. uv環境のセットアップ
2. 基本的なFFIベンチマークの実行
3. カスタムシナリオの作成
4. 結果の分析と可視化
5. トラブルシューティング

## 次のステップ

- [FFI実装ガイド](FFI_IMPLEMENTATION_GUIDE.md)で詳細な実装方法を学習
- [トラブルシューティングガイド](TROUBLESHOOTING_GUIDE.md)で問題解決方法を確認
- 独自のFFI実装を作成してベンチマークに追加

## 参考資料

- [uv Documentation](https://docs.astral.sh/uv/)
- [Python ctypes Documentation](https://docs.python.org/3/library/ctypes.html)
- [FFI Best Practices](https://doc.rust-lang.org/nomicon/ffi.html)
