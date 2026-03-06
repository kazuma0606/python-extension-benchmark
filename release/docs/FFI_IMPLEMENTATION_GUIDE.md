# FFI実装ガイド

## 概要

このドキュメントは、Python Benchmark Testシステムにおける11のFFI（Foreign Function Interface）実装の詳細ガイドです。各言語の実装方法、ビルド手順、トラブルシューティング情報を提供します。

## 目次

1. [FFI実装アーキテクチャ](#ffi実装アーキテクチャ)
2. [共通要件](#共通要件)
3. [言語別実装ガイド](#言語別実装ガイド)
4. [ビルドとデプロイ](#ビルドとデプロイ)
5. [トラブルシューティング](#トラブルシューティング)
6. [性能最適化](#性能最適化)

## FFI実装アーキテクチャ

### 統一C ABI仕様

全てのFFI実装は以下のC ABI互換関数シグネチャに準拠します：

```c
// 素数探索
int* find_primes_ffi(int n, int* count);

// 行列積
double* matrix_multiply_ffi(double* a, int rows_a, int cols_a, 
                           double* b, int rows_b, int cols_b,
                           int* result_rows, int* result_cols);

// 配列ソート
int* sort_array_ffi(int* arr, int size);

// 配列フィルタ
int* filter_array_ffi(int* arr, int size, int threshold, int* result_size);

// 並列計算
double parallel_compute_ffi(double* data, int size, int num_threads);

// メモリ解放
void free_memory_ffi(void* ptr);
```

### Python統合レイヤー

各FFI実装は統一されたPython統合レイヤーを提供します：

```python
from benchmark.ffi_implementations.ffi_base import FFIBase

class LanguageFFI(FFIBase):
    def __init__(self):
        super().__init__("path/to/shared/library")
    
    def find_primes(self, n: int) -> List[int]:
        # FFI呼び出しの実装
        pass
```

## 共通要件

### 開発環境

- **uv仮想環境**: 必須（依存関係管理）
- **Python 3.8+**: サポート対象
- **ctypes**: FFI統合用（標準ライブラリ）
- **NumPy**: 数値計算用

### ディレクトリ構造

```
benchmark/ffi_implementations/
├── {language}_ffi/
│   ├── __init__.py          # Python統合レイヤー
│   ├── functions.{ext}      # 言語実装
│   ├── build.{script}       # ビルドスクリプト
│   ├── README.md           # 言語固有ガイド
│   └── lib{name}.{dll|so|dylib}  # 共有ライブラリ
```

## 言語別実装ガイド

### 1. C FFI実装

**技術スタック**: gcc, C標準ライブラリ

**ビルド手順**:
```bash
cd benchmark/ffi_implementations/c_ffi
make clean && make
```

**特徴**:
- 最小オーバーヘッド
- 直接的なメモリ管理
- 期待性能: 10-50倍高速化

**実装例**:
```c
#include <stdlib.h>
#include <stdbool.h>

int* find_primes_ffi(int n, int* count) {
    if (n < 2) {
        *count = 0;
        return NULL;
    }
    
    int* primes = malloc(n * sizeof(int));
    int prime_count = 0;
    
    for (int num = 2; num <= n; num++) {
        bool is_prime = true;
        for (int i = 2; i * i <= num; i++) {
            if (num % i == 0) {
                is_prime = false;
                break;
            }
        }
        if (is_prime) {
            primes[prime_count++] = num;
        }
    }
    
    *count = prime_count;
    return primes;
}
```

### 2. C++ FFI実装

**技術スタック**: g++, STL

**ビルド手順**:
```bash
cd benchmark/ffi_implementations/cpp_ffi
make clean && make
```

**特徴**:
- C++機能活用（STL、アルゴリズム）
- C ABI互換（extern "C"）
- 期待性能: 10-50倍高速化

**実装例**:
```cpp
#include <vector>
#include <algorithm>

extern "C" {
    int* find_primes_ffi(int n, int* count) {
        std::vector<int> primes;
        
        for (int num = 2; num <= n; num++) {
            bool is_prime = true;
            for (int i = 2; i * i <= num; i++) {
                if (num % i == 0) {
                    is_prime = false;
                    break;
                }
            }
            if (is_prime) {
                primes.push_back(num);
            }
        }
        
        *count = primes.size();
        int* result = (int*)malloc(primes.size() * sizeof(int));
        std::copy(primes.begin(), primes.end(), result);
        return result;
    }
}
```

### 3. Rust FFI実装

**技術スタック**: Cargo, cdylib

**ビルド手順**:
```bash
cd benchmark/ffi_implementations/rust_ffi
cargo build --release
```

**特徴**:
- メモリ安全性
- ゼロコスト抽象化
- 期待性能: 10-40倍高速化

**Cargo.toml**:
```toml
[lib]
crate-type = ["cdylib"]

[dependencies]
libc = "0.2"
```

**実装例**:
```rust
use std::os::raw::c_int;
use libc::{malloc, free};

#[no_mangle]
pub extern "C" fn find_primes_ffi(n: c_int, count: *mut c_int) -> *mut c_int {
    if n < 2 {
        unsafe { *count = 0; }
        return std::ptr::null_mut();
    }
    
    let mut primes = Vec::new();
    
    for num in 2..=n {
        let mut is_prime = true;
        for i in 2..=(num as f64).sqrt() as i32 {
            if num % i == 0 {
                is_prime = false;
                break;
            }
        }
        if is_prime {
            primes.push(num);
        }
    }
    
    unsafe {
        *count = primes.len() as c_int;
        let result = malloc(primes.len() * std::mem::size_of::<c_int>()) as *mut c_int;
        for (i, &prime) in primes.iter().enumerate() {
            *result.add(i) = prime;
        }
        result
    }
}
```

### 4. Fortran FFI実装

**技術スタック**: gfortran, iso_c_binding

**ビルド手順**:
```bash
cd benchmark/ffi_implementations/fortran_ffi
make clean && make
```

**特徴**:
- 科学計算特化
- iso_c_binding使用
- 期待性能: 10-50倍高速化（科学計算）

**実装例**:
```fortran
module prime_functions
    use iso_c_binding
    implicit none
    
contains
    
    function find_primes_ffi(n, count) bind(C, name="find_primes_ffi")
        integer(c_int), intent(in), value :: n
        integer(c_int), intent(out) :: count
        type(c_ptr) :: find_primes_ffi
        
        integer, allocatable :: primes(:)
        integer :: num, i, prime_count
        logical :: is_prime
        
        if (n < 2) then
            count = 0
            find_primes_ffi = c_null_ptr
            return
        end if
        
        allocate(primes(n))
        prime_count = 0
        
        do num = 2, n
            is_prime = .true.
            do i = 2, int(sqrt(real(num)))
                if (mod(num, i) == 0) then
                    is_prime = .false.
                    exit
                end if
            end do
            
            if (is_prime) then
                prime_count = prime_count + 1
                primes(prime_count) = num
            end if
        end do
        
        count = prime_count
        ! C互換ポインタを返す実装
        find_primes_ffi = c_loc(primes(1))
    end function
    
end module
```

### 5. Julia FFI実装

**技術スタック**: PackageCompiler.jl

**ビルド手順**:
```bash
cd benchmark/ffi_implementations/julia_ffi
julia simple_build.jl
```

**特徴**:
- JIT最適化
- 高レベル言語の利便性
- 期待性能: 5-30倍高速化

**実装例**:
```julia
function find_primes_ffi(n::Cint, count::Ptr{Cint})::Ptr{Cint}
    if n < 2
        unsafe_store!(count, 0)
        return Ptr{Cint}(0)
    end
    
    primes = Int32[]
    
    for num in 2:n
        is_prime = true
        for i in 2:isqrt(num)
            if num % i == 0
                is_prime = false
                break
            end
        end
        if is_prime
            push!(primes, num)
        end
    end
    
    unsafe_store!(count, length(primes))
    
    # C互換配列を作成
    result = Libc.malloc(length(primes) * sizeof(Cint))
    result_ptr = convert(Ptr{Cint}, result)
    
    for (i, prime) in enumerate(primes)
        unsafe_store!(result_ptr, prime, i)
    end
    
    return result_ptr
end

# C互換エクスポート
Base.@ccallable function find_primes_ffi(n::Cint, count::Ptr{Cint})::Ptr{Cint}
    return find_primes_ffi(n, count)
end
```

### 6. Go FFI実装

**技術スタック**: cgo

**ビルド手順**:
```bash
cd benchmark/ffi_implementations/go_ffi
make clean && make
```

**特徴**:
- Goroutine並行処理
- ガベージコレクション
- 期待性能: 3-15倍高速化

**実装例**:
```go
package main

import "C"
import (
    "math"
    "unsafe"
)

//export find_primes_ffi
func find_primes_ffi(n C.int, count *C.int) *C.int {
    if n < 2 {
        *count = 0
        return nil
    }
    
    var primes []C.int
    
    for num := C.int(2); num <= n; num++ {
        isPrime := true
        limit := C.int(math.Sqrt(float64(num)))
        
        for i := C.int(2); i <= limit; i++ {
            if num%i == 0 {
                isPrime = false
                break
            }
        }
        
        if isPrime {
            primes = append(primes, num)
        }
    }
    
    *count = C.int(len(primes))
    
    if len(primes) == 0 {
        return nil
    }
    
    // C互換配列を作成
    result := (*C.int)(C.malloc(C.size_t(len(primes)) * C.size_t(unsafe.Sizeof(C.int(0)))))
    
    for i, prime := range primes {
        *(*C.int)(unsafe.Pointer(uintptr(unsafe.Pointer(result)) + uintptr(i)*unsafe.Sizeof(C.int(0)))) = prime
    }
    
    return result
}

func main() {} // cgoに必要
```

### 7. その他の言語実装

**Zig FFI**: メモリ安全性 + C ABI互換、期待性能: 10-40倍高速化
**Nim FFI**: Python風構文、期待性能: 5-25倍高速化  
**Kotlin FFI**: Kotlin/Native、期待性能: 2-10倍高速化
**NumPy FFI**: ベクトル化演算、期待性能: 5-20倍高速化
**Cython FFI**: Python + C最適化、期待性能: 5-30倍高速化

## ビルドとデプロイ

### 自動ビルドスクリプト

全FFI実装を一括ビルド：
```bash
python scripts/build/build_all_ffi.py
```

### Docker環境

FFI開発環境をDockerで構築：
```bash
docker-compose -f docker-compose.ffi.yml up --build
```

### クロスプラットフォーム対応

| プラットフォーム | 共有ライブラリ形式 | 注意事項 |
|------------------|-------------------|----------|
| Windows | .dll | Visual Studio Build Tools推奨 |
| Linux | .so | gcc/g++標準 |
| macOS | .dylib | Xcode Command Line Tools |

## トラブルシューティング

### 共通問題

#### 1. 共有ライブラリが見つからない

**症状**: `OSError: [WinError 126] 指定されたモジュールが見つかりません`

**解決策**:
```bash
# ライブラリパスの確認
ls benchmark/ffi_implementations/*/lib*

# 依存関係の確認（Linux）
ldd benchmark/ffi_implementations/c_ffi/libcfunctions.so

# 依存関係の確認（Windows）
dumpbin /dependents benchmark/ffi_implementations/c_ffi/cfunctions.dll
```

#### 2. 関数シンボルが見つからない

**症状**: `AttributeError: function 'find_primes_ffi' not found`

**解決策**:
```bash
# シンボルの確認（Linux）
nm -D benchmark/ffi_implementations/c_ffi/libcfunctions.so | grep find_primes

# シンボルの確認（Windows）
dumpbin /exports benchmark/ffi_implementations/c_ffi/cfunctions.dll
```

#### 3. メモリリーク

**症状**: メモリ使用量が継続的に増加

**解決策**:
- `free_memory_ffi`関数の適切な呼び出し
- Pythonガベージコレクションとの連携
- メモリプロファイリングツールの使用

### 言語固有の問題

#### C/C++
- **コンパイラバージョン不一致**: 同一コンパイラでビルド
- **リンカエラー**: `-fPIC`フラグの使用

#### Rust
- **ターゲット不一致**: `cargo build --target`で明示的指定
- **依存関係競合**: `Cargo.lock`の確認

#### Fortran
- **モジュール互換性**: gfortranバージョン統一
- **配列境界**: `iso_c_binding`の適切な使用

#### Julia
- **PackageCompiler.jl**: 最新版の使用
- **システムイメージ**: 適切なプリコンパイル

#### Go
- **cgo無効**: `CGO_ENABLED=1`の設定
- **クロスコンパイル**: `GOOS`、`GOARCH`の設定

## 性能最適化

### コンパイラ最適化

```bash
# C/C++
gcc -O3 -march=native -ffast-math

# Rust
cargo build --release

# Fortran
gfortran -O3 -march=native -ffast-math

# Go
go build -ldflags="-s -w"
```

### プロファイリング

```bash
# 性能プロファイリング
python -m cProfile -o profile.stats benchmark_script.py

# メモリプロファイリング
python -m memory_profiler benchmark_script.py
```

### ベンチマーク最適化

1. **データサイズ調整**: 小さすぎるとオーバーヘッドが支配的
2. **ウォームアップ**: JIT最適化のための事前実行
3. **測定回数**: 統計的有意性のための十分な回数
4. **システム負荷**: 他プロセスの影響を最小化

## 参考資料

- [Python ctypes Documentation](https://docs.python.org/3/library/ctypes.html)
- [C ABI Specification](https://en.wikipedia.org/wiki/Application_binary_interface)
- [FFI Best Practices](https://doc.rust-lang.org/nomicon/ffi.html)
- [uv Documentation](https://docs.astral.sh/uv/)

## 貢献ガイドライン

新しいFFI実装を追加する場合：

1. 統一C ABI仕様に準拠
2. Python統合レイヤーの実装
3. ビルドスクリプトの作成
4. README.mdの作成
5. テストケースの追加
6. 性能ベンチマークの実行

---

**最終更新**: 2026年3月6日  
**バージョン**: 1.0.0  
**メンテナー**: FFI Benchmark Team