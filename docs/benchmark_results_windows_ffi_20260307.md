# FFI ベンチマーク結果レポート（Windows ネイティブ）

- **実行日時**: 2026-03-07 13:48 〜 15:49
- **環境**: Windows 11 Pro / Python 3.12.12 / Intel64 (GenuineIntel)
- **モード**: `--mode ffi`（FFI 実装のみ）
- **データファイル**: `benchmark/results/csv/ffi_benchmark_20260307_154922_ffi_comparison.csv`

---

## 実行サマリー

| 項目 | 値 |
|---|---|
| 対象実装数 | 11 |
| 実行シナリオ数 | 6（※1スレッド・16スレッドは未実行） |
| 総ベンチマーク実行数 | 66 |
| 成功 | 30（5実装 × 6シナリオ） |
| 失敗（DLL 未検出） | 36（6実装 × 6シナリオ） |

### 未実行シナリオについて

`Parallel: Multi-threaded Computation (1 threads)` および `(16 threads)` は、
bash の括弧解釈の問題でコマンドが正常に渡らず未実行となった。

---

## 実装別ステータス

| 実装 | 言語 | ステータス | 原因 |
|---|---|---|---|
| numpy_ffi | NumPy | **SUCCESS** | NumPy Python フォールバック |
| cython_ffi | Cython | **SUCCESS** | 一部 NumPy フォールバック |
| rust_ffi | Rust | **SUCCESS** | `librustfunctions.dll` ロード成功 |
| julia_ffi | Julia | **SUCCESS** | `juliafunctions.dll` ロード成功 |
| kotlin_ffi | Kotlin | **SUCCESS** | `libfunctions.dll` ロード成功 |
| c_ffi | C | FAILED | `libfunctions.dll` 未検出 |
| cpp_ffi | C++ | FAILED | `libfunctions.dll` 未検出 |
| fortran_ffi | Fortran | FAILED | `libfortranfunctions.dll` 未検出 |
| go_ffi | Go | FAILED | `libfunctions.dll` 未検出 |
| zig_ffi | Zig | FAILED | `libfunctions.dll` 未検出 |
| nim_ffi | Nim | FAILED | `libfunctions.dll` 未検出 |

---

## シナリオ別計測結果（成功実装のみ）

### Numeric: Prime Search（素数探索 100K）

| 実装 | 平均実行時間 (ms) | 備考 |
|---|---|---|
| **numpy_ffi** | **3.06** | NumPy fallback |
| kotlin_ffi | 3.89 | ネイティブ実行 |
| julia_ffi | 3.95 | ネイティブ実行 |
| rust_ffi | 3.96 | ネイティブ実行 |
| cython_ffi | 42.36 | Cython 実装（素数探索は遅い） |

> Rust/Julia/Kotlin はほぼ同等。numpy_ffi が最速だが NumPy Python 実装による結果。

---

### Numeric: Matrix Multiplication（行列積 100×100）

| 実装 | 平均実行時間 (ms) | 備考 |
|---|---|---|
| **cython_ffi** | **2.24** | NumPy fallback |
| numpy_ffi | 2.54 | NumPy fallback |
| rust_ffi | 14.45 | ネイティブ実行 + ctypes オーバーヘッド |
| julia_ffi | 14.61 | ネイティブ実行 + ctypes オーバーヘッド |
| kotlin_ffi | 17.98 | ネイティブ実行 + ctypes オーバーヘッド |

> numpy/cython が最速だが実態は NumPy。Rust/Julia/Kotlin は ctypes でのデータ変換コストが支配的。

---

### Memory: Array Filter（配列フィルタ 10M要素）

| 実装 | 平均実行時間 (ms) | 備考 |
|---|---|---|
| **cython_ffi** | **1,319.9** | NumPy fallback |
| numpy_ffi | 1,325.9 | NumPy fallback |
| kotlin_ffi | 6,951.4 | ctypes 変換コスト大 |
| rust_ffi | 6,925.4 | ctypes 変換コスト大 |
| julia_ffi | 7,057.5 | ctypes 変換コスト大 |

> 大規模配列の ctypes 変換コストが顕著。numpy/cython（NumPy fallback）と比べて Rust/Julia/Kotlin は約 5.3x 遅い。
> これは FFI 経由でのデータ受け渡しコストの限界を示す典型例。

---

### Parallel: Multi-threaded Computation

#### 2スレッド

| 実装 | 実行時間 (ms) |
|---|---|
| **cython_ffi** | **63.0** |
| numpy_ffi | 212.4 |
| rust_ffi | 4,347.2 |
| julia_ffi | 4,545.5 |
| kotlin_ffi | 4,626.0 |

#### 4スレッド

