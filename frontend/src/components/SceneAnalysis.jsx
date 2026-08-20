export default function SceneAnalysis({ analysis }) {
  if (!analysis) return null

  const alerts = analysis.alerts || []
  const counts = Object.entries(analysis.class_counts || {})
  const categories = Object.entries(analysis.category_counts || {})

  return (
    <div className="mb-4 space-y-3">
      <div className="rounded-lg border border-cyan-500/30 bg-cyan-950/20 px-4 py-3 shadow-[0_0_18px_rgba(0,229,255,0.12)]">
        <p className="text-[10px] uppercase tracking-[0.16em] text-cyan-300">Scene summary</p>
        <p className="mt-1 text-base font-semibold text-white">{analysis.caption}</p>
        <p className="mt-2 text-sm text-slate-400">
          {analysis.total_objects} objects · {analysis.unique_classes} classes
        </p>
      </div>

      {alerts.length > 0 && (
        <ul className="space-y-2">
          {alerts.map((a) => (
            <li
              key={a.code}
              className={`rounded-lg px-3 py-2 text-sm ${
                a.level === 'warning'
                  ? 'border border-amber-500/40 bg-amber-950/40 text-amber-100'
                  : 'border border-cyan-800/50 bg-slate-950/60 text-slate-200'
              }`}
            >
              {a.message}
            </li>
          ))}
        </ul>
      )}

      {categories.length > 0 && (
        <div>
          <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-slate-500">Categories</p>
          <div className="flex flex-wrap gap-2">
            {categories.map(([name, n]) => (
              <span
                key={name}
                className="rounded-md border border-cyan-800/40 bg-slate-950/70 px-2.5 py-1 text-xs text-cyan-100"
              >
                {name}: {n}
              </span>
            ))}
          </div>
        </div>
      )}

      {counts.length > 0 && (
        <div>
          <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-slate-500">Counts</p>
          <ul className="space-y-1 text-sm text-slate-300">
            {counts.slice(0, 8).map(([name, n]) => (
              <li key={name} className="flex justify-between gap-4 border-b border-slate-800/80 py-1">
                <span>{name}</span>
                <span className="text-cyan-300">{n}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {analysis.insights?.length > 0 && (
        <div>
          <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-slate-500">Insights</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
            {analysis.insights.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
