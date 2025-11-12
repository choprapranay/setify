import React, { useMemo, useState } from "react";
import ProbabilityBar from "./components/ProbabilityBar";

// Prefer env var, fallback to localhost
const RAW_BASE = import.meta.env?.VITE_API_BASE || "http://127.0.0.1:8000";
const API_BASE = RAW_BASE.replace(/\/$/, "");

// tiny utils
const nf = (n, d = 0) =>
    new Intl.NumberFormat(undefined, { minimumFractionDigits: d, maximumFractionDigits: d }).format(n);
const cls = (...xs) => xs.filter(Boolean).join(" ");

export default function App() {
    // form state
    const [artistQuery, setArtistQuery] = useState("");
    const [tour, setTour] = useState(null);

    // model knobs
    const [pages, setPages] = useState(5);
    const [topK, setTopK] = useState(20);
    const [halfLife, setHalfLife] = useState(180);
    const [alpha, setAlpha] = useState(1);
    const [beta, setBeta] = useState(1);

    // fetched state
    const [artist, setArtist] = useState(null); // { name, mbid }
    const [tours, setTours] = useState([]);
    const [pred, setPred] = useState(null); // predict response

    // ui state
    const [loadingArtist, setLoadingArtist] = useState(false);
    const [loadingPredict, setLoadingPredict] = useState(false);
    const [err, setErr] = useState(null);

    const canSearch = artistQuery.trim().length > 1;

    async function findArtist() {
        setErr(null);
        setPred(null);
        setTours([]);
        setTour(null);
        const q = artistQuery.trim();
        if (!q) return;

        setLoadingArtist(true);
        try {
            const url = new URL("/api/artist", API_BASE);
            url.searchParams.set("artist", q);
            const res = await fetch(url.toString());
            const data = await res.json().catch(() => ({}));
            if (!res.ok) throw new Error(data?.detail || `Artist search failed (${res.status})`);
            setArtist(data); // { name, mbid }
            preloadTours(data.mbid);
        } catch (e) {
            setArtist(null);
            setErr(e.message || String(e));
        } finally {
            setLoadingArtist(false);
        }
    }

    async function preloadTours(mbid) {
        try {
            const url = new URL("/api/setlists", API_BASE);
            url.searchParams.set("mbid", mbid);
            url.searchParams.set("pages", "3");
            const r = await fetch(url.toString());
            if (!r.ok) return;
            const payload = await r.json();
            const uniq = new Set();
            for (const s of payload.setlists || []) {
                const t = s?.tour?.name;
                if (t && typeof t === "string") uniq.add(t);
            }
            setTours(Array.from(uniq).sort());
        } catch {
            // ignore
        }
    }

    async function doPredict() {
        if (!artist) {
            setErr("Pick an artist first.");
            return;
        }
        setErr(null);
        setLoadingPredict(true);
        setPred(null);
        try {
            const url = new URL("/api/predict", API_BASE);
            url.searchParams.set("mbid", artist.mbid);
            url.searchParams.set("pages", String(pages));
            url.searchParams.set("top_k", String(topK));
            url.searchParams.set("half_life_days", String(halfLife));
            url.searchParams.set("alpha", String(alpha));
            url.searchParams.set("beta", String(beta));
            if (tour) url.searchParams.set("tour", tour);
            const r = await fetch(url.toString());
            const data = await r.json().catch(() => ({}));
            if (!r.ok) throw new Error(data?.detail || `Predict failed (${r.status})`);
            setPred(data);
        } catch (e) {
            setErr(e.message || String(e));
        } finally {
            setLoadingPredict(false);
        }
    }

    // sorting
    const [sortKey, setSortKey] = useState("prob"); // "prob" | "apps" | "title" | "pos"
    const [sortDir, setSortDir] = useState("desc"); // "asc" | "desc"
    const sortedSongs = useMemo(() => {
        if (!pred) return [];
        const arr = [...pred.songs];
        const cmp = (a, b) => {
            let va = 0,
                vb = 0;
            if (sortKey === "prob") {
                va = a.probability;
                vb = b.probability;
            } else if (sortKey === "apps") {
                va = a.appearances;
                vb = b.appearances;
            } else if (sortKey === "pos") {
                va = a.typical_position ?? Infinity;
                vb = b.typical_position ?? Infinity;
            } else {
                va = a.title.toLowerCase();
                vb = b.title.toLowerCase();
            }
            if (va < vb) return sortDir === "asc" ? -1 : 1;
            if (va > vb) return sortDir === "asc" ? 1 : -1;
            return 0;
        };
        return arr.sort(cmp);
    }, [pred, sortKey, sortDir]);

    function toggleSort(k) {
        if (k === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
        else {
            setSortKey(k);
            setSortDir("desc");
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 text-gray-900">
            {/* Header */}
            <header className="sticky top-0 z-10 backdrop-blur bg-white/70 border-b">
                <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-3">
                    <h1 className="text-2xl font-semibold tracking-tight">Setify</h1>
                    {pred && (
                        <div className="flex items-center gap-2 text-sm">
              <span className="px-2 py-0.5 rounded-full bg-gray-100">
                confidence {nf(pred.confidence * 100, 1)}%
              </span>
                            <span className="px-2 py-0.5 rounded-full bg-gray-100">shows {pred.sets_considered}</span>
                            <span className="px-2 py-0.5 rounded-full bg-gray-100">unique {pred.unique_songs}</span>
                        </div>
                    )}
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
                {/* Search & Controls */}
                <section className="bg-white shadow-sm rounded-2xl p-4 border">
                    <div className="grid sm:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm mb-1">
                                Artist <span className="text-red-500">*</span>
                            </label>
                            <input
                                className="w-full border rounded-xl px-3 py-2 focus:outline-none focus:ring"
                                placeholder="e.g., Coldplay"
                                value={artistQuery}
                                onChange={(e) => setArtistQuery(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && findArtist()}
                            />
                            <div className="mt-2 flex gap-2">
                                <button
                                    onClick={findArtist}
                                    disabled={!canSearch || loadingArtist}
                                    className={cls(
                                        "px-4 py-2 rounded-xl text-white",
                                        loadingArtist ? "bg-gray-400" : "bg-black hover:opacity-90"
                                    )}
                                >
                                    {loadingArtist ? "Searching…" : "Find artist"}
                                </button>
                                {artist && <span className="text-sm text-gray-600 self-center">{artist.name}</span>}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm mb-1">Tour (optional)</label>
                            <select
                                className="w-full border rounded-xl px-3 py-2"
                                value={tour ?? ""}
                                onChange={(e) => setTour(e.target.value || null)}
                            >
                                <option value="">— Any tour —</option>
                                {tours.map((t) => (
                                    <option key={t} value={t}>
                                        {t}
                                    </option>
                                ))}
                            </select>
                            {artist && tours.length === 0 && (
                                <div className="text-xs text-gray-500 mt-1">No tours detected in recent pages.</div>
                            )}
                        </div>
                    </div>

                    {/* Knobs */}
                    <div className="mt-4 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-sm mb-1">Pages</label>
                            <input
                                type="range"
                                min={1}
                                max={10}
                                value={pages}
                                onChange={(e) => setPages(+e.target.value)}
                                className="w-full"
                            />
                            <div className="text-xs text-gray-600">{pages} page(s)</div>
                        </div>
                        <div>
                            <label className="block text-sm mb-1">Top K</label>
                            <input
                                type="range"
                                min={5}
                                max={50}
                                value={topK}
                                onChange={(e) => setTopK(+e.target.value)}
                                className="w-full"
                            />
                            <div className="text-xs text-gray-600">{topK} songs</div>
                        </div>
                        <div>
                            <label className="block text-sm mb-1">Half-life (days)</label>
                            <input
                                type="range"
                                min={30}
                                max={365}
                                value={halfLife}
                                onChange={(e) => setHalfLife(+e.target.value)}
                                className="w-full"
                            />
                            <div className="text-xs text-gray-600">{halfLife} days</div>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <label className="block text-sm mb-1">Alpha</label>
                                <input
                                    type="number"
                                    min={0}
                                    step={0.1}
                                    value={alpha}
                                    onChange={(e) => setAlpha(+e.target.value)}
                                    className="w-full border rounded-xl px-3 py-2"
                                />
                            </div>
                            <div>
                                <label className="block text-sm mb-1">Beta</label>
                                <input
                                    type="number"
                                    min={0}
                                    step={0.1}
                                    value={beta}
                                    onChange={(e) => setBeta(+e.target.value)}
                                    className="w-full border rounded-xl px-3 py-2"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="mt-4 flex gap-3">
                        <button
                            onClick={doPredict}
                            disabled={!artist || loadingPredict}
                            className={cls(
                                "px-4 py-2 rounded-xl text-white",
                                loadingPredict ? "bg-gray-400" : "bg-blue-600 hover:opacity-90"
                            )}
                        >
                            {loadingPredict ? "Predicting…" : "Predict setlist"}
                        </button>
                        {err && <div className="text-sm text-red-600 self-center">{err}</div>}
                    </div>
                </section>

                {/* Results */}
                {pred && (
                    <section className="bg-white shadow-sm rounded-2xl p-4 border">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <h2 className="text-lg font-semibold">Predicted songs</h2>
                                <p className="text-sm text-gray-600">
                                    MBID {artist?.mbid} {pred.tour ? `· ${pred.tour}` : ""}
                                </p>
                            </div>
                            <div className="text-sm text-gray-600">
                                Model {pred.model.name} · half-life {pred.model.half_life_days}d · α={pred.model.alpha} β={pred.model.beta}
                            </div>
                        </div>

                        <div className="overflow-x-auto mt-3">
                            <table className="min-w-full text-sm">
                                <thead>
                                <tr className="text-left border-b">
                                    <Th label="#" />
                                    <Th label="Song" onClick={() => toggleSort("title")} active={sortKey === "title"} dir={sortDir} />
                                    <Th label="Probability" onClick={() => toggleSort("prob")} active={sortKey === "prob"} dir={sortDir} />
                                    <Th label="Appearances" onClick={() => toggleSort("apps")} active={sortKey === "apps"} dir={sortDir} />
                                    <Th label="Typical pos" onClick={() => toggleSort("pos")} active={sortKey === "pos"} dir={sortDir} />
                                    <Th label="Last seen" />
                                </tr>
                                </thead>
                                <tbody>
                                {sortedSongs.map((s, i) => (
                                    <tr key={s.title + "-" + i} className="border-b hover:bg-gray-50">
                                        <td className="py-2 pr-4 text-gray-500 tabular-nums">{i + 1}</td>
                                        <td className="py-2 pr-4 font-medium">{s.title}</td>
                                        <td className="py-2 pr-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-56">
                                                    <ProbabilityBar p={s.probability} />
                                                </div>
                                                <div className="w-14 text-right tabular-nums">{nf(s.probability * 100, 0)}%</div>
                                            </div>
                                        </td>
                                        <td className="py-2 pr-4 tabular-nums">{s.appearances}</td>
                                        <td className="py-2 pr-4 tabular-nums">{s.typical_position ?? ""}</td>
                                        <td className="py-2 pr-4">{s.last_seen ?? ""}</td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}

                <footer className="text-xs text-gray-500 py-4">API: {API_BASE}</footer>
            </main>
        </div>
    );
}

function Th({ label, onClick, active, dir }) {
    return (
        <th
            className={cls("py-2 pr-4 select-none", onClick && "cursor-pointer hover:text-gray-700")}
            onClick={onClick}
        >
      <span className="inline-flex items-center gap-1">
        {label}
          {active && <span className="text-gray-400 text-xs">{dir === "asc" ? "▲" : "▼"}</span>}
      </span>
        </th>
    );
}
