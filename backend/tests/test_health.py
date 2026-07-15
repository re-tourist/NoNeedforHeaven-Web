"""Contract tests for the engineering health endpoint."""

from fastapi.testclient import TestClient

from buxianxian import __version__
from buxianxian.api.app import HealthResponse, create_app


def test_health_endpoint_returns_valid_application_identity() -> None:
    response = TestClient(create_app()).get("/api/health")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    health = HealthResponse.model_validate_json(response.text)
    assert health.model_dump() == {
        "status": "ok",
        "app_id": "buxianxian",
        "app_name": "不羡仙",
        "version": __version__,
    }
