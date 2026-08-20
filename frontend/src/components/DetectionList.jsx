export default function DetectionList({ detections, model }) {
  return (
    <div>
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h2 className="text-lg font-medium text-slate-100">Detections ({detections.length})</h2>
        <span className="text-xs text-slate-500">{model}</span>
      </div>
      {detections.length === 0 ? (
        <p className="text-sm text-slate-400">
          No matching objects. This model knows people, cars, animals, furniture, and similar everyday
          items — not picture frames or wall art. Try <span className="text-cyan-300">Match Strictness: Low</span> or
          another photo.
        </p>
      ) : (
        <ul className="vl-scroll max-h-[360px] space-y-2 overflow-auto">
          {detections.map((d, i) => (
            <li key={`${d.class_id}-${i}`} className="rounded-md bg-slate-800/80 px-3 py-2 text-sm text-slate-200">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{d.class_name}</span>
                <span className="text-slate-400">{(d.confidence * 100).toFixed(1)}%</span>
                {d.confidence_tier && (
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] uppercase ${
                      d.confidence_tier === 'high'
                        ? 'bg-emerald-900 text-emerald-200'
                        : d.confidence_tier === 'medium'
                          ? 'bg-amber-900 text-amber-100'
                          : 'bg-slate-700 text-slate-300'
                    }`}
                  >
                    {d.confidence_tier}
                  </span>
                )}
                {d.category_group && (
                  <span className="rounded bg-slate-700 px-1.5 py-0.5 text-[10px] text-slate-300">
                    {d.category_group}
                  </span>
                )}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {d.relative_size || 'size?'} · {d.zone || 'zone?'} · [{d.bbox.x1.toFixed(0)}, {d.bbox.y1.toFixed(0)}] → [
                {d.bbox.x2.toFixed(0)}, {d.bbox.y2.toFixed(0)}]
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
