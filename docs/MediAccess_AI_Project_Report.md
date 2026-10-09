# MediAccess AI — Project Report

**Project title:** MediAccess AI — AI-Powered Healthcare Navigation and
Provider Recommendation Platform

**Submission version:** 1.0 · **Repository:** https://github.com/Rastrith156/medaccess

> Student name, roll number, institution, guide and semester details are to be
> filled in by the submitting candidate before printing/exporting this report.

---

## Table of contents

1. Abstract summary · 2. Introduction & background · 3. Problem statement ·
4. Objectives · 5. Scope · 6. Feasibility study · 7. Functional requirements ·
8. Non-functional requirements · 9. Technology stack · 10. System architecture ·
11. Module descriptions · 12. Database design · 13. Recommendation algorithm ·
14. AI / natural-language layer · 15. API design · 16. Frontend design ·
17. Safety, ethics & data protection · 18. Testing & quality assurance ·
19. Results & verification · 20. Project schedule (stages) ·
21. Requirements not implemented in this submission · 22. Limitations ·
23. Future scope · 24. Conclusion · 25. References · 26. Appendix (layout & run guide)

---

## 1. Abstract summary

MediAccess AI helps users discover healthcare providers by specialization,
location, budget, availability, rating and language. It combines a FastAPI
REST backend, a MongoDB database of 36 clearly-labelled demo providers, a
deterministic weighted recommendation engine, an optional LLM-backed
natural-language parser with an offline fallback, and a React single-page
frontend. A safety guardrail refuses diagnosis, medication and treatment
requests. The system is verified by 71 automated tests plus live end-to-end
probing. The full abstract is in [`docs/abstract.md`](abstract.md).

## 2. Introduction & background

Healthcare navigation — finding the right doctor rather than receiving medical
advice — is a recurring information problem. Provider information is scattered
across directories, hospital websites and maps with inconsistent
specialization names, fees, languages and availability. Patients frequently
over-filter or under-filter because the interfaces offer either rigid filter
forms or opaque "AI suggestions" that cannot explain their rankings.

MediAccess AI is a college project that demonstrates a full vertical slice of
modern web application engineering applied to this domain: typed REST API,
document database with real indexes, deterministic ranking that can be
explained and unit-tested, an NLP front door with explicit safety boundaries,
and a component-based frontend — all verified by an automated test suite.

## 3. Problem statement

Design and implement a system that:

1. Stores and serves healthcare provider metadata (specialization, location,
   fee, rating, languages, availability) with efficient filtering.
2. Ranks matching providers by a **transparent, reproducible** scoring model
   combining budget, distance, availability, rating and language.
