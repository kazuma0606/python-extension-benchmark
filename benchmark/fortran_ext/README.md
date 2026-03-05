# Fortran Extension Implementation

## 概要

このディレクトリには、Fortranで実装されたベンチマーク関数が含まれています。f2py（NumPyの一部）を使用してPythonから呼び出し可能な拡張モジュールとしてビルドされます。

## 実装ファイル

### numeric.f90
- `find_primes_impl`: エラトステネスの篩による素数探索
- `matrix_multiply_impl`: 行列積計算（最適化されたループ順序）

### memory.f90
- `sort_array_impl`: クイックソートによる配列ソート
- `filter_array_impl`: 閾値による配列フィルタリング

### parallel.f90
- `parallel_compute_impl`: OpenMPを使用した並列合計計算
- `parallel_compute_explicit`: 明示的スレッド管理版

## Fortranの特徴

### 科学計算への最適化
- 数値計算に特化した言語設計
- 効率的な配列操作
- 最適化されたコンパイラ（gfortran）

### OpenMP並列化
- `!$omp parallel do reduction(+:result)` による自動並列化
- スレッド数の動的制御
- 効率的な並列リダクション

### 最適化オプション
- `-O3`: 最高レベルの最適化
- `-ffast-math`: 高速数学演算
- `-fopenmp`: OpenMP並列化サポート

## ビルド方法

```bash
# プロジェクトルートから
python build_fortran_ext.py

# または直接
cd benchmark/fortran_ext
python setup.py build_ext --inplace
```

## 期待される性能

### 数値計算
- **素数探索**: C拡張と同等以上の性能を期待
- **行列積**: 最適化されたループ順序により高性能

### メモリ操作
- **配列ソート**: クイックソートの効率的な実装
- **配列フィルタ**: シンプルなループによる高速処理

### 並列処理
- **OpenMP**: 効果的な並列化によるスケーラビリティ
- **リダクション**: 並列合計の最適化

## Fortranの利点

1. **科学計算特化**: 数値計算に最適化された言語
2. **成熟したコンパイラ**: 長年の最適化技術の蓄積
3. **並列化サポート**: OpenMPとの優れた統合
4. **メモリ効率**: 効率的なメモリレイアウト

## 技術的詳細

### f2py統合
- NumPyの配列との自動変換
- Pythonからの透明な呼び出し
- 型安全性の確保

### モジュール構造
- `module`を使用した名前空間管理
- `implicit none`による型安全性
- 現代的なFortran 90/95構文

### 最適化技術
- ループ順序の最適化（行列積）
- インライン展開の活用
- キャッシュ効率の考慮

## 注意事項

- gfortranコンパイラが必要
- OpenMP対応のため、適切なリンクオプションが必要
- 配列のインデックスはFortranの1ベース