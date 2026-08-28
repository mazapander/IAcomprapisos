import uuid

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.models import MarketObservation, ProductVisitor, UserQuestion
from app.db.session import get_session
from app.main import app


class FakeSession:
    def __init__(self):
        self.visitors = {}
        self.added = []

    async def get(self, model, identifier):
        if model is ProductVisitor:
            return self.visitors.get(identifier)
        if model is UserQuestion:
            return next((value for value in self.added if value.id == identifier), None)
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


def test_question_is_persisted_for_n8n_notification() -> None:
    fake = FakeSession()
    app.dependency_overrides[get_session] = lambda: fake
    try:
        response = TestClient(app).post(
            "/api/v1/product/questions",
            json={
                "question": "Quiero saber si esta oferta está por encima de mercado.",
                "category": "offer",
                "journey_stage": "offer_received",
                "geography_code": "PROV:48",
                "contact_email": "buyer@example.com",
                "contact_consent": True,
                "privacy_notice_accepted": True,
            },
        )
        assert response.status_code == 201
        stored = fake.added[-1]
        assert isinstance(stored, UserQuestion)
        assert stored.status == "new"
        assert stored.notification_attempts == 0
        assert stored.contact_email == "buyer@example.com"
    finally:
        app.dependency_overrides.clear()


def test_n8n_can_acknowledge_question_notification() -> None:
    fake = FakeSession()
    question = UserQuestion(
        id=uuid.uuid4(),
        question="¿Me podéis ayudar con mi oferta?",
        category="offer",
        journey_stage="offer_received",
        contact_consent=False,
        privacy_notice_version="2026-08",
        status="new",
        notification_attempts=0,
    )
    fake.add(question)
    app.dependency_overrides[get_session] = lambda: fake
    try:
        response = TestClient(app).post(
            f"/api/v1/product/admin/questions/{question.id}/notification-result",
            headers={"X-API-Key": settings.api_key},
            json={"delivered": True},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "notified"
        assert question.notification_attempts == 1
        assert question.notified_at is not None
    finally:
        app.dependency_overrides.clear()


def test_consented_market_observation_is_stored_with_useful_prices() -> None:
    fake = FakeSession()
    app.dependency_overrides[get_session] = lambda: fake
    try:
        response = TestClient(app).post(
            "/api/v1/product/market-observations",
            json={
                "geography_code": "PROV:48",
                "property_type": "apartment",
                "property_age": "over_5",
                "contributor_role": "buyer",
                "surface_area_m2": 80,
                "asking_price_eur": 320000,
                "appraisal_value_eur": 280000,
                "negotiated_price_eur": 305000,
                "observed_period": "2026-08-19",
                "market_data_consent": True,
            },
        )
        assert response.status_code == 201
        stored = fake.added[-1]
        assert isinstance(stored, MarketObservation)
        assert stored.geography_code == "PROV:48"
        assert stored.observed_period.isoformat() == "2026-08-01"
        assert response.json()["metrics"]["asking_price_eur_m2"] == 4000
        assert response.json()["metrics"]["asking_vs_appraisal_pct"] == 14.29
        assert response.json()["metrics"]["negotiated_discount_pct"] == 4.69
    finally:
        app.dependency_overrides.clear()


def test_market_observation_rejects_missing_consent_and_address_data() -> None:
    fake = FakeSession()
    app.dependency_overrides[get_session] = lambda: fake
    try:
        response = TestClient(app).post(
            "/api/v1/product/market-observations",
            json={
                "geography_code": "PROV:48",
                "property_type": "apartment",
                "property_age": "over_5",
                "surface_area_m2": 80,
                "asking_price_eur": 320000,
                "market_data_consent": False,
                "address": "Calle que no debe persistirse 1",
            },
        )
        assert response.status_code == 422
        assert not fake.added
    finally:
        app.dependency_overrides.clear()


def test_product_metrics_require_admin_key() -> None:
    response = TestClient(app).get("/api/v1/product/admin/metrics")
    assert response.status_code == 401
