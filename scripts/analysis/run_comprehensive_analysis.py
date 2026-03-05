#!/usr/bin/env python3
"""包括的性能分析実行マスタースクリプト

全ての分析コンポーネントを統合して実行し、
完全な性能分析レポートセットを生成する。
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_script(script_path: str, args: list = None) -> bool:
    """スクリプトを実行
    
    Args:
        script_path: 実行するスクリプトのパス
        args: 追加の引数リスト
        
    Returns:
        bool: 実行成功時True
    """
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ スクリプト実行エラー: {script_path}")
        print(f"   エラー出力: {e.stderr}")
        return False


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="包括的性能分析を実行（全コンポーネント）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
このスクリプトは以下の分析を順次実行します:
1. 性能分析（統計的有意性検定含む）
2. 言語別特性分析レポート生成
3. 総合評価レポート生成
4. 実装ガイド生成
5. ベンチマーク結果サマリー更新

全ての分析結果は docs/ ディレクトリに出力されます。
        """
    )
    
    parser.add_argument(
        '-f', '--file',
        help='分析対象のベンチマーク結果ファイル（省略時は最新を自動検出）'
    )
    
    parser.add_argument(
        '--skip-analysis',
        action='store_true',
        help='性能分析をスキップ（既存の分析結果を使用）'
    )
    
    args = parser.parse_args()
    
    print("🚀 包括的性能分析を開始します...")
    print(f"   開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # スクリプトパス
    scripts_dir = Path(__file__).parent
    
    analysis_scripts = [
        ("run_performance_analysis.py", "性能分析"),
        ("generate_language_characteristics.py", "言語別特性分析レポート"),
        ("generate_comprehensive_evaluation.py", "総合評価レポート"),
        ("generate_implementation_guide.py", "実装ガイド"),
        ("update_benchmark_summary.py", "ベンチマーク結果サマリー更新")
    ]
    
    success_count = 0
    total_count = len(analysis_scripts)
    
    # 性能分析をスキップする場合は最初のスクリプトを除外
    if args.skip_analysis:
        analysis_scripts = analysis_scripts[1:]
        print("⏭️  性能分析をスキップします（既存の分析結果を使用）")
        print()
    
    for i, (script_name, description) in enumerate(analysis_scripts, 1):
        print(f"📊 [{i}/{len(analysis_scripts)}] {description}を実行中...")
        
        script_path = scripts_dir / script_name
        script_args = []
        
        # ベンチマーク結果ファイルが指定されている場合は引数として渡す
        if args.file and script_name == "run_performance_analysis.py":
            script_args = ['-f', args.file]
        
        if run_script(str(script_path), script_args):
            print(f"✅ {description}が完了しました")
            success_count += 1
        else:
            print(f"❌ {description}が失敗しました")
        
        print()
    
    # 結果サマリー
    print("=" * 60)
    print("包括的性能分析結果")
    print("=" * 60)
    print(f"実行スクリプト数: {len(analysis_scripts)}")
    print(f"成功: {success_count}")
    print(f"失敗: {len(analysis_scripts) - success_count}")
    print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == len(analysis_scripts):
        print()
        print("🎉 全ての分析が正常に完了しました！")
        print()
        print("📁 生成されたレポート:")
        
        reports = [
            "docs/language_characteristics_analysis.md",
            "docs/comprehensive_evaluation_report.md", 
            "docs/implementation_guide.md",
            "docs/benchmark_results_summary.md"
        ]
        
        for report in reports:
            if Path(report).exists():
                print(f"   ✓ {report}")
            else:
                print(f"   ✗ {report} (生成されませんでした)")
        
        print()
        print("📊 分析結果ファイル:")
        analysis_dir = project_root / "benchmark" / "results" / "analysis"
        if analysis_dir.exists():
            analysis_files = list(analysis_dir.glob("performance_analysis_*.json"))
            if analysis_files:
                latest_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
                print(f"   ✓ {latest_file.relative_to(project_root)}")
        
    else:
        print()
        print("⚠️  一部の分析が失敗しました。ログを確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main()