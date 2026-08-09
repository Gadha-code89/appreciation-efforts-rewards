"""
core/calculator.py - Safe AST Arithmetic Evaluator & Student Answer Sanitizer
"""

import ast
import re
import operator
from typing import Union, Tuple

# Supported AST operators for safe evaluation
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval_ast(node: ast.AST) -> Union[int, float]:
    """
    Safely evaluate an AST node containing only numbers and allowed arithmetic operators.
    """
    if isinstance(node, ast.Expression):
        return safe_eval_ast(node.body)
    elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = safe_eval_ast(node.left)
        right = safe_eval_ast(node.right)
        op_type = type(node.op)
        if op_type in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
    elif isinstance(node, ast.UnaryOp):
        operand = safe_eval_ast(node.operand)
        op_type = type(node.op)
        if op_type in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
    else:
        raise ValueError(f"Unsupported AST node type: {type(node).__name__}")


def verify_arithmetic(expression: str) -> float:
    """
    Evaluator Agent tool to safely verify math expression results.
    E.g., "19 + 28" -> 47.0
    """
    clean_expr = expression.strip()
    if not clean_expr:
        raise ValueError("Empty arithmetic expression.")
    
    parsed = ast.parse(clean_expr, mode='eval')
    result = safe_eval_ast(parsed)
    return float(result)


def sanitize_and_evaluate_answer(raw_input: str, expected: float, tolerance: float = 1e-4) -> Tuple[bool, float]:
    """
    Sanitize student answer input string and check against expected value.
    Handles extra spaces, trailing text ("47.0", " 47 ", "47 apples").
    
    Returns: (is_correct: bool, parsed_value: float)
    """
    if not raw_input:
        return False, 0.0

    # Extract first signed integer or decimal number from raw_input string
    match = re.search(r'[-+]?\d*\.?\d+', str(raw_input).strip())
    if not match:
        return False, 0.0

    try:
        parsed_val = float(match.group(0))
        is_correct = abs(parsed_val - expected) < tolerance
        return is_correct, parsed_val
    except ValueError:
        return False, 0.0
