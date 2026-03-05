"""グラフ生成モジュール

ベンチマーク結果を可視化してPNG形式で保存する。
"""

import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
from typing import List, Dict
from benchmark.models import BenchmarkResult

# バックエンドを設定（GUIなしで動作）
matplotlib.use('Agg')


class Visualizer:
    """ベンチマーク結果の可視化を担当するクラス"""
    
    def __init__(self, base_dir: str = "benchmark/results"):
        """
        Args:
            base_dir: 結果出力のベースディレクトリ
        """
        self.base_dir = Path(base_dir)
        self.graphs_dir = self.base_dir / "graphs"
        
        # ディレクトリが存在しない場合は作成
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_execution_time(
        self,
        results: List[BenchmarkResult],
        output_path: str
    ) -> str:
        """実行時間の比較グラフを生成
        
        Args:
            results: ベンチマーク結果のリスト
            output_path: 出力ファイル名（拡張子なし）
            
        Returns:
            出力されたファイルのパス
        """
        # シナリオごとにグループ化
        scenarios: Dict[str, List[BenchmarkResult]] = {}
        for result in results:
            if result.status == "SUCCESS":
                if result.scenario_name not in scenarios:
                    scenarios[result.scenario_name] = []
                scenarios[result.scenario_name].append(result)
        
        # グラフ作成
        num_scenarios = len(scenarios)
        
        if num_scenarios == 0:
            # データがない場合は空のグラフを作成
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.text(0.5, 0.5, 'No execution time data available',
                   ha='center', va='center', fontsize=12)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            fig, axes = plt.subplots(1, num_scenarios, figsize=(6 * num_scenarios, 5))
            
            # シナリオが1つの場合、axesをリストに変換
            if num_scenarios == 1:
                axes = [axes]
            
            for idx, (scenario_name, scenario_results) in enumerate(sorted(scenarios.items())):
                ax = axes[idx]
                
                # 実装名と実行時間を抽出
                implementations = [r.implementation_name for r in scenario_results]
                mean_times = [r.mean_time for r in scenario_results]
                std_devs = [r.std_dev for r in scenario_results]
                
                # 棒グラフを描画
                bars = ax.bar(implementations, mean_times, yerr=std_devs, capsize=5)
                
                # グラフの装飾
                ax.set_xlabel('Implementation')
                ax.set_ylabel('Execution Time (ms)')
                ax.set_title(f'{scenario_name}\nExecution Time Comparison')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(axis='y', alpha=0.3)
                
                # 値をバーの上に表示
                for bar, time in zip(bars, mean_times):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{time:.2f}',
                           ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        # ファイルに保存
        full_path = self.graphs_dir / f"{output_path}.png"
        plt.savefig(full_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return str(full_path)
    
    def plot_memory_usage(
        self,
        results: List[BenchmarkResult],
        output_path: str
    ) -> str:
        """メモリ使用量の比較グラフを生成
        
        Args:
            results: ベンチマーク結果のリスト
            output_path: 出力ファイル名（拡張子なし）
            
        Returns:
            出力されたファイルのパス
        """
        # シナリオごとにグループ化
        scenarios: Dict[str, List[BenchmarkResult]] = {}
        for result in results:
            if result.status == "SUCCESS" and result.memory_usage:
                if result.scenario_name not in scenarios:
                    scenarios[result.scenario_name] = []
                scenarios[result.scenario_name].append(result)
        
        # グラフ作成
        num_scenarios = len(scenarios)
        if num_scenarios == 0:
            # メモリデータがない場合は空のグラフを作成
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.text(0.5, 0.5, 'No memory usage data available',
                   ha='center', va='center', fontsize=12)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            fig, axes = plt.subplots(1, num_scenarios, figsize=(6 * num_scenarios, 5))
            
            # シナリオが1つの場合、axesをリストに変換
            if num_scenarios == 1:
                axes = [axes]
            
            for idx, (scenario_name, scenario_results) in enumerate(sorted(scenarios.items())):
                ax = axes[idx]
                
                # 実装名とメモリ使用量を抽出
                implementations = [r.implementation_name for r in scenario_results]
                peak_memory = [max(r.memory_usage) for r in scenario_results]
                avg_memory = [sum(r.memory_usage) / len(r.memory_usage) for r in scenario_results]
                
                # 棒グラフを描画（ピークと平均）
                x = range(len(implementations))
                width = 0.35
                
                bars1 = ax.bar([i - width/2 for i in x], peak_memory, width, label='Peak Memory')
                bars2 = ax.bar([i + width/2 for i in x], avg_memory, width, label='Average Memory')
                
                # グラフの装飾
                ax.set_xlabel('Implementation')
                ax.set_ylabel('Memory Usage (MB)')
                ax.set_title(f'{scenario_name}\nMemory Usage Comparison')
                ax.set_xticks(x)
                ax.set_xticklabels(implementations, rotation=45)
                ax.legend()
                ax.grid(axis='y', alpha=0.3)
                
                # 値をバーの上に表示
                for bar in bars1:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}',
                           ha='center', va='bottom', fontsize=8)
                for bar in bars2:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}',
                           ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        # ファイルに保存
        full_path = self.graphs_dir / f"{output_path}.png"
        plt.savefig(full_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return str(full_path)
    
    def plot_scalability(
        self,
        results: List[BenchmarkResult],
        output_path: str
    ) -> str:
        """並列処理のスケーラビリティグラフを生成
        
        Args:
            results: ベンチマーク結果のリスト（並列処理シナリオ）
            output_path: 出力ファイル名（拡張子なし）
            
        Returns:
            出力されたファイルのパス
        """
        # 並列処理シナリオのみをフィルタ
        parallel_results = [r for r in results 
                          if 'parallel' in r.scenario_name.lower() and r.status == "SUCCESS"]
        
        if not parallel_results:
            # 並列処理データがない場合は空のグラフを作成
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No parallel processing data available',
                   ha='center', va='center', fontsize=12)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            # 実装ごとにグループ化
            implementations: Dict[str, List[BenchmarkResult]] = {}
            for result in parallel_results:
                if result.implementation_name not in implementations:
                    implementations[result.implementation_name] = []
                implementations[result.implementation_name].append(result)
            
            # グラフ作成（2つのサブプロット：スループットとスケーラビリティ）
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # スループットのグラフ
            for impl_name, impl_results in sorted(implementations.items()):
                # スレッド数でソート（シナリオ名から抽出を試みる）
                impl_results_sorted = sorted(impl_results, 
                                            key=lambda r: self._extract_thread_count(r.scenario_name))
                
                thread_counts = [self._extract_thread_count(r.scenario_name) for r in impl_results_sorted]
                throughputs = [r.throughput for r in impl_results_sorted]
                
                ax1.plot(thread_counts, throughputs, marker='o', label=impl_name, linewidth=2)
            
            ax1.set_xlabel('Number of Threads')
            ax1.set_ylabel('Throughput (ops/sec)')
            ax1.set_title('Parallel Processing Throughput')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_xscale('log', base=2)
            
            # スケーラビリティのグラフ（シングルスレッドを基準とした相対性能）
            for impl_name, impl_results in sorted(implementations.items()):
                impl_results_sorted = sorted(impl_results, 
                                            key=lambda r: self._extract_thread_count(r.scenario_name))
                
                thread_counts = [self._extract_thread_count(r.scenario_name) for r in impl_results_sorted]
                throughputs = [r.throughput for r in impl_results_sorted]
                
                # シングルスレッドのスループットを基準とする
                if throughputs and throughputs[0] > 0:
                    baseline = throughputs[0]
                    scalability = [t / baseline for t in throughputs]
                    ax2.plot(thread_counts, scalability, marker='o', label=impl_name, linewidth=2)
            
            # 理想的なスケーラビリティ（線形）を点線で表示
            if thread_counts:
                ax2.plot(thread_counts, thread_counts, 'k--', label='Ideal (Linear)', alpha=0.5)
            
            ax2.set_xlabel('Number of Threads')
            ax2.set_ylabel('Scalability (relative to 1 thread)')
            ax2.set_title('Parallel Processing Scalability')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.set_xscale('log', base=2)
            ax2.set_yscale('log', base=2)
        
        plt.tight_layout()
        
        # ファイルに保存
        full_path = self.graphs_dir / f"{output_path}.png"
        plt.savefig(full_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return str(full_path)
    
    def _extract_thread_count(self, scenario_name: str) -> int:
        """シナリオ名からスレッド数を抽出
        
        Args:
            scenario_name: シナリオ名
            
        Returns:
            スレッド数（抽出できない場合は1）
        """
        import re
        match = re.search(r'(\d+)\s*thread', scenario_name.lower())
        if match:
            return int(match.group(1))
        return 1
    
    def plot_comprehensive_comparison(
        self,
        results: List[BenchmarkResult],
        output_path: str
    ) -> str:
        """12実装の包括的比較グラフを生成
        
        Args:
            results: ベンチマーク結果のリスト
            output_path: 出力ファイル名（拡張子なし）
            
        Returns:
            出力されたファイルのパス
        """
        successful_results = [r for r in results if r.status == "SUCCESS"]
        
        if not successful_results:
            # データがない場合は空のグラフを作成
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.text(0.5, 0.5, 'No data available for comprehensive comparison',
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
        else:
            # 4つのサブプロット：実行時間、メモリ使用量、相対スコア、言語別統計
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. 実行時間の比較（シナリオ別）
            self._plot_execution_time_heatmap(successful_results, ax1)
            
            # 2. メモリ使用量の比較
            self._plot_memory_comparison(successful_results, ax2)
            
            # 3. 相対スコアの比較
            self._plot_relative_score_comparison(successful_results, ax3)
            
            # 4. 言語別統計
            self._plot_language_statistics(successful_results, ax4)
        
        plt.tight_layout()
        
        # ファイルに保存
        full_path = self.graphs_dir / f"{output_path}.png"
        plt.savefig(full_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return str(full_path)
    
    def _plot_execution_time_heatmap(self, results: List[BenchmarkResult], ax) -> None:
        """実行時間のヒートマップを描画"""
        import numpy as np
        
        # データを整理
        implementations = sorted(set(r.implementation_name for r in results))
        scenarios = sorted(set(r.scenario_name for r in results))
        
        # ヒートマップ用のデータ行列を作成
        data_matrix = np.full((len(implementations), len(scenarios)), np.nan)
        
        for i, impl in enumerate(implementations):
            for j, scenario in enumerate(scenarios):
                matching_results = [r for r in results 
                                  if r.implementation_name == impl and r.scenario_name == scenario]
                if matching_results:
                    data_matrix[i, j] = matching_results[0].mean_time
        
        # ヒートマップを描画
        im = ax.imshow(data_matrix, cmap='YlOrRd', aspect='auto')
        
        # 軸の設定
        ax.set_xticks(range(len(scenarios)))
        ax.set_yticks(range(len(implementations)))
        ax.set_xticklabels([s.replace(':', '\n') for s in scenarios], rotation=45, ha='right')
        ax.set_yticklabels(implementations)
        ax.set_title('Execution Time Heatmap (ms)')
        
        # カラーバーを追加
        plt.colorbar(im, ax=ax, shrink=0.8)
        
        # 値をセルに表示
        for i in range(len(implementations)):
            for j in range(len(scenarios)):
                if not np.isnan(data_matrix[i, j]):
                    text = ax.text(j, i, f'{data_matrix[i, j]:.1f}',
                                 ha="center", va="center", color="black", fontsize=8)
    
    def _plot_memory_comparison(self, results: List[BenchmarkResult], ax) -> None:
        """メモリ使用量の比較を描画"""
        # 実装別の平均メモリ使用量を計算
        impl_memory = {}
        for result in results:
            if result.memory_usage:
                impl = result.implementation_name
                peak_memory = max(result.memory_usage)
                
                if impl not in impl_memory:
                    impl_memory[impl] = []
                impl_memory[impl].append(peak_memory)
        
        # 平均値を計算
        implementations = []
        avg_memory = []
        
        for impl, memories in impl_memory.items():
            implementations.append(impl)
            avg_memory.append(sum(memories) / len(memories))
        
        # 棒グラフを描画
        bars = ax.bar(implementations, avg_memory, color='lightblue', edgecolor='navy')
        ax.set_ylabel('Average Peak Memory (MB)')
        ax.set_title('Memory Usage Comparison')
        ax.tick_params(axis='x', rotation=45)
        
        # 値をバーの上に表示
        for bar, memory in zip(bars, avg_memory):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{memory:.1f}',
                   ha='center', va='bottom', fontsize=9)
    
    def _plot_relative_score_comparison(self, results: List[BenchmarkResult], ax) -> None:
        """相対スコアの比較を描画"""
        # 実装別の平均相対スコアを計算
        impl_scores = {}
        for result in results:
            impl = result.implementation_name
            if impl not in impl_scores:
                impl_scores[impl] = []
            impl_scores[impl].append(result.relative_score)
        
        # 平均値を計算してソート
        avg_scores = []
        for impl, scores in impl_scores.items():
            avg_score = sum(scores) / len(scores)
            avg_scores.append((impl, avg_score))
        
        avg_scores.sort(key=lambda x: x[1], reverse=True)
        
        implementations = [item[0] for item in avg_scores]
        scores = [item[1] for item in avg_scores]
        
        # 棒グラフを描画（色分け：スコアに応じて）
        colors = ['green' if s >= 1.0 else 'orange' if s >= 0.5 else 'red' for s in scores]
        bars = ax.bar(implementations, scores, color=colors, alpha=0.7)
        
        ax.set_ylabel('Average Relative Score')
        ax.set_title('Performance Ranking (vs Python baseline)')
        ax.tick_params(axis='x', rotation=45)
        ax.axhline(y=1.0, color='black', linestyle='--', alpha=0.5, label='Python baseline')
        ax.legend()
        
        # 値をバーの上に表示
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{score:.2f}',
                   ha='center', va='bottom', fontsize=9)
    
    def _plot_language_statistics(self, results: List[BenchmarkResult], ax) -> None:
        """言語別統計を描画"""
        # 言語別の統計を計算
        language_map = {
            "python": "Python", "numpy_impl": "NumPy", "c_ext": "C",
            "cpp_ext": "C++", "cython_ext": "Cython", "rust_ext": "Rust",
            "fortran_ext": "Fortran", "julia_ext": "Julia", "go_ext": "Go",
            "zig_ext": "Zig", "nim_ext": "Nim", "kotlin_ext": "Kotlin"
        }
        
        language_stats = {}
        for result in results:
            lang = language_map.get(result.implementation_name, "Unknown")
            if lang not in language_stats:
                language_stats[lang] = {'count': 0, 'total_score': 0.0}
            
            language_stats[lang]['count'] += 1
            language_stats[lang]['total_score'] += result.relative_score
        
        # 平均スコアを計算
        languages = []
        avg_scores = []
        counts = []
        
        for lang, stats in language_stats.items():
            if stats['count'] > 0:
                languages.append(lang)
                avg_scores.append(stats['total_score'] / stats['count'])
                counts.append(stats['count'])
        
        # 散布図を描画（x軸：実装数、y軸：平均スコア）
        scatter = ax.scatter(counts, avg_scores, s=100, alpha=0.7, c=avg_scores, cmap='viridis')
        
        # 言語名をラベルとして追加
        for i, lang in enumerate(languages):
            ax.annotate(lang, (counts[i], avg_scores[i]), 
                       xytext=(5, 5), textcoords='offset points', fontsize=9)
        
        ax.set_xlabel('Number of Implementations')
        ax.set_ylabel('Average Relative Score')
        ax.set_title('Language Performance Overview')
        ax.grid(True, alpha=0.3)
        
        # カラーバーを追加
        plt.colorbar(scatter, ax=ax, shrink=0.8, label='Avg Score')
