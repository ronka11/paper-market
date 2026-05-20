// src/components/RecommendationsBar.jsx
export default function RecommendationsBar({ data }) {
  if (!data || !Object.keys(data).length) return null

  const total = Object.values(data).reduce((a, b) => a + b, 0)
  if (!total) return null

  const segments = [
    { key: "strong_buy",  label: "strong buy",  color: "#1a5c1a" },
    { key: "buy",         label: "buy",          color: "#3a7d3a" },
    { key: "hold",        label: "hold",         color: "#888870" },
    { key: "sell",        label: "sell",         color: "#8b2a2a" },
    { key: "strong_sell", label: "strong sell",  color: "#5c1a1a" },
  ]

  return (
    <div style={{ marginBottom: "16px" }}>
      <p style={{ fontSize: "11px", letterSpacing: "0.08em", color: "var(--text-secondary)", marginBottom: "8px" }}>
        ANALYST CONSENSUS · {total} ratings
      </p>
      <div style={{ display: "flex", height: "8px", borderRadius: "2px", overflow: "hidden", gap: "1px" }}>
        {segments.map(s => {
          const pct = (data[s.key] / total) * 100
          return pct > 0 ? (
            <div key={s.key} title={`${s.label}: ${data[s.key]}`}
              style={{ width: `${pct}%`, background: s.color }} />
          ) : null
        })}
      </div>
      <div style={{ display: "flex", gap: "12px", marginTop: "6px", flexWrap: "wrap" }}>
        {segments.map(s => data[s.key] > 0 ? (
          <span key={s.key} style={{ fontSize: "11px", color: s.color }}>
            {s.label} {data[s.key]}
          </span>
        ) : null)}
      </div>
    </div>
  )
}