3. Accepts **natural-language requests** (e.g. *"a dermatologist near
   Bangalore under ₹700 today"*) and maps them to structured search criteria.
4. Never crosses into clinical territory: no diagnosis, no medication advice,
   no treatment recommendations.
5. Degrades honestly: if the database is down, report 503/degraded states
   instead of inventing data; if no LLM is available, parsing still works via
   a deterministic fallback.

## 4. Objectives

| # | Objective | Status |
|---|---|---|
| O1 | Build a FastAPI backend with health, provider, recommendation and AI-search endpoints | Achieved (6 endpoints) |
| O2 | Persist providers in MongoDB (Docker) with an idempotent, self-verifying seed | Achieved (36 docs, 5 indexes) |
| O3 | Implement a deterministic weighted recommendation algorithm with score breakdowns | Achieved (0–100 score, 33 unit tests) |
| O4 | Implement natural-language parsing behind an LLM provider abstraction with fallback | Achieved (offline-capable) |
| O5 | Enforce a medical-safety guardrail before any query processing | Achieved (refusal verified) |
| O6 | Deliver a React UI for search, results and provider details | Achieved (3 pages) |
| O7 | Verify the whole system with automated tests and live probing | Achieved (71 tests) |

## 5. Scope

**In scope (implemented):** provider search and detail retrieval; deterministic
recommendation with explanations; natural-language query parsing (LLM
optional); health checks including honest database states; Dockerised MongoDB
with seed script; React frontend; automated backend test suite; documentation
set (architecture, database, algorithm, API, testing, this report).

**Explicitly out of scope:** authentication/user accounts, appointment booking
or real availability, real provider or patient data, medical advice of any
kind, cloud deployment, and CI/CD pipelines. Items 1, 4 and 6 are frequently
requested by submission templates — section 21 documents their status
honestly.

## 6. Feasibility study

- **Technical:** every component runs on a single development machine
  (Python 3.12, Node.js, Docker Desktop). No external service is *required* —
  the LLM is optional by design; MongoDB is containerised. All libraries are
  mainstream and actively maintained (FastAPI, Pydantic v2, PyMongo async API,
  React 19, Vite 7, Tailwind CSS 4).
- **Operational:** one `docker compose up -d mongodb`, one `uvicorn` command,
  one `npm run dev`. The seed script is idempotent and self-verifying, so
  environment setup is repeatable.
- **Economic:** zero licensing or hosting cost for development; the optional
  LLM API is pay-per-use and can remain unconfigured.

## 7. Functional requirements

| ID | Requirement | Implemented by |
|---|---|---|
| FR1 | Report service health, including database reachability | `GET /api/health`, `GET /api/health/database` |
| FR2 | Search providers by specialization, city, area, budget, rating, language, availability (AND logic, case-insensitive) | `GET /api/providers` |
| FR3 | Retrieve a single provider by id (404 if unknown) | `GET /api/providers/{id}` |
| FR4 | Rank matching providers 0–100 with component breakdown and reasons | `POST /api/recommendations` |
| FR5 | Parse a natural-language request into search criteria and return ranked results | `POST /api/ai/search` |
| FR6 | Refuse diagnosis/medication/treatment requests with a safe message | guardrail in `ai/` (before parsing) |
| FR7 | Provide guidance when a query contains no usable criteria | `ai.parse_query` guidance path |
| FR8 | Load demo data repeatably without duplicates | `database/seed.py` (upsert by id) |
| FR9 | Browse providers in a web UI (search → results → details) | frontend pages |
| FR10 | Surface database failure as 503/`degraded`, never fabricated data | all data routers + health |

## 8. Non-functional requirements

- **Reliability:** DB outage → HTTP 503 with actionable message; health
  endpoint reports `degraded`; recovery requires no restart.
- **Performance:** filtering executes inside MongoDB as one indexed query;
  the test suite runs in about a second; the frontend ships as a Vite
  production build.
- **Testability:** algorithm and parsers are FastAPI-independent modules; the
  unit suite runs without Docker (`DATABASE_MODE=memory`).
- **Security/privacy:** no secrets in code (`.env.example` only); LLM keys
  stay server-side; health endpoints expose no connection strings; query text
  is logged as *length only*, never content; MongoDB bound to loopback.
- **Maintainability:** layered architecture (router → service → database),
  Pydantic schemas at every boundary, type hints throughout, docstrings on
  every module.
- **Honesty:** demo data always marked (`is_demo: true`); disclaimers on every
  user-facing surface; documentation describes only features that exist.

## 9. Technology stack

| Layer | Technology | Version/notes |
|---|---|---|
| Frontend | React, React Router, Vite, Tailwind CSS | React 19, Vite 7, Tailwind 4 |
| Backend | Python, FastAPI, Pydantic, Uvicorn | Pydantic v2, async endpoints |
| Database | MongoDB via Docker (`mongo:8`) | PyMongo `AsyncMongoClient` |
| AI layer | OpenAI-compatible chat-completions API behind `LLMProvider` abstraction | Optional; deterministic fallback parser always available |
| Testing | pytest (+ `TestClient`), offline LLM stubs | 71 tests |
| Tooling | Docker Compose, Git | Seed script in Python |

*(An earlier draft of the README listed JWT, Jenkins, SonarQube and GCP in this
table; those were intended features, not implemented ones — see section 21.)*

## 10. System architecture

The system has three tiers: React SPA → FastAPI REST API → MongoDB, with two
in-process engines (recommendation, fallback parsing) and one optional external
service (LLM API). Full Mermaid diagrams (context, backend layering, AI
pipeline, deployment) are in [`docs/architecture-diagram.md`](architecture-diagram.md).

Layering rule: **router → service → database**. Routers translate HTTP, never
build queries; services hold business logic, never build responses; all data
access is funnelled through `app/database.py`, which abstracts the two modes
(`mongodb` / `memory`) and raises `DatabaseUnavailableError` so routers can
return an honest 503.

## 11. Module descriptions

| Module | Responsibility |
|---|---|
| `backend/app/main.py` | App creation, CORS, lifespan (connect/seed-ready), router wiring, `/docs` |
| `backend/app/config.py` | Pydantic settings from env/`.env` (modes, URI, LLM key — placeholder section for future auth) |
| `backend/app/database.py` | Async client lifecycle, ping, mode switch, `DatabaseUnavailableError` |
| `backend/app/routers/*` | 6 endpoints across health, providers, recommendations, AI search |
| `backend/app/schemas/*` | Pydantic request/response models (health, provider, recommendation, AI) |
| `backend/app/services/provider_service.py` | Hard filtering — one AND query in MongoDB, equivalent semantics in memory mode |
| `backend/app/services/recommendation_service.py` | Deterministic weighted scoring, Haversine distance, reasons, stable sort |
| `backend/app/data/providers.py` | The 36-record demo dataset (single source of truth) |
| `ai/` (repo root) | LLM abstraction: `base` (interfaces), `prompts` (system prompt, unsafe patterns, messages), `provider` (HTTP client), `parser` (orchestration + guardrail), `fallback_parser` (regex) |
| `database/seed.py` | Idempotent, verifying upsert of demo data |
| `frontend/src/*` | `api.js` client, `App.jsx` shell/routes/disclaimer, `pages/` Home, Search, ProviderDetails |
| `tests/*` | 71 tests: unit (memory), AI regression (offline), MongoDB integration |

## 12. Database design

MongoDB 8 in Docker, database `medaccess`, one collection `providers`, 36
documents validated by the `Provider` Pydantic schema. Five indexes support
the query patterns (`unique id`, `city`, `specialization`, `consultation_fee`,
`rating`). Text filters become case-insensitive unanchored regexes; budget and
rating become `$lte`/`$gte`; everything combines with AND inside a single
query. Seeding is idempotent (`replace_one` upsert by `id`) and self-verifying
(exits non-zero unless exactly 36 demo documents exist). Full field-level
documentation: [`docs/database-design.md`](database-design.md).

## 13. Recommendation algorithm

Two phases: **hard filters first** (provider service), then **weighted
scoring** of survivors:

```
match_score = budget×0.30 + distance×0.25 + availability×0.20
            + rating×0.15 + language×0.10        (0–100, rounded)
```

Unsupplied preferences score a neutral 50 so they neither reward nor penalise.
Distance is Haversine-based with a 2 km plateau then an 8 km half-life decay;
over-budget fees decay proportionally (`100 × budget / fee`). Results are
sorted by score desc, rating desc, fee asc, id asc (fully stable). Every item
returns `score_breakdown` and data-derived `reasons`. Worked example and full
specification: [`docs/recommendation-algorithm.md`](recommendation-algorithm.md).

## 14. AI / natural-language layer

Pipeline for `POST /api/ai/search`:

1. **Safety guardrail** (`has_unsafe_intent`, regex patterns for diagnosis,
   medication, prescription, symptoms, treatment wording) runs **before any
   parsing or LLM call** and returns a refusal message with zero results.
2. **Parsing** (`ai.parse_query`): if `LLM_API_KEY` is configured, an
   OpenAI-compatible chat-completions call uses a strict system prompt to
   return JSON criteria; the JSON is validated against
   `ParsedHealthcareQuery`. On missing key, HTTP error, timeout or invalid
   output, control falls to…
3. **Deterministic fallback parser**: keyword/regex extraction of
   specialization, city (with city-name synonyms and case-insensitive
   matching), budget, rating, language and today-availability.
4. **Guidance**: if no criteria are extractable, a fixed message asks the user
   for the basics instead of returning noise.
5. The parsed criteria are then filtered (MongoDB) and ranked by the same
   deterministic engine (top 5). The response's `parser` field (`llm` /
   `fallback`) records which path ran.

