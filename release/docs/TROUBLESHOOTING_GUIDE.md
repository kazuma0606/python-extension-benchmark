# トラブルシューティングガイド

## 概要

このドキュメントは、Python Benchmark TestシステムのFFI実装で発生する可能性のある問題と解決策を包括的に説明します。

## 目次

1. [一般的な問題](#一般的な問題)
2. [uv環境関連の問題](#uv環境関連の問題)
3. [FFI実装固有の問題](#ffi実装固有の問題)
4. [言語別トラブルシューティング](#言語別トラブルシューティング)
5. [性能問題](#性能問題)
6. [デバッグ手法](#デバッグ手法)
7. [よくある質問](#よくある質問)

## 一般的な問題

### 1. インポートエラー

#### 症状
```
ModuleNotFoundError: No module named 'benchmark'
```

#### 原因
- Pythonパスの設定不備
- 仮想環境の非アクティブ化
- パッケージの未インストール

#### 解決策
```bash
# 1. 仮想環境の確認
which python
echo $VIRTUAL_ENV

# 2. 仮想環境のアクティベーション
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

# 3. パッケージの確認
pip list | grep benchmark

# 4. 開発モードでのインストール
pip install -e .

# 5. Pythonパスの手動追加
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 2. 権限エラー

#### 症状
```
PermissionError: [Errno 13] Permission denied
```

#### 原因
- ファイル/ディレクトリの権限不足
- 管理者権限が必要な操作

#### 解決策
```bash
# Unix/macOS
chmod +x script.sh
sudo chown -R $USER:$USER directory/

# Windows（管理者PowerShell）
icacls "C:\path\to\file" /grant Users:F
```

### 3. メモリエラー

#### 症状
```
MemoryError: Unable to allocate array
```

#### 原因
- 大量のデータ処理
- メモリリーク
- システムリソース不足

#### 解決策
```python
# メモリ使用量の監視
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# ガベージコレクションの強制実行
import gc
gc.collect()

# データサイズの削減
# 大きなデータセットを小さなチャンクに分割
```

## uv環境関連の問題

### 1. uvコマンドが見つからない

#### 症状
```
uv: command not found
```

#### 診断
```bash
# パスの確認
echo $PATH
which uv

# インストール状況の確認
ls ~/.cargo/bin/uv
```

#### 解決策
```bash
# 1. 再インストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. パスの手動追加
export PATH="$HOME/.cargo/bin:$PATH"
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc

# 3. シェルの再起動
source ~/.bashrc

# Windows
set PATH=%USERPROFILE%\.cargo\bin;%PATH%
```

### 2. 仮想環境の作成失敗

#### 症状
```
Error: Failed to create virtual environment
```

#### 診断
```bash
# ディスク容量の確認
df -h .

# 権限の確認
ls -la .venv/

# Pythonバージョンの確認
python --version
```

#### 解決策
```bash
# 1. 既存環境の削除
rm -rf .venv/

# 2. 新しい環境の作成
uv venv

# 3. 特定Pythonバージョンでの作成
uv venv --python 3.12

# 4. 権限問題の解決
sudo chown -R $USER:$USER .venv/
```

### 3. 依存関係の競合

#### 症状
```
ResolutionImpossible: Could not find a version that satisfies the requirement
```

#### 診断
```bash
# 依存関係ツリーの確認
uv pip tree

# 競合の詳細確認
uv sync --verbose
```

#### 解決策
```bash
# 1. ロックファイルの削除
rm uv.lock

# 2. 依存関係の再解決
uv sync --refresh

# 3. バージョン制約の緩和
uv add "numpy>=1.20.0,<2.0.0"

# 4. 競合パッケージの除外
uv remove conflicting-package
```

## FFI実装固有の問題

### 1. 共有ライブラリのロードエラー

#### 症状
```
OSError: [WinError 126] 指定されたモジュールが見つかりません
```

#### 診断
```bash
# ライブラリファイルの存在確認
ls benchmark/ffi_implementations/*/lib*
ls benchmark/ffi_implementations/*/*.dll
ls benchmark/ffi_implementations/*/*.so

# 依存関係の確認（Linux）
ldd benchmark/ffi_implementations/c_ffi/libcfunctions.so

# 依存関係の確認（Windows）
dumpbin /dependents benchmark/ffi_implementations/c_ffi/cfunctions.dll
```

#### 解決策
```bash
# 1. ライブラリの再ビルド
cd benchmark/ffi_implementations/c_ffi
make clean && make

# 2. 環境変数の設定（Linux）
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:$(pwd)/benchmark/ffi_implementations/c_ffi"

# 3. 環境変数の設定（Windows）
set PATH=%PATH%;%CD%\benchmark\ffi_implementations\c_ffi

# 4. 依存ライブラリのインストール
# Windows: Visual C++ Redistributable
# Linux: sudo apt-get install libc6-dev
```

### 2. 関数シンボルが見つからない

#### 症状
```
AttributeError: function 'find_primes_ffi' not found
```

#### 診断
```bash
# シンボルの確認（Linux）
nm -D benchmark/ffi_implementations/c_ffi/libcfunctions.so | grep find_primes

# シンボルの確認（Windows）
dumpbin /exports benchmark/ffi_implementations/c_ffi/cfunctions.dll

# objdumpを使用（Linux）
objdump -T benchmark/ffi_implementations/c_ffi/libcfunctions.so
```

#### 解決策
```c
// C/C++: extern "C"の追加
extern "C" {
    int* find_primes_ffi(int n, int* count);
}

// または__declspec(dllexport)の使用（Windows）
__declspec(dllexport) int* find_primes_ffi(int n, int* count);
```

```python
# Python: 関数名の確認
import ctypes
lib = ctypes.CDLL('./libcfunctions.so')
print(dir(lib))  # 利用可能な関数一覧
```

### 3. メモリリーク

#### 症状
- メモリ使用量の継続的増加
- システムの動作が重くなる

#### 診断
```python
import psutil
import gc

def monitor_memory():
    process = psutil.Process()
    print(f"RSS: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {process.memory_info().vms / 1024 / 1024:.2f} MB")
    print(f"Objects: {len(gc.get_objects())}")

# 使用前後でメモリを監視
monitor_memory()
# FFI関数の実行
monitor_memory()
```

#### 解決策
```python
# 1. 適切なメモリ解放
from benchmark.ffi_implementations.ffi_base import FFIBase

class MyFFI(FFIBase):
    def __del__(self):
        # リソースのクリーンアップ
        if hasattr(self, '_allocated_pointers'):
            for ptr in self._allocated_pointers:
                self.lib.free_memory_ffi(ptr)

# 2. コンテキストマネージャーの使用
class FFIContext:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 自動クリーンアップ
        self.cleanup()
```

### 4. データ型の不一致

#### 症状
```
ArgumentError: argument 1: <class 'TypeError'>: wrong type
```

#### 診断
```python
import ctypes

# 期待される型の確認
lib.find_primes_ffi.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
lib.find_primes_ffi.restype = ctypes.POINTER(ctypes.c_int)

# 実際の引数の型確認
print(type(n))  # 引数の型
print(isinstance(n, int))  # 型チェック
```

#### 解決策
```python
# 適切な型変換
n = ctypes.c_int(n)
count = ctypes.c_int()

# 配列の適切な変換
arr = (ctypes.c_int * len(python_list))(*python_list)
```

## 言語別トラブルシューティング

### C/C++ FFI

#### コンパイルエラー
```bash
# 症状: undefined reference to function
# 解決策: リンカーフラグの追加
gcc -shared -fPIC -o libcfunctions.so functions.c -lm

# 症状: 'stdio.h' file not found
# 解決策: 開発ヘッダーのインストール
sudo apt-get install libc6-dev  # Linux
```

#### 実行時エラー
```bash
# 症状: Segmentation fault
# 解決策: デバッガーの使用
gdb python
(gdb) run script.py
(gdb) bt  # バックトレース

# Valgrindでメモリエラーチェック
valgrind --tool=memcheck python script.py
```

### Rust FFI

#### ビルドエラー
```bash
# 症状: linker 'cc' not found
# 解決策: Cコンパイラのインストール
sudo apt-get install build-essential

# 症状: could not find Cargo.toml
# 解決策: 正しいディレクトリでの実行
cd benchmark/ffi_implementations/rust_ffi
cargo build --release
```

#### 実行時エラー
```rust
// 症状: null pointer dereference
// 解決策: null チェックの追加
#[no_mangle]
pub extern "C" fn find_primes_ffi(n: c_int, count: *mut c_int) -> *mut c_int {
    if count.is_null() {
        return std::ptr::null_mut();
    }
    // 実装...
}
```

### Fortran FFI

#### コンパイルエラー
```bash
# 症状: gfortran: command not found
# 解決策: Fortranコンパイラのインストール
sudo apt-get install gfortran

# 症状: module file version mismatch
# 解決策: 同一バージョンでの再コンパイル
gfortran --version
make clean && make
```

### Julia FFI

#### PackageCompiler.jlエラー
```julia
# 症状: PackageCompiler not found
# 解決策: パッケージのインストール
using Pkg
Pkg.add("PackageCompiler")

# 症状: system image creation failed
# 解決策: メモリ増加とタイムアウト延長
julia --project -e 'using PackageCompiler; create_sysimage(..., cpu_target="generic")'
```

### Go FFI

#### cgoエラー
```bash
# 症状: cgo: C compiler not found
# 解決策: Cコンパイラのインストール
# Windows: Visual Studio Build Tools
# Linux: sudo apt-get install gcc

# 症状: CGO_ENABLED=0
# 解決策: cgoの有効化
export CGO_ENABLED=1
go build -buildmode=c-shared -o libgofunctions.so functions.go
```

## 性能問題

### 1. 期待より遅い実行時間

#### 診断
```python
import time
import cProfile

# プロファイリング
cProfile.run('your_function()', 'profile.stats')

# 時間測定
start = time.perf_counter()
result = your_function()
end = time.perf_counter()
print(f"Execution time: {(end - start) * 1000:.2f} ms")
```

#### 解決策
```bash
# 1. コンパイラ最適化
gcc -O3 -march=native -ffast-math

# 2. リリースビルド
cargo build --release

# 3. データサイズの確認
# 小さすぎるデータではオーバーヘッドが支配的

# 4. ウォームアップの実行
# JIT最適化のための事前実行
```

### 2. メモリ使用量が多い

#### 診断
```python
import tracemalloc

tracemalloc.start()
# コードの実行
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
tracemalloc.stop()
```

#### 解決策
```python
# 1. 不要なデータの削除
del large_data
gc.collect()

# 2. ジェネレーターの使用
def process_data():
    for item in large_dataset:
        yield process_item(item)

# 3. チャンク処理
def process_in_chunks(data, chunk_size=1000):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        yield process_chunk(chunk)
```

## デバッグ手法

### 1. ログ出力の活用

```python
import logging

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# FFI呼び出しのログ
def debug_ffi_call(func_name, *args):
    logger.debug(f"Calling {func_name} with args: {args}")
    try:
        result = getattr(lib, func_name)(*args)
        logger.debug(f"{func_name} returned: {result}")
        return result
    except Exception as e:
        logger.error(f"{func_name} failed: {e}")
        raise
```

### 2. アサーションの使用

```python
def validate_ffi_result(result, expected_type, min_size=0):
    assert result is not None, "FFI function returned None"
    assert isinstance(result, expected_type), f"Expected {expected_type}, got {type(result)}"
    if hasattr(result, '__len__'):
        assert len(result) >= min_size, f"Result size {len(result)} < minimum {min_size}"
```

### 3. 段階的テスト

```python
def test_ffi_implementation():
    # 1. ライブラリのロード
    try:
        lib = ctypes.CDLL('./libcfunctions.so')
        print("✓ Library loaded successfully")
    except Exception as e:
        print(f"✗ Library load failed: {e}")
        return
    
    # 2. 関数の存在確認
    try:
        func = lib.find_primes_ffi
        print("✓ Function found")
    except AttributeError as e:
        print(f"✗ Function not found: {e}")
        return
    
    # 3. 簡単な呼び出し
    try:
        count = ctypes.c_int()
        result = func(10, ctypes.byref(count))
        print(f"✓ Function call successful, count: {count.value}")
    except Exception as e:
        print(f"✗ Function call failed: {e}")
```

## よくある質問

### Q1: FFI実装が見つからない
**A**: uv環境がアクティブか確認し、共有ライブラリがビルドされているか確認してください。

### Q2: 性能が期待より低い
**A**: データサイズ、コンパイラ最適化、測定方法を確認してください。

### Q3: メモリリークが発生する
**A**: `free_memory_ffi`関数の適切な呼び出しと、Pythonオブジェクトの適切な削除を確認してください。

### Q4: クロスプラットフォームで動作しない
**A**: 各プラットフォーム用の共有ライブラリ（.dll/.so/.dylib）が必要です。

### Q5: ビルドエラーが発生する
**A**: 必要な開発ツール（コンパイラ、ヘッダーファイル）がインストールされているか確認してください。

## サポートリソース

### ドキュメント
- [FFI実装ガイド](FFI_IMPLEMENTATION_GUIDE.md)
- [uv環境セットアップガイド](UV_ENVIRONMENT_SETUP_GUIDE.md)

### コミュニティ
- GitHub Issues: バグ報告・機能要求
- Stack Overflow: 技術的質問

### 開発ツール
- **デバッガー**: gdb, lldb, Visual Studio Debugger
- **プロファイラー**: cProfile, py-spy, perf
- **メモリ分析**: Valgrind, AddressSanitizer

---

**最終更新**: 2026年3月6日  
**バージョン**: 1.0.0  
**メンテナー**: FFI Benchmark Team