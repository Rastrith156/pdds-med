import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { DISCLAIMER } from "../App.jsx";

/**
 * Home page — MediAccess AI landing with the main search box.
 * Stage 6: the box hands off to the structured Search page.
 * Stage 7 turns it into the natural-language AI search.
 */
export default function Home() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const submit = (event) => {
    event.preventDefault();
    navigate("/search");
  };

  return (
    <section className="mx-auto max-w-3xl px-4 py-16 text-center">
      <h1 className="text-4xl font-bold text-slate-900">
        Medi<span className="text-teal-700">Access AI</span>
      </h1>
      <p className="mt-3 text-lg text-slate-600">
        Find healthcare options that fit your needs.
      </p>

      <form onSubmit={submit} className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <label htmlFor="home-search" className="block text-left text-sm font-medium text-slate-700">
          What healthcare option are you looking for?
        </label>
        <textarea
          id="home-search"
          rows={3}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="I need a dermatologist near Bangalore under ₹700 today"
          className="mt-2 w-full resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
        />
        <button
          type="submit"
          className="mt-4 rounded-lg bg-teal-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-teal-800"
        >
          Find Healthcare Options
        </button>
      </form>

      <p className="mt-6 rounded-lg bg-amber-50 px-4 py-3 text-xs text-amber-800">
        {DISCLAIMER}
      </p>
      <p className="mt-3 text-xs text-slate-500">
        All provider records shown are clearly-labelled DEMO data.
      </p>
    </section>
  );
}
