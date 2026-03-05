#!/usr/bin/env python3
"""ベンチマーク結果サマリー更新スクリプト

12実装の結果を含む包括的サマリー、技術選択指針の更新、
制限事項と注意点を追記してベンチマーク結果サマリーを更新する。
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_analysis_results(analysis_file: str) -> Dict[str, Any]:
    """分析結果ファイルを読み込み"""
    with open(analysis_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_benchmark_results_summary(
    analysis: Dict[str, Any],
    output_file: str
) -> None:
    """ベンチマーク結果サマリーを更新"""
    
    characteristics = analysis.get('language_characteristics', {})
    classification = analysis.get('performance_classification', {})
    summary_stats = analysis.get('summary_statistics', {})
    significance_tests = analysis.get('statistical_significance', [])
    
    # 既存のサマリーファイルを読み込み（存在する場合）
    existing_content = ""
    if Path(output_file).exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # 新しいサマリーを生成
    summary_lines = []
    
    # ヘッダー
    summary_lines.extend([
        "# Python拡張ベンチマーク結果サマリー",
        "",
        f"**最終更新**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
        f"**分析対象**: {summary_stats.get('successful_results', 0)} 件のベンチマーク結果",
        f"**実装数**: {summary_stats.get('unique_implementations', 0)} 言語実装",
        "",
        "## 概要",
        "",
        "本サマリーは、Python拡張ベンチマークシステムにおける12の言語実装の",
        "包括的な性能比較結果をまとめています。各実装の性能特性、適用領域、",
        "制限事項を詳細に分析し、技術選択の指針を提供します。",
        "",
    ])
    
    # エグゼクティブサマリー
    summary_lines.extend(generate_executive_summary(characteristics, classification))
    
    # 性能ランキング
    summary_lines.extend(generate_performance_ranking(characteristics))
    
    # カテゴリ別分析
    summary_lines.extend(generate_category_analysis(characteristics, classification))
    
    # 統計的有意性
    summary_lines.extend(generate_statistical_significance_summary(significance_tests))
    
    # 技術選択指針（更新版）
    summary_lines.extend(generate_updated_selection_guidelines(characteristics, classification))
    
    # 制限事項と注意点
    summary_lines.extend(generate_limitations_and_considerations(characteristics))
    
    # 結論と推奨事項
    summary_lines.extend(generate_conclusions_and_recommendations(characteristics, classification))
    
    # ファイルに書き出し
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary_lines))


def generate_executive_summary(
    characteristics: Dict[str, Any],
    classification: Dict[str, Any]
) -> List[str]:
    """エグゼクティブサマリーを生成"""
    summary_lines = [
        "## エグゼクティブサマリー",
        "",
    ]
    
    # 主要な発見事項
    high_perf = classification.get('high_performance', [])
    total_impls = len(characteristics)
    
    if high_perf:
        top_impl = high_perf[0]
        top_char = characteristics.get(top_impl, {})
        top_lang = top_char.get('language', top_impl)
        top_score = top_char.get('overall_performance', 0.0)
        
        summary_lines.extend([
            "### 主要な発見事項",
            "",
            f"- **最高性能実装**: {top_lang}が{top_score:.2f}倍の性能向上を実現",
            f"- **高性能実装数**: {len(high_perf)}/{total_impls}の実装が2倍以上の性能向上",
            f"- **性能向上範囲**: 0.5倍〜{top_score:.1f}倍の幅広い性能特性",
        ])
    
    # カテゴリ別リーダー
    numeric_leaders = classification.get('numeric_leaders', [])
    memory_leaders = classification.get('memory_leaders', [])
    parallel_leaders = classification.get('parallel_leaders', [])
    
    summary_lines.extend([
        "",
        "### カテゴリ別リーダー",
        "",
    ])
    
    if numeric_leaders:
        numeric_char = characteristics.get(numeric_leaders[0], {})
        numeric_lang = numeric_char.get('language', numeric_leaders[0])
        numeric_score = numeric_char.get('numeric_performance', 0.0)
        summary_lines.append(f"- **数値計算**: {numeric_lang} ({numeric_score:.2f}x)")
    
    if memory_leaders:
        memory_char = characteristics.get(memory_leaders[0], {})
        memory_lang = memory_char.get('language', memory_leaders[0])
        memory_score = memory_char.get('memory_performance', 0.0)
        summary_lines.append(f"- **メモリ操作**: {memory_lang} ({memory_score:.2f}x)")
    
    if parallel_leaders:
        parallel_char = characteristics.get(parallel_leaders[0], {})
        parallel_lang = parallel_char.get('language', parallel_leaders[0])
        parallel_score = parallel_char.get('parallel_performance', 0.0)
        summary_lines.append(f"- **並列処理**: {parallel_lang} ({parallel_score:.2f}x)")
    
    summary_lines.append("")
    
    return summary_lines


def generate_performance_ranking(characteristics: Dict[str, Any]) -> List[str]:
    """性能ランキングを生成"""
    ranking_lines = [
        "## 総合性能ランキング",
        "",
        "Pure Pythonを基準（1.0x）とした相対性能で評価:",
        "",
    ]
    
    # 総合性能でソート
    sorted_impls = sorted(
        characteristics.items(),
        key=lambda x: x[1].get('overall_performance', 0.0),
        reverse=True
    )
    
    for i, (impl_name, char) in enumerate(sorted_impls, 1):
        language = char.get('language', impl_name)
        overall_perf = char.get('overall_performance', 0.0)
        
        # 性能レベルの判定
        if overall_perf >= 3.0:
            level = "🥇 超高性能"
        elif overall_perf >= 2.0:
            level = "🥈 高性能"
        elif overall_perf >= 1.0:
            level = "🥉 標準性能"
        else:
            level = "⚠️ 低性能"
        
        ranking_lines.append(f"{i:2d}. **{language}**: {overall_perf:.2f}x {level}")
    
    ranking_lines.append("")
    
    return ranking_lines


def generate_category_analysis(
    characteristics: Dict[str, Any],
    classification: Dict[str, Any]
) -> List[str]:
    """カテゴリ別分析を生成"""
    analysis_lines = [
        "## カテゴリ別詳細分析",
        "",
    ]
    
    categories = {
        "数値計算": ("numeric_performance", "numeric_leaders"),
        "メモリ操作": ("memory_performance", "memory_leaders"),
        "並列処理": ("parallel_performance", "parallel_leaders")
    }
    
    for category_name, (perf_key, leaders_key) in categories.items():
        analysis_lines.extend([
            f"### {category_name}性能",
            "",
        ])
        
        # カテゴリ別ランキング
        category_ranking = sorted(
            characteristics.items(),
            key=lambda x: x[1].get(perf_key, 0.0),
            reverse=True
        )
        
        for i, (impl_name, char) in enumerate(category_ranking[:5], 1):
            language = char.get('language', impl_name)
            perf_score = char.get(perf_key, 0.0)
            analysis_lines.append(f"{i}. **{language}**: {perf_score:.2f}x")
        
        analysis_lines.append("")
    
    return analysis_lines


def generate_statistical_significance_summary(
    significance_tests: List[Dict[str, Any]]
) -> List[str]:
    """統計的有意性サマリーを生成"""
    summary_lines = [
        "## 統計的有意性分析",
        "",
        f"**総検定数**: {len(significance_tests)} 件の実装間比較",
    ]
    
    if significance_tests:
        significant_count = sum(1 for test in significance_tests if test.get('is_significant', False))
        significance_rate = significant_count / len(significance_tests) * 100
        
        summary_lines.extend([
            f"**有意な差**: {significant_count} 件 ({significance_rate:.1f}%)",
            "",
            "### 主要な有意差",
            "",
        ])
        
        # 効果量の大きい有意差を抽出
        significant_tests = [
            test for test in significance_tests 
            if test.get('is_significant', False)
        ]
        
        # 効果量でソート
        significant_tests.sort(key=lambda x: x.get('effect_size', 0.0), reverse=True)
        
        for test in significant_tests[:5]:  # トップ5
            impl_a = test.get('implementation_a', '')
            impl_b = test.get('implementation_b', '')
            scenario = test.get('scenario', '')
            effect_size = test.get('effect_size', 0.0)
            p_value = test.get('p_value', 1.0)
            
            summary_lines.append(
                f"- **{impl_a} vs {impl_b}** ({scenario}): "
                f"効果量 {effect_size:.2f}, p={p_value:.4f}"
            )
        
        summary_lines.append("")
    
    return summary_lines


def generate_updated_selection_guidelines(
    characteristics: Dict[str, Any],
    classification: Dict[str, Any]
) -> List[str]:
    """更新された技術選択指針を生成"""
    guidelines_lines = [
        "## 技術選択指針（2026年版）",
        "",
        "12実装の包括的分析に基づく最新の技術選択指針:",
        "",
    ]
    
    # 用途別推奨
    guidelines_lines.extend([
        "### 用途別推奨実装",
        "",
        "#### 🔬 科学計算・研究開発",
        "",
    ])
    
    # 数値計算性能でソート
    numeric_ranking = sorted(
        characteristics.items(),
        key=lambda x: x[1].get('numeric_performance', 0.0),
        reverse=True
    )
    
    for i, (impl_name, char) in enumerate(numeric_ranking[:3], 1):
        language = char.get('language', impl_name)
        numeric_perf = char.get('numeric_performance', 0.0)
        strengths = char.get('strengths', [])
        
        guidelines_lines.append(f"{i}. **{language}**: {numeric_perf:.2f}x")
        if strengths:
            guidelines_lines.append(f"   - {', '.join(strengths[:2])}")
    
    guidelines_lines.extend([
        "",
        "#### 🏢 企業システム・プロダクション",
        "",
    ])
    
    # 総合性能と一貫性を考慮
    production_ranking = sorted(
        characteristics.items(),
        key=lambda x: (
            x[1].get('overall_performance', 0.0) * 
            x[1].get('performance_consistency', 0.0)
        ),
        reverse=True
    )
    
    for i, (impl_name, char) in enumerate(production_ranking[:3], 1):
        language = char.get('language', impl_name)
        overall_perf = char.get('overall_performance', 0.0)
        consistency = char.get('performance_consistency', 0.0)
        
        guidelines_lines.append(
            f"{i}. **{language}**: {overall_perf:.2f}x (一貫性: {consistency:.2f})"
        )
    
    guidelines_lines.extend([
        "",
        "#### 🚀 スタートアップ・アジャイル開発",
        "",
        "開発効率を重視した推奨順位:",
        "",
        "1. **Python**: 最高の開発効率、豊富なエコシステム",
        "2. **NumPy**: Pythonベースで高性能",
        "3. **Julia**: 科学計算特化、学習コストは中程度",
        "",
        "### プロジェクト規模別指針",
        "",
        "#### 小規模プロジェクト（〜10万行）",
        "",
        "- **Python/NumPy**: 開発速度重視",
        "- **Julia**: 数値計算が中心の場合",
        "- **Go**: シンプルな並行処理が必要な場合",
        "",
        "#### 中規模プロジェクト（10万〜100万行）",
        "",
        "- **Rust**: 安全性と性能のバランス",
        "- **Go**: 保守性と並行処理",
        "- **C++**: 既存資産の活用",
        "",
        "#### 大規模プロジェクト（100万行以上）",
        "",
        "- **C/C++**: 最高性能と制御",
        "- **Rust**: メモリ安全性重視",
        "- **Fortran**: 科学計算特化の大規模システム",
        "",
    ])
    
    return guidelines_lines


def generate_limitations_and_considerations(
    characteristics: Dict[str, Any]
) -> List[str]:
    """制限事項と注意点を生成"""
    limitations_lines = [
        "## 制限事項と注意点",
        "",
        "### 言語別制限事項",
        "",
    ]
    
    # 各言語の制限事項をまとめる
    for impl_name, char in characteristics.items():
        language = char.get('language', impl_name)
        limitations = char.get('limitations', [])
        
        if limitations:
            limitations_lines.extend([
                f"#### {language}",
                "",
            ])
            
            for limitation in limitations:
                limitations_lines.append(f"- {limitation}")
            
            limitations_lines.append("")
    
    # 共通の注意点
    limitations_lines.extend([
        "### 共通の注意点",
        "",
        "#### 性能測定について",
        "",
        "- **環境依存性**: CPU、メモリ、OS により結果が変動",
        "- **ワークロード依存性**: 実際の用途と異なる場合がある",
        "- **最適化レベル**: コンパイラ設定により大きく変動",
        "",
        "#### 開発・運用コスト",
        "",
        "- **学習コスト**: 新しい言語の習得時間",
        "- **エコシステム**: ライブラリやツールの充実度",
        "- **人材確保**: 開発者の採用難易度",
        "- **保守性**: 長期的なメンテナンスコスト",
        "",
        "#### 技術的制約",
        "",
        "- **メモリ使用量**: 言語により大きく異なる",
        "- **ビルド時間**: 開発効率に影響",
        "- **デプロイメント**: 実行環境の複雑さ",
        "- **デバッグ**: 言語固有のツールチェーン",
        "",
    ])
    
    return limitations_lines


def generate_conclusions_and_recommendations(
    characteristics: Dict[str, Any],
    classification: Dict[str, Any]
) -> List[str]:
    """結論と推奨事項を生成"""
    conclusions_lines = [
        "## 結論と推奨事項",
        "",
        "### 主要な結論",
        "",
    ]
    
    # 性能分析の結論
    high_perf = classification.get('high_performance', [])
    if high_perf:
        top_impl = high_perf[0]
        top_char = characteristics.get(top_impl, {})
        top_lang = top_char.get('language', top_impl)
        top_score = top_char.get('overall_performance', 0.0)
        
        conclusions_lines.extend([
            f"1. **最高性能**: {top_lang}が{top_score:.2f}倍の性能を実現し、",
            "   Pure Pythonからの大幅な性能向上が可能",
            "",
            f"2. **多様性**: {len(characteristics)}の異なる言語実装により、",
            "   用途に応じた最適な選択肢が存在",
            "",
            "3. **トレードオフ**: 性能と開発効率は必ずしも反比例せず、",
            "   バランスの取れた選択肢も存在",
            "",
        ])
    
    # カテゴリ別の結論
    numeric_leaders = classification.get('numeric_leaders', [])
    memory_leaders = classification.get('memory_leaders', [])
    parallel_leaders = classification.get('parallel_leaders', [])
    
    if numeric_leaders and memory_leaders and parallel_leaders:
        conclusions_lines.extend([
            "4. **専門化**: 各言語は特定の領域で優位性を示し、",
            f"   数値計算({characteristics.get(numeric_leaders[0], {}).get('language', '')}), ",
            f"   メモリ操作({characteristics.get(memory_leaders[0], {}).get('language', '')}), ",
            f"   並列処理({characteristics.get(parallel_leaders[0], {}).get('language', '')})で",
            "   それぞれ異なるリーダーが存在",
            "",
        ])
    
    # 推奨事項
    conclusions_lines.extend([
        "### 推奨事項",
        "",
        "#### 新規プロジェクト開始時",
        "",
        "1. **要件分析**: 性能要件、開発期間、チームスキルを明確化",
        "2. **プロトタイピング**: 複数の候補で小規模実装を比較",
        "3. **段階的移行**: Python → 高性能実装の段階的移行を検討",
        "",
        "#### 既存システム改善時",
        "",
        "1. **ボトルネック特定**: プロファイリングで性能課題を特定",
        "2. **部分最適化**: 全体ではなく重要部分のみを最適化",
        "3. **互換性確保**: 既存システムとの統合を重視",
        "",
        "#### 技術選択の指針",
        "",
        "1. **性能最優先**: C/C++、Rust、Zig を検討",
        "2. **開発効率重視**: Python、NumPy、Julia を選択",
        "3. **バランス重視**: Go、Nim、Kotlin を評価",
        "",
        "### 今後の展望",
        "",
        "- **新言語の追加**: WebAssembly、Swift、Dart等の評価",
        "- **最適化手法**: SIMD、GPU活用等の高度な最適化",
        "- **自動選択**: 用途に応じた自動的な実装選択システム",
        "",
        "---",
        "",
        f"*このサマリーは {datetime.now().strftime('%Y年%m月%d日')} に自動生成されました。*",
        f"*詳細な分析結果は analysis/ ディレクトリを参照してください。*",
    ])
    
    return conclusions_lines


def find_latest_analysis_file() -> str:
    """最新の分析結果ファイルを検索"""
    analysis_dir = project_root / "benchmark" / "results" / "analysis"
    
    if not analysis_dir.exists():
        raise FileNotFoundError("分析結果ディレクトリが見つかりません")
    
    analysis_files = list(analysis_dir.glob("performance_analysis_*.json"))
    
    if not analysis_files:
        raise FileNotFoundError("分析結果ファイルが見つかりません")
    
    analysis_files.sort(key=lambda x: x.name, reverse=True)
    return str(analysis_files[0])


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="ベンチマーク結果サマリーを更新",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-f', '--file',
        help='分析結果ファイル（省略時は最新を自動検出）'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='docs/benchmark_results_summary.md',
        help='出力ファイルパス'
    )
    
    args = parser.parse_args()
    
    try:
        # 分析結果ファイルを決定
        if args.file:
            analysis_file = args.file
        else:
            analysis_file = find_latest_analysis_file()
            print(f"📊 最新の分析結果を使用: {Path(analysis_file).name}")
        
        # 分析結果を読み込み
        print("📖 分析結果を読み込み中...")
        analysis = load_analysis_results(analysis_file)
        
        # サマリーを更新
        print("📝 ベンチマーク結果サマリーを更新中...")
        update_benchmark_results_summary(analysis, args.output)
        
        print(f"✅ サマリーが更新されました: {args.output}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()