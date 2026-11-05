import pytest
from fastapi.testclient import TestClient

from app.core.quota import get_quota_manager
from app.main import app


def test_models_endpoint_supports_mistral_and_qwen():
    with TestClient(app) as client:
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert "supported" in data
        supported = data["supported"]
        assert "mistralai/Mistral-7B-Instruct-v0.3" in supported
        assert "Qwen/Qwen2.5-7B-Instruct" in supported


def test_quota_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/quota")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert "remaining" in data
        assert "used_today" in data


def test_chat_lifecycle_and_streaming():
    with TestClient(app) as client:
        # Reset quota for clean test
        get_quota_manager().reset_today()

        # 1. Create a conversation
        create_resp = client.post(
            "/api/v1/chat/conversations",
            json={"title": "RAG and Mistral Session"},
            headers={"X-User-Id": "test-user"},
        )
        assert create_resp.status_code == 201
        conv = create_resp.json()
        conv_id = conv["id"]

        # 2. Stream message
        stream_resp = client.post(
            f"/api/v1/chat/conversations/{conv_id}/stream",
            json={"message": "Explain local LLM execution", "use_rag": False, "use_memory": False},
            headers={"X-User-Id": "test-user"},
        )
        assert stream_resp.status_code == 200
        body = stream_resp.text
        assert "event: citations" in body
        assert "event: token" in body
        assert "event: done" in body
