from fastapi.testclient import TestClient

from app.db.models import ProductVisitor
from app.db.session import get_session
from app.main import app


class FakeSession:
    def __init__(self):
        self.visitors = {}
        self.added = []

    async def get(self, model, identifier):
        if model is ProductVisitor:
            return self.visitors.get(identifier)
        return None

    def add(self, value):
        self.added.append(value)
        if isinstance(value, ProductVisitor):
            self.visitors[value.id] = value

    async def commit(self):
        return None


def test_consent_enables_safe_product_events() -> None:
    fake = FakeSession()
    app.dependency_overrides[get_session] = lambda: fake
    try:
        client = TestClient(app)
        consent = client.post("/api/v1/product/consent", json={"choice": "accepted"})
        assert consent.status_code == 200
        assert consent.json()["analytics_enabled"] is True
        assert client.cookies.get("iacp_consent") == "accepted"

        event = client.post(
            "/api/v1/product/events",
            json={
                "event_name": "review_completed",
                "session_id": "12345678-1234-5678-1234-567812345678",
                "page_path": "/",
                "properties": {
                    "result_status": "review",
                    "effort_bucket": "30_39",
                    "geography_code": "PROV:24",
                },
            },
        )
        assert event.status_code == 202
        assert fake.added[-1].event_name == "review_completed"
        assert "annual_income" not in fake.added[-1].properties
    finally:
        app.dependency_overrides.clear()


def test_raw_financial_values_are_rejected_from_analytics() -> None:
    fake = FakeSession()
    app.dependency_overrides[get_session] = lambda: fake
    try:
        client = TestClient(app)
        client.post("/api/v1/product/consent", json={"choice": "accepted"})
        response = client.post(
            "/api/v1/product/events",
            json={
                "event_name": "review_completed",
                "session_id": "12345678-1234-5678-1234-567812345678",
                "properties": {"annual_income_eur": 42000},
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_safe_use_case_event_is_accepted_without_financial_values() -> None:
    fake = FakeSession()
    app.dependency_overrides[get_session] = lambda: fake
    try:
        client = TestClient(app)
        client.post("/api/v1/product/consent", json={"choice": "accepted"})
        response = client.post(
            "/api/v1/product/events",
            json={
                "event_name": "tool_selected",
                "session_id": "12345678-1234-5678-1234-567812345678",
                "properties": {"use_case": "budget"},
            },
        )
        assert response.status_code == 202
        assert fake.added[-1].properties == {"use_case": "budget"}
    finally:
        app.dependency_overrides.clear()


def test_observatory_navigation_event_is_allowlisted() -> None:
    fake = FakeSession()
    app.dependency_overrides[get_session] = lambda: fake
    try:
        client = TestClient(app)
        client.post("/api/v1/product/consent", json={"choice": "accepted"})
        response = client.post(
            "/api/v1/product/events",
            json={
                "event_name": "observatory_group_changed",
                "session_id": "12345678-1234-5678-1234-567812345678",
                "properties": {"use_case": "rates"},
            },
        )
        assert response.status_code == 202
    finally:
        app.dependency_overrides.clear()


def test_question_requires_explicit_privacy_acceptance() -> None:
    fake = FakeSession()
    app.dependency_overrides[get_session] = lambda: fake
    try:
        response = TestClient(app).post(
            "/api/v1/product/questions",
            json={
                "question": "¿Qué gastos debo reservar?",
                "privacy_notice_accepted": False,
            },
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_product_metrics_require_admin_key() -> None:
    response = TestClient(app).get("/api/v1/product/admin/metrics")
    assert response.status_code == 401
