import asyncio

import pytest
from fastapi.testclient import TestClient

from app import main, providers
from app.main import app


def test_missing_api_key_is_reported_clearly(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(providers.AIProviderError, match="OPENAI_API_KEY"):
        asyncio.run(providers.generate_chat_reply("Hello", []))


def test_openai_provider_sends_history(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    request = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "A real answer"}}]}

    class FakeClient:
        def __init__(self, timeout):
            assert timeout == 60

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers, json):
            request.update(url=url, headers=headers, payload=json)
            return FakeResponse()

    monkeypatch.setattr(providers.httpx, "AsyncClient", FakeClient)
    reply, provider = asyncio.run(
        providers.generate_chat_reply(
            "What was my previous question?",
            [{"role": "user", "content": "What is Python?"}],
        )
    )

    assert reply == "A real answer"
    assert provider == "openai"
    assert request["headers"]["Authorization"] == "Bearer test-key"
    assert request["payload"]["messages"][-2]["content"] == "What is Python?"
    assert (
        request["payload"]["messages"][-1]["content"]
        == "What was my previous question?"
    )


def test_chat_flow_supports_requested_questions_and_follow_up(monkeypatch):
    calls = []

    async def fake_generate_chat_reply(message, history):
        calls.append({"message": message, "history": history})
        if message == "What was my previous question?":
            previous = history[-2]["content"]
            return f"Your previous question was: {previous}", "openai"
        return f"Answer to: {message}", "openai"

    monkeypatch.setattr(main, "generate_chat_reply", fake_generate_chat_reply)
    client = TestClient(app)
    questions = [
        "Hi, what is your name?",
        "What is Python?",
        "Write a Python program to reverse a string.",
        "Explain OOP in simple English.",
        "What was my previous question?",
    ]
    conversation_id = None

    for question in questions:
        response = client.post(
            "/chat",
            json={"message": question, "conversation_id": conversation_id},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["response"]
        assert payload["conversation_id"]
        conversation_id = payload["conversation_id"]

    assert "Explain OOP in simple English." in response.json()["response"]
    assert len(calls) == len(questions)
    assert len(calls[-1]["history"]) == 8


def test_chat_returns_provider_errors_as_json(monkeypatch):
    async def failing_generate_chat_reply(message, history):
        raise providers.AIProviderError("The AI provider is unavailable.")

    monkeypatch.setattr(main, "generate_chat_reply", failing_generate_chat_reply)
    response = TestClient(app).post("/chat", json={"message": "Hello"})

    assert response.status_code == 502
    assert response.json() == {"detail": "The AI provider is unavailable."}
