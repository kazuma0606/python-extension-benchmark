"""出力値検証モジュール

各実装モジュールの出力値が一致することを検証する。
"""

from typing import Dict, Any, List
from benchmark.models import ValidationResult


class OutputValidator:
    """出力値検証クラス"""
    
    @staticmethod
    def validate(
        outputs: Dict[str, Any],
        tolerance: float = 1e-4
    ) -> ValidationResult:
        """全実装の出力値を比較し、相対誤差が許容範囲内か検証
        
        Args:
            outputs: 実装名をキー、出力値を値とする辞書
            tolerance: 許容相対誤差（デフォルト: 0.0001）
            
        Returns:
            ValidationResult: 検証結果
        """
        if not outputs:
            return ValidationResult(
                is_valid=True,
                max_relative_error=0.0,
                mismatches=[]
            )
        
        # 実装名のリストを取得
        impl_names = list(outputs.keys())
        
        if len(impl_names) < 2:
            # 比較対象が1つ以下の場合は検証不要
            return ValidationResult(
                is_valid=True,
                max_relative_error=0.0,
                mismatches=[]
            )
        
        # 基準となる実装（最初の実装）の出力値を取得
        reference_name = impl_names[0]
        reference_output = outputs[reference_name]
        
        max_relative_error = 0.0
        mismatches = []
        
        # 他の全ての実装と比較
        for impl_name in impl_names[1:]:
            output = outputs[impl_name]
            
            # 出力値を比較
            is_match, rel_error = OutputValidator._compare_outputs(
                reference_output,
                output,
                tolerance
            )
            
            if rel_error > max_relative_error:
                max_relative_error = rel_error
            
            if not is_match:
                mismatches.append(impl_name)
                # 警告メッセージを出力
                print(f"WARNING: Output mismatch detected!")
                print(f"  Reference: {reference_name}")
                print(f"  Mismatch: {impl_name}")
                print(f"  Relative error: {rel_error:.6e}")
                print(f"  Tolerance: {tolerance:.6e}")
        
        is_valid = len(mismatches) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            max_relative_error=max_relative_error,
            mismatches=mismatches
        )
    
    @staticmethod
    def _compare_outputs(
        output1: Any,
        output2: Any,
        tolerance: float
    ) -> tuple[bool, float]:
        """2つの出力値を比較
        
        Args:
            output1: 1つ目の出力値
            output2: 2つ目の出力値
            tolerance: 許容相対誤差
            
        Returns:
            tuple[bool, float]: (一致するか, 最大相対誤差)
        """
        # 型が異なる場合は不一致
        if type(output1) != type(output2):
            return False, float('inf')
        
        # 数値の場合
        if isinstance(output1, (int, float)):
            rel_error = OutputValidator._calculate_relative_error(
                float(output1),
                float(output2)
            )
            return rel_error < tolerance, rel_error
        
        # リストの場合
        if isinstance(output1, list):
            if len(output1) != len(output2):
                return False, float('inf')
            
            max_error = 0.0
            for v1, v2 in zip(output1, output2):
                is_match, error = OutputValidator._compare_outputs(
                    v1, v2, tolerance
                )
                if not is_match:
                    return False, error
                if error > max_error:
                    max_error = error
            
            return True, max_error
        
        # その他の型は等価性で比較
        return output1 == output2, 0.0
    
    @staticmethod
    def _calculate_relative_error(a: float, b: float) -> float:
        """相対誤差を計算
        
        Args:
            a: 1つ目の値
            b: 2つ目の値
            
        Returns:
            float: 相対誤差 |a - b| / max(|a|, |b|)
        """
        if a == 0.0 and b == 0.0:
            return 0.0
        
        denominator = max(abs(a), abs(b))
        if denominator == 0.0:
            return 0.0
        
        return abs(a - b) / denominator
