"""Tests for main application."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint() -> None:
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_docs_available() -> None:
    """Test that API docs are available."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_available() -> None:
    """Test that ReDoc is available."""
    response = client.get("/redoc")
    assert response.status_code == 200

