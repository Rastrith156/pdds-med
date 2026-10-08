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
│   ├── schemas/         # request/response schemas (health, provider)
│   ├── routers/         # API routes (health, providers)
│   ├── services/        # business logic (provider search; recommendations in Stage 4)
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

## Endpoints (Stage 3)

| Method | Path                          | Description                                    |
|--------|-------------------------------|------------------------------------------------|
| GET    | `/api/health`                 | Liveness health check                          |
| GET    | `/api/providers`              | Search demo providers (filterable)             |
| GET    | `/api/providers/{id}`         | Full provider record (404 if unknown)          |
| GET    | `/docs`                       | Swagger UI                                     |
| GET    | `/redoc`                      | ReDoc documentation                            |

### Provider search filters (all optional, AND logic)

`specialization`, `city`, `area`, `maximum_budget`, `minimum_rating`,
`language`, `available_today` — text filters are case-insensitive.

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/providers?city=Bangalore&specialization=Dermatology&maximum_budget=700"
```

All records served by this API are **fictional demo data** (`is_demo: true`).

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
