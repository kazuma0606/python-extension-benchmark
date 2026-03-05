#!/usr/bin/env python3
"""実装ガイド生成スクリプト

各言語実装の詳細ガイド、トラブルシューティング情報、
ベストプラクティス集を生成する。
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def generate_implementation_guide(output_file: str) -> None:
    """実装ガイドを生成"""
    
    guide_lines = []
    
    # ヘッダー
    guide_lines.extend([
        "# 多言語拡張実装ガイド",
        "",
        f"**最終更新**: {datetime.now().strftime('%Y年%m月%d日')}",
        "",
        "## 概要",
        "",
        "本ガイドは、Python拡張ベンチマークシステムに新しい言語実装を追加する",
        "ための詳細な手順、トラブルシューティング情報、ベストプラクティスを提供します。",
        "",
        "## 目次",
        "",
        "1. [共通実装パターン](#共通実装パターン)",
        "2. [言語別実装ガイド](#言語別実装ガイド)",
        "3. [トラブルシューティング](#トラブルシューティング)",
        "4. [ベストプラクティス](#ベストプラクティス)",
        "5. [性能最適化指針](#性能最適化指針)",
        "",
    ])
    
    # 共通実装パターン
    guide_lines.extend(generate_common_implementation_patterns())
    
    # 言語別実装ガイド
    guide_lines.extend(generate_language_specific_guides())
    
    # トラブルシューティング
    guide_lines.extend(generate_troubleshooting_guide())
    
    # ベストプラクティス
    guide_lines.extend(generate_best_practices())
    
    # 性能最適化指針
    guide_lines.extend(generate_performance_optimization_guide())
    
    # ファイルに書き出し
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(guide_lines))


def generate_common_implementation_patterns() -> List[str]:
    """共通実装パターンを生成"""
    return [
        "## 共通実装パターン",
        "",
        "### 必須インターフェース",
        "",
        "全ての言語実装は以下の関数を提供する必要があります：",
        "",
        "```python",
        "def find_primes(n: int) -> List[int]:",
        '    """エラトステネスの篩による素数探索"""',
        "    pass",
        "",
        "def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:",
        '    """行列積計算"""',
        "    pass",
        "",
        "def sort_array(arr: List[int]) -> List[int]:",
        '    """配列ソート"""',
        "    pass",
        "",
        "def filter_array(arr: List[int], threshold: int) -> List[int]:",
        '    """閾値以上の要素をフィルタ"""',
        "    pass",
        "",
        "def parallel_compute(data: List[float], num_threads: int) -> float:",
        '    """並列計算（合計値を返す）"""',
        "    pass",
        "```",
        "",
        "### ディレクトリ構造",
        "",
        "```",
        "benchmark/",
        "├── {language}_ext/",
        "│   ├── __init__.py          # Python統合レイヤー",
        "│   ├── functions.{ext}      # 言語固有実装",
        "│   ├── setup.py            # ビルド設定（必要に応じて）",
        "│   └── README.md           # 言語固有ドキュメント",
        "└── ...",
        "```",
        "",
        "### Python統合レイヤー",
        "",
        "`__init__.py`では以下のパターンを使用：",
        "",
        "```python",
        "try:",
        "    # 言語固有モジュールをインポート",
        "    from . import native_functions",
        "    ",
        "    # 統一インターフェースを提供",
        "    find_primes = native_functions.find_primes",
        "    matrix_multiply = native_functions.matrix_multiply",
        "    sort_array = native_functions.sort_array",
        "    filter_array = native_functions.filter_array",
        "    parallel_compute = native_functions.parallel_compute",
        "    ",
        "except ImportError as e:",
        "    # フォールバック実装",
        "    def find_primes(n):",
        "        raise ImportError(f'Native implementation not available: {e}')",
        "    # ... 他の関数も同様",
        "```",
        "",
    ]


def generate_language_specific_guides() -> List[str]:
    """言語別実装ガイドを生成"""
    guides = [
        "## 言語別実装ガイド",
        "",
    ]
    
    # 各言語のガイドを生成
    languages = {
        "Julia": generate_julia_guide(),
        "Go": generate_go_guide(),
        "Zig": generate_zig_guide(),
        "Nim": generate_nim_guide(),
        "Kotlin": generate_kotlin_guide(),
        "Rust": generate_rust_guide(),
        "C": generate_c_guide(),
        "C++": generate_cpp_guide()
    }
    
    for language, guide_content in languages.items():
        guides.extend([
            f"### {language}実装",
            "",
        ])
        guides.extend(guide_content)
        guides.extend([
            "",
            "---",
            "",
        ])
    
    return guides


def generate_julia_guide() -> List[str]:
    """Julia実装ガイドを生成"""
    return [
        "#### 環境セットアップ",
        "",
        "```bash",
        "# Julia 1.9+をインストール",
        "# PyCall.jlまたはPythonCall.jlをインストール",
        "julia -e 'using Pkg; Pkg.add(\"PyCall\")'",
        "```",
        "",
        "#### 実装例",
        "",
        "```julia",
        "# functions.jl",
        "function find_primes(n::Int)::Vector{Int}",
        "    if n < 2",
        "        return Int[]",
        "    end",
        "    ",
        "    sieve = trues(n)",
        "    sieve[1] = false",
        "    ",
        "    for i in 2:isqrt(n)",
        "        if sieve[i]",
        "            for j in i*i:i:n",
        "                sieve[j] = false",
        "            end",
        "        end",
        "    end",
        "    ",
        "    return findall(sieve)",
        "end",
        "```",
        "",
        "#### Python統合",
        "",
        "```python",
        "# __init__.py",
        "import julia",
        "from julia import Main",
        "",
        "# Juliaスクリプトを読み込み",
        "Main.include('functions.jl')",
        "",
        "def find_primes(n):",
        "    return list(Main.find_primes(n))",
        "```",
        "",
        "#### 注意点",
        "",
        "- 初回実行時のJITコンパイル時間を考慮",
        "- 型注釈による性能向上",
        "- ベクトル化演算の活用",
    ]


def generate_go_guide() -> List[str]:
    """Go実装ガイドを生成"""
    return [
        "#### 環境セットアップ",
        "",
        "```bash",
        "# Go 1.21+をインストール",
        "# cgoを使用した共有ライブラリ作成",
        "```",
        "",
        "#### 実装例",
        "",
        "```go",
        "// functions.go",
        "package main",
        "",
        "import \"C\"",
        "",
        "//export find_primes",
        "func find_primes(n C.int) *C.int {",
        "    // 実装",
        "}",
        "",
        "func main() {}",
        "```",
        "",
        "#### ビルド",
        "",
        "```bash",
        "go build -buildmode=c-shared -o libgofunctions.so functions.go",
        "```",
        "",
        "#### Python統合",
        "",
        "```python",
        "import ctypes",
        "",
        "lib = ctypes.CDLL('./libgofunctions.so')",
        "lib.find_primes.argtypes = [ctypes.c_int]",
        "lib.find_primes.restype = ctypes.POINTER(ctypes.c_int)",
        "```",
        "",
        "#### 注意点",
        "",
        "- Goroutineの適切な使用",
        "- メモリ管理の注意",
        "- C ABI互換性の確保",
    ]


def generate_zig_guide() -> List[str]:
    """Zig実装ガイドを生成"""
    return [
        "#### 環境セットアップ",
        "",
        "```bash",
        "# Zig 0.11+をインストール",
        "```",
        "",
        "#### 実装例",
        "",
        "```zig",
        "// functions.zig",
        "const std = @import(\"std\");",
        "",
        "export fn find_primes(n: c_int) callconv(.C) [*c]c_int {",
        "    // 実装",
        "}",
        "```",
        "",
        "#### ビルド設定",
        "",
        "```zig",
        "// build.zig",
        "const std = @import(\"std\");",
        "",
        "pub fn build(b: *std.Build) void {",
        "    const lib = b.addSharedLibrary(.{",
        "        .name = \"zigfunctions\",",
        "        .root_source_file = .{ .path = \"functions.zig\" },",
        "        .target = target,",
        "        .optimize = optimize,",
        "    });",
        "    b.installArtifact(lib);",
        "}",
        "```",
        "",
        "#### 注意点",
        "",
        "- メモリ安全性の活用",
        "- コンパイル時最適化",
        "- C ABI互換性",
    ]


def generate_nim_guide() -> List[str]:
    """Nim実装ガイドを生成"""
    return [
        "#### 環境セットアップ",
        "",
        "```bash",
        "# Nim 2.0+をインストール",
        "nimble install nimpy",
        "```",
        "",
        "#### 実装例",
        "",
        "```nim",
        "# functions.nim",
        "import nimpy",
        "",
        "proc find_primes(n: int): seq[int] {.exportpy.} =",
        "  if n < 2:",
        "    return @[]",
        "  ",
        "  var sieve = newSeq[bool](n + 1)",
        "  for i in 0..n:",
        "    sieve[i] = true",
        "  ",
        "  sieve[0] = false",
        "  sieve[1] = false",
        "  ",
        "  for i in 2..int(sqrt(float(n))):",
        "    if sieve[i]:",
        "      var j = i * i",
        "      while j <= n:",
        "        sieve[j] = false",
        "        j += i",
        "  ",
        "  result = @[]",
        "  for i in 2..n:",
        "    if sieve[i]:",
        "      result.add(i)",
        "```",
        "",
        "#### ビルド",
        "",
        "```bash",
        "nim c --app:lib --out:libnimfunctions.so functions.nim",
        "```",
        "",
        "#### 注意点",
        "",
        "- nimpyによる自動統合",
        "- Python風構文の活用",
        "- 効率的なメモリ管理",
    ]


def generate_kotlin_guide() -> List[str]:
    """Kotlin実装ガイドを生成"""
    return [
        "#### 環境セットアップ",
        "",
        "```bash",
        "# Kotlin/Native 1.9+をインストール",
        "```",
        "",
        "#### 実装例",
        "",
        "```kotlin",
        "// functions.kt",
        "import kotlinx.cinterop.*",
        "",
        "@CName(\"find_primes\")",
        "fun findPrimes(n: Int): CPointer<IntVar>? {",
        "    // 実装",
        "}",
        "```",
        "",
        "#### ビルド設定",
        "",
        "```kotlin",
        "// build.gradle.kts",
        "plugins {",
        "    kotlin(\"multiplatform\")",
        "}",
        "",
        "kotlin {",
        "    val nativeTarget = when (System.getProperty(\"os.name\")) {",
        "        \"Linux\" -> linuxX64(\"native\")",
        "        \"Windows\" -> mingwX64(\"native\")",
        "        else -> macosX64(\"native\")",
        "    }",
        "    ",
        "    nativeTarget.apply {",
        "        binaries {",
        "            sharedLib {",
        "                baseName = \"kotlinfunctions\"",
        "            }",
        "        }",
        "    }",
        "}",
        "```",
        "",
        "#### 注意点",
        "",
        "- Kotlin/Nativeの制限事項",
        "- コルーチンの活用",
        "- JVMエコシステムとの統合",
    ]


def generate_rust_guide() -> List[str]:
    """Rust実装ガイドを生成"""
    return [
        "#### 環境セットアップ",
        "",
        "```bash",
        "# Rust 1.70+をインストール",
        "cargo install maturin  # PyO3使用時",
        "```",
        "",
        "#### 実装例（PyO3使用）",
        "",
        "```rust",
        "// lib.rs",
        "use pyo3::prelude::*;",
        "",
        "#[pyfunction]",
        "fn find_primes(n: usize) -> PyResult<Vec<usize>> {",
        "    if n < 2 {",
        "        return Ok(vec![]);",
        "    }",
        "    ",
        "    let mut sieve = vec![true; n + 1];",
        "    sieve[0] = false;",
        "    sieve[1] = false;",
        "    ",
        "    for i in 2..=((n as f64).sqrt() as usize) {",
        "        if sieve[i] {",
        "            let mut j = i * i;",
        "            while j <= n {",
        "                sieve[j] = false;",
        "                j += i;",
        "            }",
        "        }",
        "    }",
        "    ",
        "    Ok(sieve.iter()",
        "        .enumerate()",
        "        .filter_map(|(i, &is_prime)| if is_prime { Some(i) } else { None })",
        "        .collect())",
        "}",
        "",
        "#[pymodule]",
        "fn rust_ext(_py: Python, m: &PyModule) -> PyResult<()> {",
        "    m.add_function(wrap_pyfunction!(find_primes, m)?)?;",
        "    Ok(())",
        "}",
        "```",
        "",
        "#### 注意点",
        "",
        "- 所有権システムの理解",
        "- ゼロコスト抽象化の活用",
        "- 並行処理安全性",
    ]


def generate_c_guide() -> List[str]:
    """C実装ガイドを生成"""
    return [
        "#### 実装例",
        "",
        "```c",
        "// functions.c",
        "#include <Python.h>",
        "#include <stdlib.h>",
        "#include <math.h>",
        "",
        "static PyObject* find_primes(PyObject* self, PyObject* args) {",
        "    int n;",
        "    if (!PyArg_ParseTuple(args, \"i\", &n)) {",
        "        return NULL;",
        "    }",
        "    ",
        "    // 実装",
        "}",
        "",
        "static PyMethodDef module_methods[] = {",
        "    {\"find_primes\", find_primes, METH_VARARGS, \"Find primes\"},",
        "    {NULL, NULL, 0, NULL}",
        "};",
        "",
        "static struct PyModuleDef module_definition = {",
        "    PyModuleDef_HEAD_INIT,",
        "    \"c_ext\",",
        "    \"C extension module\",",
        "    -1,",
        "    module_methods",
        "};",
        "",
        "PyMODINIT_FUNC PyInit_c_ext(void) {",
        "    return PyModule_Create(&module_definition);",
        "}",
        "```",
        "",
        "#### 注意点",
        "",
        "- Python C APIの適切な使用",
        "- メモリリークの防止",
        "- エラーハンドリング",
    ]


def generate_cpp_guide() -> List[str]:
    """C++実装ガイドを生成"""
    return [
        "#### 実装例（pybind11使用）",
        "",
        "```cpp",
        "// functions.cpp",
        "#include <pybind11/pybind11.h>",
        "#include <pybind11/stl.h>",
        "#include <vector>",
        "#include <cmath>",
        "",
        "std::vector<int> find_primes(int n) {",
        "    if (n < 2) {",
        "        return {};",
        "    }",
        "    ",
        "    std::vector<bool> sieve(n + 1, true);",
        "    sieve[0] = sieve[1] = false;",
        "    ",
        "    for (int i = 2; i <= std::sqrt(n); ++i) {",
        "        if (sieve[i]) {",
        "            for (int j = i * i; j <= n; j += i) {",
        "                sieve[j] = false;",
        "            }",
        "        }",
        "    }",
        "    ",
        "    std::vector<int> primes;",
        "    for (int i = 2; i <= n; ++i) {",
        "        if (sieve[i]) {",
        "            primes.push_back(i);",
        "        }",
        "    }",
        "    ",
        "    return primes;",
        "}",
        "",
        "PYBIND11_MODULE(cpp_ext, m) {",
        "    m.def(\"find_primes\", &find_primes, \"Find primes using sieve\");",
        "}",
        "```",
        "",
        "#### 注意点",
        "",
        "- STLの効率的な使用",
        "- RAII原則の遵守",
        "- テンプレートの適切な使用",
    ]


def generate_troubleshooting_guide() -> List[str]:
    """トラブルシューティングガイドを生成"""
    return [
        "## トラブルシューティング",
        "",
        "### 共通問題",
        "",
        "#### ImportError: モジュールが見つからない",
        "",
        "**原因**: ビルドが失敗している、またはパスが正しくない",
        "",
        "**解決方法**:",
        "1. ビルドログを確認",
        "2. 依存関係をチェック",
        "3. パス設定を確認",
        "",
        "```bash",
        "# ビルド状況を確認",
        "python -c \"import benchmark.{language}_ext; print('OK')\"",
        "```",
        "",
        "#### 性能が期待より低い",
        "",
        "**原因**: 最適化フラグが無効、デバッグビルド",
        "",
        "**解決方法**:",
        "1. リリースビルドを使用",
        "2. 最適化フラグを有効化",
        "3. プロファイリングで特定",
        "",
        "#### メモリリーク",
        "",
        "**原因**: 手動メモリ管理の問題",
        "",
        "**解決方法**:",
        "1. Valgrindでチェック",
        "2. RAII/スマートポインタ使用",
        "3. ガベージコレクション言語を検討",
        "",
        "### 言語別問題",
        "",
        "#### Julia: JITコンパイル時間",
        "",
        "**解決方法**:",
        "- 事前コンパイル（PackageCompiler.jl）",
        "- ウォームアップ実行の追加",
        "",
        "#### Go: cgoオーバーヘッド",
        "",
        "**解決方法**:",
        "- バッチ処理でcgo呼び出しを削減",
        "- 純粋Goでの実装を検討",
        "",
        "#### Rust: 借用チェッカーエラー",
        "",
        "**解決方法**:",
        "- ライフタイムの明示",
        "- Cloneの適切な使用",
        "- Rcの検討",
        "",
        "#### Zig: コンパイルエラー",
        "",
        "**解決方法**:",
        "- 型の明示",
        "- メモリ管理の確認",
        "- C ABI互換性の確保",
        "",
    ]


def generate_best_practices() -> List[str]:
    """ベストプラクティスを生成"""
    return [
        "## ベストプラクティス",
        "",
        "### 性能最適化",
        "",
        "#### 1. アルゴリズムの選択",
        "",
        "- 時間計算量を最優先に考慮",
        "- キャッシュ効率を意識したデータ構造",
        "- 並列化可能なアルゴリズムの選択",
        "",
        "#### 2. メモリ管理",
        "",
        "- 事前にメモリを確保",
        "- 不要なコピーを避ける",
        "- メモリプールの活用",
        "",
        "#### 3. 並列処理",
        "",
        "- CPUコア数に応じたスレッド数",
        "- 負荷分散の考慮",
        "- 同期コストの最小化",
        "",
        "### コード品質",
        "",
        "#### 1. 可読性",
        "",
        "- 明確な変数名・関数名",
        "- 適切なコメント",
        "- 一貫したコーディングスタイル",
        "",
        "#### 2. 保守性",
        "",
        "- モジュール化",
        "- 単一責任原則",
        "- テスタビリティ",
        "",
        "#### 3. エラーハンドリング",
        "",
        "- 適切な例外処理",
        "- エラーメッセージの充実",
        "- グレースフルデグラデーション",
        "",
        "### テスト戦略",
        "",
        "#### 1. 単体テスト",
        "",
        "- 各関数の基本動作",
        "- 境界値テスト",
        "- エラーケーステスト",
        "",
        "#### 2. 統合テスト",
        "",
        "- Python統合の確認",
        "- 性能回帰テスト",
        "- メモリリークテスト",
        "",
        "#### 3. 性能テスト",
        "",
        "- ベンチマーク実行",
        "- プロファイリング",
        "- スケーラビリティテスト",
        "",
    ]


def generate_performance_optimization_guide() -> List[str]:
    """性能最適化指針を生成"""
    return [
        "## 性能最適化指針",
        "",
        "### 言語別最適化戦略",
        "",
        "#### Julia",
        "",
        "- 型安定性の確保",
        "- ベクトル化演算の活用",
        "- @inboundsマクロの使用",
        "- SIMD命令の活用",
        "",
        "#### Go",
        "",
        "- Goroutineプールの使用",
        "- チャネルバッファリング",
        "- メモリアロケーション削減",
        "- pprof による プロファイリング",
        "",
        "#### Rust",
        "",
        "- ゼロコスト抽象化の活用",
        "- イテレータチェーンの最適化",
        "- unsafe使用時の注意",
        "- LTOの有効化",
        "",
        "#### Zig",
        "",
        "- comptime計算の活用",
        "- SIMD組み込み関数",
        "- メモリレイアウト最適化",
        "- ReleaseFastビルド",
        "",
        "#### C/C++",
        "",
        "- コンパイラ最適化フラグ",
        "- インライン関数の使用",
        "- キャッシュ効率の考慮",
        "- プロファイルガイド最適化",
        "",
        "### 測定・分析ツール",
        "",
        "#### プロファイリング",
        "",
        "- **perf**: Linux系システム全般",
        "- **Instruments**: macOS",
        "- **Intel VTune**: Intel CPU特化",
        "- **言語固有ツール**: 各言語のプロファイラ",
        "",
        "#### ベンチマーク",
        "",
        "- **統計的有意性**: 十分な実行回数",
        "- **環境制御**: CPU周波数固定",
        "- **ウォームアップ**: JIT最適化考慮",
        "- **外れ値除去**: 統計的手法使用",
        "",
        "### 最適化の優先順位",
        "",
        "1. **アルゴリズム**: 最も影響が大きい",
        "2. **データ構造**: メモリ効率とアクセスパターン",
        "3. **並列化**: マルチコア活用",
        "4. **コンパイラ最適化**: フラグとヒント",
        "5. **マイクロ最適化**: 最後の手段",
        "",
        "---",
        "",
        f"*このガイドは {datetime.now().strftime('%Y年%m月%d日')} に生成されました。*",
    ]


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="実装ガイドを生成",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-o', '--output',
        default='docs/implementation_guide.md',
        help='出力ファイルパス（デフォルト: docs/implementation_guide.md）'
    )
    
    args = parser.parse_args()
    
    try:
        print("📝 実装ガイドを生成中...")
        generate_implementation_guide(args.output)
        print(f"✅ 実装ガイドが生成されました: {args.output}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()