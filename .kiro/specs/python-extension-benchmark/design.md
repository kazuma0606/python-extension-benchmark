# 設計書

## 概要

本システムは、Python拡張ライブラリの多言語実装（Pure Python、NumPy、C、C++、Cython、Rust、Fortran）のパフォーマンスを定量的に比較するベンチマークフレームワークである。モノレポ構成で各言語実装を管理し、統合ベンチマークランナーから一括実行・計測・可視化を行う。

### 主要機能

- 3つのベンチマークシナリオ（数値計算、メモリ操作、並列処理）の実行
- NumPyのベクトル化演算を活用した実装の性能計測
- 統計的に有意な計測（ウォームアップ + 100回実行）
- 実行時間・メモリ使用量・スループットの計測
- JSON/CSV形式での結果出力
- グラフによる可視化
- Docker環境での再現性確保
- 各実装の出力値の妥当性検証

## アーキテクチャ

### システム構成

```
┌─────────────────────────────────────────────────────────┐
│                  ベンチマークランナー                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ シナリオ実行  │  │  統計計算    │  │  結果出力    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Pure Python  │    │   C/C++      │    │ Cython/Rust  │
│ 実装モジュール│    │ 実装モジュール│    │ 実装モジュール│
└──────────────┘    └──────────────┘    └──────────────┘
```

### レイヤー構成

1. **ベンチマークランナー層**: シナリオ実行、計測、統計処理、結果出力を担当
2. **実装モジュール層**: 各言語で実装された拡張ライブラリ（共通インターフェース）
3. **インフラ層**: Docker環境、ビルドスクリプト、CI/CD

### モノレポディレクトリ構造

```
benchmark/
├── python/              # Pure Python実装
│   ├── __init__.py
│   ├── numeric.py       # 数値計算
│   ├── memory.py        # メモリ操作
│   └── parallel.py      # 並列処理
├── numpy_impl/          # NumPy実装
│   ├── __init__.py
│   ├── numeric.py       # ベクトル化演算を使用
│   ├── memory.py        # NumPy配列操作
│   └── parallel.py      # NumPyの並列処理
├── c_ext/               # C言語拡張実装
│   ├── setup.py
│   ├── numeric.c
│   ├── memory.c
│   └── parallel.c
├── cpp_ext/             # C++（pybind11）実装
│   ├── CMakeLists.txt
│   ├── numeric.cpp
│   ├── memory.cpp
│   └── parallel.cpp
├── cython_ext/          # Cython実装
│   ├── setup.py
│   ├── numeric.pyx
│   ├── memory.pyx
│   └── parallel.pyx
├── rust_ext/            # Rust（PyO3）実装
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs
│   │   ├── numeric.rs
│   │   ├── memory.rs
│   │   └── parallel.rs
├── runner/              # 統合ベンチマークランナー
│   ├── __init__.py
│   ├── benchmark.py     # メインランナー
│   ├── scenarios.py     # シナリオ定義
│   ├── statistics.py    # 統計計算
│   ├── output.py        # 結果出力
│   ├── visualize.py     # グラフ生成
│   └── validator.py     # 出力値検証
├── results/             # 計測結果出力
│   ├── json/
│   ├── csv/
│   └── graphs/
├── docker/              # Docker環境
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/               # テスト
│   ├── test_implementations.py
│   └── test_runner.py
└── README.md
```

## コンポーネントとインターフェース

### 1. ベンチマークランナー（runner/benchmark.py）

ベンチマーク実行の中核コンポーネント。

```python
class BenchmarkRunner:
    def run_scenario(
        self,
        scenario: Scenario,
        implementations: List[Implementation],
        warmup_runs: int = 10,
        measurement_runs: int = 100
    ) -> BenchmarkResult:
        """シナリオを実行し、計測結果を返す"""
        pass
    
    def run_all_scenarios(
        self,
        implementations: List[Implementation]
    ) -> List[BenchmarkResult]:
        """全シナリオを実行"""
        pass
```

### 2. シナリオ定義（runner/scenarios.py）

各ベンチマークシナリオの定義。

```python
class Scenario:
    name: str
    description: str
    input_data: Any
    
    def execute(self, implementation: Implementation) -> Tuple[Any, float, float]:
        """実装を実行し、(出力, 実行時間, メモリ使用量)を返す"""
        pass

class NumericScenario(Scenario):
    """数値計算シナリオ（素数探索、行列積）"""
    pass

class MemoryScenario(Scenario):
    """メモリ操作シナリオ（配列ソート、フィルタ）"""
    pass

class ParallelScenario(Scenario):
    """並列処理シナリオ（マルチスレッド分散計算）"""
    pass
```

### 3. 実装モジュールインターフェース

