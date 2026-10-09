# Abstract

**Project title:** MediAccess AI — AI-Powered Healthcare Navigation and Provider
Recommendation Platform

**Keywords:** healthcare navigation, provider recommendation, FastAPI, MongoDB,
React, natural-language processing, deterministic scoring, LLM safety guardrail.

---

## Abstract

Finding a suitable healthcare provider is a recurring real-world problem:
patients must compare specializations, consultation fees, distances, ratings,
languages and availability across fragmented, inconsistent sources, often under
time pressure. **MediAccess AI** is a full-stack web application that helps
users discover and rank healthcare providers using structured filters,
a deterministic recommendation engine, and optional natural-language search.

The platform is built as three cooperating components: a **FastAPI backend**
that exposes six REST endpoints (health, provider search, provider details,
recommendations and AI search), a **MongoDB database** (running in Docker) that
stores a clearly-labelled dataset of 36 fictional demo providers with
query-supporting indexes, and a **React + Vite + Tailwind CSS frontend** that
presents search, results and provider-detail pages.

Recommendations are produced by a **transparent weighted scoring formula**
(budget 30 %, distance 25 %, availability 20 %, rating 15 %, language 10 %)
applied after hard filtering, so identical inputs always yield identical
rankings and every score can be explained component by component. For natural-
language queries such as *"I need a dermatologist near Bangalore under ₹700
today"*, the system parses the request into structured filters behind
a provider abstraction: an optional LLM is used when configured, and
a deterministic regex-based **fallback parser** guarantees the feature works
offline. A **safety guardrail** runs before any parsing and refuses diagnosis,
medication and treatment questions with a healthcare-navigation message — the
system never diagnoses, never prescribes and never sees medical records.

Quality is demonstrated with an automated test suite of **71 tests** (48
in-memory unit tests, 9 MongoDB integration tests and 14 AI-parsing regression
tests), all passing, plus live API verification of filtering, ranking, safety
refusal, database-failure handling (HTTP 503) and data provenance. All
provider records are fictional demo data, and every user-facing surface carries
an explicit medical disclaimer.

**Note on scope:** user authentication, appointment booking and CI/CD pipelines
are *not* implemented in this submission; they are documented as limitations
and future work.
