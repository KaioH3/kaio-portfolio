"""
Basic tests for FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home_page():
    """Test home page loads"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Kaio H. Siqueira" in response.text


def test_health_check():
    """Test health endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_readiness_check():
    """Test readiness endpoint"""
    response = client.get("/api/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
