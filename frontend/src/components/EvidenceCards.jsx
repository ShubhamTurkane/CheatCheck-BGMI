const badge = {
  normal: "bg-emerald-50 text-emerald-800",
  unusual: "bg-slate-100 text-slate-800",
  suspicious: "bg-amber-50 text-amber-900",
  highly_unusual: "bg-red-50 text-red-900",
};

export default function EvidenceCards({ items }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {items.map((item, index) => (
        <div key={`${item.feature}-${index}`} className="rounded-xl border border-border bg-white p-5 shadow-card">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h4 className="font-bold">{item.feature}</h4>
              <div className="mt-1 text-2xl font-black">
                {item.player_value ?? "—"}
              </div>
            </div>
            <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${badge[item.indicator] || badge.normal}`}>
              {item.indicator.replace("_", " ")}
            </span>
          </div>
          {item.legit_range && (
            <div className="mt-2 text-xs text-ink-soft">Reference: {item.legit_range}</div>
          )}
          <p className="mt-3 text-sm text-ink-soft">{item.explanation}</p>
        </div>
      ))}
    </div>
  );
}
