export default function ProbabilityBar({ p }) {
    const pct = Math.max(0, Math.min(100, (p || 0) * 100));
    return (
        <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
            <div
                className="h-full bg-[--color-brand] transition-[width] duration-500"
                style={{ width: `${pct.toFixed(1)}%` }}
            />
        </div>
    );
}