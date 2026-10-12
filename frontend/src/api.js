// API client — all backend calls go through FastAPI.
// ONLY the base URL is configurable (VITE_API_BASE_URL); no keys ever live
// in the frontend (the LLM is called by the backend, never the browser).

const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* keep default detail */
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

/** GET /api/providers with optional filters (all values omitted when empty). */
export function searchProviders(filters = {}) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === null || value === undefined || value === "") continue;
    params.set(key, String(value));
  }
  const qs = params.toString();
  return request(`/api/providers${qs ? `?${qs}` : ""}`);
}

/** GET /api/providers/{id} */
export function getProvider(id) {
  return request(`/api/providers/${encodeURIComponent(id)}`);
}

/** POST /api/ai/search — natural-language query (Stage 7). */
export function askAi(query) {
  return request("/api/ai/search", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

/** GET /api/openproject/ — server-proxied project overview and work packages. */
export function getOpenProjectOverview() {
  return request("/api/openproject/");
}

/** GET /api/openproject/work-packages/{id} — server-proxied task details. */
export function getOpenProjectWorkPackage(id) {
  return request(`/api/openproject/work-packages/${encodeURIComponent(id)}`);
}
