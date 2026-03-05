#!/usr/bin/env python3
"""包括的性能分析実行スクリプト

既存のベンチマーク結果から包括的な性能分析を実行し、
言語別特性、統計的有意性検定、性能分類を行う。
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from benchmark.models import BenchmarkResult, EnvironmentInfo
from benchmark.runner.performance_analyzer import PerformanceAnalyzer


def load_benchmark_results(results_file: str) -> List[BenchmarkResult]:
    """ベンチマーク結果ファイルを読み込み
    
    Args:
        results_file: 結果ファイルのパス
        
    Returns:
        List[BenchmarkResult]: ベンチマーク結果のリスト
    """
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = []
    for result_data in data.get('results', []):
        # 環境情報を復元
        env_data = result_data.get('environment', {})
        environment = EnvironmentInfo(
            os=env_data.get('os', 'Unknown'),
            cpu=env_data.get('cpu', 'Unknown'),
            memory_gb=env_data.get('memory_gb', 0.0),
            python_version=env_data.get('python_version', '3.11'),
            docker=env_data.get('docker', False)
        )
        
        # ベンチマーク結果を復元
        result = BenchmarkResult(
            scenario_name=result_data['scenario_name'],
            implementation_name=result_data['implementation_name'],
            execution_times=result_data['execution_times'],
            memory_usage=result_data['memory_usage'],
            min_time=result_data['min_time'],
            median_time=result_data['median_time'],
            mean_time=result_data['mean_time'],
            std_dev=result_data['std_dev'],
            relative_score=result_data['relative_score'],
            throughput=result_data['throughput'],
            output_value=result_data.get('output_value'),
            timestamp=datetime.fromisoformat(result_data['timestamp']),
            environment=environment,
            status=result_data.get('status', 'SUCCESS'),
            error_message=result_data.get('error_message'),
            thread_count=result_data.get('thread_count')
        )
        results.append(result)
    
    return results


def find_latest_results_file() -> Optional[str]:
    """最新のベンチマーク結果ファイルを検索
    
    Returns:
        Optional[str]: 最新の結果ファイルパス、見つからない場合はNone
    """
    results_dir = project_root / "benchmark" / "results" / "json"
    
    if not results_dir.exists():
        return None
    
    # benchmark_results_で始まるファイルを検索
    result_files = list(results_dir.glob("benchmark_results_*.json"))
    
    if not result_files:
        return None
    
    # ファイル名でソート（タイムスタンプ順）
    result_files.sort(key=lambda x: x.name, reverse=True)
    return str(result_files[0])


def run_comprehensive_analysis(
    results_file: Optional[str] = None,
    output_dir: Optional[str] = None
) -> None:
    """包括的性能分析を実行
    
    Args:
        results_file: 分析対象の結果ファイル（Noneの場合は最新を使用）
        output_dir: 出力ディレクトリ（Noneの場合はデフォルト）
    """
    print("🔍 包括的性能分析を開始します...")
    
    # 結果ファイルを決定
    if results_file is None:
        results_file = find_latest_results_file()
        if results_file is None:
            print("❌ ベンチマーク結果ファイルが見つかりません")
            print("   先にベンチマークを実行してください")
            return
        print(f"📊 最新の結果ファイルを使用: {Path(results_file).name}")
    else:
        print(f"📊 指定された結果ファイルを使用: {results_file}")
    
    # 出力ディレクトリを決定
    if output_dir is None:
        output_dir = project_root / "benchmark" / "results" / "analysis"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # ベンチマーク結果を読み込み
        print("📖 ベンチマーク結果を読み込み中...")
        results = load_benchmark_results(results_file)
        print(f"   {len(results)} 件の結果を読み込みました")
        
        # 成功した結果の統計
        successful_results = [r for r in results if r.status == "SUCCESS"]
        print(f"   成功: {len(successful_results)} 件, エラー: {len(results) - len(successful_results)} 件")
        
        if not successful_results:
            print("❌ 分析可能な結果がありません")
            return
        
        # 性能分析を実行
        print("\n🧮 性能分析を実行中...")
        analyzer = PerformanceAnalyzer()
        analysis = analyzer.analyze_comprehensive_performance(results)
        
        # 結果を保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = output_dir / f"performance_analysis_{timestamp}.json"
        
        print(f"💾 分析結果を保存中: {analysis_file}")
        analyzer.save_analysis_results(analysis, str(analysis_file))
        
        # サマリーを表示
        print_analysis_summary(analysis)
        
        print(f"\n✅ 包括的性能分析が完了しました")
        print(f"   詳細な結果: {analysis_file}")
        
    except Exception as e:
        print(f"❌ 分析中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


def print_analysis_summary(analysis: dict) -> None:
    """分析結果のサマリーを表示
    
    Args:
        analysis: 分析結果の辞書
    """
    print(f"\n{'='*80}")
    print(f"性能分析サマリー")
    print(f"{'='*80}")
    
    # 基本統計
    summary = analysis.get('summary_statistics', {})
    print(f"\n📊 基本統計:")
    print(f"   総結果数: {summary.get('total_results', 0)}")
    print(f"   成功結果数: {summary.get('successful_results', 0)}")
    print(f"   成功率: {summary.get('success_rate', 0.0):.1%}")
    print(f"   実装数: {summary.get('unique_implementations', 0)}")
    print(f"   シナリオ数: {summary.get('unique_scenarios', 0)}")
    
    # 性能分類
    classification = analysis.get('performance_classification', {})
    print(f"\n🏆 性能分類:")
    
    high_perf = classification.get('high_performance', [])
    if high_perf:
        print(f"   高性能実装: {', '.join(high_perf)}")
    
    medium_perf = classification.get('medium_performance', [])
    if medium_perf:
        print(f"   中性能実装: {', '.join(medium_perf)}")
    
    low_perf = classification.get('low_performance', [])
    if low_perf:
        print(f"   低性能実装: {', '.join(low_perf)}")
    
    # カテゴリ別リーダー
    print(f"\n🥇 カテゴリ別リーダー:")
    numeric_leaders = classification.get('numeric_leaders', [])
    if numeric_leaders:
        print(f"   数値計算: {', '.join(numeric_leaders[:3])}")
    
    memory_leaders = classification.get('memory_leaders', [])
    if memory_leaders:
        print(f"   メモリ操作: {', '.join(memory_leaders[:3])}")
    
    parallel_leaders = classification.get('parallel_leaders', [])
    if parallel_leaders:
        print(f"   並列処理: {', '.join(parallel_leaders[:3])}")
    
    # 統計的有意性
    significance_tests = analysis.get('statistical_significance', [])
    significant_count = sum(1 for test in significance_tests if test.get('is_significant', False))
    print(f"\n📈 統計的有意性検定:")
    print(f"   総検定数: {len(significance_tests)}")
    print(f"   有意な差: {significant_count} 件")
    
    # 言語特性（トップ5）
    characteristics = analysis.get('language_characteristics', {})
    if characteristics:
        print(f"\n🌟 言語特性（総合性能トップ5）:")
        sorted_langs = sorted(
            characteristics.items(),
            key=lambda x: x[1].get('overall_performance', 0.0),
            reverse=True
        )
        
        for i, (impl_name, char) in enumerate(sorted_langs[:5], 1):
            language = char.get('language', impl_name)
            overall_perf = char.get('overall_performance', 0.0)
            strengths = char.get('strengths', [])
            
            print(f"   {i}. {language} ({impl_name}): {overall_perf:.2f}x")
            if strengths:
                print(f"      得意分野: {', '.join(strengths[:2])}")
    
    print(f"\n{'='*80}")


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="包括的性能分析を実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 最新の結果ファイルを自動検出して分析
  python scripts/analysis/run_performance_analysis.py
  
  # 特定の結果ファイルを指定して分析
  python scripts/analysis/run_performance_analysis.py -f benchmark/results/json/benchmark_results_20260305_045149.json
  
  # 出力ディレクトリを指定
  python scripts/analysis/run_performance_analysis.py -o /path/to/output
        """
    )
    
    parser.add_argument(
        '-f', '--file',
        help='分析対象のベンチマーク結果ファイル（省略時は最新を自動検出）'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='分析結果の出力ディレクトリ（省略時はbenchmark/results/analysis）'
    )
    
    args = parser.parse_args()
    
    run_comprehensive_analysis(
        results_file=args.file,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()