"""Tests for API application."""

from fastapi.testclient import TestClient

from src.api.app import create_api_app
from src.utils.config import Settings


def test_health_endpoint() -> None:
    settings = Settings()
    app = create_api_app(settings)

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == settings.app.name
    assert payload["version"] == settings.app.version


def test_create_job_endpoint() -> None:
    settings = Settings()
    app = create_api_app(settings)

    client = TestClient(app)
    response = client.post("/jobs", json={"name": "demo"})

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "demo"
    assert payload["status"] == "queued"
    assert "job_id" in payload
