export default function ProbabilityBar({ probability }) {
    const pct = Math.max(0, Math.min(100, (probability || 0) * 100));
    return (
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/10" role="presentation">
            <div
                className="h-full bg-gradient-to-r from-[--color-brand] via-orange-400 to-amber-400 transition-[width] duration-500"
                style={{ width: `${pct.toFixed(1)}%` }}
            />
        </div>
    );
}