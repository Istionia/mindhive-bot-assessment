import pytest
from fastapi import status
from httpx import AsyncClient

from app import app, controller

@pytest.fixture(autouse=True)
def mock_controller_run(monkeypatch):
    """
    Monkey-patch the controller.run method to return a predictable response
    so we can test the endpoint logic in isolation.
    """
    async def dummy_run(user, memory):
        return f"Hello, {user}!"
    monkeypatch.setattr(controller, "run", dummy_run)

@pytest.mark.anyio
async def test_chat_success():
    """
    When both 'user' and 'content' are provided,
    the endpoint should return 200 and the mocked greeting.
    """
    async with AsyncClient(app=app, base_url="http://test") as client: # type: ignore
        resp = await client.post("/chat", json={"user": "alice", "content": "Hi"})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "response" in body
    assert body["response"] == "Hello, alice!"

@pytest.mark.anyio
async def test_chat_missing_user_field():
    """
    Omitting the 'user' field should yield a 422 validation error.
    """
    async with AsyncClient(app=app, base_url="http://test") as client: # type: ignore
        resp = await client.post("/chat", json={"content": "Hi"})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.anyio
async def test_chat_missing_content_field():
    """
    Omitting the 'content' field should yield a 422 validation error.
    """
    async with AsyncClient(app=app, base_url="http://test") as client: # type: ignore
        resp = await client.post("/chat", json={"user": "alice"})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.anyio
async def test_chat_invalid_json():
    """
    Sending invalid JSON should yield a 422 error.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:  # type: ignore
        resp = await client.post(
            "/chat",
            data="not a json payload",  # type: ignore
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY