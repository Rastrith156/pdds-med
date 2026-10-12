import { useEffect, useState } from "react";
import { getOpenProjectOverview, getOpenProjectWorkPackage } from "../api.js";

const STATUS_STYLE = {
  Closed: "bg-emerald-50 text-emerald-800",
  Resolved: "bg-teal-50 text-teal-800",
  "In progress": "bg-sky-50 text-sky-800",
  New: "bg-slate-100 text-slate-700",
};

function Status({ value }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${STATUS_STYLE[value] || "bg-amber-50 text-amber-800"}`}>
      {value}
    </span>
  );
}

export default function OpenProject() {
  const [overview, setOverview] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    let active = true;
    getOpenProjectOverview()
      .then((data) => { if (active) setOverview(data); })
      .catch((err) => { if (active) setError(err.message || "Could not load OpenProject."); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const selectPackage = async (id) => {
    setSelected(null);
    setDetailError("");
    try {
      setSelected(await getOpenProjectWorkPackage(id));
    } catch (err) {
      setDetailError(err.message || "Could not load work-package details.");
    }
  };

  return (
    <section className="mx-auto max-w-5xl px-4 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-teal-700">Project workspace</p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">OpenProject</h1>
          <p className="mt-1 text-sm text-slate-600">Project overview and work packages from your OpenProject instance.</p>
        </div>
        {overview?.workspace_url && (
          <a href={overview.workspace_url} target="_blank" rel="noreferrer" className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800">
            Open workspace <span aria-hidden="true">↗</span>
          </a>
        )}
      </div>

      {loading && <p role="status" className="py-12 text-center text-sm text-slate-500">Connecting to OpenProject…</p>}

      {!loading && !error && overview && !overview.configured && (
        <div className="mt-6 border-l-4 border-amber-400 bg-amber-50 px-5 py-4">
          <h2 className="font-semibold text-slate-900">OpenProject is not connected</h2>
          <p className="mt-1 text-sm text-slate-700">{overview.setup_instructions}</p>
          <p className="mt-3 text-sm text-slate-700">Add these variables to the backend environment:</p>
          <ul className="mt-2 list-inside list-disc text-sm text-slate-700">
            <li><code>OPENPROJECT_URL</code>: your OpenProject instance base URL</li>
            <li><code>OPENPROJECT_API_KEY</code>: an API token created in your profile</li>
            <li><code>OPENPROJECT_PROJECT_ID</code>: the numeric project ID</li>
          </ul>
          <p className="mt-2 text-xs text-slate-600">Keep the API key on the backend. Restart the API after configuration.</p>
        </div>
      )}

      {!loading && error && (
        <div role="alert" className="mt-6 border-l-4 border-red-500 bg-red-50 px-5 py-4 text-sm text-red-800">
          {error} OpenProject data was not available; check the backend connection and instance configuration.
        </div>
      )}

      {!loading && overview?.configured && overview.project && (
        <>
          <section className="grid gap-6 border-b border-slate-200 py-6 sm:grid-cols-[minmax(0,1fr)_16rem]">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Connected project</p>
              <h2 className="mt-1 text-xl font-bold text-slate-900">{overview.project.name}</h2>
              {overview.project.description && <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{overview.project.description}</p>}
            </div>
            <div className="self-start border-l border-slate-200 pl-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Work packages</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{overview.total_count}</p>
              {overview.total_count > overview.work_packages.length && <p className="mt-1 text-xs text-slate-500">Showing first {overview.work_packages.length}</p>}
            </div>
          </section>

          <section className="grid gap-6 py-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Work packages</h2>
              {overview.work_packages.length === 0 ? (
                <p className="mt-4 border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">This project has no work packages.</p>
              ) : (
                <div className="mt-3 divide-y divide-slate-200 border-y border-slate-200">
                  {overview.work_packages.map((item) => (
                    <button key={item.id} type="button" onClick={() => selectPackage(item.id)} className="grid w-full gap-3 px-3 py-4 text-left hover:bg-white sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-semibold text-slate-900">{item.subject}</span>
                        <span className="mt-1 block text-xs text-slate-500">#{item.id}{item.assignee ? ` · ${item.assignee}` : ""}</span>
                      </span>
                      <Status value={item.status} />
                    </button>
                  ))}
                </div>
              )}
            </div>

            <aside aria-live="polite" className="border-t border-slate-200 pt-5 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0">
              <h2 className="text-lg font-bold text-slate-900">Work-package details</h2>
              {detailError && <p role="alert" className="mt-3 text-sm text-red-700">{detailError}</p>}
              {!selected && !detailError && <p className="mt-3 text-sm text-slate-500">Select a work package to view its details.</p>}
              {selected && (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-slate-500">#{selected.id}</p>
                  <h3 className="mt-1 font-semibold text-slate-900">{selected.subject}</h3>
                  <div className="mt-3"><Status value={selected.status} /></div>
                  <dl className="mt-4 space-y-3 text-sm">
                    {selected.assignee && <div><dt className="text-xs text-slate-500">Assignee</dt><dd>{selected.assignee}</dd></div>}
                    {selected.priority && <div><dt className="text-xs text-slate-500">Priority</dt><dd>{selected.priority}</dd></div>}
                    {selected.start_date && <div><dt className="text-xs text-slate-500">Start</dt><dd>{selected.start_date}</dd></div>}
                    {selected.due_date && <div><dt className="text-xs text-slate-500">Due</dt><dd>{selected.due_date}</dd></div>}
                  </dl>
                  {selected.description && <p className="mt-4 whitespace-pre-wrap border-t border-slate-200 pt-3 text-sm text-slate-600">{selected.description}</p>}
                  <a href={selected.url} target="_blank" rel="noreferrer" className="mt-4 inline-block text-sm font-semibold text-teal-700 hover:underline">View in OpenProject ↗</a>
                </div>
              )}
            </aside>
          </section>
        </>
      )}
    </section>
  );
}