The AI layer only ever *parses the user's query*: it never ranks, never reads
provider records, never sees API keys (the server holds them; the browser
calls only the backend), and never produces clinical output.

## 15. API design

Six REST endpoints (details, example payloads and status codes:
[`docs/api-reference.md`](api-reference.md)):

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness; `degraded` when DB unreachable |
| GET | `/api/health/database` | DB ping without leaking configuration |
| GET | `/api/providers` | Filtered search (7 optional filters, AND logic) |
| GET | `/api/providers/{id}` | Single record (404 if unknown) |
| POST | `/api/recommendations` | Filter → deterministic ranking (limit 1–20) |
| POST | `/api/ai/search` | Natural language → parse → filter → rank (top 5) |

Cross-cutting response conventions: Pydantic validation → 422; database
unreachable in `mongodb` mode → 503 with an actionable message; safety
refusal/guidance → 200 with `message` and `count: 0` (the request itself was
well-formed — the content was declined, not the protocol). Swagger UI at
`/docs` doubles as live documentation.

## 16. Frontend design

React 19 + Vite 7 + Tailwind CSS 4, React Router.

| Route/page | Behaviour |
|---|---|
| `/` (`Home.jsx`) | Hero, project explanation, demo-data notice, disclaimer |
| `/search` (`Search.jsx`) | Filter form + results list (count, cards, links); natural-language input via `askAi()` → `POST /api/ai/search` |
| `/providers/:id` (`ProviderDetails.jsx`) | Full record: fees, languages, availability, coordinates; 404 state; "sample DEMO data" notice |

