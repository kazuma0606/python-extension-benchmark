# 設計文書

## 概要

Windows環境でのFFI実装フォールバック問題を解決するための包括的な監査・検証システムを設計します。既存のFFI実装には複数のバグが存在し、Windows環境でライブラリロードやフォールバック動作に問題があることを前提とします。このシステムはRustで実装され、各FFI実装の問題を特定・修正し、正確な性能測定を可能にします。

## アーキテクチャ

システムは以下の主要コンポーネントで構成されます：

```
FFI Audit System (Rust Implementation)
├── FFI Implementation Debugger
│   ├── Library Loading Diagnostics
│   ├── Symbol Resolution Validator
│   ├── Calling Convention Checker
│   └── Memory Layout Validator
├── Bug Detection Engine
│   ├── Windows DLL Loading Issues
│   ├── Path Resolution Problems
│   ├── Dependency Chain Analyzer
│   └── Runtime Error Classifier
├── FFI Implementation Fixer
│   ├── Build Script Generator
│   ├── Library Path Corrector
│   ├── Symbol Export Validator
│   └── Compatibility Layer Generator
├── Fallback Prevention System
│   ├── Execution Path Monitor
│   ├── Performance Anomaly Detector
│   └── Native Code Verification
└── Comprehensive Audit Reporter
    ├── Bug Analysis Reporter
    ├── Fix Recommendation Generator
    └── Performance Validation Reporter
```

## コンポーネントとインターフェース

### FFI Implementation Debugger (Rust)

各FFI実装の問題を診断・特定するコンポーネント：

```rust
pub struct FFIImplementationDebugger {
    pub fn diagnose_library_loading(&self, ffi_impl: &str) -> LibraryDiagnostics;
    pub fn validate_symbol_resolution(&self, ffi_impl: &str) -> SymbolValidation;
    pub fn check_calling_convention(&self, ffi_impl: &str) -> CallingConventionResult;
    pub fn validate_memory_layout(&self, ffi_impl: &str) -> MemoryLayoutResult;
}
```

### Bug Detection Engine (Rust)

既存実装のバグを検出・分類するエンジン：

```rust
pub struct BugDetectionEngine {
    pub fn detect_dll_loading_issues(&self, ffi_impl: &str) -> Vec<DLLIssue>;
    pub fn analyze_path_resolution(&self, ffi_impl: &str) -> PathAnalysis;
    pub fn analyze_dependency_chain(&self, ffi_impl: &str) -> DependencyAnalysis;
    pub fn classify_runtime_errors(&self, errors: &[RuntimeError]) -> ErrorClassification;
}
```

### FFI Implementation Fixer (Rust)

検出された問題を修正するコンポーネント：

```rust
pub struct FFIImplementationFixer {
    pub fn generate_build_script(&self, ffi_impl: &str, issues: &[Issue]) -> BuildScript;
    pub fn correct_library_paths(&self, ffi_impl: &str) -> PathCorrection;
    pub fn validate_symbol_exports(&self, library_path: &str) -> SymbolExportValidation;
    pub fn generate_compatibility_layer(&self, ffi_impl: &str) -> CompatibilityLayer;
}
```

## データモデル

### LibraryDiagnostics (Rust)

```rust
#[derive(Debug, Clone)]
pub struct LibraryDiagnostics {
    pub implementation: String,
    pub library_exists: bool,
    pub library_loadable: bool,
    pub loading_errors: Vec<LoadingError>,
    pub missing_dependencies: Vec<String>,
    pub architecture_mismatch: bool,
    pub path_issues: Vec<PathIssue>,
}
```

### DLLIssue (Rust)

```rust
#[derive(Debug, Clone)]
pub struct DLLIssue {
    pub issue_type: DLLIssueType,
    pub error_code: Option<u32>,
    pub description: String,
    pub affected_library: String,
    pub resolution_steps: Vec<String>,
}

#[derive(Debug, Clone)]
pub enum DLLIssueType {
    LoadFailure,
    SymbolNotFound,
    ArchitectureMismatch,
    DependencyMissing,
    PathResolutionFailure,
}
```

### BuildScript (Rust)

```rust
#[derive(Debug, Clone)]
pub struct BuildScript {
    pub language: String,
    pub script_content: String,
    pub required_tools: Vec<String>,
    pub environment_variables: HashMap<String, String>,
    pub build_commands: Vec<String>,
    pub validation_commands: Vec<String>,
}
```

## 正確性プロパティ

*プロパティとは、システムのすべての有効な実行において真であるべき特性や動作のことです。プロパティは、人間が読める仕様と機械で検証可能な正確性保証の橋渡しとなります。*

