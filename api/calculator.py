from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import ast
import operator as op

router = APIRouter();

_SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg
}

def _safe_eval(node):
    """
    Recursively evaluate an AST node for numeric expressions,
    allowing only the operators in _SAFE_OPERATORS.
    """
    # 1. Literal numbers (Python ≥3.8 uses ast.Constant for numbers)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        else:
            raise ValueError(f"Constants of type {type(node.value)} are not supported")

    # 2. Numeric literals in older Python versions
    if isinstance(node, ast.Num):  # <number>
        return node.n

    # 3. Binary operations (e.g. 1 + 2, 3*4)
    if isinstance(node, ast.BinOp):
        left_val = _safe_eval(node.left)
        right_val = _safe_eval(node.right)
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[op_type](left_val, right_val)
        else:
            raise ValueError(f"Operator {op_type.__name__} is not supported")

    # 4. Unary operations (e.g. -5)
    if isinstance(node, ast.UnaryOp):
        operand_val = _safe_eval(node.operand)
        op_type = type(node.op)
        if op_type in _SAFE_OPERATORS:
            return _SAFE_OPERATORS[op_type](operand_val)
        else:
            raise ValueError(f"Unary operator {op_type.__name__} is not supported")

    # 5. Anything else is disallowed
    raise ValueError(f"Unsupported expression node: {node!r}")

class CalcResponse(BaseModel):
    expression: str = Field(..., description="The original expression")
    result: float = Field(..., description="Evaluated numeric result")

@router.get(
    "/calculate",
    response_model=CalcResponse,
    summary="Evaluate a simple arithmetic expression",
    description="Pass an `expression` query param like `2+2*3`. Returns the computed result."
)
async def calculate(
    expression: str = Query(..., description="Math expression to evaluate")
) -> CalcResponse:
    try:
        # 5.1 Parse into AST
        tree = ast.parse(expression, mode="eval")
        # 5.2 Evaluate safely
        result = _safe_eval(tree.body)
        # 5.3 Return structured response
        if isinstance(result, complex):
            raise ValueError("Complex numbers are not supported")
        return CalcResponse(expression=expression, result=float(result))
    except Exception as e:
        # On any parse or eval error, return HTTP 400
        raise HTTPException(status_code=400, detail=f"Invalid expression: {e}")

# (Later) In api/main.py you'll include this:
# app.include_router(calculator_router, prefix="/api", tags=["calculator"])


