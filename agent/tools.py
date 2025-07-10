import os
import ast
import operator as op
import requests
from typing import Dict, Any

# Supported operators for safe evaluation
_SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}

def _safe_eval(node):
    """
    Recursively evaluate an AST node containing a numeric expression.
    Only allows safe operators defined in _SAFE_OPERATORS.
    """
    if isinstance(node, ast.Num):  # <number>
        return node.n
    if isinstance(node, ast.BinOp):  # <left> <operator> <right>
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op_func = _SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Operator {node.op} not supported")
        return op_func(left, right)
    if isinstance(node, ast.UnaryOp):  # - <operand>
        operand = _safe_eval(node.operand)
        op_func = _SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unary operator {node.op} not supported")
        return op_func(operand)
    raise ValueError(f"Unsupported expression: {node}")

class CalculatorTool:
    """
    Simple calculator tool for arithmetic expressions.
    Uses a safe AST-based evaluator to prevent code injection.
    """
    def __init__(self):
        pass

    def evaluate(self, expression: str) -> Any:
        """
        Evaluate a mathematical expression string safely.
        Returns the numeric result or raises ValueError on invalid input.
        """
        try:
            # Parse expression into AST
            tree = ast.parse(expression, mode='eval')
            return _safe_eval(tree.body)
        except Exception as e:
            raise ValueError(f"Error evaluating expression '{expression}': {e}")

class OutletTool:
    """
    Wrapper for querying the ZUS outlets Text2SQL FastAPI endpoint.

    Expects the API to be hosted at OUTLET_API_BASE (env var or default localhost).
    """
    def __init__(self):
        # Base URL for outlet queries
        self.base_url = os.getenv('OUTLET_API_BASE', 'http://localhost:8000')

    def query(self, slots: Dict[str, Any], intent: str) -> str:
        """
        Build a natural language query based on slots and intent, send to /outlets endpoint,
        and parse the response into a user-friendly string.
        """
        # Construct the user NL query
        if intent == 'find_outlet':
            # Look for outlets by location
            locator = slots.get('location') or slots.get('outlet')
            nl_query = f"Show me outlets in {locator}"
        elif intent == 'get_opening_hours':
            outlet = slots.get('outlet')
            location = slots.get('location')
            if outlet and location:
                nl_query = f"What are the opening hours for {outlet} in {location}?"
            elif outlet:
                nl_query = f"What are the opening hours for {outlet}?"
            else:
                nl_query = f"What are the opening hours?"
        else:
            nl_query = 'Show me all outlets.'

        # Call the FastAPI endpoint
        try:
            resp = requests.get(
                f"{self.base_url}/outlets", params={"query": nl_query}, timeout=5
            )
            resp.raise_for_status()
            data = resp.json()
            # Assume the API returns {'results': [...], 'summary': '...'}
            summary = data.get('summary')
            results = data.get('results', [])
            # Format results into a string
            if summary:
                return summary
            if results:
                lines = [f"- {r}" for r in results]
                return "Here are the outlets I found:\n" + "\n".join(lines)
            return "No outlets found matching your query."
        except requests.RequestException as e:
            return f"Sorry, I couldn't reach the outlets service: {e}"
        
def generate_sql(query: str) -> str:
    """
    Calls LLaMA 3 via OpenRouter to convert a user query into SQL.
    """
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        raise EnvironmentError("Missing OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    schema = """
    Table: outlets
    Columns:
    - id: INTEGER
    - name: TEXT
    - location: TEXT
    - address: TEXT
    - opening_time: TEXT (HH:MM)
    - closing_time: TEXT (HH:MM)
    - dine_in: BOOLEAN
    - delivery: BOOLEAN
    - pickup: BOOLEAN
    """

    system_prompt = "You are a helpful SQL generator that only returns valid SQLite SELECT queries. Do not explain."

    user_prompt = f"""
    Given this table schema:

    {schema}

    Convert this user query into a valid SQLite SELECT statement:
    "{query}"
    """

    body = {
        "model": "meta-llama/llama-3.3-70b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
        response.raise_for_status()
        sql = response.json()["choices"][0]["message"]["content"]
        return sql.strip().split("```")[0]  # if model wraps output in code block
    except Exception as e:
        raise RuntimeError(f"Failed to generate SQL: {e}")
