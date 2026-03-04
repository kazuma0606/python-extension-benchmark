"""プロパティベーステスト: 出力値検証モジュール

出力値の比較実行、不一致時の警告出力、検証結果の包含を検証する。
"""

import pytest
from hypothesis import given, strategies as st
from io import StringIO
import sys

from benchmark.runner.validator import OutputValidator
from benchmark.models import ValidationResult


# カスタム戦略: 実装名と出力値の辞書を生成
@st.composite
def outputs_dict_strategy(draw, num_implementations=None):
    """実装名と出力値の辞書を生成する戦略"""
    if num_implementations is None:
        num_implementations = draw(st.integers(min_value=2, max_value=5))
    
    impl_names = [f"impl_{i}" for i in range(num_implementations)]
    
    # 出力値の型を選択
    output_type = draw(st.sampled_from(['float', 'int', 'list_float', 'list_int']))
    
    outputs = {}
    if output_type == 'float':
        base_value = draw(st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
        for name in impl_names:
            outputs[name] = base_value
    elif output_type == 'int':
        base_value = draw(st.integers(min_value=-1000, max_value=1000))
        for name in impl_names:
            outputs[name] = base_value
    elif output_type == 'list_float':
        size = draw(st.integers(min_value=1, max_value=10))
        base_list = draw(st.lists(
            st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=size,
            max_size=size
        ))
        for name in impl_names:
            outputs[name] = base_list.copy()
    elif output_type == 'list_int':
        size = draw(st.integers(min_value=1, max_value=10))
        base_list = draw(st.lists(st.integers(min_value=-100, max_value=100), min_size=size, max_size=size))
        for name in impl_names:
            outputs[name] = base_list.copy()
    
    return outputs


@given(outputs_dict_strategy())
def test_property_15_output_comparison_execution(outputs):
    """Feature: python-extension-benchmark, Property 15: 出力値の比較実行
    
    **検証: 要件 9.1**
    
    任意の実装モジュールのリストと入力データに対して、全ての実装モジュールの出力値が
    比較され、検証結果が生成されなければならない
    """
    # 検証を実行
    result = OutputValidator.validate(outputs)
    
    # 検証結果が生成されることを確認
    assert isinstance(result, ValidationResult)
    assert isinstance(result.is_valid, bool)
    assert isinstance(result.max_relative_error, float)
    assert isinstance(result.mismatches, list)
    
    # 全ての実装が同じ出力値を持つ場合、検証は成功するべき
    assert result.is_valid == True
    assert result.max_relative_error < 1e-4
    assert len(result.mismatches) == 0


@st.composite
def mismatched_outputs_strategy(draw):
    """不一致のある出力値の辞書を生成する戦略"""
    num_implementations = draw(st.integers(min_value=2, max_value=5))
    impl_names = [f"impl_{i}" for i in range(num_implementations)]
    
    # 基準値を生成
    base_value = draw(st.floats(min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False))
    
    outputs = {}
    outputs[impl_names[0]] = base_value
    
    # 少なくとも1つの実装に不一致を作る
    for i, name in enumerate(impl_names[1:], 1):
        if i == 1:
            # 最初の実装は必ず不一致にする（相対誤差 > 0.0001）
            # 相対誤差が0.0001を超えるように値を変更
            error_factor = draw(st.floats(min_value=0.001, max_value=0.1))
            outputs[name] = base_value * (1.0 + error_factor)
        else:
            # 他の実装はランダムに一致/不一致
            match = draw(st.booleans())
            if match:
                outputs[name] = base_value
            else:
                error_factor = draw(st.floats(min_value=0.001, max_value=0.1))
                outputs[name] = base_value * (1.0 + error_factor)
    
    return outputs


@given(mismatched_outputs_strategy())
def test_property_17_warning_on_mismatch(outputs):
    """Feature: python-extension-benchmark, Property 17: 不一致時の警告出力
    
    **検証: 要件 9.3**
    
    任意の検証結果に対して、出力値が一致しない実装が存在する場合、
    警告メッセージが出力され、不一致の詳細が記録されなければならない
    """
    # 標準出力をキャプチャ
    captured_output = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        # 検証を実行
        result = OutputValidator.validate(outputs, tolerance=1e-4)
        
        # 標準出力を復元
        sys.stdout = old_stdout
        output_text = captured_output.getvalue()
        
        # 不一致がある場合、警告メッセージが出力されるべき
        if not result.is_valid:
            assert "WARNING" in output_text
            assert "mismatch" in output_text.lower()
            assert len(result.mismatches) > 0
            
            # 不一致の詳細が記録されているべき
            for mismatch_impl in result.mismatches:
                # 不一致した実装名が出力に含まれるべき
                assert mismatch_impl in output_text or "impl_" in output_text
    finally:
        sys.stdout = old_stdout


@given(outputs_dict_strategy())
def test_property_18_validation_result_inclusion(outputs):
    """Feature: python-extension-benchmark, Property 18: 検証結果の包含
    
    **検証: 要件 9.4**
    
    任意のベンチマーク結果に対して、出力値の検証結果（is_valid、max_relative_error、
    mismatches）が含まれなければならない
    """
    # 検証を実行
    result = OutputValidator.validate(outputs)
    
    # ValidationResultが必要なフィールドを全て持つことを確認
    assert hasattr(result, 'is_valid')
    assert hasattr(result, 'max_relative_error')
    assert hasattr(result, 'mismatches')
    
    # フィールドの型が正しいことを確認
    assert isinstance(result.is_valid, bool)
    assert isinstance(result.max_relative_error, float)
    assert isinstance(result.mismatches, list)
    
    # max_relative_errorは非負であるべき
    assert result.max_relative_error >= 0.0
    
    # mismatchesの各要素は文字列であるべき
    for mismatch in result.mismatches:
        assert isinstance(mismatch, str)


# エッジケースのテスト
def test_empty_outputs():
    """空の出力辞書の場合"""
    result = OutputValidator.validate({})
    assert result.is_valid == True
    assert result.max_relative_error == 0.0
    assert len(result.mismatches) == 0


def test_single_output():
    """1つだけの出力の場合"""
    outputs = {"impl_0": 42.0}
    result = OutputValidator.validate(outputs)
    assert result.is_valid == True
    assert result.max_relative_error == 0.0
    assert len(result.mismatches) == 0


def test_exact_match():
    """完全に一致する出力の場合"""
    outputs = {
        "python": 100.0,
        "numpy": 100.0,
        "cython": 100.0
    }
    result = OutputValidator.validate(outputs)
    assert result.is_valid == True
    assert result.max_relative_error == 0.0
    assert len(result.mismatches) == 0


def test_within_tolerance():
    """許容範囲内の誤差がある場合"""
    outputs = {
        "python": 100.0,
        "numpy": 100.00005,  # 相対誤差 5e-7 < 1e-4
    }
    result = OutputValidator.validate(outputs, tolerance=1e-4)
    assert result.is_valid == True
    assert result.max_relative_error < 1e-4


def test_exceeds_tolerance():
    """許容範囲を超える誤差がある場合"""
    outputs = {
        "python": 100.0,
        "numpy": 100.02,  # 相対誤差 2e-4 > 1e-4
    }
    
    # 標準出力をキャプチャ
    captured_output = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        result = OutputValidator.validate(outputs, tolerance=1e-4)
        sys.stdout = old_stdout
        output_text = captured_output.getvalue()
        
        assert result.is_valid == False
        assert result.max_relative_error > 1e-4
        assert "numpy" in result.mismatches
        assert "WARNING" in output_text
    finally:
        sys.stdout = old_stdout


def test_list_outputs():
    """リスト出力の比較"""
    outputs = {
        "python": [1, 2, 3, 4, 5],
        "numpy": [1, 2, 3, 4, 5],
    }
    result = OutputValidator.validate(outputs)
    assert result.is_valid == True


def test_list_outputs_mismatch():
    """リスト出力の不一致"""
    outputs = {
        "python": [1, 2, 3, 4, 5],
        "numpy": [1, 2, 3, 4, 6],  # 最後の要素が異なる
    }
    
    captured_output = StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        result = OutputValidator.validate(outputs)
        sys.stdout = old_stdout
        
        assert result.is_valid == False
        assert "numpy" in result.mismatches
    finally:
        sys.stdout = old_stdout
