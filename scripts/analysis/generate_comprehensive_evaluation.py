#!/usr/bin/env python3
"""総合評価レポート生成スクリプト

性能分析結果から開発効率vs性能分析、用途別推奨マトリックス、
技術選択指針を含む総合評価レポートを生成する。
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def load_analysis_results(analysis_file: str) -> Dict[str, Any]:
    """分析結果ファイルを読み込み"""
    with open(analysis_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_comprehensive_evaluation_report(
    analysis: Dict[str, Any],
    output_file: str
) -> None:
    """総合評価レポートを生成"""
    characteristics = analysis.get('language_characteristics', {})
    classification = analysis.get('performance_classification', {})
    summary_stats = analysis.get('summary_statistics', {})
    
    # Markdownレポートを生成
    report_lines = []
    
    # ヘッダー
    report_lines.extend([
        "# 多言語拡張ベンチマーク - 総合評価レポート",
        "",
        f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
        f"**分析対象**: {summary_stats.get('successful_results', 0)} 件のベンチマーク結果",
        "",
        "## エグゼクティブサマリー",
        "",
    ])
    
    # エグゼクティブサマリーを生成
    executive_summary = generate_executive_summary(characteristics, classification)
    report_lines.extend(executive_summary)
    report_lines.append("")
    
    # 開発効率vs性能分析
    report_lines.extend([
        "## 開発効率 vs 性能分析",
        "",
        "各言語実装の開発効率と性能のバランスを4象限で分析します。",
        "",
    ])
    
    efficiency_analysis = generate_efficiency_vs_performance_analysis(characteristics)
    report_lines.extend(efficiency_analysis)
    
    # 用途別推奨マトリックス
    report_lines.extend([
        "## 用途別推奨マトリックス",
        "",
        "具体的な用途に対する推奨実装を示します。",
        "",
    ])
    
    recommendation_matrix = generate_recommendation_matrix(characteristics)
    report_lines.extend(recommendation_matrix)
    
    # 技術選択指針
    report_lines.extend([
        "## 技術選択指針",
        "",
        "プロジェクトの要件に応じた技術選択の指針を提供します。",
        "",
    ])
    
    selection_guidelines = generate_selection_guidelines(characteristics, classification)
    report_lines.extend(selection_guidelines)
    
    # ファイルに書き出し
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))


def generate_executive_summary(
    characteristics: Dict[str, Any],
    classification: Dict[str, Any]
) -> List[str]:
    """エグゼクティブサマリーを生成"""
    summary_lines = []
    
    # 主要な発見事項
    high_perf = classification.get('high_performance', [])
    total_impls = len(characteristics)
    
    if high_perf:
        top_impl = high_perf[0]
        top_char = characteristics.get(top_impl, {})
        top_lang = top_char.get('language', top_impl)
        top_score = top_char.get('overall_performance', 0.0)
        
        summary_lines.extend([
            f"**主要な発見事項:**",
            "",
            f"- **最高性能**: {top_lang}が{top_score:.2f}xの性能を実現",
            f"- **実装数**: {total_impls}の言語実装を比較分析",
            f"- **高性能実装**: {len(high_perf)}の実装が2倍以上の性能向上を達成",
        ])
    
    # カテゴリ別リーダー
    numeric_leaders = classification.get('numeric_leaders', [])
    memory_leaders = classification.get('memory_leaders', [])
    parallel_leaders = classification.get('parallel_leaders', [])
    
    if numeric_leaders:
        numeric_char = characteristics.get(numeric_leaders[0], {})
        numeric_lang = numeric_char.get('language', numeric_leaders[0])
        summary_lines.append(f"- **数値計算リーダー**: {numeric_lang}")
    
    if memory_leaders:
        memory_char = characteristics.get(memory_leaders[0], {})
        memory_lang = memory_char.get('language', memory_leaders[0])
        summary_lines.append(f"- **メモリ操作リーダー**: {memory_lang}")
    
    if parallel_leaders:
        parallel_char = characteristics.get(parallel_leaders[0], {})
        parallel_lang = parallel_char.get('language', parallel_leaders[0])
        summary_lines.append(f"- **並列処理リーダー**: {parallel_lang}")
    
    return summary_lines


def generate_efficiency_vs_performance_analysis(
    characteristics: Dict[str, Any]
) -> List[str]:
    """開発効率vs性能分析を生成"""
    analysis_lines = []
    
    # 開発効率の評価（主観的スコア 1-5）
    dev_efficiency_scores = {
        "python": 5,
        "numpy_impl": 4,
        "julia_ext": 4,
        "kotlin_ext": 3,
        "go_ext": 3,
        "nim_ext": 3,
        "cython_ext": 2,
        "rust_ext": 2,
        "cpp_ext": 1,
        "c_ext": 1,
        "zig_ext": 1,
        "fortran_ext": 1
    }
    
    # 4象限に分類
    quadrants = {
        "高性能・高効率": [],
        "高性能・低効率": [],
        "低性能・高効率": [],
        "低性能・低効率": []
    }
    
    for impl_name, char in characteristics.items():
        language = char.get('language', impl_name)
        performance = char.get('overall_performance', 0.0)
        efficiency = dev_efficiency_scores.get(impl_name, 3)
        
        if performance >= 1.5 and efficiency >= 3:
            quadrants["高性能・高効率"].append((language, performance, efficiency))
        elif performance >= 1.5 and efficiency < 3:
            quadrants["高性能・低効率"].append((language, performance, efficiency))
        elif performance < 1.5 and efficiency >= 3:
            quadrants["低性能・高効率"].append((language, performance, efficiency))
        else:
            quadrants["低性能・低効率"].append((language, performance, efficiency))
    
    # 各象限の説明
    for quadrant_name, languages in quadrants.items():
        if languages:
            analysis_lines.extend([
                f"### {quadrant_name}",
                "",
            ])
            
            for lang, perf, eff in languages:
                analysis_lines.append(f"- **{lang}**: 性能{perf:.2f}x, 開発効率{eff}/5")
            
            analysis_lines.append("")
            
            # 象限別の推奨事項
            if quadrant_name == "高性能・高効率":
                analysis_lines.extend([
                    "**推奨**: 理想的な選択肢。積極的に採用を検討",
                    "",
                ])
            elif quadrant_name == "高性能・低効率":
                analysis_lines.extend([
                    "**推奨**: 性能が最重要な場合に選択。開発コスト増加に注意",
                    "",
                ])
            elif quadrant_name == "低性能・高効率":
                analysis_lines.extend([
                    "**推奨**: プロトタイピングや開発速度重視の場合に適用",
                    "",
                ])
            else:
                analysis_lines.extend([
                    "**推奨**: 特別な理由がない限り避けることを推奨",
                    "",
                ])
    
    return analysis_lines


def generate_recommendation_matrix(
    characteristics: Dict[str, Any]
) -> List[str]:
    """用途別推奨マトリックスを生成"""
    matrix_lines = []
    
    # 用途別の推奨実装を決定
    use_cases = {
        "科学計算・数値解析": {
            "criteria": "numeric_performance",
            "description": "高精度な数値計算が必要な研究・解析用途"
        },
        "大規模データ処理": {
            "criteria": "memory_performance", 
            "description": "大量のデータを効率的に処理する必要がある用途"
        },
        "リアルタイム処理": {
            "criteria": "performance_consistency",
            "description": "予測可能で一貫した性能が必要な用途"
        },
        "並列・分散システム": {
            "criteria": "parallel_performance",
            "description": "マルチコア・マルチノードでの並列処理が重要な用途"
        },
        "プロトタイピング": {
            "criteria": "development_efficiency",
            "description": "迅速な開発とイテレーションが重要な用途"
        },
        "プロダクション運用": {
            "criteria": "overall_performance",
            "description": "安定した性能と信頼性が必要な本番環境"
        }
    }
    
    for use_case, config in use_cases.items():
        matrix_lines.extend([
            f"### {use_case}",
            "",
            f"*{config['description']}*",
            "",
        ])
        
        # 推奨実装を決定
        if config['criteria'] == 'development_efficiency':
            # 開発効率重視の場合
            dev_efficiency = {
                "python": 5, "numpy_impl": 4, "julia_ext": 4,
                "kotlin_ext": 3, "go_ext": 3, "nim_ext": 3,
                "cython_ext": 2, "rust_ext": 2, "cpp_ext": 1,
                "c_ext": 1, "zig_ext": 1, "fortran_ext": 1
            }
            
            recommendations = []
            for impl_name, char in characteristics.items():
                language = char.get('language', impl_name)
                eff_score = dev_efficiency.get(impl_name, 3)
                recommendations.append((impl_name, language, eff_score))
            
            recommendations.sort(key=lambda x: x[2], reverse=True)
            
        else:
            # 性能基準の場合
            recommendations = []
            for impl_name, char in characteristics.items():
                language = char.get('language', impl_name)
                score = char.get(config['criteria'], 0.0)
                recommendations.append((impl_name, language, score))
            
            recommendations.sort(key=lambda x: x[2], reverse=True)
        
        # トップ3を表示
        for i, (impl_name, language, score) in enumerate(recommendations[:3], 1):
            if config['criteria'] == 'development_efficiency':
                matrix_lines.append(f"{i}. **{language}**: 開発効率 {score}/5")
            else:
                matrix_lines.append(f"{i}. **{language}**: {score:.2f}x")
        
        matrix_lines.append("")
    
    return matrix_lines


def generate_selection_guidelines(
    characteristics: Dict[str, Any],
    classification: Dict[str, Any]
) -> List[str]:
    """技術選択指針を生成"""
    guidelines_lines = []
    
    guidelines_lines.extend([
        "### 性能要件別選択指針",
        "",
        "#### 🚀 最高性能が必要な場合",
        "",
    ])
    
    high_perf = classification.get('high_performance', [])
    for impl in high_perf[:3]:
        char = characteristics.get(impl, {})
        language = char.get('language', impl)
        score = char.get('overall_performance', 0.0)
        guidelines_lines.append(f"- **{language}**: {score:.2f}x - 最高レベルの性能")
    
    guidelines_lines.extend([
        "",
        "#### ⚖️ バランス重視の場合",
        "",
    ])
    
    medium_perf = classification.get('medium_performance', [])
    for impl in medium_perf[:3]:
        char = characteristics.get(impl, {})
        language = char.get('language', impl)
        score = char.get('overall_performance', 0.0)
        guidelines_lines.append(f"- **{language}**: {score:.2f}x - 性能と開発効率のバランス")
    
    guidelines_lines.extend([
        "",
        "### プロジェクト特性別選択指針",
        "",
        "#### 🔬 研究・学術用途",
        "",
        "- **Julia**: 科学計算に特化、研究者に親しみやすい",
        "- **NumPy**: 豊富な科学計算ライブラリ",
        "- **Fortran**: 数値計算の伝統的選択肢",
        "",
        "#### 🏢 企業・商用システム",
        "",
        "- **Go**: 保守性とスケーラビリティ",
        "- **Rust**: メモリ安全性と性能",
        "- **C++**: 既存システムとの統合",
        "",
        "#### 🚀 スタートアップ・アジャイル開発",
        "",
        "- **Python**: 迅速なプロトタイピング",
        "- **Nim**: Python風構文で高性能",
        "- **Kotlin**: JVMエコシステム活用",
        "",
        "### 技術的制約による選択指針",
        "",
        "#### メモリ制約がある環境",
        "",
    ])
    
    # メモリ効率の良い実装を推奨
    memory_efficient = ["c_ext", "cpp_ext", "zig_ext", "rust_ext"]
    for impl in memory_efficient:
        if impl in characteristics:
            char = characteristics[impl]
            language = char.get('language', impl)
            guidelines_lines.append(f"- **{language}**: 最小限のメモリ使用量")
    
    guidelines_lines.extend([
        "",
        "#### 既存システムとの統合が必要",
        "",
        "- **C/C++**: 最も広範な互換性",
        "- **Kotlin**: JVMエコシステム",
        "- **Go**: シンプルなC ABI",
        "",
        "#### 開発チームのスキルセット",
        "",
        "- **Python経験者**: NumPy → Cython → Nim",
        "- **Java経験者**: Kotlin → Scala → Go",
        "- **C++経験者**: Rust → Zig → C++",
        "- **関数型言語経験者**: Julia → Haskell → OCaml",
        "",
    ])
    
    return guidelines_lines


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
        description="総合評価レポートを生成",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-f', '--file',
        help='分析結果ファイル（省略時は最新を自動検出）'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='docs/comprehensive_evaluation_report.md',
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
        
        # レポートを生成
        print("📝 総合評価レポートを生成中...")
        generate_comprehensive_evaluation_report(analysis, args.output)
        
        print(f"✅ レポートが生成されました: {args.output}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()