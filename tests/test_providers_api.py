"""API tests for the provider endpoints (Stage 3).

Runs against the in-memory demo dataset via FastAPI's TestClient —
no server, database or network required.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.provider import Provider

client = TestClient(app)


def test_health_endpoint_still_works() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "MediAccess AI"}


def test_list_providers_returns_30_plus() -> None:
    response = client.get("/api/providers")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(body["providers"])
    assert body["count"] >= 30


def test_all_providers_are_demo_records() -> None:
    body = client.get("/api/providers").json()
    assert all(p["is_demo"] is True for p in body["providers"])


def test_get_provider_by_valid_id_returns_full_record() -> None:
    first = client.get("/api/providers").json()["providers"][0]
    response = client.get(f"/api/providers/{first['id']}")
    assert response.status_code == 200
    assert response.json() == first


def test_get_provider_invalid_id_returns_404() -> None:
    response = client.get("/api/providers/no-such-provider")
    assert response.status_code == 404
    assert response.json() == {"detail": "Provider not found"}


def test_filter_by_city() -> None:
    body = client.get("/api/providers", params={"city": "Bangalore"}).json()
    assert body["count"] == 6
    assert all(p["city"] == "Bangalore" for p in body["providers"])


def test_filter_by_specialization() -> None:
    body = client.get("/api/providers", params={"specialization": "Dermatology"}).json()
    assert body["count"] == 5
    assert all(p["specialization"] == "Dermatology" for p in body["providers"])


def test_filter_by_maximum_budget() -> None:
    body = client.get("/api/providers", params={"maximum_budget": 700}).json()
    assert body["count"] > 0
    assert all(p["consultation_fee"] <= 700 for p in body["providers"])


def test_filter_by_minimum_rating() -> None:
    body = client.get("/api/providers", params={"minimum_rating": 4.5}).json()
    assert body["count"] > 0
    assert all(p["rating"] >= 4.5 for p in body["providers"])


def test_filter_by_language() -> None:
    body = client.get("/api/providers", params={"language": "Malayalam"}).json()
    assert body["count"] == 6
    assert all("Malayalam" in p["languages"] for p in body["providers"])


def test_filter_by_availability_today() -> None:
    today = datetime.now().strftime("%A")
    body = client.get("/api/providers", params={"available_today": "true"}).json()
    assert body["count"] > 0
    assert all(today in p["available_days"] for p in body["providers"])


def test_multiple_filters_combined() -> None:
    params = {"city": "Bangalore", "specialization": "Dermatology", "maximum_budget": 700}
    body = client.get("/api/providers", params=params).json()
    assert body["count"] == 1
    provider = body["providers"][0]
    assert provider["city"] == "Bangalore"
    assert provider["specialization"] == "Dermatology"
    assert provider["consultation_fee"] <= 700


def test_city_filter_is_case_insensitive() -> None:
    expected = client.get("/api/providers", params={"city": "Bangalore"}).json()["count"]
    lower = client.get("/api/providers", params={"city": "bangalore"}).json()["count"]
    upper = client.get("/api/providers", params={"city": "BANGALORE"}).json()["count"]
    assert lower == upper == expected == 6


def test_specialization_filter_is_case_insensitive() -> None:
    proper = client.get("/api/providers", params={"specialization": "Dermatology"}).json()["count"]
    lower = client.get("/api/providers", params={"specialization": "dermatology"}).json()["count"]
    assert lower == proper == 5


def test_schema_rejects_invalid_rating() -> None:
    raw = client.get("/api/providers").json()["providers"][0]
    raw["rating"] = 5.5
    with pytest.raises(ValidationError):
        Provider.model_validate(raw)