全ての言語実装が準拠する共通インターフェース。

```python
# 各実装モジュールが提供すべき関数

def find_primes(n: int) -> List[int]:
    """n以下の素数を全て返す（エラトステネスの篩）"""
    pass

def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """行列積を計算"""
    pass

def sort_array(arr: List[int]) -> List[int]:
    """配列をソート"""
    pass

def filter_array(arr: List[int], threshold: int) -> List[int]:
    """閾値以上の要素をフィルタ"""
    pass

def parallel_compute(data: List[float], num_threads: int) -> float:
    """マルチスレッドで分散計算（合計値を返す）"""
    pass
```

### 4. 統計計算（runner/statistics.py）

計測データから統計値を計算。

```python
class Statistics:
    @staticmethod
    def calculate(measurements: List[float]) -> StatResult:
        """最小値、中央値、平均値、標準偏差を計算"""
        pass
    
    @staticmethod
    def calculate_relative_score(
        target_time: float,
        baseline_time: float
    ) -> float:
        """ベースライン（Pure Python）に対する相対スコアを計算"""
        pass
```

### 5. 結果出力（runner/output.py）

計測結果をJSON/CSV形式で出力。

```python
class OutputWriter:
    def write_json(self, results: List[BenchmarkResult], path: str) -> None:
        """JSON形式で出力"""
        pass
    
    def write_csv(self, results: List[BenchmarkResult], path: str) -> None:
        """CSV形式で出力"""
        pass
```

### 6. グラフ生成（runner/visualize.py）

計測結果を可視化。

```python
class Visualizer:
    def plot_execution_time(
        self,
        results: List[BenchmarkResult],
        output_path: str
    ) -> None:
        """実行時間の比較グラフを生成"""
        pass
    
    def plot_memory_usage(
        self,
        results: List[BenchmarkResult],
        output_path: str
    ) -> None:
        """メモリ使用量の比較グラフを生成"""
        pass
    
    def plot_scalability(
        self,
        results: List[BenchmarkResult],
        output_path: str
    ) -> None:
        """並列処理のスケーラビリティグラフを生成"""
        pass
```

### 7. 出力値検証（runner/validator.py）

各実装の出力値が一致することを検証。

```python
class OutputValidator:
    @staticmethod
    def validate(
        outputs: Dict[str, Any],
        tolerance: float = 1e-4
    ) -> ValidationResult:
        """全実装の出力値を比較し、相対誤差が許容範囲内か検証"""
        pass
```

## データモデル

### BenchmarkResult

```python
@dataclass
class BenchmarkResult:
    scenario_name: str
    implementation_name: str
    execution_times: List[float]  # 100回の計測結果
    memory_usage: List[float]     # 100回のメモリ使用量
    min_time: float
    median_time: float
    mean_time: float
    std_dev: float
    relative_score: float         # Pure Pythonを1.0とした相対スコア
    throughput: float             # ops/sec
    output_value: Any             # 実装の出力値
    timestamp: datetime
    environment: EnvironmentInfo
```

### EnvironmentInfo

```python
@dataclass
class EnvironmentInfo:
    os: str
    cpu: str
    memory_gb: float
    python_version: str
    docker: bool
```

### StatResult

```python
@dataclass
class StatResult:
    min: float
    median: float
    mean: float
    std_dev: float
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    is_valid: bool
    max_relative_error: float
    mismatches: List[str]  # 不一致があった実装名のリスト
```

### Scenario

```python
@dataclass
class Scenario:
    name: str
    description: str
    input_data: Any
    expected_output_type: type
```

### Implementation

```python
@dataclass
class Implementation:
    name: str              # "python", "numpy", "c_ext", "cpp_ext", etc.
    module: ModuleType     # インポートされたPythonモジュール
    language: str          # "Python", "NumPy", "C", "C++", "Cython", "Rust"
```

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において真であるべき特性や振る舞いのことです。本質的には、システムが何をすべきかについての形式的な記述です。プロパティは、人間が読める仕様と機械で検証可能な正確性保証の橋渡しとなります。*

### プロパティ1: シナリオ実行の完全性

*任意の*シナリオと実装モジュールのリストに対して、シナリオを実行すると、全ての実装モジュールが呼び出され、結果が記録されなければならない

**検証: 要件 1.1, 1.2, 2.1, 2.2, 3.1**

### プロパティ2: 実行時間の記録

*任意の*実装モジュールとシナリオに対して、実行が完了すると、実行時間がミリ秒単位で記録され、結果に含まれなければならない

**検証: 要件 1.3**

### プロパティ3: 相対スコアの計算正確性

*任意の*実行時間のセットに対して、Pure Python実装の実行時間をベースラインとした相対スコアは、各実装の実行時間をPure Pythonの実行時間で割った値と等しくなければならない

