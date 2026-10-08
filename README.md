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

```
┌────────────────────┐        ┌─────────────────────────┐
│  React + Vite UI   │ ─────► │   FastAPI Backend       │
│  (frontend/)       │  REST  │   (backend/app)         │
└────────────────────┘        │                         │
                              │  /api/health            │
                              │  /api/providers         │
                              │  /api/recommendations   │
                              └────────┬────────────────┘
                                       │
              ┌────────────────────────┼───────────────────────┐
              ▼                        ▼                       ▼
   ┌──────────────────┐    ┌─────────────────────┐   ┌────────────────────┐
   │ Recommendation   │    │ AI Parser           │   │ MongoDB (Docker)   │
   │ engine           │    │ (ai/) — LLM with    │   │ (database/)        │
   │ deterministic    │    │ fallback parser     │   │ users, providers   │
   └──────────────────┘    └─────────────────────┘   └────────────────────┘
```

**Directory layout**

| Path            | Purpose                                             |
|-----------------|-----------------------------------------------------|
| `frontend/`     | React + Vite + Tailwind CSS single-page application |
| `backend/`      | FastAPI application (API, services, schemas, utils) |
| `ai/`           | LLM provider abstraction and navigation-query parser|
| `database/`     | Seed scripts and database helpers                   |
| `tests/`        | Cross-cutting tests (backend unit tests live here)  |
| `docs/`         | Architecture and process documentation              |
| `deployment/`   | Docker / CI/CD / GCP deployment configuration       |

---

## 🛠️ Technology Stack

| Layer          | Technology                                        |
|----------------|---------------------------------------------------|
| Frontend       | React, Vite, Tailwind CSS                         |
| Backend        | Python, FastAPI, Pydantic, Uvicorn                |
| Database       | MongoDB (running via Docker)                      |
| AI             | LLM API behind a provider abstraction + fallback  |
| Authentication | JWT (JSON Web Tokens)                             |
| Containerization | Docker + Docker Compose                         |
| CI/CD          | Jenkins                                           |
| Code quality   | SonarQube                                         |
| Deployment     | Google Cloud Platform (GCP)                       |

---

## 📦 Development Status

**Phase 1 — in progress.** Incremental build; each stage is verified before the
next begins.

| Stage | Description                            | Status      |
|-------|----------------------------------------|-------------|
| 1     | Project foundation (structure, docs)   | ✅ Complete |
| 2     | FastAPI backend + `/api/health`        | ✅ Complete |
| 3     | Demo provider data + provider API      | ✅ Complete |
| 4     | Deterministic recommendation engine    | ✅ Complete |
| 5     | MongoDB via Docker + seed script       | ⬜ Not started |
| 6     | React + Vite frontend                  | ⬜ Not started |
| 7     | AI natural-language parsing            | ⬜ Not started |
| 8     | Final verification                     | ⬜ Not started |

---

## 🚀 Getting Started (after Stage 2+)

```powershell
# 1. Clone and enter the project
git clone https://github.com/Rastrith156/medaccess.git
cd medaccess

# 2. Create your local environment file (never commit it)
Copy-Item .env.example .env

# 3. Backend (Stage 2+)
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000/docs for Swagger UI
```

Further run instructions will be added as each stage lands.

---

## 📄 License & Data Notice

All provider records are **fictional demo data** created for development and
testing. No real personal healthcare information is stored in this repository.
