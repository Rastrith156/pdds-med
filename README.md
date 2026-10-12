# MediAccess AI

> An AI-powered **healthcare navigation and provider recommendation platform**.
> It helps users find suitable healthcare providers based on specialization,
> location, budget, availability, distance, rating and language preferences.

---

## ⚠️ Important Disclaimer

**MediAccess AI provides healthcare navigation and provider information. It does
not diagnose conditions or replace professional medical advice.**

- This system **must never** diagnose diseases, prescribe medicines, or make
  treatment decisions.
- All provider data in this project is **clearly labelled demo/sample data**.
  It is fictional and does not describe real people or real clinics.
- No real appointment availability is simulated — availability fields are part
  of the demo dataset only.

---

## 🎯 Project Purpose

Finding the right healthcare provider is hard: users must compare
specializations, fees, distances, ratings, languages and availability across
fragmented sources. MediAccess AI provides:

1. **Provider Search API** — filter demo providers by specialization, city,
   budget, rating, language and availability.
2. **Deterministic Recommendation Engine** — ranks providers with a transparent,
   testable scoring formula (budget, distance, availability, rating, language).
3. **Natural-language Search (AI)** — parses requests like *"I need a
   dermatologist near Bangalore under ₹700 today"* into structured search
   filters, behind a swappable LLM provider abstraction with a deterministic
   fallback parser for offline development.
4. **Web Frontend** — React + Vite + Tailwind UI for search, results and
   provider details.

---

## 🏗️ Architecture

```text
┌────────────────────┐        ┌───────────────────────────────┐
│  React + Vite UI   │ ─────► │   FastAPI Backend             │
│  (frontend/)       │  REST  │   (backend/app)               │
└────────────────────┘        │                               │
                              │  GET  /api/health             │
                              │  GET  /api/health/database    │
                              │  GET  /api/providers          │
                              │  GET  /api/providers/{id}     │
                              │  POST /api/recommendations    │
                              │  POST /api/ai/search          │
                              └────────┬──────────────────────┘
                                       │
              ┌────────────────────────┼───────────────────────┐
              ▼                        ▼                       ▼
   ┌──────────────────┐    ┌─────────────────────┐   ┌────────────────────┐
   │ Recommendation   │    │ AI parsing (ai/)    │   │ MongoDB 8          │
   │ engine           │    │ safety guardrail →  │   │ (Docker)           │
   │ (deterministic)  │    │ optional LLM →      │   │ medaccess.providers│
   │                  │    │ regex fallback      │   │ 36 demo docs       │
   └──────────────────┘    └─────────────────────┘   └────────────────────┘
```

**Directory layout**

| Path            | Purpose                                             |
|-----------------|-----------------------------------------------------|
| `frontend/`     | React + Vite + Tailwind CSS single-page application |
| `backend/`      | FastAPI application (API, services, schemas, utils) |
| `ai/`           | LLM provider abstraction + navigation-query parser  |
| `database/`     | Idempotent MongoDB seed script                      |
| `tests/`        | Cross-cutting tests (unit, AI regression, MongoDB integration) |
| `docs/`         | Project report, abstract, architecture, DB, algorithm, API, testing docs |
| `deployment/`   | Reserved for deployment configuration (empty)       |

---

## 🛠️ Technology Stack

| Layer          | Technology                                        |
|----------------|---------------------------------------------------|
| Frontend       | React 19, Vite 7, Tailwind CSS 4, React Router    |
| Backend        | Python 3.12+, FastAPI, Pydantic v2, Uvicorn       |
| Database       | MongoDB 8 in Docker (PyMongo async client)        |
| AI             | OpenAI-compatible LLM API (optional) + deterministic fallback parser |
| Testing        | pytest (71 tests: unit + AI regression + MongoDB integration) |
| Containerization | Docker + Docker Compose (MongoDB service)       |

> **Not implemented (honestly disclosed):** user authentication/JWT, appointment
> booking, CI/CD (Jenkins/GitHub Actions), SonarQube and cloud deployment are
> *not* part of this repository. See
> [`docs/MediAccess_AI_Project_Report.md`](docs/MediAccess_AI_Project_Report.md)
> §21 for details.

---

## 📦 Development Status

**All planned stages are complete.**

