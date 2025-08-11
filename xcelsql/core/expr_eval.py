"""Expression evaluation engine for template transformations."""
from __future__ import annotations
import re
import ast
import operator
from typing import Any, Dict, List, Optional, Tuple, Callable, Union

# Registry for custom functions
_CUSTOM_FUNCTIONS: Dict[str, Callable] = {}
_ALLOW_EVAL_FALLBACK = False

def set_eval_fallback(allow: bool) -> None:
    """Set whether Python eval() fallback is allowed."""
    global _ALLOW_EVAL_FALLBACK
    _ALLOW_EVAL_FALLBACK = allow

def register_custom_function(name: str, func: Callable) -> None:
    """Register a custom function for use in expressions."""
    _CUSTOM_FUNCTIONS[name] = func

def list_registered_functions() -> List[Tuple[str, str]]:
    """Return list of (name, docstring) for registered functions."""
    return [(name, func.__doc__ or '') for name, func in _CUSTOM_FUNCTIONS.items()]

class SafeEval:
    """Safely evaluate expressions with limited functionality."""
    
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: lambda x, y: x and y,
        ast.Or: lambda x, y: x or y,
        ast.Not: operator.not_,
    }

    def __init__(self):
        self.variables: Dict[str, Any] = {}
    
    def eval(self, expr: str, variables: Dict[str, Any]) -> Any:
        """Evaluate an expression with the given variables."""
        self.variables = {**variables, **_CUSTOM_FUNCTIONS}
        try:
            node = ast.parse(expr, mode='eval').body
            return self._eval_node(node)
        except Exception as e:
            if _ALLOW_EVAL_FALLBACK:
                try:
                    # Fallback to Python's eval() if allowed
                    return eval(expr, {"__builtins__": {}}, {**variables, **_CUSTOM_FUNCTIONS})
                except Exception as e2:
                    raise ValueError(f"Failed to evaluate expression: {e} (fallback: {e2})")
            raise ValueError(f"Failed to evaluate expression: {e}")
    
    def _eval_node(self, node: ast.AST) -> Any:
        """Recursively evaluate an AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            raise NameError(f"Name '{node.id}' is not defined")
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in self.OPERATORS:
                return self.OPERATORS[op_type](self._eval_node(node.left), self._eval_node(node.right))
            raise TypeError(f"Unsupported binary operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in self.OPERATORS:
                return self.OPERATORS[op_type](self._eval_node(node.operand))
            raise TypeError(f"Unsupported unary operator: {op_type.__name__}")
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            for op, comp in zip(node.ops, node.comparators):
                op_type = type(op)
                if op_type not in self.OPERATORS:
                    raise TypeError(f"Unsupported comparison operator: {op_type.__name__}")
                right = self._eval_node(comp)
                if not self.OPERATORS[op_type](left, right):
                    return False
                left = right
            return True
        elif isinstance(node, ast.BoolOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                raise TypeError(f"Unsupported boolean operator: {op_type.__name__}")
            if op_type == ast.And:
                for value in node.values:
                    result = self._eval_node(value)
                    if not result:
                        return False
                return True
            else:  # Or
                for value in node.values:
                    result = self._eval_node(value)
                    if result:
                        return True
                return False
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if not func_name or func_name not in self.variables:
                raise NameError(f"Function '{func_name}' is not defined")
            args = [self._eval_node(arg) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}
            return self.variables[func_name](*args, **kwargs)
        elif isinstance(node, ast.IfExp):  # Ternary operator
            condition = self._eval_node(node.test)
            return self._eval_node(node.body) if condition else self._eval_node(node.orelse)
        elif isinstance(node, ast.List):
            return [self._eval_node(elt) for elt in node.elts]
        elif isinstance(node, ast.Dict):
            keys = [self._eval_node(key) for key in node.keys]
            values = [self._eval_node(value) for value in node.values]
            return dict(zip(keys, values))
        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value)
            if isinstance(node.slice, ast.Index):  # Python 3.8 and earlier
                idx = self._eval_node(node.slice.value)
            else:  # Python 3.9+
                idx = self._eval_node(node.slice)
            return value[idx]
        elif isinstance(node, ast.Attribute):
            value = self._eval_node(node.value)
            return getattr(value, node.attr)
        else:
            raise TypeError(f"Unsupported node type: {type(node).__name__}")

def evaluate_expression(expr: str, row_data: Dict[str, Any], strict: bool = False) -> Any:
    """Evaluate an expression using row data."""
    evaluator = SafeEval()
    try:
        return evaluator.eval(expr, row_data)
    except Exception as e:
        if strict:
            raise ValueError(f"Expression evaluation error: {e}")
        return f"[Error: {e}]"