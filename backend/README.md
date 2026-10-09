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
│   ├── main.py          # FastAPI app, CORS, lifespan, router wiring
│   ├── config.py        # env-driven settings (.env, never hardcoded secrets)
│   ├── database.py      # MongoDB access: mongodb | memory modes, 503 on outage
│   ├── data/            # clearly-labelled DEMO provider dataset (36 records)
│   ├── models/          # reserved for document models (currently empty placeholder)
│   ├── schemas/         # request/response schemas (health, provider, recommendation, ai)
│   ├── routers/         # API routes (health, providers, recommendations, ai_search)
│   ├── services/        # business logic (provider search, recommendation engine)
│   └── utils/           # reserved for shared helpers (currently empty placeholder)
├── requirements.txt
├── requirements-dev.txt # pytest + httpx (tests)
└── README.md
```

The `ai/` package (LLM abstraction, safety guardrail, fallback parser) lives at
the **repository root**, not inside `backend/`; tests and the backend add the
root to `sys.path`.


## Run locally (Windows)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Endpoints

| Method | Path                          | Description                                    |
|--------|-------------------------------|------------------------------------------------|
| GET    | `/api/health`                 | Liveness health check (`degraded` if DB down)  |
| GET    | `/api/health/database`        | Database ping (no credentials exposed)         |
| GET    | `/api/providers`              | Search demo providers (filterable)             |
| GET    | `/api/providers/{id}`         | Full provider record (404 if unknown)          |
| POST   | `/api/recommendations`        | Score + rank providers (deterministic engine)  |
| POST   | `/api/ai/search`              | Natural-language search (guardrail → LLM → fallback) |
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

### Database modes

| `DATABASE_MODE` | Behaviour |
|---|---|
| `mongodb` | Real MongoDB (default for running the app). Startup pings the DB; query-time failures return HTTP 503 — never fabricated results. |
| `memory` | Serves the in-code demo dataset without any connection — **unit tests only**. |

Optional AI configuration: `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`. With no
key, natural-language search still works through the deterministic fallback
parser (the response's `parser` field reports which path ran).

### Natural-language search example

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/ai/search -Method Post `
  -ContentType 'application/json' `
  -Body '{"query":"I need a dermatologist near Bangalore under 700 today"}'
```

Unsafe queries (diagnosis/medication/treatment wording) are refused **before
any parsing** and return `count: 0` with a safe navigation message.

## Tests (from the repository root)

```powershell
# Unit tests (memory mode — no Docker needed)
& .\backend\.venv\Scripts\python.exe -m pytest tests/ -q

# Full suite incl. MongoDB integration — 71 tests expected
$env:RUN_MONGO_INTEGRATION = '1'
$env:DATABASE_MODE = 'mongodb'
& .\backend\.venv\Scripts\python.exe -m pytest tests/ -q
```

See [`../docs/testing.md`](../docs/testing.md) for the full test strategy.
