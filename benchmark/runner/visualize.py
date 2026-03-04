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
