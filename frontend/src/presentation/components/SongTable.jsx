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
            <div className="flex flex-col items-center gap-3 py-8 text-sm text-slate-400">
                <span className="h-3 w-3 animate-ping rounded-full bg-[--color-brand]" />
                <span>Checking shows...</span>
            </div>
        );
    }

    if (!songs?.length) {
        return (
            <div className="rounded-xl border border-dashed border-white/10 bg-white/5 px-4 py-6 text-center text-sm text-slate-500">
                Type an artist above to see what's been on their setlists
            </div>
        );
    }

    return (
        <div className="overflow-hidden rounded-xl border border-white/10 bg-white/5">
            <table className="min-w-full text-left text-sm text-slate-200">
                <thead>
                <tr className="bg-[--color-brand]/10 text-xs uppercase tracking-[0.2em] text-slate-400">
                    {headers.map((header) => (
                        <th key={header.key} className="px-4 py-2.5">
                            <button
                                type="button"
                                className="flex items-center gap-2 font-medium text-slate-300 transition hover:text-white"
                                onClick={() => onSort(header.key === "title" ? "title" : header.key)}
                            >
                                <span className={sortKey === header.key ? "text-white" : ""}>{header.label.toLowerCase()}</span>
                                {sortKey === header.key && (
                                    <span className="text-[--color-brand]">{sortDir === "asc" ? "↑" : "↓"}</span>
                                )}
                            </button>
                        </th>
                    ))}
                </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                {songs.map((song) => (
                    <tr key={song.title} className="group transition hover:bg-[--color-brand]/5">
                        <td className="px-4 py-2.5 text-base font-medium text-white transition-colors">{song.title}</td>
                        <td className="px-4 py-2.5">
                            <div className="flex items-center gap-3">
                                    <span className="w-16 tabular-nums text-slate-100 font-semibold">
                                        {formatNumber(song.probability * 100, 1)}%
                                    </span>
                                <ProbabilityBar probability={song.probability} />
                            </div>
                        </td>
                        <td className="px-4 py-2.5 tabular-nums text-slate-100">
                            {song.appearances === 0 ? "—" : formatNumber(song.appearances)}
                        </td>
                        <td className="px-4 py-2.5 tabular-nums text-slate-100">
                            {song.typicalPosition ? `#${formatNumber(song.typicalPosition)}` : "—"}
                        </td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
}