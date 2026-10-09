# System Architecture

Diagrams use [Mermaid](https://mermaid.js.org/). They render automatically on
GitHub and in any Mermaid-enabled Markdown viewer (VS Code extensions,
Typora, etc.).

## 1. High-level system context

```mermaid
flowchart LR
    U["User (browser)"] -->|"HTTP / JSON (REST)"| FE["Frontend<br/>React 19 + Vite 7 + Tailwind CSS 4<br/>frontend/"]
    FE -->|"REST calls<br/>(base URL = VITE_API_BASE_URL)"| API["Backend<br/>FastAPI (Python 3.12+)<br/>backend/app"]
    API -->|"Single filtered queries<br/>(pymongo AsyncMongoClient)"| DB[("MongoDB 8 (Docker)<br/>medaccess.providers<br/>36 demo docs / 5 indexes")]
    API -->|"Optional: parse only<br/>(server-side, never from browser)"| LLM["LLM API<br/>(OpenAI-compatible,<br/>only if LLM_API_KEY set)"]
    API --- ENG["Recommendation engine<br/>(deterministic, in-process)"]
    API --- FBP["Fallback parser<br/>(regex, in-process)"]
```

Key rules visible in this diagram:

- The browser calls **only** the FastAPI backend; no API key ever ships to the
  frontend.
- The LLM (when configured) is called **by the backend**, only to parse the
  user's query into search parameters — never to rank, never to access data.
- If no LLM is configured, parsing degrades to the in-process fallback parser.

## 2. Backend internal structure (layered)

```mermaid
flowchart TD
    subgraph "backend/app (FastAPI)"
        MAIN["main.py<br/>app factory, CORS, router wiring, /docs"]
        subgraph "Routers (HTTP layer)"
            RH["health.py<br/>/api/health, /api/health/database"]
            RP["providers.py<br/>/api/providers, /api/providers/{id}"]
            RR["recommendations.py<br/>/api/recommendations"]
            RA["ai_search.py<br/>/api/ai/search"]
        end
        subgraph "Schemas (Pydantic)"
            SH["health / provider / recommendation / ai"]
        end
        subgraph "Services (business logic)"
            PS["provider_service<br/>hard filtering"]
            RS["recommendation_service<br/>weighted scoring 0-100"]
        end
        DB["database.py<br/>mongodb | memory modes,<br/>DatabaseUnavailableError"]
    end
    AI["ai/ package (repository root)<br/>base · prompts · provider · parser · fallback_parser"]
    DATA["data/providers.py<br/>36 DEMO providers (source of truth)"]
    MONGO[("MongoDB")]

    MAIN --> RH & RP & RR & RA
    RH & RP & RR & RA --> SH
    RR --> PS --> DB
    RR --> RS
    RA --> AI
    RA --> PS
    RA --> RS
    DB --> MONGO
    PS --> DATA
```

Layering rule: **router → service → database**. Routers never build queries;
services never build HTTP responses. `recommendation_service` is deliberately
FastAPI-free so the algorithm can be unit-tested without a server.

## 3. AI search request pipeline (Stage 7)

```mermaid
flowchart LR
    Q["POST /api/ai/search<br/>{query}"] --> G{"Safety guardrail<br/>has_unsafe_intent()"}
    G -->|"diagnosis / medication /<br/>treatment wording"| REF["Refusal message<br/>count = 0"]
    G -->|"safe navigation query"| P["ai.parse_query()"]
    P -->|"LLM configured"| LLM["LLM returns JSON criteria"]
    P -->|"no key / failure /<br/>invalid JSON"| FB["Regex fallback parser"]
    LLM --> V{"validated +<br/>has criteria?"}
    V -->|"no"| FB
    V -->|"yes"| FILTER
    FB --> FILTER{"Hard filters<br/>provider_service<br/>(MongoDB AND-query)"}
    FILTER --> RANK["Deterministic ranking<br/>recommendation_service<br/>(top 5)"]
    RANK --> RES["AISearchResponse<br/>{query, parser, parsed_request,<br/>message, count, recommendations}"]
```

`parser` in the response is `"llm"` or `"fallback"`, so the path actually taken
is always visible and testable.

## 4. Deployment topology (local development)

```mermaid
flowchart TB
    subgraph "Developer machine"
        subgraph "Docker Compose (docker-compose.yml)"
            M["medaccess-mongodb<br/>mongo:8, healthcheck: mongosh ping<br/>127.0.0.1:27017 (loopback only)<br/>volume: medaccess_mongodb_data"]
        end
        B["Backend: uvicorn app.main:app<br/>127.0.0.1:8000<br/>(backend/.venv)"]
        F["Frontend: npm run dev<br/>127.0.0.1:5173 → proxies API origin<br/>npm run build → frontend/dist"]
        S["database/seed.py<br/>idempotent upsert by id"]
    end
    B --> M
    S --> M
    F --> B
```

Only MongoDB runs in Docker; backend and frontend run directly on the host.
The database port is bound to `127.0.0.1` so it is never reachable from other
machines in local development.
