"""エラーハンドリングモジュール

実装モジュールのインポートエラーと実行時エラーを処理し、
エラー情報を記録しながら他の実装の実行を継続する。
"""

import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from types import ModuleType


@dataclass
class ErrorLog:
    """エラーログ"""
    timestamp: datetime
    implementation_name: str
    scenario_name: str
    error_type: str
    error_message: str
    stack_trace: Optional[str]


class ErrorHandler:
    """エラーハンドリングクラス"""
    
    def __init__(self):
        """初期化"""
        self.error_logs: List[ErrorLog] = []
    
    def handle_import_error(
        self,
        implementation_name: str,
        error: Exception
    ) -> ErrorLog:
        """インポートエラーを処理
        
        Args:
            implementation_name: 実装モジュール名
            error: 発生した例外
            
        Returns:
            ErrorLog: エラーログ
        """
        error_log = ErrorLog(
            timestamp=datetime.now(),
            implementation_name=implementation_name,
            scenario_name="N/A",
            error_type="ImportError",
            error_message=str(error),
            stack_trace=traceback.format_exc()
        )
        
        self.error_logs.append(error_log)
        
        # 実装別の詳細なエラーメッセージ
        language_hints = {
            "julia_ext": "Julia environment may not be properly set up. Check Julia installation and PyCall.jl.",
            "go_ext": "Go shared library may not be built. Run 'make' in benchmark/go_ext/.",
            "zig_ext": "Zig shared library may not be built. Run 'zig build' in benchmark/zig_ext/.",
            "nim_ext": "Nim extension may not be compiled. Check nimpy installation and compilation.",
            "kotlin_ext": "Kotlin/Native library may not be built. Run 'gradle build' in benchmark/kotlin_ext/.",
            "rust_ext": "Rust extension may not be compiled. Run 'maturin develop' in benchmark/rust_ext/.",
            "fortran_ext": "Fortran extension may not be compiled. Check gfortran installation.",
            "cython_ext": "Cython extension may not be compiled. Run build_cython.py script.",
            "cpp_ext": "C++ extension may not be compiled. Check CMake build process.",
            "c_ext": "C extension may not be compiled. Run 'python setup.py build_ext --inplace'."
        }
        
        hint = language_hints.get(implementation_name, "Check implementation setup and dependencies.")
        
        # ユーザーへの通知
        print(f"⚠️  Warning: Failed to import implementation '{implementation_name}'")
        print(f"   Error: {error}")
        print(f"   Hint: {hint}")
        print(f"   This implementation will be skipped.\n")
        
        return error_log
    
    def handle_execution_error(
        self,
        implementation_name: str,
        scenario_name: str,
        error: Exception
    ) -> ErrorLog:
        """実行時エラーを処理
        
        Args:
            implementation_name: 実装モジュール名
            scenario_name: シナリオ名
            error: 発生した例外
            
        Returns:
            ErrorLog: エラーログ
        """
        error_log = ErrorLog(
            timestamp=datetime.now(),
            implementation_name=implementation_name,
            scenario_name=scenario_name,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc()
        )
        
        self.error_logs.append(error_log)
        
        # ユーザーへの通知
        print(f"⚠️  Warning: Error in implementation '{implementation_name}' "
              f"for scenario '{scenario_name}'")
        print(f"   Error: {error}")
        print(f"   Other implementations will continue.\n")
        
        return error_log
    
    def safe_import_module(
        self,
        module_name: str,
        implementation_name: str
    ) -> Optional[ModuleType]:
        """モジュールを安全にインポート
        
        Args:
            module_name: インポートするモジュール名
            implementation_name: 実装名（エラーログ用）
            
        Returns:
            Optional[ModuleType]: インポートされたモジュール、失敗時はNone
        """
        try:
            module = __import__(module_name, fromlist=[''])
            return module
        except ImportError as e:
            self.handle_import_error(implementation_name, e)
            return None
        except Exception as e:
            self.handle_import_error(implementation_name, e)
            return None
    
    def get_error_summary(self) -> str:
        """エラーサマリーを取得
        
        Returns:
            str: エラーサマリー文字列
        """
        if not self.error_logs:
            return "No errors occurred."
        
        summary = f"\n{'='*60}\n"
        summary += f"Error Summary: {len(self.error_logs)} error(s) occurred\n"
        summary += f"{'='*60}\n\n"
        
        for i, log in enumerate(self.error_logs, 1):
            summary += f"{i}. [{log.error_type}] {log.implementation_name}"
            if log.scenario_name != "N/A":
                summary += f" - {log.scenario_name}"
            summary += f"\n   {log.error_message}\n"
            summary += f"   Time: {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        return summary
    
    def print_error_summary(self) -> None:
        """エラーサマリーを出力"""
        print(self.get_error_summary())
    
    def get_implementation_statistics(self) -> dict:
        """実装別の統計情報を取得
        
        Returns:
            dict: 実装別のエラー統計
        """
        stats = {}
        for log in self.error_logs:
            impl = log.implementation_name
            if impl not in stats:
                stats[impl] = {
                    'import_errors': 0,
                    'execution_errors': 0,
                    'total_errors': 0
                }
            
            if log.error_type == "ImportError":
                stats[impl]['import_errors'] += 1
            else:
                stats[impl]['execution_errors'] += 1
            stats[impl]['total_errors'] += 1
        
        return stats

    def has_errors(self) -> bool:
        """エラーが発生したかどうか
        
        Returns:
            bool: エラーが発生した場合True
        """
        return len(self.error_logs) > 0
