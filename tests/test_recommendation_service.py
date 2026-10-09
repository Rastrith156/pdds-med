"""Unit and API tests for the deterministic recommendation engine (Stage 4).

Component/ranking tests exercise pure functions (no server required);
API tests use FastAPI's TestClient.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.provider import Provider
from app.schemas.recommendation import RecommendationRequest
from app.services import recommendation_service as rs

_ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def make_provider(
    pid: str = "t-001",
    fee: float = 500.0,
    rating: float = 4.5,
    lat: float = 12.9716,
    lng: float = 77.5946,
    days: list[str] | None = None,
    languages: list[str] | None = None,
) -> Provider:
    """Build a valid demo Provider for scoring tests."""
    return Provider.model_validate(
        {
            "id": pid,
            "name": f"Dr. Test {pid} (Demo)",
            "specialization": "General Medicine",
            "hospital": "Test Clinic (Demo)",
            "city": "Bangalore",
            "area": "Test Area",
            "consultation_fee": fee,
            "rating": rating,
            "languages": languages or ["English", "Kannada"],
            "available_days": days or _ALL_DAYS,
            "available_slots": ["09:00"],
            "latitude": lat,
            "longitude": lng,
            "verified": False,
            "is_demo": True,
        }
    )


def score_one(provider: Provider, **kwargs):
    """Score a single provider and return its RecommendationItem."""
    items = rs.recommend_providers([provider], **kwargs)
    assert len(items) == 1
    return items[0]


# ---------------------------------------------------------------- components

def test_match_score_always_between_0_and_100(client) -> None:
    param_sets = [
        {},
        {"budget": 1000},
        {"budget": 100, "latitude": 12.9716, "longitude": 77.5946,
         "available_today": True, "language": "Kannada"},
        {"budget": 10, "latitude": 15.8497, "longitude": 74.4977,
         "available_today": True, "language": "Tamil"},
    ]
    providers = [
        make_provider("t-a", fee=300, rating=5.0),
        make_provider("t-b", fee=1500, rating=0.0, days=["Sunday"], languages=["English"]),
    ]
    for kwargs in param_sets:
        for provider in providers:
            score = score_one(provider, **kwargs).match_score
            assert 0 <= score <= 100, f"score {score} out of range for {kwargs}"


def test_within_budget_outranks_over_budget(client) -> None:
    within = make_provider("t-in", fee=500)
    over = make_provider("t-over", fee=1200)
    assert score_one(within, budget=700).match_score > score_one(over, budget=700).match_score


def test_lower_distance_outranks_higher_distance(client) -> None:
    near = make_provider("t-near", lat=12.9716, lng=77.5946)
    far = make_provider("t-far", lat=15.8497, lng=74.4977)  # ~500 km from Bangalore
    kwargs = {"latitude": 12.9716, "longitude": 77.5946}
    near_item = score_one(near, **kwargs)
    far_item = score_one(far, **kwargs)
    assert near_item.distance_km == 0.0
    assert far_item.distance_km > 400
    assert near_item.score_breakdown.distance > far_item.score_breakdown.distance
    assert near_item.match_score > far_item.match_score


def test_available_today_outranks_unavailable_when_requested(client) -> None:
    monday = make_provider("t-mon", days=["Monday"])
    wednesday = make_provider("t-wed", days=["Wednesday"])
    kwargs = {"available_today": True, "today": "Wednesday"}
    assert score_one(wednesday, **kwargs).score_breakdown.availability == 100
    assert score_one(monday, **kwargs).score_breakdown.availability == 0
    assert score_one(wednesday, **kwargs).match_score > score_one(monday, **kwargs).match_score


def test_rating_score_formula_and_ordering(client) -> None:
    assert rs.rating_score(5.0) == pytest.approx(100)
    assert rs.rating_score(4.5) == pytest.approx(90)
    assert rs.rating_score(4.0) == pytest.approx(80)
    assert rs.rating_score(3.5) == pytest.approx(70)
    scores = [rs.rating_score(r) for r in [0.0, 3.5, 4.0, 4.5, 5.0]]
    assert scores == sorted(scores)


def test_language_match_scores_higher(client) -> None:
    speaks = make_provider("t-lang-yes", languages=["English", "kannada"])
    silent = make_provider("t-lang-no", languages=["English", "Tamil"])
    kwargs = {"language": "Kannada"}
    assert score_one(speaks, **kwargs).score_breakdown.language == 100  # case-insensitive
    assert score_one(silent, **kwargs).score_breakdown.language == 0
    assert score_one(speaks, **kwargs).match_score > score_one(silent, **kwargs).match_score


def test_missing_budget_gives_neutral_score(client) -> None:
    assert rs.budget_score(9999, None) == rs.NEUTRAL_SCORE == 50


def test_missing_location_gives_neutral_distance_and_no_invented_value(client) -> None:
    item = score_one(make_provider())
    assert item.score_breakdown.distance == 50
    assert item.distance_km is None
    assert "Distance not calculated (no location provided)" in item.reasons


def test_missing_language_gives_neutral_score(client) -> None:
    assert rs.language_score(["English"], None) == rs.NEUTRAL_SCORE == 50
    assert rs.language_score(["English"], "   ") == rs.NEUTRAL_SCORE


def test_final_score_uses_exact_weights(client) -> None:
    # Integral components: budget 100, distance 100, availability 100,
    # rating 4.0 -> 80, language 100.
    item = score_one(
        make_provider("t-w", fee=500, rating=4.0, days=["Monday"]),
        budget=700,
        latitude=12.9716,
        longitude=77.5946,
        available_today=True,
        today="Monday",
        language="Kannada",
    )
    b = item.score_breakdown
    assert (b.budget, b.distance, b.availability, b.rating, b.language) == (100, 100, 100, 80, 100)
    expected = round(100 * 0.30 + 100 * 0.25 + 100 * 0.20 + 80 * 0.15 + 100 * 0.10)
    assert item.match_score == expected == 97


# ------------------------------------------------------------------ ranking

def test_results_sorted_highest_first(client) -> None:
    providers = [make_provider(f"t-s{i}", fee=300 + i * 200, rating=3.5 + i * 0.3) for i in range(6)]
    scores = [item.match_score for item in rs.recommend_providers(providers)]
    assert scores == sorted(scores, reverse=True)


def test_limit_respected(client) -> None:
    providers = [make_provider(f"t-l{i}", rating=3.5 + (i % 5) * 0.3) for i in range(10)]
    full = rs.recommend_providers(providers, limit=10)
    limited = rs.recommend_providers(providers, limit=3)
    assert len(full) == 10
    assert len(limited) == 3
    assert [i.provider.id for i in limited] == [i.provider.id for i in full[:3]]


def test_empty_provider_list_returns_empty(client) -> None:
    assert rs.recommend_providers([]) == []


def test_no_matching_filters_returns_empty_response(client) -> None:
    response = client.post(
        "/api/recommendations",
        json={"city": "Bangalore", "specialization": "Dermatology", "maximum_budget": 100},
    )
    assert response.status_code == 200
    assert response.json() == {"count": 0, "recommendations": []}


def test_budget_boundary_exact_and_slightly_over(client) -> None:
    assert rs.budget_score(700, 700) == 100  # exactly at budget -> full score
    slightly_over = rs.budget_score(701, 700)
    assert 0 < slightly_over < 100


def test_rating_boundary_values(client) -> None:
    assert rs.rating_score(5.0) == pytest.approx(100)
    assert rs.rating_score(0.0) == 0
    zero = score_one(make_provider("t-zero", rating=0.0))
    five = score_one(make_provider("t-five", rating=5.0))
    assert 0 <= zero.match_score <= 100
    assert five.match_score > zero.match_score


def test_tie_break_ordering_is_deterministic(client) -> None:
    high_rating = make_provider("t-003", fee=500, rating=4.8)  # wins on rating
    cheapest = make_provider("t-001", fee=400, rating=4.5)     # wins tie on fee
    a = make_provider("t-002", fee=500, rating=4.5)            # then id asc
    b = make_provider("t-004", fee=500, rating=4.5)
    expected = ["t-003", "t-001", "t-002", "t-004"]
    first = rs.recommend_providers([b, a, high_rating, cheapest])
    second = rs.recommend_providers([a, b, cheapest, high_rating])
    assert [i.provider.id for i in first] == expected
    assert [i.provider.id for i in second] == expected  # same result, any order


def test_haversine_known_distances(client) -> None:
    assert rs.haversine_km(12.9716, 77.5946, 12.9716, 77.5946) == 0
    bangalore_mysore = rs.haversine_km(12.9716, 77.5946, 12.2988, 76.6394)
    assert 100 <= bangalore_mysore <= 160  # real-world Bangalore <-> Mysore ~130 km


# ---------------------------------------------------------------- API tests

@pytest.mark.parametrize(
    "payload",
    [
        {"maximum_budget": 0},
        {"maximum_budget": -5},
        {"minimum_rating": 5.5},
        {"minimum_rating": -1},
        {"latitude": 91},
        {"latitude": -91},
        {"longitude": 200},
        {"limit": 0},
        {"limit": 21},
        {"latitude": 12.9716},     # longitude missing
        {"longitude": 77.5946},    # latitude missing
    ],
)
def test_invalid_request_values_rejected(client, payload: dict) -> None:
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 422


def test_paired_coordinate_validation_in_schema(client) -> None:
    with pytest.raises(ValidationError):
        RecommendationRequest(latitude=12.9716)


def test_combined_recommendation_request(client) -> None:
    payload = {
        "specialization": "Dermatology",
        "city": "Bangalore",
        "maximum_budget": 700,
        "available_today": True,
        "language": "Kannada",
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(body["recommendations"]) <= 5
    today = datetime.now().strftime("%A")
    for rec in body["recommendations"]:
        provider = rec["provider"]
        assert provider["specialization"] == "Dermatology"
        assert provider["city"] == "Bangalore"
        assert provider["consultation_fee"] <= 700
        assert today in provider["available_days"]
        assert "Kannada" in provider["languages"]
        assert set(rec["score_breakdown"]) == {"budget", "distance", "availability", "rating", "language"}
        assert 0 <= rec["match_score"] <= 100
        assert isinstance(rec["reasons"], list) and rec["reasons"]


def test_recommendations_without_hard_filters_still_return_results(client) -> None:
    response = client.post("/api/recommendations", json={"city": "Bangalore", "limit": 5})
    body = response.json()
    assert body["count"] > 0
    assert all(r["provider"]["city"] == "Bangalore" for r in body["recommendations"])


def test_recommendations_with_coordinates_include_distance(client) -> None:
    payload = {
        "specialization": "Dermatology",
        "city": "Bangalore",
        "maximum_budget": 700,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "limit": 5,
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    for rec in response.json()["recommendations"]:
        assert rec["distance_km"] is not None
        assert 0 <= rec["score_breakdown"]["distance"] <= 100
        assert "Located nearby" in rec["reasons"] or "Within reasonable travel distance" in rec["reasons"]
