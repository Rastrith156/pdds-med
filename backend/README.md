# MediAccess AI — Backend

FastAPI service that powers the MediAccess AI healthcare-navigation platform.

> **Disclaimer:** This API provides healthcare navigation and provider
> information only. It does not diagnose conditions or replace professional
> medical advice.

## Stack

- **FastAPI** — web framework (Swagger UI enabled at `/docs`)
- **Pydantic** — settings and schema validation
- **Uvicorn** — ASGI server

## Project structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, middleware, router wiring
│   ├── config.py        # env-driven settings (.env, never hardcoded secrets)
│   ├── database.py      # MongoDB access (fails loudly until Stage 5)
│   ├── data/            # clearly-labelled DEMO provider dataset
│   ├── models/          # document models (Stage 5)
│   ├── schemas/         # request/response schemas (health, provider, recommendation)
│   ├── routers/         # API routes (health, providers, recommendations)
│   ├── services/        # business logic (provider search, recommendation engine)
│   └── utils/           # shared helpers
├── requirements.txt
├── requirements-dev.txt # pytest + httpx (tests)
└── README.md
```

## Run locally (Windows)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Endpoints (Stage 4)

| Method | Path                          | Description                                    |
|--------|-------------------------------|------------------------------------------------|
| GET    | `/api/health`                 | Liveness health check                          |
| GET    | `/api/providers`              | Search demo providers (filterable)             |
| GET    | `/api/providers/{id}`         | Full provider record (404 if unknown)          |
| POST   | `/api/recommendations`        | Score + rank providers (deterministic engine)  |
| GET    | `/docs`                       | Swagger UI                                     |
| GET    | `/redoc`                      | ReDoc documentation                            |

### Provider search filters (all optional, AND logic)

`specialization`, `city`, `area`, `maximum_budget`, `minimum_rating`,
`language`, `available_today` — text filters are case-insensitive.

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/providers?city=Bangalore&specialization=Dermatology&maximum_budget=700"
```

All records served by this API are **fictional demo data** (`is_demo: true`).

### Recommendations (deterministic — no LLM)

`POST /api/recommendations` filters candidates, then ranks them with a fixed
weighted formula (see `app/services/recommendation_service.py`):

`match_score = budget×0.30 + distance×0.25 + availability×0.20 + rating×0.15 + language×0.10`

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/recommendations -Method Post `
  -ContentType 'application/json' `
  -Body '{"specialization":"Dermatology","city":"Bangalore","maximum_budget":700,"available_today":true,"language":"Kannada","limit":5}'
```

Response items contain `provider`, `match_score`, `distance_km` (null when no
coordinates given), `score_breakdown` and data-derived `reasons`.

### Health check

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

```json
{
  "status": "healthy",
  "service": "MediAccess AI"
}
```

## Configuration

All settings are read from environment variables (optionally a `.env` file —
copy `.env.example` from the repository root). See `app/config.py`.
