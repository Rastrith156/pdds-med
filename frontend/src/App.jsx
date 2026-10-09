import { Routes, Route, Link, NavLink } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Search from "./pages/Search.jsx";
import ProviderDetails from "./pages/ProviderDetails.jsx";

/** Canonical navigation disclaimer (shown on every page). */
export const DISCLAIMER =
  "MediAccess AI provides healthcare navigation and provider information. It does not diagnose conditions or replace professional medical advice.";

function Navbar() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-bold text-teal-700">
          MediAccess<span className="text-slate-800"> AI</span>
        </Link>
        <div className="flex gap-4 text-sm font-medium">
          <NavLink to="/" className={({ isActive }) => (isActive ? "text-teal-700" : "text-slate-600 hover:text-teal-700")}>
            Home
          </NavLink>
          <NavLink to="/search" className={({ isActive }) => (isActive ? "text-teal-700" : "text-slate-600 hover:text-teal-700")}>
            Search
          </NavLink>
        </div>
      </nav>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <p className="mx-auto max-w-5xl px-4 py-4 text-xs text-slate-500">
        {DISCLAIMER} All provider records are clearly-labelled DEMO data.
      </p>
    </footer>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/search" element={<Search />} />
          <Route path="/providers/:id" element={<ProviderDetails />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
