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
            <div className="relative z-10 mx-auto flex max-w-5xl flex-col gap-6 px-4 py-6 sm:py-8">
                <header className="space-y-3">
                    <div className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full bg-[--color-brand] shadow-[0_0_18px_rgba(245,158,11,0.6)]" />
                        <span className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                            study for your next concert
                        </span>
                    </div>
                    <h1 className="text-5xl font-black tracking-tight bg-gradient-to-r from-[--color-brand] via-orange-400 to-amber-400 bg-clip-text text-transparent sm:text-6xl">setify</h1>
                    <p className="max-w-2xl text-base text-slate-400 leading-relaxed">
                        Drop an artist name and see what's been on their setlists. Perfect for prepping your setlist or just seeing what's likely to come up.
                    </p>
                </header>

                <section className="rounded-2xl border border-[--color-brand]/20 bg-slate-900/60 p-5 shadow-[0_20px_60px_rgba(245,158,11,0.2)] backdrop-blur-xl">
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                            <label className="flex flex-1 flex-col text-sm font-medium text-slate-400">
                                Artist
                                <div className="mt-2 flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 shadow-inner transition focus-within:border-[--color-brand] focus-within:bg-slate-900/60">
                                    <input
                                        className="w-full bg-transparent text-base font-medium text-white placeholder:text-slate-600 focus:outline-none"
                                        placeholder="gunna, drake, travis scott..."
                                        value={artistQuery}
                                        onChange={(event) => setArtistQuery(event.target.value)}
                                    />
                                </div>
                            </label>
                            <button
                                type="submit"
                                disabled={loading || !canPredict}
                                className="group relative inline-flex items-center justify-center overflow-hidden rounded-xl px-6 py-2.5 font-semibold text-white shadow-lg transition focus:outline-none focus:ring-2 focus:ring-[--color-brand]/70 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                                <span className="absolute inset-0 bg-gradient-to-r from-[--color-brand] via-orange-500 to-amber-500 opacity-90 transition-transform duration-300 group-hover:scale-105" />
                                <span className="relative flex items-center gap-2">
                                    {loading ? (
                                        <>
                                            <span className="h-2 w-2 animate-ping rounded-full bg-white" />
                                            <span>Checking...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>GO</span>
                                        </>
                                    )}
                                </span>
                            </button>
                        </div>
                    </form>
                    {error && (
                        <div className="mt-3 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-2.5 text-sm text-red-200">
                            {error}
                        </div>
                    )}
                </section>
                <section className="space-y-4 rounded-2xl border border-[--color-brand]/20 bg-slate-900/50 p-5 shadow-[0_20px_60px_rgba(245,158,11,0.15)] backdrop-blur-xl">
                    <div>
                        <h2 className="text-lg font-semibold text-white mb-1">Predicted Setlist</h2>
                        <p className="text-xs text-slate-500">
                            {prediction
                                ? `Based on ${formatNumber(prediction.meta?.pages_fetched ?? 0)} pages of recent shows`
                                : "Start typing an artist above to see what's been on their setlists"}
                        </p>
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
            <div className="absolute -top-32 left-1/2 h-80 w-80 -translate-x-1/2 rounded-full bg-[--color-brand]/25 blur-[120px]" />
            <div className="absolute bottom-[-18%] left-[-5%] h-96 w-96 rounded-full bg-orange-500/15 blur-[140px]" />
            <div className="absolute bottom-[-25%] right-[-5%] h-[28rem] w-[28rem] rounded-full bg-amber-500/15 blur-[160px]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(245,158,11,0.08),_transparent_55%)]" />
        </div>
    );
}