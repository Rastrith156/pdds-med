# Database Design (MongoDB)

## 1. Overview

| Aspect | Value |
|---|---|
| Database engine | MongoDB 8 (Docker image `mongo:8`) |
| Container name | `medaccess-mongodb` |
| Database name | `medaccess` (env `DATABASE_NAME`) |
| Connection string | `mongodb://127.0.0.1:27017` (env `MONGODB_URI`, loopback only) |
| Collections in use | `providers` (the only application collection) |
| Access driver | PyMongo `AsyncMongoClient` (official async API — chosen over the deprecated Motor driver) |
| Seed script | `database/seed.py` (idempotent, verifiable) |

There is intentionally **no `users` collection**: authentication is not
implemented in this submission (see limitations). No real personal or medical
data is stored anywhere — all records are fictional demo data.

## 2. Document model — `medaccess.providers`

Source of truth: `backend/app/data/providers.py` (36 records, `demo-001` …
`demo-036`), validated by the Pydantic schema `app/schemas/provider.py::Provider`
before any write or read.

```json
{
  "_id": "ObjectId (managed by MongoDB)",
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
```

Field constraints (enforced by Pydantic, not only by convention):

| Field | Type | Constraint |
|---|---|---|
| `id` | string | non-empty, unique (unique index) |
| `name`, `specialization`, `hospital`, `city`, `area` | string | non-empty |
| `consultation_fee` | float | `> 0` (INR) |
| `rating` | float | `0 … 5` |
| `languages` | string[] | at least one |
| `available_days` | string[] | valid weekday names only (validator normalises case, removes duplicates) |
| `available_slots` | string[] | `HH:MM` 24-hour format (regex validator) |
| `latitude` / `longitude` | float | WGS-84 ranges ±90 / ±180 |
| `is_demo` | literal `true` | **always** true — makes demo data self-identifying |

## 3. Indexes (created idempotently at startup and by the seed script)

| Index | Field | Purpose |
|---|---|---|
| `id_1` (unique) | `id` | upsert key for idempotent seeding; case-insensitive lookup by API |
| `city_1` | `city` | equality/regex city filters |
| `specialization_1` | `specialization` | equality/regex specialization filters |
| `consultation_fee_1` | `consultation_fee` | `$lte` budget filters |
| `rating_1` | `rating` | `$gte` minimum-rating filters |

Text filters are applied in MongoDB as **unanchored, case-insensitive regexes**
(`$regex` + `$options: "i"`), preserving the case-insensitive substring
semantics defined in the filtering stage. Multiple filters combine with
**AND logic inside one query** — the collection is never loaded into memory to
be filtered by the application.

Example filter built by `provider_service._build_mongo_filter()`:

```json
{
  "specialization": { "$regex": "Dermatology", "$options": "i" },
  "city":           { "$regex": "Bangalore",  "$options": "i" },
  "consultation_fee": { "$lte": 700 },
  "rating":         { "$gte": 4.0 },
  "available_days": { "$regex": "^Friday$", "$options": "i" }
}
```

## 4. Dual database modes (`app/database.py`)

| Mode | `DATABASE_MODE` | Behaviour | Used by |
|---|---|---|---|
| `mongodb` | `mongodb` (production default) | Real client; startup **fails loudly** with `DatabaseUnavailableError` if the ping fails; runtime query failures become **HTTP 503** instead of fabricated results | Running app, integration tests |
| `memory` | `memory` | No connection at all; services answer from the in-code demo dataset | Unit tests only (never for real serving) |

`GET /api/health` honestly reports `degraded` when MongoDB is required but
unreachable; `GET /api/health/database` pings the database without exposing
credentials or connection strings.

## 5. Seeding (`database/seed.py`)

```powershell
docker compose up -d mongodb
backend\.venv\Scripts\python.exe database\seed.py
```

Properties:

- **Idempotent** — `replace_one({"id": ...}, doc, upsert=True)` per record;
  running it any number of times yields exactly 36 documents.
- **Never invents data** — records come only from `DEMO_PROVIDERS`.
- **Self-verifying** — after seeding it checks `count == 36` for both the
  whole collection and the demo-id query, and exits non-zero on any mismatch.
- **Safe to print** — no connection strings or credentials are ever logged.

Observed output on this machine: `total = 36`, all demo ids present,
`is_demo = true`.
