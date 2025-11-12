import ProbabilityBar from "./ProbabilityBar";

const headers = [
    { key: "title", label: "Song" },
    { key: "prob", label: "Probability" },
    { key: "apps", label: "Appearances" },
    { key: "pos", label: "Typical position" },
];

export default function SongTable({ songs, sortKey, sortDir, onSort, formatNumber }) {
    if (!songs?.length) {
        return (
            <div className="text-sm text-gray-500">Run a prediction to see likely songs.</div>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                <tr>
                    {headers.map((header) => (
                        <th key={header.key} className="px-4 py-2 text-left">
                            <button
                                type="button"
                                className="flex items-center gap-1 font-medium text-gray-600"
                                onClick={() => onSort(header.key === "title" ? "title" : header.key)}
                            >
                                <span>{header.label}</span>
                                {sortKey === header.key && (
                                    <span>{sortDir === "asc" ? "↑" : "↓"}</span>
                                )}
                            </button>
                        </th>
                    ))}
                    <th className="px-4 py-2 text-left">Last seen</th>
                </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                {songs.map((song) => (
                    <tr key={song.title} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium">{song.title}</td>
                        <td className="px-4 py-2">
                            <div className="flex items-center gap-3">
                                    <span className="w-16 tabular-nums">
                                        {formatNumber(song.probability * 100, 1)}%
                                    </span>
                                <ProbabilityBar probability={song.probability} />
                            </div>
                        </td>
                        <td className="px-4 py-2 tabular-nums">
                            {formatNumber(song.appearances)}
                        </td>
                        <td className="px-4 py-2 tabular-nums">
                            {song.typicalPosition ? `#${formatNumber(song.typicalPosition)}` : "—"}
                        </td>
                        <td className="px-4 py-2 text-gray-500">
                            {song.lastSeen ? song.lastSeen : "—"}
                        </td>
                    </tr>
                ))}
                </tbody>
            </table>
        </div>
    );
}