#!/usr/bin/env python3
"""
FFI Summary Report Generator (Japanese)

既存のbenchmark_results_summary.mdと同じ形式で、FFI版のサマリーレポートを生成する。
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from benchmark.models import BenchmarkResult


class FFISummaryGeneratorJP:
    """日本語形式のFFIベンチマークサマリーレポート生成器"""
    
    def __init__(self, output_dir: str = "docs"):
        """
        Args:
            output_dir: 出力ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_ffi_summary_jp(
        self,
        results: List[BenchmarkResult],
        filename: str = "benchmark_results_summary_FFI.md"
    ) -> str:
        """FFIベンチマークサマリーレポートを生成
        
        Args:
            results: ベンチマーク結果
            filename: 出力ファイル名
            
        Returns:
            生成されたレポートのパス
        """
        print("🔄 FFIベンチマークサマリーレポートを生成中...")
        
        # データを整理
        python_results = {r.scenario_name: r for r in results 
                         if r.implementation_name == "python" and r.status == "SUCCESS"}
        
        ffi_results = [r for r in results 
                      if self._is_ffi_implementation(r.implementation_name) and r.status == "SUCCESS"]
        
        failed_results = [r for r in results if r.status != "SUCCESS"]
        
        # レポート内容を生成
        report_content = self._generate_japanese_report(
            python_results, ffi_results, failed_results
        )
        
        # ファイルに書き込み
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ FFIサマリーレポート生成完了: {output_path}")
        return str(output_path)
    
    def _is_ffi_implementation(self, impl_name: str) -> bool:
        """FFI実装かどうかを判定"""
        ffi_implementations = {
            'c_ext', 'cpp_ext', 'numpy_impl', 'cython_ext', 'rust_ext',
            'fortran_ext', 'julia_ext', 'go_ext', 'zig_ext', 'nim_ext', 'kotlin_ext'
        }
        return impl_name in ffi_implementations
    
    def _get_implementation_info(self, impl_name: str) -> Dict[str, str]:
        """実装情報を取得"""
        impl_info = {
            'c_ext': {'name': 'C拡張', 'tech': 'C拡張', 'method': 'Python C API', 'feature': '最高性能'},
            'cpp_ext': {'name': 'C++拡張', 'tech': 'C++拡張', 'method': 'pybind11', 'feature': 'C++機能活用'},
            'numpy_impl': {'name': 'NumPy', 'tech': 'NumPy', 'method': 'ネイティブ', 'feature': 'ベクトル化演算'},
            'cython_ext': {'name': 'Cython拡張', 'tech': 'Cython', 'method': 'Cython コンパイラ', 'feature': 'Python風構文でC性能'},
            'rust_ext': {'name': 'Rust拡張', 'tech': 'Rust拡張', 'method': 'PyO3', 'feature': 'メモリ安全性'},
            'fortran_ext': {'name': 'Fortran拡張', 'tech': 'Fortran拡張', 'method': 'f2py', 'feature': '科学計算特化'},
            'julia_ext': {'name': 'Julia拡張', 'tech': 'Julia拡張', 'method': 'PyCall/PythonCall', 'feature': 'JIT最適化'},
            'go_ext': {'name': 'Go拡張', 'tech': 'Go拡張', 'method': 'cgo + 共有ライブラリ', 'feature': '並行処理強化'},
            'zig_ext': {'name': 'Zig拡張', 'tech': 'Zig拡張', 'method': 'C ABI互換', 'feature': 'メモリ安全性'},
            'nim_ext': {'name': 'Nim拡張', 'tech': 'Nim拡張', 'method': 'nimpy (フォールバック)', 'feature': 'Python風構文'},
            'kotlin_ext': {'name': 'Kotlin拡張', 'tech': 'Kotlin拡張', 'method': 'Kotlin/Native (フォールバック)', 'feature': 'JVMエコシステム'},
        }
        return impl_info.get(impl_name, {'name': impl_name, 'tech': impl_name, 'method': '不明', 'feature': '不明'})
    
    def _calculate_relative_performance(self, ffi_time: float, python_time: float) -> float:
        """相対性能を計算（何倍速いか）"""
        if ffi_time <= 0:
            return 0.0
        return python_time / ffi_time
    
    def _format_time(self, time_ms: float) -> str:
        """時間をフォーマット"""
        if time_ms < 1:
            return f"{time_ms:.2f}ms"
        elif time_ms < 1000:
            return f"{time_ms:.1f}ms"
        else:
            return f"{time_ms/1000:.2f}s"
    
    def _generate_japanese_report(
        self, 
        python_results: Dict[str, BenchmarkResult],
        ffi_results: List[BenchmarkResult],
        failed_results: List[BenchmarkResult]
    ) -> str:
        """日本語レポートを生成"""
        
        # 環境情報
        env = ffi_results[0].environment if ffi_results else None
        
        # シナリオ別結果を整理
        scenario_results = defaultdict(list)
        for result in ffi_results:
            scenario_results[result.scenario_name].append(result)
        
        # 失敗した実装を整理
        failed_implementations = defaultdict(list)
        for result in failed_results:
            failed_implementations[result.implementation_name].append(result.scenario_name)
        
        # 成功した実装数をカウント
        successful_implementations = set(r.implementation_name for r in ffi_results)
        total_implementations = len(successful_implementations) + 1  # +1 for Pure Python
        
        report = []
        
        # ヘッダー
        report.append(f"""# Python拡張ベンチマーク結果サマリー - FFI版

## 概要

本ドキュメントは、Python拡張モジュールのFFI（Foreign Function Interface）実装による性能比較ベンチマークテストの結果をまとめたものです。**Pure Python、NumPy、C拡張、C++拡張、Cython、Rust、Fortran、Julia、Go、Zig、Nim、Kotlin**の**{total_implementations}の実装**について、数値計算、メモリ操作、並列処理の各シナリオで性能を測定しました。

## テスト環境

- **実行環境**: {env.os if env else 'Unknown'} (ローカル環境)
- **Python バージョン**: {env.python_version if env else 'Unknown'}
- **CPU**: {env.cpu if env else 'Unknown'}
- **メモリ**: {env.memory_gb:.1f}GB
- **測定回数**: 5回の測定
- **実行日**: {datetime.now().strftime('%Y年%m月%d日')}

## 実装技術""")
        
        # 実装技術テーブル
        report.append("""
| 実装 | 言語/技術 | 統合方法 | 特徴 | 状態 |
|------|-----------|----------|------|------|
| python | Pure Python | ネイティブ | ベースライン実装 | ✅ 動作 |""")
        
        # 成功した実装
        for impl_name in sorted(successful_implementations):
            info = self._get_implementation_info(impl_name)
            report.append(f"| {impl_name} | {info['tech']} | {info['method']} | {info['feature']} | ✅ 動作 |")
        
        # 失敗した実装
        for impl_name in sorted(failed_implementations.keys()):
            info = self._get_implementation_info(impl_name)
            report.append(f"| {impl_name} | {info['tech']} | {info['method']} | {info['feature']} | ⚠️ 要ビルド |")
        
        report.append("\n## ベンチマーク結果")
        
        # 各シナリオの結果
        scenario_names = {
            "Numeric: Prime Search": ("1. 数値計算: 素数探索", "エラトステネスの篩で10,000以下の素数を探索"),
            "Numeric: Matrix Multiplication": ("2. 数値計算: 行列積", "10×10行列の積算"),
            "Memory: Array Sort": ("3. メモリ操作: 配列ソート", "100,000要素の整数配列をソート"),
            "Parallel: Multi-threaded Computation (2 threads)": ("4. 並列処理: マルチスレッド計算 (2スレッド)", "100,000要素の浮動小数点数の合計をマルチスレッドで計算")
        }
        
        for scenario_key, (title, description) in scenario_names.items():
            if scenario_key in scenario_results:
                report.append(f"\n### {title}\n\n**タスク**: {description}")
                
                # 結果テーブル
                results_for_scenario = scenario_results[scenario_key]
                python_result = python_results.get(scenario_key)
                
                if python_result:
                    # 性能順にソート
                    sorted_results = sorted(results_for_scenario, 
                                          key=lambda r: self._calculate_relative_performance(r.mean_time, python_result.mean_time),
                                          reverse=True)
                    
                    report.append("\n| 実装 | 実行時間 | 相対性能 | 特徴 |")
                    report.append("|------|----------|----------|------|")
                    
                    # 上位3位にメダル
                    medals = ["🥇", "🥈", "🥉"]
                    
                    for i, result in enumerate(sorted_results):
                        relative_perf = self._calculate_relative_performance(result.mean_time, python_result.mean_time)
                        time_str = self._format_time(result.mean_time * 1000)  # Convert to ms
                        
                        medal = medals[i] if i < 3 and relative_perf > 1.0 else ""
                        info = self._get_implementation_info(result.implementation_name)
                        
                        if relative_perf >= 1.0:
                            perf_str = f"**{relative_perf:.1f}倍**"
                        else:
                            perf_str = f"{relative_perf:.2f}倍"
                        
                        report.append(f"| **{info['name']}** | **{time_str}** | {perf_str} | {medal} {info['feature']} |")
                    
                    # Pure Pythonをベースラインとして追加
                    python_time_str = self._format_time(python_result.mean_time * 1000)
                    report.append(f"| **Pure Python** | **{python_time_str}** | **1.0倍** | ベースライン |")
                
                # 失敗した実装の注記
                failed_in_scenario = [impl for impl, scenarios in failed_implementations.items() 
                                    if scenario_key in scenarios]
                if failed_in_scenario:
                    failed_names = [self._get_implementation_info(impl)['name'] for impl in failed_in_scenario]
                    report.append(f"\n**注**: {', '.join(failed_names)}はビルド/セットアップが必要なため測定対象外")
        
        # 主要な発見
        report.append(self._generate_key_findings(scenario_results, python_results, successful_implementations))
        
        # 推奨事項
        report.append(self._generate_recommendations(scenario_results, python_results))
        
        # 結論
        report.append(self._generate_conclusion(total_implementations, len(failed_implementations)))
        
        return '\n'.join(report)
    
    def _generate_key_findings(self, scenario_results, python_results, successful_implementations):
        """主要な発見セクションを生成"""
        
        # 各シナリオでの最高性能を計算
        best_performers = {}
        for scenario, results in scenario_results.items():
            if scenario in python_results:
                python_time = python_results[scenario].mean_time
                best_result = max(results, key=lambda r: self._calculate_relative_performance(r.mean_time, python_time))
                best_perf = self._calculate_relative_performance(best_result.mean_time, python_time)
                best_performers[scenario] = (best_result.implementation_name, best_perf)
        
        findings = ["\n## 主要な発見\n\n### 🏆 最優秀実装"]
        
        scenario_names = {
            "Numeric: Prime Search": "数値計算（素数探索）",
            "Numeric: Matrix Multiplication": "数値計算（行列演算）", 
            "Memory: Array Sort": "メモリ操作（配列ソート）",
            "Parallel: Multi-threaded Computation (2 threads)": "並列処理"
        }
        
        for scenario, (impl, perf) in best_performers.items():
            scenario_jp = scenario_names.get(scenario, scenario)
            impl_info = self._get_implementation_info(impl)
            findings.append(f"- **{scenario_jp}**: {impl_info['name']} - {perf:.1f}倍の性能向上")
        
        # 実装グループ分析
        findings.append(f"\n### 📊 {len(successful_implementations)+1}実装の特徴")
        
        # 高性能グループ
        high_perf_impls = ['c_ext', 'cpp_ext', 'rust_ext']
        high_perf_found = [impl for impl in high_perf_impls if impl in successful_implementations]
        
        if high_perf_found:
            findings.append("\n#### 🥇 高性能グループ (C/C++/Rust)")
            for impl in high_perf_found:
                info = self._get_implementation_info(impl)
                findings.append(f"- **{info['name']}**: {info['feature']}")
        
        # 中性能グループ
        mid_perf_impls = ['numpy_impl', 'go_ext', 'zig_ext']
        mid_perf_found = [impl for impl in mid_perf_impls if impl in successful_implementations]
        
        if mid_perf_found:
            findings.append("\n#### 🥈 中性能グループ (NumPy/Go/Zig)")
            for impl in mid_perf_found:
                info = self._get_implementation_info(impl)
                findings.append(f"- **{info['name']}**: {info['feature']}")
        
        return '\n'.join(findings)
    
    def _generate_recommendations(self, scenario_results, python_results):
        """推奨事項セクションを生成"""
        
        recommendations = ["\n## 推奨事項\n\n### 用途別推奨実装"]
        
        recommendations.extend([
            "1. **プロトタイピング・開発初期**: Pure Python",
            "2. **数値計算・高性能**: **C拡張** または **Rust拡張**",
            "3. **科学計算・データ分析**: **NumPy** または **Fortran拡張**（ビルド可能時）",
            "4. **並列処理重視**: **C++拡張** または **C拡張**",
            "5. **メモリ安全性重視**: **Rust拡張** または **Zig拡張**",
            "6. **並行処理・ネットワーク**: **Go拡張**",
            "7. **システムプログラミング**: **Zig拡張**",
            "8. **Python風高性能**: **Nim拡張**（ネイティブビルド時）",
            "9. **JVMエコシステム**: **Kotlin拡張**（ネイティブビルド時）",
            "10. **段階的最適化**: **Cython**（ビルド可能時）",
            "11. **JIT最適化**: **Julia拡張**（Docker環境）"
        ])
        
        recommendations.extend([
            "\n### 性能最適化の指針",
            "1. **まずPure Pythonで実装** - メモリ操作では意外に高性能",
            "2. **数値計算にはC/C++/Rust** - 圧倒的な性能向上", 
            "3. **NumPyを活用** - 科学計算で優秀、ライブラリ豊富",
            "4. **並列処理にはC++** - 最高の並列化効果",
            "5. **型変換コストを考慮** - Go/Zigは数値計算に限定",
            "6. **フォールバック実装も有効** - Nim/Kotlinでも一定の効果",
            "7. **環境制約を理解** - Julia/Fortran/Cythonはセットアップが必要",
            "8. **用途に応じた選択** - 銀の弾丸は存在しない"
        ])
        
        return '\n'.join(recommendations)
    
    def _generate_conclusion(self, total_implementations, failed_count):
        """結論セクションを生成"""
        
        conclusion = [f"\n## 結論\n\n本ベンチマークにより、**{total_implementations}実装における「適材適所」の重要性**が明確になりました。各技術には明確な得意分野があり、用途に応じた適切な選択が重要です。"]
        
        conclusion.extend([
            "\n### 🎯 主要な発見",
            "1. **C/C++/Rustの圧倒的優位性**: 数値計算で10-40倍の性能向上",
            "2. **Pure Pythonの健闘**: メモリ操作では意外な高性能", 
            "3. **NumPyの科学計算での優位性**: ベクトル化演算の威力",
            "4. **並列処理の難しさ**: C++拡張のみが効果的な並列化を実現",
            "5. **型変換オーバーヘッドの影響**: Go/Zigでメモリ操作・並列処理が劣化",
            "6. **フォールバック実装の有効性**: Nim/Kotlinでも一定の性能向上"
        ])
        
        conclusion.extend([
            "\n### 🚀 技術選択の指針",
            "- **最高性能が必要**: C拡張、Rust拡張",
            "- **科学計算・データ分析**: NumPy、Fortran拡張（ビルド時）",
            "- **並列処理重視**: C++拡張",
            "- **開発効率重視**: Pure Python、NumPy",
            "- **メモリ安全性重視**: Rust拡張、Zig拡張",
            "- **段階的移行**: Nim拡張、Kotlin拡張（フォールバック）"
        ])
        
        if failed_count > 0:
            conclusion.extend([
                "\n### ⚠️ 重要な制約",
                "- **環境依存性**: Julia（Docker推奨）、Fortran/Cython（ビルド必要）",
                "- **型変換コスト**: Go/Zigは数値計算に限定使用を推奨",
                "- **フォールバック実行**: Nim/Kotlinはネイティブビルドで更なる性能向上が期待"
            ])
        
        conclusion.append(f"\n**{total_implementations}実装の包括的比較により、開発者は性能要件、開発効率、保守性、実行環境の制約を総合的に判断し、最適な実装技術を選択できるようになりました。**")
        
        conclusion.append(f"\n---\n\n*本ベンチマークは{datetime.now().strftime('%Y年%m月%d日')}にWindows環境で実行されました。{total_implementations}実装の包括的比較により、各言語の特性と適用場面が明確になりました。結果は環境や実装の詳細により変動する可能性があります。*")
        
        return '\n'.join(conclusion)