import React from "react";
import SongTable from "./presentation/components/SongTable.jsx";
import { usePredictor } from "./presentation/hooks/usePredictor";

export default function App() {
    const {
        state: {
            artistQuery,
            artist,
            prediction,
            error,
            loading,
            sortedSongs,
            sortKey,
            sortDir,
            canPredict,
            formatNumber,
        },
        actions: { setArtistQuery, predict, toggleSort },
    } = usePredictor();

    const handleSubmit = (event) => {
        event.preventDefault();
        predict();
    };

    return (
        <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
            <GradientBackdrop />
            <div className="relative z-10 mx-auto flex max-w-5xl flex-col gap-10 px-4 py-10">
                <header className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
                    <div className="space-y-3">
                        <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.45em] text-slate-400">
                            <span className="h-2 w-2 rounded-full bg-[--color-brand] shadow-[0_0_18px_rgba(192,132,252,0.8)]" />
                            Live setlist oracle
                        </span>
                        <h1 className="text-4xl font-black tracking-tight text-white sm:text-5xl">Setify</h1>
                        <p className="max-w-xl text-base text-slate-300">
                            Type an artist, hit predict, and we will analyse their recent shows to surface the
                            songs most likely to appear on a setlist.
                        </p>
                    </div>
                    {prediction && (
                        <div className="flex flex-wrap gap-3">
                            <StatPill
                                label="Confidence"
                                value={`${formatNumber(prediction.confidence * 100, 1)}%`}
                            />
                            <StatPill label="Shows" value={formatNumber(prediction.setsConsidered)} />
                            <StatPill label="Unique songs" value={formatNumber(prediction.uniqueSongs)} />
                        </div>
                    )}
                </header>

                <section className="rounded-3xl border border-white/10 bg-slate-900/60 p-6 shadow-[0_30px_80px_rgba(15,23,42,0.45)] backdrop-blur-xl">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
                            <label className="flex flex-1 flex-col text-sm font-medium text-slate-300">
                                Artist
                                <div className="mt-2 flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 shadow-inner transition focus-within:border-[--color-brand] focus-within:bg-slate-900/60">
                                    <span className="text-lg text-[--color-brand]">🎶</span>
                                    <input
                                        className="w-full bg-transparent text-base font-medium text-white placeholder:text-slate-500 focus:outline-none"
                                        placeholder="e.g. The 1975"
                                        value={artistQuery}
                                        onChange={(event) => setArtistQuery(event.target.value)}
                                    />
                                </div>
                            </label>
                            <button
                                type="submit"
                                disabled={loading || !canPredict}
                                className="group relative inline-flex items-center justify-center overflow-hidden rounded-2xl px-6 py-3 font-semibold text-white shadow-lg transition focus:outline-none focus:ring-2 focus:ring-[--color-brand]/70 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                                <span className="absolute inset-0 bg-gradient-to-r from-[--color-brand] via-fuchsia-500 to-rose-500 opacity-90 transition-transform duration-300 group-hover:scale-105" />
                                <span className="relative flex items-center gap-2">
                                    {loading ? (
                                        <>
                                            <span className="h-2 w-2 animate-ping rounded-full bg-white" />
                                            <span>Predicting…</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>Predict setlist</span>
                                        </>
                                    )}

                                </span>
                            </button>
                        </div>
                        <p className="text-sm text-slate-400">
                            We tune the recency weighting automatically — no sliders, just smart predictions.
                        </p>
                    </form>
                    {artist && !loading && !error && (
                        <p className="mt-4 text-sm text-slate-300">
                            Predicting for <span className="font-semibold text-white">{artist.name}</span>.
                        </p>
                    )}
                    {error && (
                        <div className="mt-4 rounded-2xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                            {error}
                        </div>
                    )}
                </section>
                <section className="space-y-5 rounded-3xl border border-white/10 bg-slate-900/50 p-6 shadow-[0_20px_60px_rgba(8,15,40,0.55)] backdrop-blur-xl">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"><div>
                        <h2 className="text-xl font-semibold text-white">Predicted set</h2>
                        <p className="text-sm text-slate-400">
                            {prediction
                                ? `Analysed ${formatNumber(prediction.meta?.pages_fetched ?? 0)} pages of recent shows.`
                                : "Run a prediction to see the most likely openers, sing-alongs, and deep cuts."}
                        </p>
                    </div>
                        {prediction?.model?.name && (
                            <span className="rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-slate-300">
                                {prediction.model.name}
                            </span>
                        )}
                    </div>
                    <SongTable
                        songs={sortedSongs}
                        sortKey={sortKey}
                        sortDir={sortDir}
                        onSort={toggleSort}
                        formatNumber={formatNumber}
                        loading={loading}
                    />
                </section>
            </div>
        </div>
    );
}

function GradientBackdrop() {
    return (
        <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
            <div className="absolute -top-32 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-[--color-brand]/30 blur-[120px]" />
            <div className="absolute bottom-[-18%] left-[-5%] h-96 w-96 rounded-full bg-rose-500/20 blur-[140px]" />
            <div className="absolute bottom-[-25%] right-[-5%] h-[28rem] w-[28rem] rounded-full bg-sky-500/20 blur-[160px]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(148,163,255,0.12),_transparent_55%)]" />
        </div>
    );
}

function StatPill({ label, value }) {
    return(
        <div className="flex flex-col items-start gap-1 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm text-slate-200 shadow-inner">
            <span className="text-xs uppercase tracking-[0.4em] text-slate-400">{label}</span>
            <span className="text-lg font-semibold text-white">{value}</span>
        </div>
    );
}