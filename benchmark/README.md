# Python Extension Benchmark Framework

ベンチマークフレームワークは、Python拡張ライブラリの多言語実装のパフォーマンスを定量的に比較します。

## プロジェクト構造

```
benchmark/
├── python/              # Pure Python実装
├── numpy_impl/          # NumPy実装
├── c_ext/               # C言語拡張実装
├── cpp_ext/             # C++（pybind11）実装
├── cython_ext/          # Cython実装
├── rust_ext/            # Rust（PyO3）実装
├── runner/              # 統合ベンチマークランナー
├── results/             # 計測結果出力
│   ├── json/
│   ├── csv/
│   └── graphs/
├── interface.py         # 共通インターフェース定義
└── conftest.py          # Pytest/Hypothesis設定
```

## セットアップ

```bash
# 依存関係のインストール
pip install -r requirements.txt

# テストの実行
pytest
```

## 共通インターフェース

全ての実装モジュールは以下の関数を提供する必要があります：

- `find_primes(n: int) -> List[int]`: n以下の素数を全て返す
- `matrix_multiply(a, b) -> List[List[float]]`: 行列積を計算
- `sort_array(arr: List[int]) -> List[int]`: 配列をソート
- `filter_array(arr: List[int], threshold: int) -> List[int]`: 閾値以上の要素をフィルタ
- `parallel_compute(data: List[float], num_threads: int) -> float`: マルチスレッドで分散計算

詳細は `interface.py` を参照してください。