| Stage | Description                            | Status      |
|-------|----------------------------------------|-------------|
| 1     | Project foundation (structure, docs)   | ✅ Complete |
| 2     | FastAPI backend + `/api/health`        | ✅ Complete |
| 3     | Demo provider data + provider API      | ✅ Complete |
| 4     | Deterministic recommendation engine    | ✅ Complete |
| 5     | MongoDB via Docker + seed script       | ✅ Complete |
| 6     | React + Vite frontend                  | ✅ Complete |
| 7     | AI natural-language parsing + guardrail| ✅ Complete |
| 8     | Final verification + submission docs   | ✅ Complete |

Verification: **71/71 automated tests pass** (including live MongoDB
integration), frontend production build succeeds, and the running system was
probed end-to-end (filters, ranking, AI search, safety refusal, DB failure →
503 → recovery, seed idempotency). Details: [`docs/testing.md`](docs/testing.md).

---

## 🚀 Getting Started (Windows)

**Prerequisites:** Python 3.12+, Node.js 18+, Docker Desktop, Git.

```powershell
# 1. Clone and enter the project
git clone https://github.com/Rastrith156/medaccess.git
cd medaccess

# 2. Local environment file (never commit it)
Copy-Item .env.example .env

# 3. Database — MongoDB in Docker + idempotent seed (36 demo providers)
docker compose up -d mongodb
backend\.venv\Scripts\python.exe database\seed.py
# (First time only: create the venv —
#  cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1;
#  pip install -r requirements.txt -r requirements-dev.txt; cd ..)

# 4. Backend → http://127.0.0.1:8000  (Swagger UI at /docs)
$env:DATABASE_MODE = 'mongodb'
& .\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend `
  --reload --host 127.0.0.1 --port 8000

# 5. Frontend (new terminal) → http://127.0.0.1:5173
cd frontend
npm install
npm run dev
```

### Optional OpenProject integration

The OpenProject page is available from the main navigation. To connect it,
configure `OPENPROJECT_URL` (instance base URL), `OPENPROJECT_API_KEY` (an API
token created in your OpenProject profile), and `OPENPROJECT_PROJECT_ID` (the
numeric project ID) in the backend process environment or the root `.env` file.
Copy `.env.example` for the complete list of settings, then restart the backend.
The browser never receives the API token; the backend uses OpenProject REST API
v3 with HTTP Basic authentication (`apikey` username and token password). The
integration remains disconnected until all three values are valid. Details:
[`docs/api-reference.md`](docs/api-reference.md#7-openproject-integration).

**Run the tests** (from the repository root):

```powershell
# Unit tests only — no database required (memory mode)
& .\backend\.venv\Scripts\python.exe -m pytest tests/ -q

# Full suite including MongoDB integration — 71 tests expected
$env:RUN_MONGO_INTEGRATION = '1'
$env:DATABASE_MODE = 'mongodb'
& .\backend\.venv\Scripts\python.exe -m pytest tests/ -q
```

> Tip: if your shell already exports `DATABASE_MODE=memory`, set it back to
> `mongodb` before starting the server or running integration tests.

---

## 📚 Documentation

| Document | Contents |
|----------|----------|
| [`docs/MediAccess_AI_Project_Report.md`](docs/MediAccess_AI_Project_Report.md) | Full 26-section project report (incl. honest "not implemented" section) |
| [`docs/abstract.md`](docs/abstract.md) | Submission abstract |
| [`docs/architecture-diagram.md`](docs/architecture-diagram.md) | Mermaid diagrams: system context, backend layers, AI pipeline, deployment |
| [`docs/database-design.md`](docs/database-design.md) | MongoDB schema, indexes, dual modes, seeding |
| [`docs/recommendation-algorithm.md`](docs/recommendation-algorithm.md) | Scoring formula, worked example, tie-breaking |
| [`docs/api-reference.md`](docs/api-reference.md) | All 6 endpoints with example requests/responses |
| [`docs/testing.md`](docs/testing.md) | Test strategy, commands, verified results |
| [`backend/README.md`](backend/README.md) | Backend-specific run/API notes |

---

## 📄 License & Data Notice

All provider records are **fictional demo data** created for development and
testing. No real personal healthcare information is stored in this repository.
