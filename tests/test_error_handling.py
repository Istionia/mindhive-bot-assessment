import pytest
from httpx import AsyncClient
from fastapi import status
from app import app, controller

async def raise_runtime_error(user, memory):
    # Simulate an unexpected crash in controller.run
    raise RuntimeError("something broke")

async def raise_value_error(user, memory):
    # Simulate a known, user-facing error
    raise ValueError("bad input")

@pytest.mark.anyio
async def test_unhandled_exception_results_in_500(monkeypatch):
    """
    When controller.run raises RuntimeError, FastAPI should return 500 Internal Server Error.
    Docs: https://fastapi.tiangolo.com/tutorial/handling-errors/
    """
    monkeypatch.setattr(controller, "run", raise_runtime_error)
    async with AsyncClient(app=app, base_url="http://test") as client:  # type: ignore
        resp = await client.post("/chat", json={"user": "alice", "content": "hi"})
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = resp.json()
    # Default error response contains a "detail" field
    assert "detail" in body
    assert body["detail"] == "Internal Server Error"


@pytest.mark.anyio
async def test_value_error_results_in_500_by_default(monkeypatch):
    """
    When controller.run raises ValueError and no custom handler is set,
    FastAPI treats it as an unhandled exception => 500.
    Pydantic vs HTTPException: for custom 400, wrap in HTTPException.
    """
    monkeypatch.setattr(controller, "run", raise_value_error)
    async with AsyncClient(app=app, base_url="http://test") as client: # type: ignore
        resp = await client.post("/chat", json={"user": "bob", "content": "hello"})
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = resp.json()
    assert "detail" in body