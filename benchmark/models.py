"""データモデル定義

ベンチマーク結果、環境情報、統計結果、検証結果などのデータクラスを定義する。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Dict
from types import ModuleType


@dataclass
class EnvironmentInfo:
    """実行環境情報"""
    os: str
    cpu: str
    memory_gb: float
    python_version: str
    docker: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'os': self.os,
            'cpu': self.cpu,
            'memory_gb': self.memory_gb,
            'python_version': self.python_version,
            'docker': self.docker,
        }


@dataclass
class StatResult:
    """統計計算結果"""
    min: float
    median: float
    mean: float
    std_dev: float


@dataclass
class ValidationResult:
    """出力値検証結果"""
    is_valid: bool
    max_relative_error: float
    mismatches: List[str]  # 不一致があった実装名のリスト


@dataclass
class BenchmarkResult:
    """ベンチマーク計測結果"""
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
    validation: Optional[ValidationResult] = None
    status: str = "SUCCESS"       # SUCCESS or ERROR
    error_message: Optional[str] = None
    # 並列処理用の追加フィールド
    thread_count: Optional[int] = None  # 使用したスレッド数
    scalability: Optional[float] = None  # スケーラビリティ（シングルスレッドに対する倍率）

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'scenario_name': self.scenario_name,
            'implementation_name': self.implementation_name,
            'execution_times': self.execution_times,
            'memory_usage': self.memory_usage,
            'min_time': self.min_time,
            'median_time': self.median_time,
            'mean_time': self.mean_time,
            'std_dev': self.std_dev,
            'relative_score': self.relative_score,
            'throughput': self.throughput,
            'output_value': self.output_value,
            'timestamp': self.timestamp.isoformat(),
            'environment': {
                'os': self.environment.os,
                'cpu': self.environment.cpu,
                'memory_gb': self.environment.memory_gb,
                'python_version': self.environment.python_version,
                'docker': self.environment.docker,
            },
            'validation': {
                'is_valid': self.validation.is_valid,
                'max_relative_error': self.validation.max_relative_error,
                'mismatches': self.validation.mismatches,
            } if self.validation else None,
            'status': self.status,
            'error_message': self.error_message,
            'thread_count': self.thread_count,
            'scalability': self.scalability,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkResult':
        """辞書形式から復元"""
        env = EnvironmentInfo(**data['environment'])
        validation = ValidationResult(**data['validation']) if data.get('validation') else None
        timestamp = datetime.fromisoformat(data['timestamp'])
        
        return cls(
            scenario_name=data['scenario_name'],
            implementation_name=data['implementation_name'],
            execution_times=data['execution_times'],
            memory_usage=data['memory_usage'],
            min_time=data['min_time'],
            median_time=data['median_time'],
            mean_time=data['mean_time'],
            std_dev=data['std_dev'],
            relative_score=data['relative_score'],
            throughput=data['throughput'],
            output_value=data['output_value'],
            timestamp=timestamp,
            environment=env,
            validation=validation,
            status=data.get('status', 'SUCCESS'),
            error_message=data.get('error_message'),
            thread_count=data.get('thread_count'),
            scalability=data.get('scalability'),
        )


@dataclass
class Scenario:
    """ベンチマークシナリオ定義"""
    name: str
    description: str
    input_data: Any
    expected_output_type: type


@dataclass
class Implementation:
    """実装モジュール情報"""
    name: str              # "python", "numpy", "c_ext", "cpp_ext", etc.
    module: ModuleType     # インポートされたPythonモジュール
    language: str          # "Python", "NumPy", "C", "C++", "Cython", "Rust"
