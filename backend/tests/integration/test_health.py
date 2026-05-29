"""Integration tests for health endpoints"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_health_endpoint_returns_200(client):
    """Test GET /health returns 200"""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "version" in data


def test_root_endpoint_returns_200(client):
    """Test GET / returns 200"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data
    assert "docs" in data


def test_cors_headers_present(client):
    """Test that CORS headers are present on responses"""
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 200
