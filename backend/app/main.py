"""MediAccess AI — FastAPI application entrypoint.

Run locally:
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Swagger UI:    http://127.0.0.1:8000/docs
ReDoc:         http://127.0.0.1:8000/redoc
Health check:  http://127.0.0.1:8000/api/health
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, providers

settings = get_settings()

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


@app.get("/", include_in_schema=False)
def read_root() -> dict:
    """Convenience root endpoint pointing to docs and health."""
    return {
        "service": "MediAccess AI",
        "docs": "/docs",
        "health": "/api/health",
    }