`api.js` is the single HTTP client (base URL from `VITE_API_BASE_URL`,
default `http://127.0.0.1:8000`); it standardises error extraction from
FastAPI `detail` bodies. The medical disclaimer is a single exported constant
rendered in the footer of every page. The browser never holds API keys and
never calls any LLM directly. Production build (`npm run build`) verified.

## 17. Safety, ethics & data protection

- **Navigation, not medicine:** the system never diagnoses, prescribes or
  suggests treatments. This is enforced in code (guardrail patterns), in text
  (system prompt forbids clinical replies), and in UI (disclaimer on every
  page) — and verified by tests and live probes.
- **Guardrail ordering:** unsafe intent is detected *before* any parsing or
  network call, so a refused query generates no LLM traffic at all.
- **Demo data only:** every provider document carries `is_demo: true`;
  names, hospitals, coordinates and availability are fictional; the UI and
  docs repeat this notice.
- **No personal data:** there are no users, no accounts and no health records
  in the system; natural-language queries are logged as a *length only*.
- **Secrets hygiene:** API keys are environment variables; `.env` is
  git-ignored; `.env.example` contains placeholders only; health endpoints
  never expose connection strings.

## 18. Testing & quality assurance

71 automated tests (full detail and commands:
[`docs/testing.md`](testing.md)):

| Group | Count | What it proves |
|---|---|---|
| Provider API unit (memory mode) | 15 | Filter semantics, case-insensitivity, 404s, no DB needed |
| Recommendation algorithm | 33 | Exact scores, neutral-score behaviour, tie-breaking, distance math, reasons |
| AI parsing regression | 14 | Fallback extraction (case-insensitive), synonyms, guardrail-before-LLM, fallback on LLM failure, LLM path with valid JSON, guidance |
| MongoDB integration (live DB) | 9 | Connect/ping, idempotent seed = 36 docs, real filter queries, provenance |

