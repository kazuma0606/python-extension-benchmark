# Scripts Directory

このディレクトリには、プロジェクトで使用するスクリプトファイルが目的別に整理されています。

## 📁 Directory Structure

```
scripts/
├── build/               # ビルドスクリプト
│   ├── build_c_ext.py          # C拡張のビルド
│   ├── build_cpp_ext.py        # C++拡張のビルド
│   ├── build_cython.py         # Cython拡張のビルド
│   ├── build_fortran_ext.py    # Fortran拡張のビルド
│   ├── build_rust_ext.py       # Rust拡張のビルド
│   ├── build_julia_ext.py      # Julia拡張のビルド
│   ├── build_go_ext.py         # Go拡張のビルド
│   ├── build_zig_ext.py        # Zig拡張のビルド
│   ├── build_nim_ext.py        # Nim拡張のビルド
│   ├── setup_pycall.jl         # Julia PyCall設定
│   └── reinstall_pycall.jl     # Julia PyCall再インストール
├── test/                # テスト・検証スクリプト
│   ├── run_julia_property_tests.py    # Juliaプロパティテスト実行
│   ├── run_go_property_tests.py       # Goプロパティテスト実行
│   ├── test_julia_property_direct.py  # Julia直接プロパティテスト
│   ├── test_julia_structure.py        # Julia構造テスト
│   ├── test_julia_functions.jl        # Julia関数テスト
│   └── validate_julia_ext.py          # Julia拡張検証
└── demo/                # デモスクリプト
    └── demo_error_handling.py         # エラーハンドリングデモ
```

## 🚀 Usage

### ビルドスクリプト (scripts/build/)

各言語拡張をビルドするためのスクリプトです。プロジェクトルートから実行してください。

```bash
# 個別の拡張をビルド
python scripts/build/build_julia_ext.py
python scripts/build/build_go_ext.py
python scripts/build/build_zig_ext.py
python scripts/build/build_nim_ext.py

# 従来の拡張をビルド
python scripts/build/build_c_ext.py
python scripts/build/build_cpp_ext.py
python scripts/build/build_rust_ext.py
```

### テストスクリプト (scripts/test/)

各拡張の動作確認やプロパティベーステストを実行するスクリプトです。

```bash
# プロパティベーステスト実行
python scripts/test/run_julia_property_tests.py
python scripts/test/run_go_property_tests.py

# 構造・統合テスト
python scripts/test/test_julia_structure.py
python scripts/test/validate_julia_ext.py

# 直接テスト
python scripts/test/test_julia_property_direct.py
```

### デモスクリプト (scripts/demo/)

機能のデモンストレーションを行うスクリプトです。

```bash
# エラーハンドリングのデモ
python scripts/demo/demo_error_handling.py
```

## 📝 Notes

- すべてのスクリプトはプロジェクトルートから実行することを前提としています
- パス参照は新しいディレクトリ構造に合わせて調整済みです
- 古いルートディレクトリのスクリプトファイルは削除されています

## 🔧 Migration

以前のルートディレクトリにあったスクリプトファイルは以下のように移動されました：

| 旧パス | 新パス |
|--------|--------|
| `build_*.py` | `scripts/build/build_*.py` |
| `run_*_property_tests.py` | `scripts/test/run_*_property_tests.py` |
| `test_julia*.py` | `scripts/test/test_julia*.py` |
| `demo_error_handling.py` | `scripts/demo/demo_error_handling.py` |
| `*.jl` | `scripts/build/*.jl` または `scripts/test/*.jl` |
| `validate_julia_ext.py` | `scripts/test/validate_julia_ext.py` |

この変更により、プロジェクトルートディレクトリがより整理され、スクリプトファイルが目的別に分類されました。