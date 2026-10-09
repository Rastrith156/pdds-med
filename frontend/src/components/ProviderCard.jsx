import { Link } from "react-router-dom";

/** Compact provider summary card used in result lists. */
export default function ProviderCard({ provider }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-900">{provider.name}</h3>
          <p className="text-sm text-teal-700">{provider.specialization}</p>
        </div>
        <span className="rounded bg-teal-50 px-2 py-0.5 text-xs font-medium text-teal-700">
          ★ {provider.rating}
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        {provider.hospital} · {provider.area}, {provider.city}
      </p>
      <div className="mt-3 flex items-center justify-between text-sm">
        <span className="font-semibold text-slate-800">₹{provider.consultation_fee}</span>
        <div className="flex items-center gap-3">
          {provider.is_demo && (
            <span className="rounded border border-amber-300 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700">
              Demo
            </span>
          )}
          <Link
            to={`/providers/${provider.id}`}
            className="font-medium text-teal-700 hover:underline"
          >
            View details →
          </Link>
        </div>
      </div>
    </article>
  );
}
