import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getProvider } from "../api.js";

const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

/** Full provider record — everything is fetched from the live API. */
export default function ProviderDetails() {
  const { id } = useParams();
  const [provider, setProvider] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getProvider(id)
      .then((data) => !cancelled && setProvider(data))
      .catch((err) => !cancelled && setError(err.message || "Failed to load provider"))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) return <p className="mx-auto max-w-3xl px-4 py-10 text-sm text-slate-500">Loading…</p>;

  if (error)
    return (
      <section className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        <Link to="/search" className="mt-4 inline-block text-sm font-medium text-teal-700 hover:underline">
          ← Back to search
        </Link>
      </section>
    );

  const days = [...provider.available_days].sort(
    (a, b) => DAY_ORDER.indexOf(a) - DAY_ORDER.indexOf(b)
  );

  return (
    <section className="mx-auto max-w-3xl px-4 py-8">
      <Link to="/search" className="text-sm font-medium text-teal-700 hover:underline">
        ← Back to search
      </Link>

      <div className="mt-3 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-slate-900">{provider.name}</h1>
            <p className="text-teal-700">{provider.specialization}</p>
          </div>
          <div className="text-right text-sm">
            <p className="text-lg font-semibold text-slate-900">★ {provider.rating}</p>
            <p className="font-semibold text-slate-800">₹{provider.consultation_fee}</p>
          </div>
        </div>

        <dl className="mt-5 grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
          <div><dt className="text-slate-500">Hospital / Clinic</dt><dd className="font-medium">{provider.hospital}</dd></div>
          <div><dt className="text-slate-500">Location</dt><dd className="font-medium">{provider.area}, {provider.city}</dd></div>
          <div><dt className="text-slate-500">Languages</dt><dd className="font-medium">{provider.languages.join(", ")}</dd></div>
          <div><dt className="text-slate-500">Consultation fee</dt><dd className="font-medium">₹{provider.consultation_fee}</dd></div>
          <div><dt className="text-slate-500">Available days</dt><dd className="font-medium">{days.join(", ")}</dd></div>
          <div><dt className="text-slate-500">Available slots</dt><dd className="font-medium">{provider.available_slots.join(", ")}</dd></div>
          <div><dt className="text-slate-500">Verified</dt><dd className="font-medium">{provider.verified ? "Yes" : "No"}</dd></div>
          <div><dt className="text-slate-500">Coordinates (demo)</dt><dd className="font-medium">{provider.latitude}, {provider.longitude}</dd></div>
        </dl>

        <div className="mt-5 flex flex-wrap gap-2">
          {provider.is_demo && (
            <span className="rounded border border-amber-300 bg-amber-50 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-amber-700">
              Demo data — fictional sample record
            </span>
          )}
          {provider.verified && (
            <span className="rounded border border-teal-300 bg-teal-50 px-2 py-1 text-xs font-semibold text-teal-700">
              Verified (demo flag)
            </span>
          )}
        </div>

        <p className="mt-5 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
          Availability shown is sample DEMO data — no real appointments exist.
        </p>
      </div>
    </section>
  );
}
