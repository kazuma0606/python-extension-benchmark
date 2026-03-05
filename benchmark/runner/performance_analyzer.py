"""性能分析モジュール

ベンチマーク結果から包括的な性能分析を実行し、
言語別特性、統計的有意性検定、性能分類を行う。
"""

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Optional scipy import with fallback
try:
    from scipy import stats
    import numpy as np
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    # Fallback implementations
    class stats:
        @staticmethod
        def ttest_ind(a, b, equal_var=False):
            # Simple t-test approximation
            mean_a = statistics.mean(a)
            mean_b = statistics.mean(b)
            std_a = statistics.stdev(a) if len(a) > 1 else 0.0
            std_b = statistics.stdev(b) if len(b) > 1 else 0.0
            
            # Simplified t-statistic
            pooled_std = ((std_a**2 / len(a)) + (std_b**2 / len(b)))**0.5
            if pooled_std > 0:
                t_stat = (mean_a - mean_b) / pooled_std
                # Rough p-value approximation
                p_value = 0.05 if abs(t_stat) > 2.0 else 0.5
            else:
                t_stat = 0.0
                p_value = 1.0
            
            return t_stat, p_value
        
        @staticmethod
        def t():
            class T:
                @staticmethod
                def ppf(alpha, df):
                    # Rough approximation for t-distribution critical value
                    return 2.0 if alpha > 0.9 else 1.0
            return T()
    
    class np:
        @staticmethod
        def sqrt(x):
            return x**0.5

from benchmark.models import BenchmarkResult


@dataclass
class LanguageCharacteristics:
    """言語特性分析結果"""
    language: str
    implementation_name: str
    
    # 性能特性
    numeric_performance: float  # 数値計算性能スコア
    memory_performance: float   # メモリ操作性能スコア
    parallel_performance: float # 並列処理性能スコア
    overall_performance: float  # 総合性能スコア
    
    # 得意分野
    strengths: List[str]
    weaknesses: List[str]
    
    # 統計情報
    success_rate: float
    avg_relative_score: float
    performance_consistency: float  # 性能の一貫性（標準偏差の逆数）
    
    # 制限事項
    limitations: List[str]
    
    # 推奨用途
    recommended_use_cases: List[str]


@dataclass
class StatisticalSignificance:
    """統計的有意性検定結果"""
    implementation_a: str
    implementation_b: str
    scenario: str
    p_value: float
    is_significant: bool
    effect_size: float  # Cohen's d
    confidence_interval: Tuple[float, float]


@dataclass
class PerformanceClassification:
    """性能分類結果"""
    high_performance: List[str]      # 高性能実装
    medium_performance: List[str]    # 中性能実装
    low_performance: List[str]       # 低性能実装
    
    numeric_leaders: List[str]       # 数値計算リーダー
    memory_leaders: List[str]        # メモリ操作リーダー
    parallel_leaders: List[str]      # 並列処理リーダー
    
    most_consistent: List[str]       # 最も一貫した性能
    most_reliable: List[str]         # 最も信頼性の高い実装


