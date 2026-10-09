"""MongoDB integration tests (Stage 5) - opt-in.

Run ONLY when MongoDB is available and explicitly requested:

    docker compose up -d mongodb
    backend\\.venv\\Scripts\\python.exe database\\seed.py
    $env:RUN_MONGO_INTEGRATION='1'
    .\\backend\\.venv\\Scripts\\python.exe -m pytest tests/test_mongodb_integration.py -v

The default test run stays independent of the database: conftest.py sets
DATABASE_MODE=memory, which skips this entire module.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_MONGO_INTEGRATION") != "1",
    reason="Opt-in MongoDB integration tests: set RUN_MONGO_INTEGRATION=1",
)

if os.environ.get("DATABASE_MODE") != "mongodb":
    pytest.skip(
        "MongoDB integration tests require DATABASE_MODE=mongodb "
        "(set RUN_MONGO_INTEGRATION=1; conftest then defaults it for you).",
        allow_module_level=True,
    )

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT / "database"))

import seed as seed_script  # noqa: E402

# NOTE: the session-scoped ``client`` fixture lives in conftest.py so every
# test file shares ONE TestClient (single portal event loop). AsyncMongoClient
# is bound to the loop it was created on — multiple TestClients would raise
# "Cannot use AsyncMongoClient in different event loop".


def test_mongodb_connection_and_ping(client) -> None:
    response = client.get("/api/health/database")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "mongodb"}
    assert client.get("/api/health").json()["status"] == "healthy"


def test_seed_operation_inserts_exactly_36(client) -> None:
    stats = asyncio.run(seed_script.seed_providers())
    assert stats["inserted"] + stats["skipped"] + stats["updated"] == 36
    assert stats["total"] == 36
    assert stats["found"] == 36


def test_seed_is_idempotent(client) -> None:
    asyncio.run(seed_script.seed_providers())
    second = asyncio.run(seed_script.seed_providers())
    assert second["inserted"] == 0  # no duplicates on re-run
    assert second["total"] == 36  # still exactly 36, never 72


def test_provider_count_is_36_from_mongodb(client) -> None:
    body = client.get("/api/providers").json()
    assert body["count"] == 36
    assert all(p["is_demo"] is True for p in body["providers"])


def test_provider_retrieval_from_mongodb(client) -> None:
    body = client.get("/api/providers/demo-002").json()
    assert body["id"] == "demo-002"
    assert body["city"] == "Bangalore"
    assert body["is_demo"] is True


def test_provider_filtering_from_mongodb(client) -> None:
    city = client.get("/api/providers", params={"city": "Bangalore"}).json()
    assert city["count"] == 6
    assert all(p["city"] == "Bangalore" for p in city["providers"])
    combo = client.get(
        "/api/providers",
        params={"city": "Bangalore", "specialization": "Dermatology", "maximum_budget": 700},
    ).json()
    assert combo["count"] == 1
    assert combo["providers"][0]["id"] == "demo-002"


def test_unknown_provider_returns_404(client) -> None:
    response = client.get("/api/providers/not-a-real-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Provider not found"}


def test_recommendations_served_from_mongodb(client) -> None:
    body = client.post(
        "/api/recommendations",
        json={"city": "Bangalore", "limit": 5},
    ).json()
    assert body["count"] == 5
    assert all(r["provider"]["city"] == "Bangalore" for r in body["recommendations"])
    scores = [r["match_score"] for r in body["recommendations"]]
    assert scores == sorted(scores, reverse=True)


def test_recommendation_formula_unchanged(client) -> None:
    """Exact Stage 4 values, weekday-independent (no available_today)."""
    rec = client.post(
        "/api/recommendations",
        json={
            "specialization": "Dermatology",
            "city": "Bangalore",
            "maximum_budget": 700,
            "language": "Kannada",
            "limit": 5,
        },
    ).json()["recommendations"][0]
    assert rec["provider"]["id"] == "demo-002"
    assert rec["score_breakdown"] == {
        "budget": 100,
        "distance": 50,
        "availability": 50,
        "rating": 96,
        "language": 100,
    }
    # 100*.30 + 50*.25 + 50*.20 + 96*.15 + 100*.10 = 76.9 -> 77 (Stage 4 result)
    assert rec["match_score"] == 77