| 実装 | 実行時間 (ms) |
|---|---|
| **cython_ffi** | **62.4** |
| numpy_ffi | 212.4 |
| rust_ffi | 4,568.1 |
| julia_ffi | 4,524.5 |
| kotlin_ffi | 4,660.6 |

#### 8スレッド

| 実装 | 実行時間 (ms) |
|---|---|
| **cython_ffi** | **66.4** |
| numpy_ffi | 213.1 |
| rust_ffi | 4,560.5 |
| julia_ffi | 4,555.7 |
| kotlin_ffi | 4,646.4 |

---

### スレッド数によるスケーリング分析

| 実装 | 2スレッド (ms) | 4スレッド (ms) | 8スレッド (ms) | スケール効果 |
|---|---|---|---|---|
| numpy_ffi | 212.4 | 212.4 | 213.1 | なし（GIL 制約） |
| cython_ffi | 63.0 | 62.4 | 66.4 | ほぼなし |
| rust_ffi | 4,347.2 | 4,568.1 | 4,560.5 | なし |
| julia_ffi | 4,545.5 | 4,524.5 | 4,555.7 | なし |
| kotlin_ffi | 4,626.0 | 4,660.6 | 4,646.4 | なし |

> **全実装でスレッドスケーリングの恩恵がない。**
> FFI 経由の並列処理では Python 側のオーバーヘッドとデータ転送がボトルネックとなり、
> スレッドを増やしても性能が向上しない。

---

## 主要な知見

### 1. ctypes のデータ変換コストが支配的

大規模データ（10M 要素の配列）では、ctypes による Python ↔ ネイティブ変換コストが
計算コストを大幅に上回る。Rust/Julia/Kotlin が NumPy より 5x 以上遅いのはこのため。

### 2. numpy_ffi / cython_ffi の「速さ」は実態と異なる

これらが速いシナリオの多くは NumPy Python フォールバックによる結果であり、
ネイティブコードとして動作しているわけではない。Audit System がこれを正しく検出している。

### 3. FFI 経由での並列処理は効果がない

スレッド数を 2→4→8 に増やしても性能はほぼ変わらない。
FFI 呼び出し自体がシリアルなボトルネックになっているため、並列処理の恩恵を受けられない。
並列処理が目的であれば、マイクロサービスアーキテクチャが適切。

### 4. 6実装が DLL 未検出でゼロ結果

C, C++, Fortran, Go, Zig, Nim は DLL ファイルが存在しないため全 ERROR。
これらは以前の実行時に構築されていたが、現在の環境では再ビルドが必要。
（Docker/Linux 環境では C/C++/Go/Zig/Nim は正常動作していた）

---

## 成功実装の総合ランキング

計測できたシナリオでの平均的なパフォーマンス評価：

| 順位 | 実装 | 素数探索 | 行列積 | 配列フィルタ | 並列（代表：2スレッド） |
|---|---|---|---|---|---|
| 1 | **cython_ffi** | 42.4ms | **2.2ms** | **1,320ms** | **63ms** |
| 2 | **numpy_ffi** | **3.1ms** | 2.5ms | 1,326ms | 212ms |
| 3 | **rust_ffi** | 4.0ms | 14.5ms | 6,925ms | 4,347ms |
| 4 | **julia_ffi** | 4.0ms | 14.6ms | 7,057ms | 4,546ms |
| 5 | **kotlin_ffi** | 3.9ms | 18.0ms | 6,951ms | 4,626ms |

---

## 環境別結果の比較

| 環境 | 成功実装数 | シナリオ数 | 備考 |
|---|---|---|---|
| Docker/Linux（2026-03-06） | 10/11 | 9/9 | julia_ffi のみ ERROR |
| **Windows ネイティブ（今回）** | **5/11** | **6/9** | DLL 未ビルドの実装が多い |

---

## DLL 未検出実装の再ビルド手順

```bash
# C / C++ FFI（要: MinGW または MSVC）
cd benchmark/ffi_implementations/c_ffi
gcc -O2 -shared -fPIC -o libfunctions.dll functions.c

cd benchmark/ffi_implementations/cpp_ffi
g++ -O2 -shared -fPIC -o libfunctions.dll functions.cpp

# Fortran FFI
cd benchmark/ffi_implementations/fortran_ffi
gfortran -O2 -shared -fPIC -o libfortranfunctions.dll functions.f90 \
  -static-libgcc -static-libgfortran

# Go FFI（要: CGO 有効化）
cd benchmark/ffi_implementations/go_ffi
go build -buildmode=c-shared -o libfunctions.dll .

# Zig FFI
cd benchmark/ffi_implementations/zig_ffi
zig build-lib -dynamic -O ReleaseFast functions.zig

# Nim FFI
cd benchmark/ffi_implementations/nim_ffi
nim c --app:lib --out:libfunctions.dll functions.nim
```
