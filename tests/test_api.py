"""Tests for API application."""

from fastapi import APIRouter
from fastapi.testclient import TestClient

from src.api.app import create_api_app
from src.utils.config import Settings
from src.utils.exceptions import ValidationError


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


def test_ready_endpoint() -> None:
    settings = Settings()
    app = create_api_app(settings)

    client = TestClient(app)
    response = client.get("/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["app"] == settings.app.name


def test_ready_endpoint_reports_ready_after_startup() -> None:
    settings = Settings()
    app = create_api_app(settings)

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["app"] == settings.app.name


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


def test_docs_disabled_when_configured() -> None:
    settings = Settings(api={"docs_enabled": False})
    app = create_api_app(settings)

    client = TestClient(app)

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_request_id_header_is_returned() -> None:
    settings = Settings()
    app = create_api_app(settings)

    client = TestClient(app)
    response = client.get("/health", headers={"X-Request-ID": "req-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"


def test_app_exception_returns_structured_error() -> None:
    settings = Settings()
    app = create_api_app(settings)
    router = APIRouter()

    @router.get("/test-error")
    async def test_error() -> None:
        raise ValidationError("boom")

    app.include_router(router)
    client = TestClient(app)
    response = client.get("/test-error", headers={"X-Request-ID": "req-err"})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "boom",
        "code": "validation_error",
        "request_id": "req-err",
    }
