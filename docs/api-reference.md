# API Reference

Base URL (local): `http://127.0.0.1:8000`
Interactive docs: `GET /docs` (Swagger UI) · `GET /redoc` (ReDoc)

**Authentication: none.** This submission does not implement authentication;
all endpoints are open on localhost and MongoDB is bound to `127.0.0.1` only.
See *Limitations* in the project report.

**Conventions**

- All request/response bodies are JSON (`Content-Type: application/json`).
- Validation failures return FastAPI's standard **422** with a `detail` array.
- When MongoDB (required in `mongodb` mode) is unreachable, data endpoints
  return **503** with a human-readable `detail` — the API never fabricates
  results. `GET /api/health` instead reports `"degraded"` (it stays 200 so
  monitoring can see the state).

---

## 1. `GET /api/health` — service liveness

```json
// 200 OK
{ "status": "healthy", "service": "MediAccess AI" }
```

`status` becomes `"degraded"` when MongoDB is required but unreachable.

## 2. `GET /api/health/database` — database liveness

```json
// 200 OK
{ "status": "healthy", "database": "mongodb" }
```

Variants: `"database": "memory"` (unit-test mode) and
`{"status": "unhealthy", "database": "unavailable"}` when the ping fails.
No credentials or connection strings are ever exposed.

## 3. `GET /api/providers` — search demo providers

Query parameters (all optional, **AND** logic, text filters case-insensitive):

| Parameter | Type | Constraint | Example |
|---|---|---|---|
| `specialization` | string | — | `Dermatology` |
| `city` | string | — | `Bangalore` |
| `area` | string | — | `Indiranagar` |
| `maximum_budget` | float | > 0 (INR) | `700` |
| `minimum_rating` | float | 0–5 | `4.5` |
| `language` | string | — | `Kannada` |
| `available_today` | bool | default `false` | `true` |

```
GET /api/providers?city=Bangalore&maximum_budget=700&available_today=true
```

```json
// 200 OK (shape)
{
  "count": 2,
  "providers": [
    {
      "id": "demo-001",
      "name": "Dr. A. Kumar",
      "specialization": "Dermatology",
      "hospital": "Sunrise Skin Clinic",
      "city": "Bangalore",
      "area": "Indiranagar",
      "consultation_fee": 650,
      "rating": 4.6,
      "languages": ["English", "Kannada", "Hindi"],
      "available_days": ["Monday", "Wednesday", "Friday"],
      "available_slots": ["09:30", "10:00", "17:00"],
      "latitude": 12.9784,
      "longitude": 77.6408,
      "verified": true,
      "is_demo": true
    }
  ]
}
```

Errors: **503** database unreachable.

## 4. `GET /api/providers/{provider_id}` — one provider

`GET /api/providers/demo-001` → the full provider object (same shape as above).

Errors: **404** `{"detail": "Provider not found"}` · **503** database down.
Lookup is case-insensitive.

## 5. `POST /api/recommendations` — ranked recommendations (deterministic)

Request (every field optional):

```json
{
  "specialization": "Dermatology",
  "city": "Bangalore",
  "maximum_budget": 700,
  "minimum_rating": 4.0,
  "language": "Kannada",
  "available_today": true,
  "latitude": 12.97,
  "longitude": 77.59,
  "limit": 5
}
```

Constraints: `maximum_budget > 0`; `0 ≤ minimum_rating ≤ 5`; `limit` 1–20
(default 10); `latitude`/`longitude` must be supplied **together** or not at
all (422 otherwise).

```json
// 200 OK (shape)
{
  "count": 1,
  "recommendations": [
    {
      "provider": { "...": "full provider record" },
      "match_score": 99,
      "distance_km": 1.4,
      "score_breakdown": { "budget": 100, "distance": 100, "availability": 100, "rating": 92, "language": 100 },
      "reasons": ["Within budget", "Available today", "High provider rating", "Located nearby"]
    }
  ]
}
```

`distance_km` is `null` when no coordinates were supplied. Scoring:
see `docs/recommendation-algorithm.md`. Errors: **422**, **503**.

## 6. `POST /api/ai/search` — natural-language search (Stage 7)

```json
{ "query": "I need a dermatologist near Bangalore under 700 today" }
```

`query` is required, max 1000 characters.

```json
// 200 OK — successful parse (shape)
{
  "query": "I need a dermatologist near Bangalore under 700 today",
  "parser": "fallback",
  "parsed_request": {
    "specialization": "Dermatology", "city": "Bangalore", "area": null,
    "maximum_budget": 700, "minimum_rating": null, "language": null,
    "latitude": null, "longitude": null,
    "available_today": true
  },
  "message": null,
  "count": 5,
  "recommendations": [ { "...": "RecommendationItem, same shape as #5" } ]
}
```

- `parser` is `"llm"` (LLM configured and returned valid criteria) or
  `"fallback"` (no key, LLM error, or unparseable output — the deterministic
  regex parser handled the query).
- **Safety refusal** — diagnosis/medication/treatment phrasing is refused
  *before* any parsing: `parsed_request: null`, `message`: safe-navigation
  text, `count: 0`, `recommendations: []`.
- **Guidance** — a query with no usable criteria returns
  `message` asking the user for specialization/city/budget, `count: 0`.
- Ranking inside this endpoint is still fully deterministic (limit 5).
- Errors: **422**, **503** (database down after a successful parse).

---

## Endpoint summary

| Method | Path | Tag | Purpose |
|---|---|---|---|
| GET | `/api/health` | Health | Service liveness (honest `degraded` state) |
| GET | `/api/health/database` | Health | Database ping, no secrets exposed |
| GET | `/api/providers` | Providers | Filtered demo-provider search |
| GET | `/api/providers/{id}` | Providers | Full record by id (404 if unknown) |
| POST | `/api/recommendations` | Recommendations | Filter → deterministic weighted ranking |
| POST | `/api/ai/search` | AI Search | Natural-language query → parse → filter → rank |