### プロパティ 1: FFI実装バグ検出

*任意の*FFI実装について、ライブラリロードに失敗する場合、具体的なバグの種類と原因が特定されなければならない
**検証対象: 要件 1.1, 1.3**

### プロパティ 2: ライブラリ診断正確性

*任意の*FFI実装について、診断システムはライブラリの存在、ロード可能性、依存関係の状態を正確に報告しなければならない
**検証対象: 要件 1.2**

### プロパティ 3: バグ修正有効性

*任意の*検出されたバグについて、生成された修正手順を適用した後、そのバグは解決されなければならない
**検証対象: 要件 1.4**

### プロパティ 4: フォールバック完全検出

*任意の*ベンチマーク実行について、Python実装が使用された場合、フォールバック検出システムが100%の確率でこれを識別しなければならない
**検証対象: 要件 2.1**

### プロパティ 5: フォールバック時即座停止

*任意の*ベンチマーク実行について、フォールバックが検出された瞬間に、システムは実行を停止し詳細な診断情報を提供しなければならない
**検証対象: 要件 2.2**

### プロパティ 6: ネイティブコード実行保証

*任意の*修正されたFFI実装について、すべての関数呼び出しは実際のネイティブコードを実行し、Python実装を使用してはならない
**検証対象: 要件 2.3**

### プロパティ 7: 性能測定純粋性

*任意の*FFI実装について、測定された実行時間にはPythonインタープリターのオーバーヘッドが含まれてはならない
**検証対象: 要件 2.4**

### プロパティ 8: 汚染結果除外

*任意の*ベンチマーク結果セットについて、フォールバックまたは部分的Python実行が関与した結果は完全に除外されなければならない
**検証対象: 要件 2.5**

### プロパティ 9: 言語固有バグ特定

*任意の*サポートされている言語について、その言語固有のFFI実装バグ（コンパイル問題、リンク問題、ABI不整合）が特定されなければならない
**検証対象: 要件 3.1-3.8**

### プロパティ 10: ミニマルテスト実行

*任意の*FFI実装について、修正後のテストは最小限の依存関係で実行可能でなければならない
**検証対象: 要件 4.1**

### プロパティ 11: 機能的等価性保証

*任意の*修正されたFFI実装について、すべての操作結果は対応するPython実装と数学的に等価でなければならない
**検証対象: 要件 4.2-4.5**

### プロパティ 12: Windows問題完全診断

*任意の*Windows環境でのFFI実装について、すべてのプラットフォーム固有の問題が診断され、具体的な修正手順が提供されなければならない
**検証対象: 要件 5.1-5.5**

### プロパティ 13: 性能向上実現

*任意の*修正されたFFI実装について、pure Pythonベースラインと比較して統計的に有意な性能向上が実現されなければならない
**検証対象: 要件 6.1-6.5**

## エラーハンドリング

### 既存実装のバグ分類

- **ビルドエラー**: コンパイル失敗、リンクエラー、依存関係不足
- **ランタイムエラー**: DLLロード失敗、シンボル解決失敗、ABI不整合
- **パフォーマンスエラー**: 意図しないフォールバック、部分的Python実行

### Windows固有問題の診断

- **DLLロード問題**: 詳細なWindows エラーコード分析と解決策提示
- **パス解決問題**: 相対パス、絶対パス、環境変数の問題診断
- **アーキテクチャ不整合**: 32bit/64bit混在問題の検出と修正

### 自動修復機能

- **ビルドスクリプト生成**: 検出された問題に基づく修正済みビルドスクリプト
- **依存関係解決**: 不足している依存関係の自動インストール提案
- **互換性レイヤー**: ABI不整合の自動修正

## テスト戦略

### 単体テスト (Rust)

- 各FFI実装の個別診断テスト
- バグ検出エンジンの精度テスト
- 修正手順の有効性テスト

### プロパティベーステスト (Rust + Python)

Rustコンポーネントには`proptest`クレートを使用し、Pythonコンポーネントには`Hypothesis`ライブラリを使用します。各テストは最低100回の反復実行を行います。

**Rustテスト実装要件:**
- `proptest`を使用したプロパティベーステスト
- 各テストは対応する設計文書のプロパティを明示的に参照
- テストタグ形式: `// Feature: windows-ffi-audit, Property {number}: {property_text}`

**Pythonテスト実装要件:**
- `Hypothesis`を使用したプロパティベーステスト  
- テストタグ形式: `# Feature: windows-ffi-audit, Property {number}: {property_text}`

### 統合テスト

- 全FFI実装の同時診断・修正テスト
- 修正後のベンチマーク実行テスト
- レポート生成の包括的テスト