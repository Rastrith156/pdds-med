"""Test configuration.

Makes the ``backend`` package importable so tests can live in the
repository-level ``tests/`` folder, and defaults ``DATABASE_MODE`` to
``memory`` so UNIT tests never require a running MongoDB (Stage 5 test
strategy). Integration tests override this by setting ``DATABASE_MODE=
mongodb`` and ``RUN_MONGO_INTEGRATION=1`` explicitly.

Provides ONE session-scoped ``client`` shared by every test file. This is
essential: ``AsyncMongoClient`` is bound to the event loop it was created
on, so all tests must run requests through a single TestClient context
(single portal event loop — exactly like production's single uvicorn loop).
Multiple TestClients would raise "Cannot use AsyncMongoClient in different
event loop".
"""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault(
    "DATABASE_MODE",
    "mongodb" if os.environ.get("RUN_MONGO_INTEGRATION") == "1" else "memory",
)

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Repository root hosts the framework-independent ai/ package (Stage 7).
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def client():
    """App with lifespan run ONCE for the whole session.

    mongodb mode: connects to MongoDB and creates indexes on entry,
    closes the connection on exit. memory mode: lifespan starts without a
    database (unit tests).
    """
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
