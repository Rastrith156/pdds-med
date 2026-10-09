# Recommendation Algorithm

Module: `backend/app/services/recommendation_service.py`
Tested by: `tests/test_recommendation_service.py` (33 tests).

## 1. Design principles

1. **Deterministic** — no LLM, no randomness, no time-dependent surprises
   (except the weekday used for availability, which tests can override).
   Identical inputs always produce identical rankings.
2. **Transparent** — every response carries a `score_breakdown` (the five
   normalized component scores) and human-readable `reasons`, so any ranking
   can be explained to the user.
3. **Two-phase: filter, then rank.** Hard constraints (specialization, city,
   maximum budget, minimum rating, …) are applied first as filters by
   `provider_service`; the scoring engine only ranks the surviving candidates.
4. **Neutral when unconstrained** — a preference the user did not supply
   contributes `NEUTRAL_SCORE = 50` so it neither rewards nor penalises anyone.

## 2. The formula

```
match_score = budget      × 0.30
            + distance    × 0.25
            + availability× 0.20
            + rating      × 0.15
            + language    × 0.10
```

Each component is normalized to 0–100; the weighted sum is rounded to an
integer in 0–100.

| Component | Rule | Score |
|---|---|---|
| **budget** | fee ≤ budget (incl. exact match) | 100 |
| | fee > budget | `100 × budget / fee` (fee = 2× budget → 50; 10× → 10) |
| | budget not supplied | 50 (neutral) |
| **distance** | Haversine km ≤ 2 | 100 |
| | > 2 km | `100 × 0.5^((km − 2) / 8)` — 8 km half-life beyond the first 2 km |
| | coordinates not supplied | 50 (neutral; `distance_km` stays `null` — a distance is never invented) |
| **availability** | today requested + provider available | 100 |
| | today requested + not available | 0 |
| | not requested | 50 (neutral) |
| **rating** | provider rating 0–5 | `rating / 5 × 100` (4.5 → 90) |
| **language** | requested + supported (case-insensitive) | 100 |
| | requested + unsupported | 0 |
| | not requested | 50 (neutral) |

Distance uses the great-circle **Haversine** formula with Earth radius
6 371 km over WGS-84 coordinates.

## 3. Worked example (the Stage 4 acceptance case)

Request: `{ "maximum_budget": 700, "latitude": 12.97, "longitude": 77.59,
"available_today": true, "language": "Kannada", "limit": 5 }`
— provider: fee ₹650, rating 4.6, 1.4 km away, available today, speaks Kannada.

```
budget       = 100            (650 ≤ 700)
distance     = 100            (1.4 km ≤ 2)
availability = 100            (available today)
rating       = 4.6/5 × 100 = 92
language     = 100            (Kannada supported)
match_score  = 100×.30 + 100×.25 + 100×.20 + 92×.15 + 100×.10
             = 30 + 25 + 20 + 13.8 + 10 = 98.8 → 99 (rounded)
```

The response also returns `distance_km: 1.4` and reasons such as
"Within budget", "Available today", "High provider rating", "Located nearby".

## 4. Ranking and tie-breaking

Results are sorted by:

1. `match_score` **descending**,
2. provider `rating` **descending**,
3. `consultation_fee` **ascending**,
4. provider `id` **ascending** (guarantees a stable, repeatable order).

Then the top `limit` items are returned (`limit` ∈ 1–20 for
`POST /api/recommendations`; the AI search endpoint uses a fixed limit of 5).

## 5. Response shape

```json
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

## 6. Why deterministic instead of an LLM?

- **Explainability** — a candidate can show exactly which component produced
  a score; an LLM cannot justify weights this precisely.
- **Reproducibility** — examiners can re-run the same request and obtain the
  same ranking; unit tests can assert exact numbers (the suite contains 33
  such tests).
- **Safety** — ranking never involves free-text generation, so it cannot
  hallucinate provider attributes. The AI layer is confined to *parsing the
  user's query*, and the engine always ranks with verified database fields.
