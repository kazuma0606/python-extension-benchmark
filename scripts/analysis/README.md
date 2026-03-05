# 性能分析スクリプト

このディレクトリには、Python拡張ベンチマークシステムの包括的性能分析を実行するためのスクリプトが含まれています。

## 概要

12の言語実装（Python、NumPy、C、C++、Cython、Rust、Fortran、Julia、Go、Zig、Nim、Kotlin）の性能を分析し、以下のレポートを生成します：

- 言語別特性分析
- 総合評価レポート
- 実装ガイド
- ベンチマーク結果サマリー

## スクリプト一覧

### 1. `run_comprehensive_analysis.py` (推奨)

全ての分析を一括実行するマスタースクリプトです。

```bash
# 最新のベンチマーク結果を自動検出して全分析を実行
python scripts/analysis/run_comprehensive_analysis.py

# 特定のベンチマーク結果ファイルを指定
python scripts/analysis/run_comprehensive_analysis.py -f benchmark/results/json/benchmark_results_20260305_045149.json

# 性能分析をスキップして既存の分析結果からレポートのみ生成
python scripts/analysis/run_comprehensive_analysis.py --skip-analysis
```

### 2. `run_performance_analysis.py`

ベンチマーク結果から統計的分析を実行します。

```bash
# 最新の結果ファイルを自動検出
python scripts/analysis/run_performance_analysis.py

# 特定のファイルを指定
python scripts/analysis/run_performance_analysis.py -f benchmark/results/json/benchmark_results_20260305_045149.json

# 出力ディレクトリを指定
python scripts/analysis/run_performance_analysis.py -o /path/to/output
```

**出力**: `benchmark/results/analysis/performance_analysis_YYYYMMDD_HHMMSS.json`

### 3. `generate_language_characteristics.py`

言語別の特性分析レポートを生成します。

```bash
# 最新の分析結果を使用
python scripts/analysis/generate_language_characteristics.py

# 特定の分析結果ファイルを指定
python scripts/analysis/generate_language_characteristics.py -f benchmark/results/analysis/performance_analysis_20260305_045149.json

# 出力ファイルを指定
python scripts/analysis/generate_language_characteristics.py -o docs/custom_characteristics.md
```

**出力**: `docs/language_characteristics_analysis.md`

### 4. `generate_comprehensive_evaluation.py`

総合評価レポートを生成します。

```bash
# 最新の分析結果を使用
python scripts/analysis/generate_comprehensive_evaluation.py

# カスタム出力ファイル
python scripts/analysis/generate_comprehensive_evaluation.py -o docs/evaluation_2026.md
```

**出力**: `docs/comprehensive_evaluation_report.md`

### 5. `generate_implementation_guide.py`

実装ガイドを生成します。

```bash
# 実装ガイドを生成
python scripts/analysis/generate_implementation_guide.py

# カスタム出力ファイル
python scripts/analysis/generate_implementation_guide.py -o docs/custom_guide.md
```

**出力**: `docs/implementation_guide.md`

### 6. `update_benchmark_summary.py`

ベンチマーク結果サマリーを更新します。

```bash
# 最新の分析結果でサマリーを更新
python scripts/analysis/update_benchmark_summary.py

# カスタム出力ファイル
python scripts/analysis/update_benchmark_summary.py -o docs/summary_2026.md
```

**出力**: `docs/benchmark_results_summary.md`

## 使用方法

### 基本的な使用手順

1. **ベンチマーク実行**: まず、ベンチマークを実行して結果ファイルを生成
   ```bash
   python -m benchmark.runner.benchmark
   ```

2. **包括的分析実行**: 全ての分析を一括実行
   ```bash
   python scripts/analysis/run_comprehensive_analysis.py
   ```

3. **レポート確認**: `docs/` ディレクトリ内の生成されたレポートを確認

### 個別分析の実行

特定の分析のみを実行したい場合は、対応するスクリプトを個別に実行してください。

## 出力ファイル

### 分析結果ファイル
- `benchmark/results/analysis/performance_analysis_*.json`: 詳細な分析結果（JSON形式）

### レポートファイル
- `docs/language_characteristics_analysis.md`: 言語別特性分析
- `docs/comprehensive_evaluation_report.md`: 総合評価レポート
- `docs/implementation_guide.md`: 実装ガイド
- `docs/benchmark_results_summary.md`: ベンチマーク結果サマリー

## 分析内容

### 性能分析
- 統計的有意性検定（Welchのt検定）
- 効果量計算（Cohen's d）
- 信頼区間計算
- 性能分類（高性能/中性能/低性能）

### 言語特性分析
- カテゴリ別性能評価（数値計算/メモリ操作/並列処理）
- 得意分野・弱点の特定
- 制限事項の文書化
- 推奨用途の決定

### 技術選択指針
- 用途別推奨マトリックス
- 開発効率vs性能トレードオフ分析
- プロジェクト規模別指針
- 技術的制約による選択指針

## 依存関係

以下のPythonパッケージが必要です：

```bash
pip install scipy numpy
```

## トラブルシューティング

### よくある問題

1. **分析結果ファイルが見つからない**
   - 先にベンチマークを実行してください
   - `benchmark/results/json/` ディレクトリを確認してください

2. **スクリプト実行エラー**
   - Python環境とパスを確認してください
   - 依存関係がインストールされているか確認してください

3. **レポート生成失敗**
   - 分析結果ファイルが正しい形式か確認してください
   - 出力ディレクトリの書き込み権限を確認してください

### ログの確認

各スクリプトは実行時に詳細なログを出力します。エラーが発生した場合は、ログメッセージを確認してください。

## カスタマイズ

### 新しい分析の追加

1. 新しい分析スクリプトを作成
2. `run_comprehensive_analysis.py` の `analysis_scripts` リストに追加
3. 必要に応じて引数処理を追加

### レポート形式の変更

各レポート生成スクリプト内の `generate_*` 関数を修正することで、出力形式をカスタマイズできます。

## 更新履歴

- 2026-03-06: 初版作成
- 包括的性能分析システムの実装完了