class PerformanceAnalyzer:
    """性能分析クラス"""
    
    def __init__(self):
        """初期化"""
        self.language_map = {
            "python": "Python",
            "numpy_impl": "NumPy",
            "c_ext": "C",
            "cpp_ext": "C++",
            "cython_ext": "Cython",
            "rust_ext": "Rust",
            "fortran_ext": "Fortran",
            "julia_ext": "Julia",
            "go_ext": "Go",
            "zig_ext": "Zig",
            "nim_ext": "Nim",
            "kotlin_ext": "Kotlin"
        }
        
        self.scenario_categories = {
            "find_primes": "numeric",
            "matrix_multiply": "numeric", 
            "sort_array": "memory",
            "filter_array": "memory",
            "parallel_compute": "parallel"
        }
    
    def analyze_comprehensive_performance(
        self,
        results: List[BenchmarkResult]
    ) -> Dict[str, Any]:
        """包括的性能分析を実行
        
        Args:
            results: ベンチマーク結果のリスト
            
        Returns:
            Dict[str, Any]: 分析結果の辞書
        """
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_results": len(results),
            "language_characteristics": self._analyze_language_characteristics(results),
            "statistical_significance": self._perform_statistical_tests(results),
            "performance_classification": self._classify_performance(results),
            "summary_statistics": self._calculate_summary_statistics(results)
        }
        
        return analysis
    
    def _analyze_language_characteristics(
        self,
        results: List[BenchmarkResult]
    ) -> Dict[str, LanguageCharacteristics]:
        """言語別特性を分析
        
        Args:
            results: ベンチマーク結果のリスト
            
        Returns:
            Dict[str, LanguageCharacteristics]: 実装名をキーとした特性分析結果
        """
        characteristics = {}
        
        # 実装別に結果をグループ化
        by_implementation = defaultdict(list)
        for result in results:
            if result.status == "SUCCESS":
                by_implementation[result.implementation_name].append(result)
        
        for impl_name, impl_results in by_implementation.items():
            characteristics[impl_name] = self._analyze_single_language(
                impl_name, impl_results
            )
        
        return characteristics
    
    def _analyze_single_language(
        self,
        impl_name: str,
        results: List[BenchmarkResult]
    ) -> LanguageCharacteristics:
        """単一言語の特性を分析
        
        Args:
            impl_name: 実装名
            results: その実装の結果リスト
            
        Returns:
            LanguageCharacteristics: 言語特性分析結果
        """
        language = self.language_map.get(impl_name, "Unknown")
        
        # カテゴリ別性能を計算
        numeric_scores = []
        memory_scores = []
        parallel_scores = []
        all_scores = []
        
        for result in results:
            category = self.scenario_categories.get(result.scenario_name, "other")
            score = result.relative_score
            
            all_scores.append(score)
            
            if category == "numeric":
                numeric_scores.append(score)
            elif category == "memory":
                memory_scores.append(score)
            elif category == "parallel":
                parallel_scores.append(score)
        
        # 性能スコアを計算
        numeric_perf = statistics.mean(numeric_scores) if numeric_scores else 0.0
        memory_perf = statistics.mean(memory_scores) if memory_scores else 0.0
        parallel_perf = statistics.mean(parallel_scores) if parallel_scores else 0.0
        overall_perf = statistics.mean(all_scores) if all_scores else 0.0
        
        # 性能の一貫性を計算（標準偏差の逆数）
        consistency = 1.0 / (statistics.stdev(all_scores) + 0.001) if len(all_scores) > 1 else 1.0
        
        # 得意分野と弱点を特定
        strengths, weaknesses = self._identify_strengths_weaknesses(
            impl_name, numeric_perf, memory_perf, parallel_perf
        )
        
        # 制限事項を特定
        limitations = self._identify_limitations(impl_name, results)
        
        # 推奨用途を決定
        recommended_uses = self._determine_recommended_uses(
            impl_name, numeric_perf, memory_perf, parallel_perf, consistency
        )
        
        return LanguageCharacteristics(
            language=language,
            implementation_name=impl_name,
            numeric_performance=numeric_perf,
            memory_performance=memory_perf,
            parallel_performance=parallel_perf,
            overall_performance=overall_perf,
            strengths=strengths,
            weaknesses=weaknesses,
            success_rate=1.0,  # 成功した結果のみを分析しているため
            avg_relative_score=overall_perf,
            performance_consistency=consistency,
            limitations=limitations,
            recommended_use_cases=recommended_uses
        )
    
    def _identify_strengths_weaknesses(
        self,
        impl_name: str,
        numeric_perf: float,
        memory_perf: float,
        parallel_perf: float
    ) -> Tuple[List[str], List[str]]:
        """得意分野と弱点を特定
        
        Args:
            impl_name: 実装名
            numeric_perf: 数値計算性能
            memory_perf: メモリ操作性能
            parallel_perf: 並列処理性能
            
        Returns:
            Tuple[List[str], List[str]]: (得意分野, 弱点)
        """
        strengths = []
        weaknesses = []
        
        # 性能閾値
        high_threshold = 2.0  # 2倍以上の性能
        low_threshold = 0.5   # 半分以下の性能
        
        # 数値計算
        if numeric_perf >= high_threshold:
            strengths.append("高性能数値計算")
        elif numeric_perf <= low_threshold:
            weaknesses.append("数値計算性能")
        
        # メモリ操作
        if memory_perf >= high_threshold:
            strengths.append("効率的メモリ操作")
        elif memory_perf <= low_threshold:
            weaknesses.append("メモリ操作性能")
        
        # 並列処理
        if parallel_perf >= high_threshold:
            strengths.append("優秀な並列処理")
        elif parallel_perf <= low_threshold:
            weaknesses.append("並列処理性能")
        
        # 言語固有の特性
        if impl_name == "julia_ext":
            strengths.append("科学計算特化")
            strengths.append("JITコンパイル最適化")
        elif impl_name == "go_ext":
            strengths.append("Goroutineによる軽量並行処理")
            strengths.append("ガベージコレクション")
        elif impl_name == "zig_ext":
            strengths.append("メモリ安全性")
            strengths.append("コンパイル時最適化")
        elif impl_name == "nim_ext":
            strengths.append("Python風構文")
            strengths.append("C並み性能")
        elif impl_name == "kotlin_ext":
            strengths.append("JVMエコシステム")
            strengths.append("コルーチン")
        
        return strengths, weaknesses
    
    def _identify_limitations(
        self,
        impl_name: str,
        results: List[BenchmarkResult]
    ) -> List[str]:
        """制限事項を特定
        
        Args:
            impl_name: 実装名
            results: 結果リスト
            
        Returns:
            List[str]: 制限事項のリスト
        """
        limitations = []
        
        # 言語固有の制限事項
        if impl_name == "julia_ext":
            limitations.append("初回実行時のJITコンパイル時間")
            limitations.append("メモリ使用量が大きい場合がある")
        elif impl_name == "go_ext":
            limitations.append("ガベージコレクションによる一時停止")
            limitations.append("数値計算ライブラリの制限")
        elif impl_name == "zig_ext":
            limitations.append("手動メモリ管理の複雑さ")
            limitations.append("エコシステムの未成熟")
        elif impl_name == "nim_ext":
            limitations.append("コミュニティサイズの制限")
            limitations.append("ライブラリエコシステムの制限")
        elif impl_name == "kotlin_ext":
            limitations.append("Kotlin/Nativeの性能制限")
            limitations.append("ビルド時間の長さ")
        
        # 性能ベースの制限事項
        avg_score = statistics.mean([r.relative_score for r in results])
        if avg_score < 0.5:
            limitations.append("全体的な性能が低い")
        
        # 一貫性ベースの制限事項
        scores = [r.relative_score for r in results]
        if len(scores) > 1 and statistics.stdev(scores) > 1.0:
            limitations.append("性能の一貫性に欠ける")
        
        return limitations
    
    def _determine_recommended_uses(
        self,
        impl_name: str,
        numeric_perf: float,
        memory_perf: float,
        parallel_perf: float,
        consistency: float
    ) -> List[str]:
        """推奨用途を決定
        
        Args:
            impl_name: 実装名
            numeric_perf: 数値計算性能
            memory_perf: メモリ操作性能
            parallel_perf: 並列処理性能
            consistency: 性能の一貫性
            
        Returns:
            List[str]: 推奨用途のリスト
        """
        recommendations = []
        
        # 性能ベースの推奨
        if numeric_perf >= 2.0:
            recommendations.append("科学計算・数値解析")
            recommendations.append("機械学習・AI")
        
        if memory_perf >= 2.0:
            recommendations.append("大規模データ処理")
            recommendations.append("メモリ集約的アプリケーション")
        
        if parallel_perf >= 2.0:
            recommendations.append("並列・分散処理")
            recommendations.append("高スループットシステム")
        
        if consistency >= 2.0:
            recommendations.append("リアルタイムシステム")
            recommendations.append("予測可能な性能が必要なシステム")
        
        # 言語固有の推奨用途
        if impl_name == "julia_ext":
            recommendations.extend([
                "研究・プロトタイピング",
                "高性能科学計算"
            ])
        elif impl_name == "go_ext":
            recommendations.extend([
                "Webサービス・API",
                "マイクロサービス",
                "並行処理システム"
            ])
        elif impl_name == "zig_ext":
            recommendations.extend([
                "システムプログラミング",
                "組み込みシステム",
                "性能重視アプリケーション"
            ])
        elif impl_name == "nim_ext":
            recommendations.extend([
                "Pythonからの移行",
                "バランス重視アプリケーション"
            ])
        elif impl_name == "kotlin_ext":
            recommendations.extend([
                "JVMエコシステム活用",
                "Android開発との統合"
            ])
        
        return list(set(recommendations))  # 重複を除去
    
    def _perform_statistical_tests(
        self,
        results: List[BenchmarkResult]
    ) -> List[StatisticalSignificance]:
        """統計的有意性検定を実行
        
        Args:
            results: ベンチマーク結果のリスト
            
        Returns:
            List[StatisticalSignificance]: 統計的有意性検定結果
        """
        significance_tests = []
        
        # シナリオ別に結果をグループ化
        by_scenario = defaultdict(lambda: defaultdict(list))
        for result in results:
            if result.status == "SUCCESS" and result.execution_times:
                by_scenario[result.scenario_name][result.implementation_name] = result.execution_times
        
        # 各シナリオで実装間の比較を実行
        for scenario_name, implementations in by_scenario.items():
            impl_names = list(implementations.keys())
            
            for i in range(len(impl_names)):
                for j in range(i + 1, len(impl_names)):
                    impl_a = impl_names[i]
                    impl_b = impl_names[j]
                    
                    times_a = implementations[impl_a]
                    times_b = implementations[impl_b]
                    
                    if len(times_a) >= 3 and len(times_b) >= 3:
                        significance = self._calculate_statistical_significance(
                            impl_a, impl_b, scenario_name, times_a, times_b
                        )
                        significance_tests.append(significance)
        
        return significance_tests
    
    def _calculate_statistical_significance(
        self,
        impl_a: str,
        impl_b: str,
        scenario: str,
        times_a: List[float],
        times_b: List[float]
    ) -> StatisticalSignificance:
        """2つの実装間の統計的有意性を計算
        
        Args:
            impl_a: 実装A名
            impl_b: 実装B名
            scenario: シナリオ名
            times_a: 実装Aの実行時間リスト
            times_b: 実装Bの実行時間リスト
            
        Returns:
            StatisticalSignificance: 統計的有意性検定結果
        """
        # Welchのt検定を実行
        t_stat, p_value = stats.ttest_ind(times_a, times_b, equal_var=False)
        
        # 効果量（Cohen's d）を計算
        mean_a = statistics.mean(times_a)
        mean_b = statistics.mean(times_b)
        std_a = statistics.stdev(times_a) if len(times_a) > 1 else 0.0
        std_b = statistics.stdev(times_b) if len(times_b) > 1 else 0.0
        
        pooled_std = np.sqrt(((len(times_a) - 1) * std_a**2 + (len(times_b) - 1) * std_b**2) / 
                            (len(times_a) + len(times_b) - 2))
        
        effect_size = abs(mean_a - mean_b) / pooled_std if pooled_std > 0 else 0.0
        
        # 信頼区間を計算（平均の差）
        se_diff = np.sqrt(std_a**2 / len(times_a) + std_b**2 / len(times_b))
        df = len(times_a) + len(times_b) - 2
        t_critical = stats.t.ppf(0.975, df)  # 95%信頼区間
        
        mean_diff = mean_a - mean_b
        margin_error = t_critical * se_diff
        confidence_interval = (mean_diff - margin_error, mean_diff + margin_error)
        
        return StatisticalSignificance(
            implementation_a=impl_a,
            implementation_b=impl_b,
            scenario=scenario,
            p_value=p_value,
            is_significant=p_value < 0.05,
            effect_size=effect_size,
            confidence_interval=confidence_interval
        )
    
    def _classify_performance(
        self,
        results: List[BenchmarkResult]
    ) -> PerformanceClassification:
        """性能を分類
        
        Args:
            results: ベンチマーク結果のリスト
            
        Returns:
            PerformanceClassification: 性能分類結果
        """
        # 実装別の平均性能を計算
        impl_scores = defaultdict(list)
        impl_consistency = {}
        
        for result in results:
            if result.status == "SUCCESS":
                impl_scores[result.implementation_name].append(result.relative_score)
        
        # 平均スコアと一貫性を計算
        avg_scores = {}
        for impl, scores in impl_scores.items():
            avg_scores[impl] = statistics.mean(scores)
            impl_consistency[impl] = 1.0 / (statistics.stdev(scores) + 0.001) if len(scores) > 1 else 1.0
        
        # 性能レベルで分類
        sorted_impls = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
        
        high_performance = []
        medium_performance = []
        low_performance = []
        
        for impl, score in sorted_impls:
            if score >= 2.0:
                high_performance.append(impl)
            elif score >= 1.0:
                medium_performance.append(impl)
            else:
                low_performance.append(impl)
        
        # カテゴリ別リーダーを特定
        numeric_leaders = self._find_category_leaders(results, "numeric")
        memory_leaders = self._find_category_leaders(results, "memory")
        parallel_leaders = self._find_category_leaders(results, "parallel")
        
        # 一貫性と信頼性でソート
        most_consistent = sorted(impl_consistency.items(), key=lambda x: x[1], reverse=True)
        most_consistent = [impl for impl, _ in most_consistent[:3]]
        
        # 信頼性は成功率と一貫性の組み合わせで判定
        most_reliable = most_consistent[:2]  # 簡略化
        
        return PerformanceClassification(
            high_performance=high_performance,
            medium_performance=medium_performance,
            low_performance=low_performance,
            numeric_leaders=numeric_leaders,
            memory_leaders=memory_leaders,
            parallel_leaders=parallel_leaders,
            most_consistent=most_consistent,
            most_reliable=most_reliable
        )
    
    def _find_category_leaders(
        self,
        results: List[BenchmarkResult],
        category: str
    ) -> List[str]:
        """カテゴリ別のリーダーを特定
        
        Args:
            results: ベンチマーク結果のリスト
            category: カテゴリ名 ("numeric", "memory", "parallel")
            
        Returns:
            List[str]: リーダー実装のリスト
        """
        category_results = defaultdict(list)
        
        for result in results:
            if result.status == "SUCCESS":
                scenario_category = self.scenario_categories.get(result.scenario_name)
                if scenario_category == category:
                    category_results[result.implementation_name].append(result.relative_score)
        
        # 平均スコアでソート
        avg_scores = {
            impl: statistics.mean(scores)
            for impl, scores in category_results.items()
        }
        
        sorted_leaders = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
        return [impl for impl, _ in sorted_leaders[:3]]  # トップ3
    
    def _calculate_summary_statistics(
        self,
        results: List[BenchmarkResult]
    ) -> Dict[str, Any]:
        """サマリー統計を計算
        
        Args:
            results: ベンチマーク結果のリスト
            
        Returns:
            Dict[str, Any]: サマリー統計
        """
        successful_results = [r for r in results if r.status == "SUCCESS"]
        
        if not successful_results:
            return {
                "total_results": len(results),
                "successful_results": 0,
                "success_rate": 0.0
            }
        
        all_scores = [r.relative_score for r in successful_results]
        all_times = [r.mean_time for r in successful_results]
        
        return {
            "total_results": len(results),
            "successful_results": len(successful_results),
            "success_rate": len(successful_results) / len(results),
            "performance_statistics": {
                "min_relative_score": min(all_scores),
                "max_relative_score": max(all_scores),
                "mean_relative_score": statistics.mean(all_scores),
                "median_relative_score": statistics.median(all_scores),
                "std_relative_score": statistics.stdev(all_scores) if len(all_scores) > 1 else 0.0
            },
            "timing_statistics": {
                "min_execution_time": min(all_times),
                "max_execution_time": max(all_times),
                "mean_execution_time": statistics.mean(all_times),
                "median_execution_time": statistics.median(all_times)
            },
            "unique_implementations": len(set(r.implementation_name for r in successful_results)),
            "unique_scenarios": len(set(r.scenario_name for r in successful_results))
        }
    
    def save_analysis_results(
        self,
        analysis: Dict[str, Any],
        output_path: str
    ) -> None:
        """分析結果をJSONファイルに保存
        
        Args:
            analysis: 分析結果
            output_path: 出力ファイルパス
        """
        # DataClassをJSONシリアライズ可能な形式に変換
        serializable_analysis = self._make_serializable(analysis)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_analysis, f, indent=2, ensure_ascii=False)
    
    def _make_serializable(self, obj: Any) -> Any:
        """オブジェクトをJSONシリアライズ可能な形式に変換
        
        Args:
            obj: 変換対象オブジェクト
            
        Returns:
            Any: シリアライズ可能なオブジェクト
        """
        if hasattr(obj, '__dict__'):
            return asdict(obj)
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return list(obj)
        else:
            return obj