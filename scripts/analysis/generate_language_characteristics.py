#!/usr/bin/env python3
"""言語別特性分析レポート生成スクリプト

性能分析結果から言語別の特性、制限事項、推奨用途を
詳細にドキュメント化したレポートを生成する。
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
    """分析結果ファイルを読み込み
    
    Args:
        analysis_file: 分析結果ファイルのパス
        
    Returns:
        Dict[str, Any]: 分析結果
    """
    with open(analysis_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_language_characteristics_report(
    analysis: Dict[str, Any],
    output_file: str
) -> None:
    """言語別特性レポートを生成
    
    Args:
        analysis: 分析結果
        output_file: 出力ファイルパス
    """
    characteristics = analysis.get('language_characteristics', {})
    classification = analysis.get('performance_classification', {})
    summary_stats = analysis.get('summary_statistics', {})
    
    # Markdownレポートを生成
    report_lines = []
    
    # ヘッダー
    report_lines.extend([
        "# 多言語拡張ベンチマーク - 言語別特性分析レポート",
        "",
        f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
        f"**分析対象**: {summary_stats.get('successful_results', 0)} 件のベンチマーク結果",
        f"**実装数**: {summary_stats.get('unique_implementations', 0)} 言語実装",
        "",
        "## 概要",
        "",
        "本レポートは、Python拡張ベンチマークシステムにおける12の言語実装の",
        "性能特性、得意分野、制限事項、推奨用途を詳細に分析した結果をまとめています。",
        "",
    ])
    
    # 性能分類サマリー
    report_lines.extend([
        "## 性能分類サマリー",
        "",
    ])
    
    high_perf = classification.get('high_performance', [])
    medium_perf = classification.get('medium_performance', [])
    low_perf = classification.get('low_performance', [])
    
    if high_perf:
        report_lines.extend([
            "### 🏆 高性能実装 (2.0x以上)",
            "",
        ])
        for impl in high_perf:
            char = characteristics.get(impl, {})
            language = char.get('language', impl)
            overall_perf = char.get('overall_performance', 0.0)
            report_lines.append(f"- **{language}** ({impl}): {overall_perf:.2f}x")
        report_lines.append("")
    
    if medium_perf:
        report_lines.extend([
            "### 🥈 中性能実装 (1.0x - 2.0x)",
            "",
        ])
        for impl in medium_perf:
            char = characteristics.get(impl, {})
            language = char.get('language', impl)
            overall_perf = char.get('overall_performance', 0.0)
            report_lines.append(f"- **{language}** ({impl}): {overall_perf:.2f}x")
        report_lines.append("")
    
    if low_perf:
        report_lines.extend([
            "### 🥉 低性能実装 (1.0x未満)",
            "",
        ])
        for impl in low_perf:
            char = characteristics.get(impl, {})
            language = char.get('language', impl)
            overall_perf = char.get('overall_performance', 0.0)
            report_lines.append(f"- **{language}** ({impl}): {overall_perf:.2f}x")
        report_lines.append("")
    
    # カテゴリ別リーダー
    report_lines.extend([
        "## カテゴリ別性能リーダー",
        "",
    ])
    
    numeric_leaders = classification.get('numeric_leaders', [])
    memory_leaders = classification.get('memory_leaders', [])
    parallel_leaders = classification.get('parallel_leaders', [])
    
    if numeric_leaders:
        report_lines.extend([
            "### 🧮 数値計算リーダー",
            "",
        ])
        for i, impl in enumerate(numeric_leaders[:3], 1):
            char = characteristics.get(impl, {})
            language = char.get('language', impl)
            numeric_perf = char.get('numeric_performance', 0.0)
            report_lines.append(f"{i}. **{language}**: {numeric_perf:.2f}x")
        report_lines.append("")
    
    if memory_leaders:
        report_lines.extend([
            "### 💾 メモリ操作リーダー",
            "",
        ])
        for i, impl in enumerate(memory_leaders[:3], 1):
            char = characteristics.get(impl, {})
            language = char.get('language', impl)
            memory_perf = char.get('memory_performance', 0.0)
            report_lines.append(f"{i}. **{language}**: {memory_perf:.2f}x")
        report_lines.append("")
    
    if parallel_leaders:
        report_lines.extend([
            "### ⚡ 並列処理リーダー",
            "",
        ])
        for i, impl in enumerate(parallel_leaders[:3], 1):
            char = characteristics.get(impl, {})
            language = char.get('language', impl)
            parallel_perf = char.get('parallel_performance', 0.0)
            report_lines.append(f"{i}. **{language}**: {parallel_perf:.2f}x")
        report_lines.append("")
    
    # 言語別詳細分析
    report_lines.extend([
        "## 言語別詳細分析",
        "",
        "各言語実装の詳細な特性分析結果を以下に示します。",
        "",
    ])
    
    # 性能順でソート
    sorted_characteristics = sorted(
        characteristics.items(),
        key=lambda x: x[1].get('overall_performance', 0.0),
        reverse=True
    )
    
    for impl_name, char in sorted_characteristics:
        language = char.get('language', impl_name)
        
        report_lines.extend([
            f"### {language} ({impl_name})",
            "",
        ])
        
        # 性能指標
        overall_perf = char.get('overall_performance', 0.0)
        numeric_perf = char.get('numeric_performance', 0.0)
        memory_perf = char.get('memory_performance', 0.0)
        parallel_perf = char.get('parallel_performance', 0.0)
        consistency = char.get('performance_consistency', 0.0)
        
        report_lines.extend([
            "#### 性能指標",
            "",
            f"- **総合性能**: {overall_perf:.2f}x (Pure Pythonとの比較)",
            f"- **数値計算**: {numeric_perf:.2f}x",
            f"- **メモリ操作**: {memory_perf:.2f}x", 
            f"- **並列処理**: {parallel_perf:.2f}x",
            f"- **性能一貫性**: {consistency:.2f} (高いほど安定)",
            "",
        ])
        
        # 得意分野
        strengths = char.get('strengths', [])
        if strengths:
            report_lines.extend([
                "#### ✅ 得意分野",
                "",
            ])
            for strength in strengths:
                report_lines.append(f"- {strength}")
            report_lines.append("")
        
        # 弱点
        weaknesses = char.get('weaknesses', [])
        if weaknesses:
            report_lines.extend([
                "#### ⚠️ 弱点・課題",
                "",
            ])
            for weakness in weaknesses:
                report_lines.append(f"- {weakness}")
            report_lines.append("")
        
        # 制限事項
        limitations = char.get('limitations', [])
        if limitations:
            report_lines.extend([
                "#### 🚫 制限事項",
                "",
            ])
            for limitation in limitations:
                report_lines.append(f"- {limitation}")
            report_lines.append("")
        
        # 推奨用途
        recommended_uses = char.get('recommended_use_cases', [])
        if recommended_uses:
            report_lines.extend([
                "#### 💡 推奨用途",
                "",
            ])
            for use_case in recommended_uses:
                report_lines.append(f"- {use_case}")
            report_lines.append("")
        
        # 技術的特徴
        report_lines.extend([
            "#### 🔧 技術的特徴",
            "",
        ])
        
        # 言語固有の技術的特徴を追加
        technical_features = get_technical_features(impl_name)
        for feature in technical_features:
            report_lines.append(f"- {feature}")
        
        report_lines.extend([
            "",
            "---",
            "",
        ])
    
    # 技術選択指針
    report_lines.extend([
        "## 技術選択指針",
        "",
        "用途別の推奨実装を以下に示します。",
        "",
    ])
    
    # 用途別推奨マトリックス
    use_case_matrix = generate_use_case_matrix(characteristics)
    
    for use_case, recommendations in use_case_matrix.items():
        report_lines.extend([
            f"### {use_case}",
            "",
        ])
        
        for i, (impl, reason) in enumerate(recommendations[:3], 1):
            char = characteristics.get(impl, {})
            language = char.get('language', impl)
            report_lines.append(f"{i}. **{language}**: {reason}")
        
        report_lines.append("")
    
    # 開発効率 vs 性能のトレードオフ
    report_lines.extend([
        "## 開発効率 vs 性能トレードオフ",
        "",
        "各言語の開発効率と性能のバランスを評価します。",
        "",
    ])
    
    tradeoff_analysis = generate_tradeoff_analysis(characteristics)
    
    for category, languages in tradeoff_analysis.items():
        report_lines.extend([
            f"### {category}",
            "",
        ])
        
        for lang_info in languages:
            report_lines.append(f"- **{lang_info['language']}**: {lang_info['description']}")
        
        report_lines.append("")
    
    # 結論
    report_lines.extend([
        "## 結論",
        "",
        "本分析により、以下の知見が得られました：",
        "",
    ])
    
    conclusions = generate_conclusions(characteristics, classification)
    for conclusion in conclusions:
        report_lines.append(f"- {conclusion}")
    
    report_lines.extend([
        "",
        "---",
        "",
        f"*このレポートは {datetime.now().strftime('%Y年%m月%d日')} に自動生成されました。*",
    ])
    
    # ファイルに書き出し
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))


def get_technical_features(impl_name: str) -> List[str]:
    """実装の技術的特徴を取得
    
    Args:
        impl_name: 実装名
        
    Returns:
        List[str]: 技術的特徴のリスト
    """
    features_map = {
        "python": [
            "インタープリター言語",
            "動的型付け",
            "GIL（Global Interpreter Lock）による制限",
            "豊富なライブラリエコシステム"
        ],
        "numpy_impl": [
            "NumPyによるベクトル化演算",
            "C/Fortranで実装された高速ライブラリ",
            "メモリ効率的な配列操作",
            "科学計算に特化"
        ],
        "c_ext": [
            "ネイティブコンパイル",
            "手動メモリ管理",
            "最小限のランタイムオーバーヘッド",
            "ハードウェアレベル最適化"
        ],
        "cpp_ext": [
            "オブジェクト指向プログラミング",
            "テンプレートによる汎用プログラミング",
            "STLライブラリ活用",
            "ゼロコスト抽象化"
        ],
        "cython_ext": [
            "Python風構文でC拡張を記述",
            "段階的最適化が可能",
            "NumPyとの密接な統合",
            "型注釈による性能向上"
        ],
        "rust_ext": [
            "メモリ安全性保証",
            "ゼロコスト抽象化",
            "所有権システム",
            "並行処理安全性"
        ],
        "fortran_ext": [
            "科学計算に特化した言語設計",
            "配列操作の最適化",
            "数値計算ライブラリとの親和性",
            "長年の最適化技術蓄積"
        ],
        "julia_ext": [
            "JITコンパイル（LLVM）",
            "多重ディスパッチ",
            "数値計算に特化した設計",
            "Python/R/MATLABとの相互運用性"
        ],
        "go_ext": [
            "Goroutineによる軽量スレッド",
            "チャネルベース通信",
            "ガベージコレクション",
            "シンプルな言語設計"
        ],
        "zig_ext": [
            "コンパイル時安全性チェック",
            "手動メモリ管理",
            "C ABI互換性",
            "最小限のランタイム"
        ],
        "nim_ext": [
            "Python風構文",
            "マクロシステム",
            "複数バックエンド対応",
            "メモリ管理選択可能"
        ],
        "kotlin_ext": [
            "JVMエコシステム活用",
            "Null安全性",
            "コルーチンによる非同期処理",
            "Java相互運用性"
        ]
    }
    
    return features_map.get(impl_name, ["技術的特徴情報なし"])


def generate_use_case_matrix(characteristics: Dict[str, Any]) -> Dict[str, List[tuple]]:
    """用途別推奨マトリックスを生成
    
    Args:
        characteristics: 言語特性データ
        
    Returns:
        Dict[str, List[tuple]]: 用途別推奨実装とその理由
    """
    matrix = {}
    
    # 数値計算・科学計算
    numeric_impls = sorted(
        characteristics.items(),
        key=lambda x: x[1].get('numeric_performance', 0.0),
        reverse=True
    )
    matrix["数値計算・科学計算"] = [
        (impl, f"数値計算性能 {char.get('numeric_performance', 0.0):.2f}x")
        for impl, char in numeric_impls[:3]
    ]
    
    # 大規模データ処理
    memory_impls = sorted(
        characteristics.items(),
        key=lambda x: x[1].get('memory_performance', 0.0),
        reverse=True
    )
    matrix["大規模データ処理"] = [
        (impl, f"メモリ操作性能 {char.get('memory_performance', 0.0):.2f}x")
        for impl, char in memory_impls[:3]
    ]
    
    # 並列・分散処理
    parallel_impls = sorted(
        characteristics.items(),
        key=lambda x: x[1].get('parallel_performance', 0.0),
        reverse=True
    )
    matrix["並列・分散処理"] = [
        (impl, f"並列処理性能 {char.get('parallel_performance', 0.0):.2f}x")
        for impl, char in parallel_impls[:3]
    ]
    
    # リアルタイムシステム
    consistent_impls = sorted(
        characteristics.items(),
        key=lambda x: x[1].get('performance_consistency', 0.0),
        reverse=True
    )
    matrix["リアルタイムシステム"] = [
        (impl, f"性能一貫性 {char.get('performance_consistency', 0.0):.2f}")
        for impl, char in consistent_impls[:3]
    ]
    
    return matrix


def generate_tradeoff_analysis(characteristics: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """開発効率vs性能トレードオフ分析を生成
    
    Args:
        characteristics: 言語特性データ
        
    Returns:
        Dict[str, List[Dict[str, str]]]: カテゴリ別の言語情報
    """
    # 開発効率の主観的評価（1-5スケール）
    dev_efficiency = {
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
    
    analysis = {
        "高性能・高開発効率": [],
        "高性能・低開発効率": [],
        "低性能・高開発効率": [],
        "バランス型": []
    }
    
    for impl_name, char in characteristics.items():
        language = char.get('language', impl_name)
        overall_perf = char.get('overall_performance', 0.0)
        dev_eff = dev_efficiency.get(impl_name, 3)
        
        if overall_perf >= 2.0 and dev_eff >= 4:
            analysis["高性能・高開発効率"].append({
                "language": language,
                "description": f"性能{overall_perf:.1f}x、開発効率高。理想的な選択肢"
            })
        elif overall_perf >= 2.0 and dev_eff <= 2:
            analysis["高性能・低開発効率"].append({
                "language": language,
                "description": f"性能{overall_perf:.1f}x、開発コスト高。性能重視案件向け"
            })
        elif overall_perf < 1.0 and dev_eff >= 4:
            analysis["低性能・高開発効率"].append({
                "language": language,
                "description": f"性能{overall_perf:.1f}x、開発効率高。プロトタイピング向け"
            })
        else:
            analysis["バランス型"].append({
                "language": language,
                "description": f"性能{overall_perf:.1f}x、バランス重視。汎用的な用途"
            })
    
    return analysis


def generate_conclusions(
    characteristics: Dict[str, Any],
    classification: Dict[str, Any]
) -> List[str]:
    """結論を生成
    
    Args:
        characteristics: 言語特性データ
        classification: 性能分類データ
        
    Returns:
        List[str]: 結論のリスト
    """
    conclusions = []
    
    # 最高性能実装
    high_perf = classification.get('high_performance', [])
    if high_perf:
        top_impl = high_perf[0]
        top_char = characteristics.get(top_impl, {})
        top_lang = top_char.get('language', top_impl)
        top_score = top_char.get('overall_performance', 0.0)
        conclusions.append(
            f"最高性能は{top_lang}の{top_score:.2f}xで、Pure Pythonの{top_score:.1f}倍の性能を実現"
        )
    
    # カテゴリ別リーダー
    numeric_leaders = classification.get('numeric_leaders', [])
    if numeric_leaders:
        leader = numeric_leaders[0]
        leader_char = characteristics.get(leader, {})
        leader_lang = leader_char.get('language', leader)
        conclusions.append(f"数値計算では{leader_lang}が最も優秀な性能を示した")
    
    # 実装の多様性
    total_impls = len(characteristics)
    conclusions.append(f"{total_impls}の異なる言語実装により、用途に応じた最適な選択が可能")
    
    # 性能向上の範囲
    all_scores = [char.get('overall_performance', 0.0) for char in characteristics.values()]
    if all_scores:
        max_score = max(all_scores)
        min_score = min(all_scores)
        conclusions.append(
            f"性能向上幅は{min_score:.1f}x〜{max_score:.1f}xの範囲で、"
            f"最大{max_score/min_score:.1f}倍の性能差が存在"
        )
    
    return conclusions


def find_latest_analysis_file() -> str:
    """最新の分析結果ファイルを検索
    
    Returns:
        str: 最新の分析結果ファイルパス
    """
    analysis_dir = project_root / "benchmark" / "results" / "analysis"
    
    if not analysis_dir.exists():
        raise FileNotFoundError("分析結果ディレクトリが見つかりません")
    
    analysis_files = list(analysis_dir.glob("performance_analysis_*.json"))
    
    if not analysis_files:
        raise FileNotFoundError("分析結果ファイルが見つかりません")
    
    # ファイル名でソート（タイムスタンプ順）
    analysis_files.sort(key=lambda x: x.name, reverse=True)
    return str(analysis_files[0])


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="言語別特性分析レポートを生成",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '-f', '--file',
        help='分析結果ファイル（省略時は最新を自動検出）'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='docs/language_characteristics_analysis.md',
        help='出力ファイルパス（デフォルト: docs/language_characteristics_analysis.md）'
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
        print("📝 言語別特性レポートを生成中...")
        generate_language_characteristics_report(analysis, args.output)
        
        print(f"✅ レポートが生成されました: {args.output}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()