Result on this machine: **71 passed** (`0.90 s`), including all integration
tests against the Dockerised MongoDB. Frontend: Vitest is configured but no
component tests exist yet — disclosed honestly in `docs/testing.md`.

## 19. Results & verification

Beyond automated tests, the running system was probed end-to-end (all observed
passing):

| Verification | Observed result |
|---|---|
| Health + DB health with container up | `healthy` / `database: "mongodb"` |
| Combined provider filters | Correct AND results, case-insensitive text matching |
| Recommendation acceptance case | `match_score` 77 with a consistent `score_breakdown` |
| AI search, natural-language query | Parsed criteria, ranked results, `parser: "fallback"` (no LLM key configured) |
| AI search, "Do I have …?" query | Safety refusal message, `count: 0`, no results |
| Stop MongoDB container | Data endpoints → 503 with actionable detail; `/api/health` → `degraded` |
| Restart MongoDB | Immediate recovery, no application restart |
| Mutate a seeded document | Change visible in the API response (true provenance, no caching fiction) |
| Re-run seed script | Still exactly 36 documents (idempotent) |
| `npm run build` | Successful production build (`frontend/dist`) |
| Full test suite | 71/71 passed |

## 20. Project schedule (development stages)

| Stage | Description | Status |
|---|---|---|
| 1 | Project foundation (structure, initial docs) | ✅ Complete |
| 2 | FastAPI backend + `/api/health` | ✅ Complete |
| 3 | Demo provider dataset + provider search API | ✅ Complete |
| 4 | Deterministic recommendation engine | ✅ Complete |
| 5 | MongoDB (Docker) + idempotent seed + integration tests | ✅ Complete |
| 6 | React + Vite frontend (search, results, details) | ✅ Complete |
| 7 | AI natural-language parsing with safety guardrail + fallback | ✅ Complete |
| 8 | Submission documentation, regression testing, final verification | ✅ Complete (71/71 green) |

## 21. Requirements not implemented in this submission

Some items commonly required by submission templates are **not present in this
repository**. They are listed here explicitly so the report never claims
features that do not exist:

| Template item | Actual status in this repository |
|---|---|
| User authentication (JWT / bcrypt / login) | **Not implemented.** `config.py` contains only environment *placeholders* (secret key, algorithm, token expiry) marked "reserved for a later stage"; no login endpoint, no token issuing/validation, no password hashing anywhere. |
| Appointment booking module | **Not implemented.** `available_days` / `available_slots` are static demo fields for filtering only; no booking API, no booking UI, no appointment collection. |
| CI/CD pipeline (Jenkins / GitHub Actions) | **Not implemented.** No `Jenkinsfile`, no workflow files; tests are run manually (commands in `docs/testing.md`). |
| Code quality gate (SonarQube) | **Not implemented.** No Sonar configuration in the repository. |
| Cloud deployment (GCP or other) | **Not implemented.** The application runs locally; `docker-compose.yml` provisions MongoDB only. |
| Frontend automated tests | **Partially prepared:** Vitest + Testing Library are installed and configured, but no `*.test.jsx` files exist yet. |

If a submission checklist requires any of these, the honest options are: (a)
mark them as future work citing this section, or (b) implement them in a
follow-up submission — the codebase is structured to make (b) straightforward.

## 22. Limitations

