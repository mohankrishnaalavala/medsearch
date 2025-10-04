"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_health_endpoint() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "services" in data


def test_create_search() -> None:
    """Test creating a search request."""
    search_data = {
        "query": "What are the latest treatments for Type 2 diabetes?",
        "filters": {
            "date_range": {
                "start": "2020-01-01",
                "end": "2024-12-31"
            }
        }
    }

    response = client.post("/api/v1/search", json=search_data)
    assert response.status_code == 200
    data = response.json()
    assert "search_id" in data
    assert data["status"] == "processing"
    assert "estimated_time" in data


def test_create_search_invalid_query() -> None:
    """Test creating search with invalid query."""
    search_data = {
        "query": "",  # Empty query
    }

    response = client.post("/api/v1/search", json=search_data)
    assert response.status_code == 422  # Validation error


def test_create_conversation() -> None:
    """Test creating a conversation."""
    conversation_data = {
        "user_id": "test_user",
        "title": "Test Conversation"
    }

    response = client.post("/api/v1/conversations", json=conversation_data)
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["user_id"] == "test_user"
    assert data["title"] == "Test Conversation"


def test_get_conversation() -> None:
    """Test getting a conversation."""
    # First create a conversation
    conversation_data = {
        "user_id": "test_user",
        "title": "Test Conversation"
    }

    create_response = client.post("/api/v1/conversations", json=conversation_data)
    conversation_id = create_response.json()["conversation_id"]

    # Then get it
    response = client.get(f"/api/v1/conversations/{conversation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == conversation_id


def test_get_nonexistent_conversation() -> None:
    """Test getting a nonexistent conversation."""
    response = client.get("/api/v1/conversations/nonexistent")
    assert response.status_code == 404


def test_get_user_conversations() -> None:
    """Test getting user conversations."""
    user_id = "test_user_123"

    # Create a few conversations
    for i in range(3):
        conversation_data = {
            "user_id": user_id,
            "title": f"Conversation {i}"
        }
        client.post("/api/v1/conversations", json=conversation_data)

    # Get user conversations
    response = client.get(f"/api/v1/users/{user_id}/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_docs_available() -> None:
    """Test that API docs are available."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_available() -> None:
    """Test that ReDoc is available."""
    response = client.get("/redoc")
    assert response.status_code == 200