**検証: 要件 1.4**

### プロパティ4: メモリ使用量の記録

*任意の*実装モジュールとシナリオに対して、実行が完了すると、ピークメモリ使用量と平均メモリ使用量がメガバイト単位で記録され、結果に含まれなければならない

**検証: 要件 2.3, 2.4**

### プロパティ5: 並列処理のスレッド数バリエーション

*任意の*並列処理シナリオに対して、実行時間とスループットが各スレッド数（1、2、4、8、16）で記録されなければならない

**検証: 要件 3.2, 3.3**

### プロパティ6: スケーラビリティ計算

*任意の*並列処理結果に対して、スケーラビリティは各スレッド数でのスループットをシングルスレッドのスループットで割った値として計算されなければならない

**検証: 要件 3.4**

### プロパティ7: 統計計算の正確性

*任意の*計測データのリストに対して、計算された最小値、中央値、平均値、標準偏差は、標準的な統計関数の結果と一致しなければならない

**検証: 要件 4.3**

### プロパティ8: ウォームアップデータの除外

*任意の*ベンチマーク実行に対して、統計計算に使用されるデータはウォームアップ実行の結果を含まず、本計測の結果のみを含まなければならない

**検証: 要件 4.4**

### プロパティ9: JSON出力のラウンドトリップ

*任意の*ベンチマーク結果に対して、JSON形式で出力し、再度読み込んだデータは元のデータと等価でなければならない

**検証: 要件 5.1**

### プロパティ10: CSV出力のラウンドトリップ

*任意の*ベンチマーク結果に対して、CSV形式で出力し、再度読み込んだデータは元のデータと等価でなければならない（数値精度の許容範囲内）

**検証: 要件 5.2**

### プロパティ11: 出力フィールドの完全性

*任意の*ベンチマーク結果の出力に対して、実行時間、メモリ使用量、スループット、相対スコア、実行日時、環境情報（OS、CPU、メモリ）が含まれなければならない

**検証: 要件 5.3, 5.4**

### プロパティ12: グラフファイルの生成

*任意の*ベンチマーク結果に対して、実行時間、メモリ使用量、スケーラビリティのグラフがPNG形式で生成され、指定されたパスに保存されなければならない

**検証: 要件 6.1, 6.2, 6.3, 6.4**

### プロパティ13: 関数シグネチャの統一性

*任意の*実装モジュールに対して、提供される関数（find_primes、matrix_multiply、sort_array、filter_array、parallel_compute）のシグネチャは、定義されたインターフェースと一致しなければならない

**検証: 要件 8.1**

### プロパティ14: エラー時の継続実行

*任意の*実装モジュールのリストに対して、1つの実装がエラーを発生させても、他の実装モジュールの実行は継続され、エラー情報が記録されなければならない

**検証: 要件 8.3**

### プロパティ15: 出力値の比較実行

*任意の*実装モジュールのリストと入力データに対して、全ての実装モジュールの出力値が比較され、検証結果が生成されなければならない

**検証: 要件 9.1**

### プロパティ16: 相対誤差の検証正確性

*任意の*2つの数値に対して、相対誤差の計算は |a - b| / max(|a|, |b|) として正しく計算され、0.0001未満かどうかの判定が正確でなければならない

**検証: 要件 9.2**

### プロパティ17: 不一致時の警告出力

*任意の*検証結果に対して、出力値が一致しない実装が存在する場合、警告メッセージが出力され、不一致の詳細が記録されなければならない

**検証: 要件 9.3**

### プロパティ18: 検証結果の包含

*任意の*ベンチマーク結果に対して、出力値の検証結果（is_valid、max_relative_error、mismatches）が含まれなければならない

**検証: 要件 9.4**

### プロパティ19: 結果出力先の正確性

*任意の*ベンチマーク実行に対して、計測結果は指定された専用ディレクトリ（results/json、results/csv、results/graphs）に出力されなければならない

**検証: 要件 10.3**

## エラーハンドリング

### エラーの種類と対応

1. **実装モジュールのインポートエラー**
   - 対応: エラーをログに記録し、該当実装をスキップして他の実装を継続
   - ユーザーへの通知: 警告メッセージを表示

2. **実装モジュールの実行時エラー**
   - 対応: エラー情報を記録し、該当実装の結果に"ERROR"ステータスを設定
   - ユーザーへの通知: エラーメッセージとスタックトレースを表示

3. **メモリ不足エラー**
   - 対応: 実行を中断し、エラーを記録
   - ユーザーへの通知: メモリ不足の警告と推奨される対処法を表示

4. **出力ファイルの書き込みエラー**
   - 対応: 代替パスへの書き込みを試行、失敗した場合は標準出力に結果を表示
   - ユーザーへの通知: ファイル書き込みエラーを表示

