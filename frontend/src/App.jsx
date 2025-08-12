import React, { useState } from "react";
import ProbabilityBar from "./components/ProbabilityBar";

export default function App() {
    const [artist, setArtist] = useState("");
    const [tour, setTour] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [data, setData] = useState(null);

    const canSearch = artist.trim().length > 1;

    async function onSubmit(e) {
        e.preventDefault();
        if (!canSearch) return;
        setLoading(true); setError(""); setData(null);
        try {
            // TEMP demo: replace with backend call later
            await new Promise(r => setTimeout(r, 700));
            setData({
                artist: artist.trim(),
                tour: tour.trim() || null,
                total_setlists: 24,
                confidence: 0.78,
                songs: [
                    { title: "Sample Song A", appearances: 20, probability: 0.16 },
                    { title: "Sample Song B", appearances: 18, probability: 0.12 },
                    { title: "Sample Song C", appearances: 17, probability: 0.10 },
                    { title: "Sample Song D", appearances: 15, probability: 0.08 },
                ],
            });
        } catch {
            setError("Something went wrong. Try again.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen flex flex-col items-center justify-center py-14 px-4">
            <div className="w-full max-w-3xl">
                {/* Header */}
                <div className="text-center">
                    <h1 className="text-5xl font-bold tracking-tight text-gray-900">
                        Setify
                    </h1>
                    <p className="mt-3 text-gray-600">
                        Predict likely songs for an artist’s tour with clean probabilities.
                    </p>
                </div>

                {/* Form */}
                <form onSubmit={onSubmit} className="card mt-8 p-6 bg-white/80 backdrop-blur-lg shadow-lg rounded-xl">
                    <div className="grid sm:grid-cols-2 gap-5">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Artist <span className="text-red-500">*</span>
                            </label>
                            <input
                                className="mt-1 w-full rounded-xl border border-gray-300 bg-white text-gray-900 px-3 py-2 placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-[--color-brand]/30"
                                placeholder="e.g., Taylor Swift"
                                value={artist}
                                onChange={(e) => setArtist(e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">
                                Tour (optional)
                            </label>
                            <input
                                className="mt-1 w-full rounded-xl border border-gray-300 bg-white text-gray-900 px-3 py-2 placeholder-gray-400 focus:outline-none focus:ring-4 focus:ring-[--color-brand]/30"
                                placeholder="e.g., The Eras Tour"
                                value={tour}
                                onChange={(e) => setTour(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="mt-5 flex items-center gap-3">
                        <button
                            type="submit"
                            disabled={!canSearch || loading}
                            className="inline-flex items-center justify-center rounded-xl bg-[--color-brand] hover:bg-[--color-brand-600] px-5 py-2.5 font-semibold text-gray-900 shadow-md disabled:opacity-50 transition"
                        >
                            {loading ? "Predicting…" : "Predict"}
                        </button>
                        {error && <span className="text-sm text-red-600">{error}</span>}
                    </div>
                </form>

                {/* Results */}
                {data && (
                    <section className="ard mt-6 p-6 bg-white/80 backdrop-blur-lg shadow-lg rounded-xl">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                                <h2 className="text-xl font-semibold">Top Predictions</h2>
                                <p className="text-sm text-gray-600">
                                    {data.artist}{data.tour ? ` · ${data.tour}` : ""} · {data.total_setlists} shows
                                </p>
                            </div>
                            <div className="text-sm">
                                Confidence:{" "}
                                <strong className="text-[--color-accent]">
                                    {Math.round(data.confidence * 100)}%
                                </strong>
                            </div>
                        </div>

                        <ul className="mt-5 space-y-3">
                            {data.songs.slice(0, 25).map((s, idx) => (
                                <li key={s.title + idx} className="grid grid-cols-[2rem,1fr,6rem] items-center gap-3">
                                    <div className="text-gray-500 tabular-nums">{idx + 1}.</div>
                                    <div>
                                        <div className="font-medium">{s.title}</div>
                                        <div className="mt-1"><ProbabilityBar p={s.probability} /></div>
                                        <div className="mt-1 text-xs text-gray-500">Appearances: {s.appearances}</div>
                                    </div>
                                    <div className="text-right font-semibold tabular-nums">
                                        {(s.probability * 100).toFixed(1)}%
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </section>
                )}

                <p className="mt-8 text-center text-xs text-gray-500">
                    made by therealpc.
                </p>
            </div>
        </div>
    );
}