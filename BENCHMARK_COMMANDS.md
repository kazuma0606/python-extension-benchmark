# FFI Benchmark - コマンドラインリファレンス

## 前提条件

- Python 3.12（uv 管理）
- uv 0.10.4+
- プロジェクトルート: `C:\Users\yoshi\py_benchmark_test`

すべてのコマンドはプロジェクトルートから実行する。

```bash
cd C:\Users\yoshi\py_benchmark_test
```

---

## ベンチマーク実行

### 環境確認（まずここから）

利用可能な実装・ライブラリのロード状況を確認する。

```bash
PYTHONIOENCODING=utf-8 uv run python -m benchmark.runner.ffi_benchmark_runner --mode check
```

---

### モード別実行

#### 全実装（Extension + FFI）

```bash
PYTHONIOENCODING=utf-8 uv run python -m benchmark.runner.ffi_benchmark_runner --mode all
```

> 所要時間の目安: 6時間以上（Array Sort 10M 要素がボトルネック）

#### FFI 実装のみ（ctypes ベース・11実装）

```bash
PYTHONIOENCODING=utf-8 uv run python -m benchmark.runner.ffi_benchmark_runner --mode ffi
```

> 所要時間の目安: 約3時間（Array Sort 込み）

#### Extension 実装のみ（.pyd/.so ベース・12実装）

```bash
PYTHONIOENCODING=utf-8 uv run python -m benchmark.runner.ffi_benchmark_runner --mode extensions
```

---

### シナリオを絞って実行（高速版）

Array Sort（10M 要素・1回8秒）を除いた8シナリオのみ実行する場合。

```bash
PYTHONIOENCODING=utf-8 uv run python -m benchmark.runner.ffi_benchmark_runner ^
  --mode ffi ^
  --scenarios ^
    "Numeric: Prime Search" ^
    "Numeric: Matrix Multiplication" ^
    "Memory: Array Filter" ^
    "Parallel: Multi-threaded Computation (1 threads)" ^
    "Parallel: Multi-threaded Computation (2 threads)" ^
    "Parallel: Multi-threaded Computation (4 threads)" ^
    "Parallel: Multi-threaded Computation (8 threads)" ^
    "Parallel: Multi-threaded Computation (16 threads)"
```

> bash / Git Bash の場合は `^` を `\` に置き換える。

---

### 利用可能なシナリオ一覧

| シナリオ名 | 内容 | 備考 |
|---|---|---|
| `Numeric: Prime Search` | 素数探索（100K） | 高速 |
| `Numeric: Matrix Multiplication` | 行列積（100×100） | 高速 |
| `Memory: Array Sort` | 配列ソート（10M要素） | **非常に遅い** |
| `Memory: Array Filter` | 配列フィルタリング | 高速 |
| `Parallel: Multi-threaded Computation (1 threads)` | 並列計算（1スレッド） | 高速 |
| `Parallel: Multi-threaded Computation (2 threads)` | 並列計算（2スレッド） | 高速 |
| `Parallel: Multi-threaded Computation (4 threads)` | 並列計算（4スレッド） | 高速 |
| `Parallel: Multi-threaded Computation (8 threads)` | 並列計算（8スレッド） | 高速 |
| `Parallel: Multi-threaded Computation (16 threads)` | 並列計算（16スレッド） | 高速 |

---

### 出力ファイルのプレフィックスを指定

```bash
PYTHONIOENCODING=utf-8 uv run python -m benchmark.runner.ffi_benchmark_runner ^
  --mode ffi ^
  --output-prefix my_benchmark
```

---

## 出力ファイル

実行後、以下のファイルが自動生成される。

```
benchmark/results/
├── csv/
│   ├── {prefix}_{timestamp}.csv              # 基本結果
│   └── {prefix}_{timestamp}_ffi_comparison.csv  # FFI比較（言語・タイプ列付き）
├── json/
│   ├── {prefix}_{timestamp}.json             # 基本結果
│   ├── {prefix}_{timestamp}_ffi_comparison.json
│   └── {prefix}_{timestamp}_comprehensive.json
└── benchmark_results_summary_FFI.md          # 統計レポート（Markdown）
```

---

## FFI ライブラリのビルド

各 FFI 実装の共有ライブラリを再ビルドする場合。

### Cython FFI

```bash
cd benchmark/ffi_implementations/cython_ffi
uv run python -m cython -3 --module-name=cython_functions functions.pyx -o cython_functions_gen.c

PYDIR="C:/Users/yoshi/AppData/Roaming/uv/python/cpython-3.12-windows-x86_64-none"
gcc -O2 -shared -o cython_functions.cp312-win_amd64.pyd cython_functions_gen.c \
  -I"$PYDIR/include" \
  -I"$(uv run python -c 'import numpy; print(numpy.get_include())')" \
  -L. -lpython312 -Wl,--enable-auto-import
