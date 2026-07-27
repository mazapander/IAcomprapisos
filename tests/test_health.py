from fastapi.testclient import TestClient
from app.main import app

def test_health() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_is_served() -> None:
    response = TestClient(app).get("/")
    assert response.status_code == 200
    assert "IA Compra Pisos" in response.text
