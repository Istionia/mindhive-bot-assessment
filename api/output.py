from typing import Any, List, Dict

def format_outlets_response(records: List[Dict[str, Any]], summary: str | None) -> Dict[str, Any]:
    """
    Standardize the JSON structure for outlets responses.
    """
    return {
        "count": len(records),
        "summary": summary,
        "outlets": records,
    }

def format_products_response(query: str, matches: List[Dict[str, Any]], answer: str) -> Dict[str, Any]:
    """
    Standardize the JSON structure for product RAG responses.
    """
    return {
        "query": query,
        "hits": matches,
        "answer": answer,
    }
