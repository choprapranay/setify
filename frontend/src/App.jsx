import React from "react";
import SongTable from "./presentation/components/SongTable.jsx";
import { usePredictor } from "./presentation/hooks/usePredictor";
const cls = (...xs) => xs.filter(Boolean).join(" ");

export default function App() {
    const {
        state: {
            artistQuery,
            artist,
            tours,
            selectedTour,
            pages,
            topK,
            halfLife,
            alpha,
            beta,
            prediction,
            error,
            loadingArtist,
            loadingPrediction,
            sortedSongs,
            sortKey,
            sortDir,
            canSearch,
            formatNumber,
        },
        actions: {
            setArtistQuery,
            setSelectedTour,
            setPages,
            setTopK,
            setHalfLife,
            setAlpha,
            setBeta,
            search,
            predict,
            toggleSort,
        },
    } = usePredictor();

    return (
        <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 text-gray-900">
            <header className="sticky top-0 z-10 backdrop-blur bg-white/70 border-b">
                <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-3">
                    <h1 className="text-2xl font-semibold tracking-tight">Setify</h1>
                    {prediction && (
                        <div className="flex items-center gap-2 text-sm">
                                                    <span className="px-2 py-0.5 rounded-full bg-gray-100">
                                confidence {formatNumber(prediction.confidence * 100, 1)}%
                            </span>
                            <span className="px-2 py-0.5 rounded-full bg-gray-100">
                                shows {formatNumber(prediction.setsConsidered)}
                            </span>
                            <span className="px-2 py-0.5 rounded-full bg-gray-100">
                                unique {formatNumber(prediction.uniqueSongs)}
                            </span>
                        </div>
                    )}
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">
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
                                onKeyDown={(e) => e.key === "Enter" && search()}
                            />
                            <div className="mt-2 flex gap-2 items-center">
                                <button
                                    onClick={search}
                                    disabled={!canSearch || loadingArtist}
                                    className={cls(
                                        "px-4 py-2 rounded-xl text-white",
                                        loadingArtist ? "bg-gray-400" : "bg-black hover:opacity-90"
                                    )}
                                >
                                    {loadingArtist ? "Searching…" : "Find artist"}
                                </button>
                                {artist && <span className="text-sm text-gray-600">{artist.name}</span>}
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm mb-1">Tour (optional)</label>
                            <select
                                className="w-full border rounded-xl px-3 py-2"
                                value={selectedTour ?? ""}
                                onChange={(e) => setSelectedTour(e.target.value || null)}
                            >
                                <option value="">All tours</option>
                                {tours.map((tour) => (
                                    <option key={tour} value={tour}>
                                        {tour}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                    <div className="grid sm:grid-cols-3 gap-4 mt-4">
                        <Knob
                            label="Pages"
                            value={pages}
                            onChange={(value) => setPages(Number(value))}
                            min={1}
                            max={10}
                        />
                        <Knob
                            label="Top K"
                            value={topK}
                            onChange={(value) => setTopK(Number(value))}
                            min={1}
                            max={50}
                        />
                        <Knob
                            label="Half-life (days)"
                            value={halfLife}
                            onChange={(value) => setHalfLife(Number(value))}
                            min={7}
                            max={1000}
                        />
                        <Knob
                            label="Alpha"
                            value={alpha}
                            step="0.1"
                            onChange={(value) => setAlpha(Number(value))}
                            min={0}
                            max={5}
                        />
                        <Knob
                            label="Beta"
                            value={beta}
                            step="0.1"
                            onChange={(value) => setBeta(Number(value))}
                            min={0}
                            max={5}
                        />
                    </div>
                    <div className="mt-4">
                        <button
                            onClick={predict}
                            disabled={loadingPrediction}
                            className={cls("px-5 py-2 rounded-xl text-white",
                                loadingPrediction ? "bg-gray-400" : "bg-black hover:opacity-90"
                            )}
                        >
                            {loadingPrediction ? "Predicting…" : "Predict setlist"}
                        </button>
                    </div>
                </section>
                {error && (
                    <div className="bg-red-50 text-red-700 border border-red-200 px-4 py-3 rounded-xl">
                        {error}
                    </div>
                )}
                <section className="bg-white shadow-sm rounded-2xl p-4 border space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-lg font-semibold">Predicted songs</h2>
                        {prediction && (
                            <div className="text-sm text-gray-500">
                                Model: {prediction.model?.name ?? "—"}
                            </div>
                        )}
                    </div>
                    <SongTable
                        songs={sortedSongs}
                        sortKey={sortKey}
                        sortDir={sortDir}
                        onSort={toggleSort}
                        formatNumber={formatNumber}
                    />
                </section>
            </main>
        </div>
    );
}

function Knob({ label, value, onChange, min, max, step = 1 }) {
    return (
        <label className="block text-sm">
            <span className="block mb-1">{label}</span>
            <input
                type="number"
                className="w-full border rounded-xl px-3 py-2"
                value={value}
                min={min}
                max={max}
                step={step}
                onChange={(e) => onChange(e.target.value)}
            />
        </label>
    );
}