5. **出力値の不一致**
   - 対応: 警告として記録し、実行は継続
   - ユーザーへの通知: 不一致の詳細（どの実装間で、どの程度の誤差か）を表示

### エラーログ形式

```python
@dataclass
class ErrorLog:
    timestamp: datetime
    implementation_name: str
    scenario_name: str
    error_type: str
    error_message: str
    stack_trace: Optional[str]
```

## テスト戦略

### ユニットテスト

各コンポーネントの個別機能をテストする。

1. **統計計算のテスト**
   - 既知の入力に対する統計値の正確性
   - エッジケース（空リスト、単一要素、全て同じ値）

2. **相対スコア計算のテスト**
   - 既知の実行時間に対する相対スコアの正確性
   - ゼロ除算の処理

3. **出力値検証のテスト**
   - 一致する出力値のケース
   - 不一致する出力値のケース
   - 相対誤差の境界値

4. **ファイル出力のテスト**
   - JSON/CSV形式の正確性
   - ファイルの存在確認

### プロパティベーステスト

普遍的なプロパティを多数の入力で検証する。

**使用ライブラリ**: Hypothesis（Python）

**設定**: 各プロパティテストは最低100回の反復実行を行う

**プロパティテストの実装**:

1. **プロパティ3のテスト: 相対スコアの計算正確性**
   ```python
   @given(st.lists(st.floats(min_value=0.001, max_value=1000.0), min_size=2))
   def test_relative_score_calculation(execution_times):
       """Feature: python-extension-benchmark, Property 3: 相対スコアの計算正確性"""
       baseline = execution_times[0]
       for time in execution_times:
           expected = time / baseline
           actual = calculate_relative_score(time, baseline)
           assert abs(expected - actual) < 1e-10
   ```

2. **プロパティ7のテスト: 統計計算の正確性**
   ```python
   @given(st.lists(st.floats(min_value=0.0, max_value=1000.0), min_size=10))
   def test_statistics_calculation(measurements):
       """Feature: python-extension-benchmark, Property 7: 統計計算の正確性"""
       result = Statistics.calculate(measurements)
       assert result.min == min(measurements)
       assert result.mean == statistics.mean(measurements)
       assert abs(result.std_dev - statistics.stdev(measurements)) < 1e-10
   ```

3. **プロパティ9のテスト: JSON出力のラウンドトリップ**
   ```python
   @given(benchmark_result_strategy())
   def test_json_round_trip(result):
       """Feature: python-extension-benchmark, Property 9: JSON出力のラウンドトリップ"""
       json_str = json.dumps(result.to_dict())
       restored = BenchmarkResult.from_dict(json.loads(json_str))
       assert result == restored
   ```

4. **プロパティ14のテスト: エラー時の継続実行**
   ```python
   @given(st.lists(st.booleans(), min_size=3, max_size=10))
   def test_error_continuation(error_flags):
       """Feature: python-extension-benchmark, Property 14: エラー時の継続実行"""
       implementations = create_test_implementations(error_flags)
       results = runner.run_scenario(scenario, implementations)
       # エラーが発生した実装以外は全て実行されるべき
       assert len(results) == len(implementations)
       assert sum(1 for r in results if r.status == "ERROR") == sum(error_flags)
   ```

5. **プロパティ16のテスト: 相対誤差の検証正確性**
   ```python
   @given(st.floats(min_value=-1000.0, max_value=1000.0),
          st.floats(min_value=-1000.0, max_value=1000.0))
   def test_relative_error_calculation(a, b):
       """Feature: python-extension-benchmark, Property 16: 相対誤差の検証正確性"""
       if a == 0 and b == 0:
           return  # スキップ
       expected = abs(a - b) / max(abs(a), abs(b))
       actual = calculate_relative_error(a, b)
       assert abs(expected - actual) < 1e-10
   ```

### 統合テスト

システム全体の動作をテストする。

1. **エンドツーエンドベンチマーク実行**
   - Pure Python実装のみで全シナリオを実行
   - 結果ファイルの生成確認
   - グラフファイルの生成確認

2. **複数実装の比較**
   - Pure PythonとCython実装で同一シナリオを実行
   - 出力値の一致確認
   - 相対スコアの妥当性確認

### テスト実行環境

- ローカル環境: pytest + Hypothesis
- CI環境: GitHub Actions（Python 3.9, 3.10, 3.11）
- Docker環境: 本番環境と同一の設定でテスト実行

### カバレッジ目標

- ユニットテスト: 80%以上
- プロパティベーステスト: 全ての正確性プロパティをカバー
- 統合テスト: 主要なユースケースをカバー
