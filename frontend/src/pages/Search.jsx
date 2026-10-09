import { useEffect, useState } from "react";
import { searchProviders } from "../api.js";
import ProviderCard from "../components/ProviderCard.jsx";

const EMPTY_FILTERS = {
  specialization: "",
  city: "",
  area: "",
  maximum_budget: "",
  minimum_rating: "",
  language: "",
  available_today: false,
};

/** Structured provider search — every result comes from the live FastAPI API. */
export default function Search() {
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const set = (key) => (event) =>
    setFilters((prev) => ({
      ...prev,
      [key]: event.target.type === "checkbox" ? event.target.checked : event.target.value,
    }));

  const run = async (event) => {
    event?.preventDefault();
    setLoading(true);
    setError("");
    try {
      const params = { ...filters };
      params.available_today = params.available_today ? "true" : "";
      setResult(await searchProviders(params));
    } catch (err) {
      setResult(null);
      setError(err.message || "Search failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-900">Search providers</h1>
      <p className="mt-1 text-sm text-slate-500">
        Filter clearly-labelled DEMO providers. All filters combine with AND logic.
      </p>

      <form
        onSubmit={run}
        className="mt-4 grid grid-cols-1 gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        <input className="input" placeholder="Specialization" value={filters.specialization} onChange={set("specialization")} />
        <input className="input" placeholder="City" value={filters.city} onChange={set("city")} />
        <input className="input" placeholder="Area" value={filters.area} onChange={set("area")} />
        <input className="input" type="number" min="1" placeholder="Max budget (₹)" value={filters.maximum_budget} onChange={set("maximum_budget")} />
        <input className="input" type="number" min="0" max="5" step="0.1" placeholder="Min rating (0-5)" value={filters.minimum_rating} onChange={set("minimum_rating")} />
        <input className="input" placeholder="Language" value={filters.language} onChange={set("language")} />
        <label className="flex items-center gap-2 text-sm text-slate-700">
          <input type="checkbox" checked={filters.available_today} onChange={set("available_today")} />
          Available today
        </label>
        <button type="submit" className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800">
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      <style>{`.input{border:1px solid #cbd5e1;border-radius:.5rem;padding:.5rem .75rem;font-size:.875rem}
        .input:focus{outline:2px solid #0d9488;outline-offset:-1px}`}</style>

      {error && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error} — is the backend running at http://127.0.0.1:8000 ?
        </div>
      )}

      {!error && (
        <p className="mt-6 text-sm font-medium text-slate-600">
          {loading ? "Loading…" : `${result?.count ?? 0} healthcare options found`}
        </p>
      )}

      {!error && !loading && result?.count === 0 && (
        <div className="mt-4 rounded-lg border border-slate-200 bg-white px-4 py-6 text-center text-sm text-slate-500">
          No providers match your filters. Try widening the budget or removing a filter.
        </div>
      )}

      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {result?.providers?.map((provider) => (
          <ProviderCard key={provider.id} provider={provider} />
        ))}
      </div>
    </section>
  );
}