```

### Fortran FFI

```bash
cd benchmark/ffi_implementations/fortran_ffi
gfortran -O2 -shared -fPIC -o libfortranfunctions.dll functions.f90 \
  -static-libgcc -static-libgfortran
```

### Rust FFI

```bash
cd benchmark/ffi_implementations/rust_ffi
cargo build --release
```

### C / C++ FFI

```bash
cd benchmark/ffi_implementations/c_ffi
# Makefile がある場合
make

# または直接コンパイル
gcc -O2 -shared -fPIC -o libcfunctions.dll functions.c
```

---

## テスト実行

### 正常動作確認（全 FFI 実装の疎通確認）

```bash
PYTHONIOENCODING=utf-8 uv run python -m pytest benchmark/test_ffi_correctness.py -v
```

### FFI 監査システム（Audit System）のテスト

```bash
# Python 統合テスト
cd audit
uv run python tests/test_ffi_diagnostics.py
uv run python tests/test_ffi_benchmark_validation.py

# Rust 単体テスト（Python DLL のパスが必要）
PYDIR="/c/Users/yoshi/AppData/Roaming/uv/python/cpython-3.12.12-windows-x86_64-none"
PATH="$PYDIR:$PATH" cargo test --lib -- --test-threads=1
```

### Rust プロパティテスト

```bash
cd audit
PYDIR="/c/Users/yoshi/AppData/Roaming/uv/python/cpython-3.12.12-windows-x86_64-none"
PATH="$PYDIR:$PATH" cargo test --lib 2>&1 | tail -20
```

---

## FFI 実装一覧

### FFI 実装（ctypes ベース）

| 実装名 | 言語 | 共有ライブラリ |
|---|---|---|
| `c_ffi` | C | `libcfunctions.dll` |
| `cpp_ffi` | C++ | `libcppfunctions.dll` |
| `numpy_ffi` | NumPy（Python） | `.pyd`（NumPy フォールバック） |
| `cython_ffi` | Cython | `cython_functions.cp312-win_amd64.pyd` |
| `rust_ffi` | Rust | `librust_functions.dll` |
| `fortran_ffi` | Fortran | `libfortranfunctions.dll` |
| `julia_ffi` | Julia | `juliafunctions.dll`（PackageCompiler） |
| `go_ffi` | Go | `libgofunctions.dll` |
| `zig_ffi` | Zig | `libzigfunctions.dll` |
| `nim_ffi` | Nim | `libnimfunctions.dll` |
| `kotlin_ffi` | Kotlin | `libkotlinfunctions.dll` |

### Extension 実装（Python 拡張モジュール）

| 実装名 | 言語 | モジュール |
|---|---|---|
| `python` | Pure Python | ネイティブ |
| `numpy_impl` | NumPy | ネイティブ |
| `c_ext` | C | `.pyd` |
| `cpp_ext` | C++（pybind11） | `.pyd` |
| `cython_ext` | Cython | `.pyd` |
| `rust_ext` | Rust（PyO3） | `.pyd` |
| `fortran_ext` | Fortran | `.pyd` |
| `julia_ext` | Julia | `.pyd` |
| `go_ext` | Go | `.pyd` |
| `zig_ext` | Zig | `.pyd` |
| `nim_ext` | Nim | `.pyd` |
| `kotlin_ext` | Kotlin | `.pyd` |

---

## 既知の制限・注意事項

| 項目 | 内容 |
|---|---|
| Array Sort の遅さ | Python list ↔ ctypes 変換のオーバーヘッドで 1 回あたり 7〜10 秒かかる |
| NumPy FFI | DLL は `PyInit_*` のみエクスポート → 全演算が NumPy（Python）フォールバック |
| Cython FFI | `filter_array` が .pyd 未実装 → NumPy フォールバック |
| Julia FFI | Docker 環境では動作しない（Windows ネイティブのみ） |
| フォールバック防止 | Audit System は検出・報告のみ。フォールバック自体の防止は実装側の課題 |
| DLL ロード（Fortran） | `libwinpthread-1.dll` 等を fortran_ffi ディレクトリにコピーする必要あり |
| DLL ロード（Julia） | `lib_build/bin` を `os.environ['PATH']` の先頭に追加する必要あり |

---

## 過去の実行結果

| ファイル | 環境 | 実装 | シナリオ | 備考 |
|---|---|---|---|---|
| `benchmark_results_20260305_045149.csv` | Docker/Linux | 6 extension | 9/9 | 全 SUCCESS |
| `docker_ffi_benchmark_working_20260306_205657.csv` | Docker/Linux | 11 FFI | 9/9 | julia_ffi のみ全 ERROR |
| `benchmark_results_summary_FFI.md` | Windows-native | 8 FFI | 4/9 | 部分的な結果 |
