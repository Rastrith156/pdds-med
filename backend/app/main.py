"""MediAccess AI — FastAPI application entrypoint.

Run locally:
    docker compose up -d mongodb          # MongoDB (Stage 5)
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Swagger UI:    http://127.0.0.1:8000/docs
ReDoc:         http://127.0.0.1:8000/redoc
Health check:  http://127.0.0.1:8000/api/health
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# The vendor-neutral AI package (ai/) lives at the repository root so it can
# be reused outside FastAPI; make it importable wherever the app is started.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app import database
from app.config import get_settings
from app.routers import ai_search, health, openproject, providers, recommendations

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Connect MongoDB on startup (loud failure) and close it on shutdown."""
    await database.connect_database()
    yield
    await database.disconnect_database()


app = FastAPI(
    title="MediAccess AI",
    version="0.1.0",
    description=(
        "Healthcare navigation and provider recommendation API.\n\n"
        "**Disclaimer:** MediAccess AI provides healthcare navigation and "
        "provider information. It does not diagnose conditions or replace "
        "professional medical advice. All provider records are clearly "
        "labelled demo data."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(providers.router)
app.include_router(recommendations.router)
app.include_router(ai_search.router)
app.include_router(openproject.router)


@app.get("/", include_in_schema=False)
def read_root() -> dict:
    """Convenience root endpoint pointing to docs and health."""
    return {
        "service": "MediAccess AI",
        "docs": "/docs",
        "health": "/api/health",
    }
