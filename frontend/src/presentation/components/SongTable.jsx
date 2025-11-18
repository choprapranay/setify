import ProbabilityBar from "./ProbabilityBar";

const headers = [
    { key: "title", label: "Song" },
    { key: "prob", label: "Probability" },
    { key: "apps", label: "Appearances" },
    { key: "pos", label: "Typical position" },
];

export default function SongTable({ songs, sortKey, sortDir, onSort, formatNumber, loading = false }) {
    if (loading) {
        return (
            <div className="flex flex-col items-center gap-3 py-10 text-sm text-slate-300">
                <span className="h-3 w-3 animate-ping rounded-full bg-[--color-brand]" />
                <span className="tracking-[0.4em] uppercase">Predicting…</span>
            </div>
        );
    }

    if (!songs?.length) {
        return (
            <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 px-4 py-8 text-center text-sm text-slate-400">
                Run a prediction to see likely songs.
            </div>
        );
    }

    return (
        <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/5">
            <table className="min-w-full text-left text-sm text-slate-200">
                <thead>
                <tr className="bg-white/10 text-xs uppercase tracking-[0.3em] text-slate-400">
                    {headers.map((header) => (
                        <th key={header.key} className="px-4 py-3">
                            <button
                                type="button"
                                className="flex items-center gap-2 font-semibold text-slate-200 transition hover:text-white"
                                onClick={() => onSort(header.key === "title" ? "title" : header.key)}
                            >
                                <span>{header.label}</span>
                                {sortKey === header.key && (
                                    <span className="text-[--color-brand]">{sortDir === "asc" ? "↑" : "↓"}</span>
                                )}
                            </button>
                        </th>
                    ))}
                    <th className="px-4 py-3">Last seen</th>
                </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                {songs.map((song) => (
                    <tr key={song.title} className="transition hover:bg-white/10">
                        <td className="px-4 py-3 text-base font-semibold text-white">{song.title}</td>
                        <td className="px-4 py-3">
                            <div className="flex items-center gap-3">
                                    <span className="w-16 tabular-nums text-slate-100">
                                        {formatNumber(song.probability * 100, 1)}%
                                    </span>
                                <ProbabilityBar probability={song.probability} />
                            </div>
                        </td>
                        <td className="px-4 py-3 tabular-nums text-slate-100">
                            {formatNumber(song.appearances)}
                        </td>
                        <td className="px-4 py-3 tabular-nums text-slate-100">
                            {song.typicalPosition ? `#${formatNumber(song.typicalPosition)}` : "—"}
                        </td>
                        <td className="px-4 py-3 text-slate-300">
                            {song.lastSeen ? song.lastSeen : "—"}
                        </td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
}