1. Demo dataset is small (36 providers, 5 cities' worth of variety) — fine for
   demonstration, not for production coverage.
2. LLM parsing is untested against a live model in this submission (no API key
   available); the LLM code path is exercised only with stubbed providers, and
   real queries fall back to the deterministic parser — the `parser` field
   makes this visible.
3. Fallback parsing is keyword/regex based: it handles common phrasings and
   synonyms but is not a general NLP parser.
4. Distance scoring requires coordinates supplied by the caller; there is no
   geocoding or browser geolocation integration yet.
5. No authentication, rate limiting or per-user state (by scope, section 21).
6. Single-node setup: no replication, sharding or horizontal scaling story.

## 23. Future scope

- JWT authentication with roles (patient / admin) — config placeholders already
  reserved.
- Appointment request workflow (new `appointments` collection + endpoints),
  clearly separated from real-world availability claims.
- Geolocation in the frontend to feed `latitude`/`longitude` automatically.
- CI pipeline (GitHub Actions) running unit tests on push and integration
  tests against a MongoDB service container; SonarQube quality gate.
- Live LLM evaluation harness with fixed prompts and regression fixtures.
- Containerising the backend/frontend for cloud deployment (Cloud Run/GKE or
  similar) with managed MongoDB Atlas.

## 24. Conclusion

MediAccess AI delivers a complete, honestly documented healthcare-navigation
demonstrator: a typed FastAPI REST API over a Dockerised MongoDB with real
indexes and idempotent seeding; a transparent, fully unit-tested
recommendation algorithm whose every score can be explained component by
component; a natural-language front door with an explicit medical-safety
guardrail and an offline-capable deterministic fallback; a clean React
frontend carrying its disclaimer on every page; and 71 automated tests plus a
record of live end-to-end verification. Equally important, the report states
clearly what the system does **not** contain (authentication, appointment
booking, CI/CD, cloud deployment) rather than overstating the work — the
verification tables in section 19 can be reproduced by anyone following the
run guide in the appendix.

## 25. References

1. FastAPI documentation — https://fastapi.tiangolo.com/
2. Pydantic v2 documentation — https://docs.pydantic.dev/
3. MongoDB manual: indexes and queries — https://www.mongodb.com/docs/manual/
4. PyMongo async API — https://pymongo.readthedocs.io/
5. React documentation — https://react.dev/
6. Vite guide — https://vite.dev/guide/
7. Tailwind CSS documentation — https://tailwindcss.com/docs
8. Haversine formula — https://en.wikipedia.org/wiki/Haversine_formula
9. OpenAI Chat Completions API (compatible endpoint used by `ai/provider.py`)
10. Twelve-Factor App (configuration in the environment) — https://12factor.net/
11. OWASP API Security Top 10 (threat model informing the "no secrets in the
    client" rule) — https://owasp.org/API-Security/
12. Docker Compose documentation — https://docs.docker.com/compose/

## 26. Appendix — repository layout & run guide

```
medaccess/
├── backend/            FastAPI app (app/{main,config,database}.py,
│   │                   routers/, schemas/, services/, data/), .venv, requirements
│   └── README.md       backend-specific docs
├── ai/                 framework-independent parsing package (6 modules)
├── database/seed.py    idempotent MongoDB seeder (verifies 36 docs)
├── frontend/           React 19 + Vite 7 + Tailwind 4 SPA (npm run dev/build)
├── tests/              71 pytest tests (unit + AI regression + integration)
├── docs/               this report + abstract, architecture, database,
│                       algorithm, API, testing documents
├── docker-compose.yml  MongoDB 8 service (loopback only, healthcheck)
├── .env.example        all configuration keys (placeholders)
└── README.md           project overview & quick start
```

Run everything (Windows, from the repository root):

```powershell
# 1. Database
docker compose up -d mongodb
backend\.venv\Scripts\python.exe database\seed.py        # idempotent

# 2. Backend → http://127.0.0.1:8000  (Swagger: /docs)
$env:DATABASE_MODE = 'mongodb'
& .\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend `
  --reload --host 127.0.0.1 --port 8000

# 3. Frontend → http://127.0.0.1:5173
cd frontend; npm install; npm run dev

# 4. Tests (unit only, or full suite)
& .\backend\.venv\Scripts\python.exe -m pytest tests/ -q
$env:RUN_MONGO_INTEGRATION = '1'; $env:DATABASE_MODE = 'mongodb'
& .\backend\.venv\Scripts\python.exe -m pytest tests/ -q   # 71 expected
```

Glossary: **navigation** = finding providers, never medical advice ·
**fallback parser** = deterministic regex parser used when no LLM is configured
· **match score** = weighted 0–100 ranking output · **demo data** = fictional
records flagged `is_demo: true`.

— End of report —





