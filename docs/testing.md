# Testing & Quality Assurance

## 1. Test strategy

| Layer | Location | Mode | Needs MongoDB? | Count |
|---|---|---|---|---|
| API unit tests (providers) | `tests/test_providers_api.py` | `DATABASE_MODE=memory` | No | 15 |
| Algorithm unit tests | `tests/test_recommendation_service.py` | `memory` | No | 33 |
| AI parsing regression tests | `tests/test_ai_fallback_parser.py` | `memory`, fully offline (stubbed LLM providers — no key, no network) | No | 14 |
| **Unit subtotal** | | | | **62** |
| MongoDB integration tests | `tests/test_mongodb_integration.py` | `DATABASE_MODE=mongodb` + `RUN_MONGO_INTEGRATION=1` | **Yes** (Docker) | 9 |
| **Total** | | | | **71** |

Design notes:

- `tests/conftest.py` forces `DATABASE_MODE=memory` by default so the unit
  suite never requires a running database, and puts `backend/` and the
  repository root on `sys.path` (the `ai/` package lives at the repo root).
- One **session-scoped** `TestClient` is shared because `AsyncMongoClient` is
  bound to a single event loop — exactly like production's single uvicorn loop.
- Integration tests opt in with `RUN_MONGO_INTEGRATION=1`; they seed through
  the real `database/seed.py` code path (idempotency is asserted), exercise
  real filter queries, and verify provenance (mutating a document is visible
  through the API immediately).
- The AI tests never call the network: they inject stub `LLMProvider`
  implementations to prove the guardrail runs **before** the model, that LLM
  failures fall back to the regex parser, and that valid LLM JSON is used when
  supplied. They also lock down a fixed regression: city matching must be
  case-insensitive (`_first_match` previously omitted `re.IGNORECASE`).

## 2. How to run the tests (Windows, from the repository root)

```powershell
# Unit tests only (no database required)
& .\backend\.venv\Scripts\python.exe -m pytest tests/ -q

# Full suite INCLUDING MongoDB integration tests
$env:RUN_MONGO_INTEGRATION = '1'
$env:DATABASE_MODE = 'mongodb'
docker compose up -d mongodb        # once — container must be healthy
& .\backend\.venv\Scripts\python.exe -m pytest tests/ -q
```

Requirements: `docker compose up -d mongodb` healthy; backend dependencies
from `backend/requirements.txt` + `backend/requirements-dev.txt` installed in
`backend\.venv`.

## 3. Verified results (this machine)

```
71 passed, 1 warning in 0.90s
```

- 71/71 tests pass, including all 9 live MongoDB integration tests.
- The single warning is a third-party `StarletteDeprecationWarning` from
  FastAPI's `TestClient` (about `httpx`), not a failure in project code.

## 4. Frontend testing status (honest disclosure)

Vitest **is configured** (`vite.config.js`: jsdom environment, globals,
`include: ["src/**/*.test.{js,jsx}"]`, script `npm test` → `vitest run`,
`@testing-library/react` installed) but **no frontend test files exist yet**.
Frontend verification to date is manual (build + live API interaction):

```powershell
cd frontend
npm run build     # production build must succeed — used as a regression gate
```

Adding component tests under `src/**/*.test.jsx` requires no further
configuration.

## 5. Manual / live verification performed

Beyond the automated suite, the running system was probed end-to-end:

| Check | Observed result |
|---|---|
| `GET /api/health`, `/api/health/database` | `healthy` / `mongodb` with container up |
| `GET /api/providers` with combined filters | Correct AND filtering, case-insensitive text |
| `POST /api/recommendations` (budget/rating/language) | `match_score` 77 for the acceptance case; breakdown adds up |
| `POST /api/ai/search` — natural-language query | Parsed criteria via fallback parser, ranked results, `parser: "fallback"` |
| `POST /api/ai/search` — "Do I have …?" phrasing | Safety refusal, `count: 0`, no results |
| DB stopped → data endpoints | HTTP 503 with clear `detail`; `/api/health` → `degraded` |
| DB restarted | Endpoints recover with no app restart |
| Data provenance | Editing a seeded document is immediately reflected in API responses |
| `npm run build` (frontend) | Production build succeeds; `frontend/dist` generated |
| Seed idempotency | Re-running `database/seed.py` keeps exactly 36 documents |

## 6. CI/CD

No CI pipeline (Jenkins/GitHub Actions) or SonarQube integration exists in
this repository — tests are executed manually with the commands above. This is
documented as a limitation/future work in the project report.
