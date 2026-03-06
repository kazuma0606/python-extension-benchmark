# uv環境セットアップガイド

## 概要

このドキュメントは、Python Benchmark TestシステムでFFI実装を使用するために必要なuv仮想環境のセットアップ手順を説明します。

## 目次

1. [uvとは](#uvとは)
2. [インストール手順](#インストール手順)
3. [プロジェクトセットアップ](#プロジェクトセットアップ)
4. [環境確認](#環境確認)
5. [トラブルシューティング](#トラブルシューティング)
6. [ベストプラクティス](#ベストプラクティス)

## uvとは

uvは、Pythonプロジェクトの依存関係管理とパッケージングを高速化するツールです。Rustで書かれており、従来のpipやvenvよりも大幅に高速です。

### 主な特徴

- **高速**: Rustによる実装で従来ツールより10-100倍高速
- **互換性**: pip、venv、pipenvとの互換性
- **統合**: プロジェクト管理からデプロイまでの一元化
- **信頼性**: 決定論的な依存関係解決

## インストール手順

### Windows

#### PowerShellを使用（推奨）
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Scoopを使用
```powershell
scoop install uv
```

#### Chocolateyを使用
```powershell
choco install uv
```

### macOS

#### Homebrewを使用（推奨）
```bash
brew install uv
```

#### curlを使用
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Linux

#### curlを使用（推奨）
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### pipを使用
```bash
pip install uv
```

### インストール確認

```bash
uv --version
```

期待される出力例：
```
uv 0.10.4 (079e3fd05 2026-02-17)
```

## プロジェクトセットアップ

### 1. プロジェクトディレクトリに移動

```bash
cd /path/to/py_benchmark_test
```

### 2. uv環境の初期化

#### 新規プロジェクトの場合
```bash
uv init
```

#### 既存プロジェクトの場合
```bash
uv sync
```

### 3. 仮想環境のアクティベーション

#### Windows
```cmd
.venv\Scripts\activate
```

#### Unix/macOS
```bash
source .venv/bin/activate
```

### 4. 依存関係のインストール

```bash
# 基本依存関係
uv add numpy pytest hypothesis

# 開発依存関係
uv add --dev pytest-cov black flake8

# FFI開発用依存関係
uv add psutil matplotlib
```

### 5. プロジェクト設定ファイル

#### pyproject.toml（自動生成される）
```toml
[project]
name = "py-benchmark-test"
version = "0.1.0"
description = "Python Benchmark Test with FFI implementations"
dependencies = [
    "numpy>=1.21.0",
    "pytest>=7.0.0",
    "hypothesis>=6.0.0",
    "psutil>=5.8.0",
    "matplotlib>=3.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "flake8>=5.0.0",
]
```

## 環境確認

### 自動環境チェック

プロジェクトに含まれる環境チェッカーを使用：

```bash
python -c "from benchmark.ffi_implementations.uv_checker import UVEnvironmentChecker; UVEnvironmentChecker().print_environment_status()"
```

期待される出力例：
```
============================================================
UV ENVIRONMENT STATUS
============================================================
Virtual Env: /path/to/py_benchmark_test/.venv
Python Executable: /path/to/py_benchmark_test/.venv/bin/python
Python Version: 3.12.12
Platform: linux
Cwd: /path/to/py_benchmark_test
Uv Lock Found: /path/to/py_benchmark_test/uv.lock
Pyproject Toml: /path/to/py_benchmark_test/pyproject.toml

UV Version: uv 0.10.4 (079e3fd05 2026-02-17)

Required Packages:
  ctypes: ✓ Available
  numpy: ✓ Available
  pytest: ✓ Available
  hypothesis: ✓ Available

✓ Environment validation: PASSED
============================================================
```

### 手動確認

#### 1. 仮想環境の確認
```bash
which python  # Unix/macOS
where python  # Windows
```

#### 2. パッケージの確認
```bash
uv pip list
```

#### 3. プロジェクトファイルの確認
```bash
ls -la uv.lock pyproject.toml
```

## トラブルシューティング

### よくある問題と解決策

#### 1. uvが見つからない

**症状**: `uv: command not found`

**解決策**:
```bash
# パスの確認
echo $PATH

# 手動でパスを追加（Unix/macOS）
export PATH="$HOME/.cargo/bin:$PATH"

# 手動でパスを追加（Windows）
set PATH=%USERPROFILE%\.cargo\bin;%PATH%

# シェル設定ファイルに追加
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### 2. 仮想環境がアクティブにならない

**症状**: `(venv)`が表示されない

**解決策**:
```bash
# 仮想環境の存在確認
ls -la .venv/

# 手動アクティベーション
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate.bat  # Windows

# uv経由での実行
uv run python script.py
```

#### 3. 依存関係の競合

**症状**: `ResolutionImpossible` エラー

**解決策**:
```bash
# ロックファイルの削除
rm uv.lock

# 依存関係の再解決
uv sync --refresh

# 特定パッケージの更新
uv add "numpy>=1.21.0,<2.0.0"
```

#### 4. パッケージが見つからない

**症状**: `ModuleNotFoundError`

**解決策**:
```bash
# インストール状況の確認
uv pip show numpy

# 再インストール
uv add --force-reinstall numpy

# 開発モードでのインストール
uv pip install -e .
```

#### 5. 権限エラー

**症状**: `Permission denied`

**解決策**:
```bash
# ユーザーディレクトリの権限確認
ls -la ~/.cargo/

# 権限の修正（Unix/macOS）
chmod -R 755 ~/.cargo/

# 管理者権限での実行（Windows）
# PowerShellを管理者として実行
```

### FFI固有の問題

#### 1. 共有ライブラリのビルドエラー

**症状**: コンパイラが見つからない

**解決策**:
```bash
# Windows: Visual Studio Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# macOS: Xcode Command Line Tools
xcode-select --install

# Linux: 開発ツールのインストール
sudo apt-get install build-essential  # Ubuntu/Debian
sudo yum groupinstall "Development Tools"  # CentOS/RHEL
```

#### 2. 言語固有のツールチェーン

```bash
# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Go
# https://golang.org/dl/

# Julia
# https://julialang.org/downloads/

# Fortran
sudo apt-get install gfortran  # Linux
brew install gcc  # macOS
```

## ベストプラクティス

### 1. プロジェクト管理

```bash
# 定期的な依存関係更新
uv sync --upgrade

# セキュリティ監査
uv pip audit

# 依存関係ツリーの確認
uv pip tree
```

### 2. 開発ワークフロー

```bash
# 開発環境での実行
uv run python benchmark_script.py

# テストの実行
uv run pytest

# コードフォーマット
uv run black .

# リンティング
uv run flake8 .
```

### 3. CI/CD統合

#### GitHub Actions例
```yaml
name: Test with uv

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
      with:
        version: "latest"
    
    - name: Set up Python
      run: uv python install 3.12
    
    - name: Install dependencies
      run: uv sync
    
    - name: Run tests
      run: uv run pytest
```

### 4. 環境の再現性

```bash
# 環境のエクスポート
uv export --format requirements-txt > requirements.txt

# 環境の復元
uv pip install -r requirements.txt

# ロックファイルからの復元
uv sync --frozen
```

### 5. 性能最適化

```bash
# 並列インストール
uv sync --no-cache

# キャッシュクリア
uv cache clean

# インデックス設定
uv pip install --index-url https://pypi.org/simple/
```

## 高度な使用法

### 1. 複数Python環境

```bash
# Python バージョンの管理
uv python install 3.11 3.12 3.13

# 特定バージョンでの環境作成
uv venv --python 3.11

# バージョン切り替え
uv python pin 3.12
```

### 2. プロジェクトテンプレート

```bash
# テンプレートからの作成
uv init --template package my-project

# カスタムテンプレート
uv init --template https://github.com/user/template.git
```

### 3. スクリプト実行

```bash
# 一時的な依存関係でスクリプト実行
uv run --with requests script.py

# インラインスクリプト
uv run --with numpy -c "import numpy; print(numpy.__version__)"
```

## 参考資料

### 公式ドキュメント
- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [Python Packaging Guide](https://packaging.python.org/)

### コミュニティリソース
- [uv Discord](https://discord.gg/astral-sh)
- [Python Packaging Discussion](https://discuss.python.org/c/packaging/)

### 関連ツール
- [Ruff](https://docs.astral.sh/ruff/) - 高速Python linter
- [Hatch](https://hatch.pypa.io/) - プロジェクト管理
- [PDM](https://pdm.fming.dev/) - 代替パッケージマネージャー

## サポート

### 問題報告

1. **環境情報の収集**:
   ```bash
   uv --version
   python --version
   uv pip list
   ```

2. **ログの確認**:
   ```bash
   uv sync --verbose
   ```

3. **問題の再現**:
   - 最小限の再現手順
   - エラーメッセージの全文
   - 環境情報

### コミュニティサポート

- GitHub Issues: バグ報告・機能要求
- Discord: リアルタイムサポート
- Stack Overflow: `uv` タグ

---

**最終更新**: 2026年3月6日  
**バージョン**: 1.0.0  
**メンテナー**: FFI Benchmark Team