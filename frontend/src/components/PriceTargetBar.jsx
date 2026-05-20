// src/components/PriceTargetBar.jsx
export default function PriceTargetBar({ targets, currentPrice }) {
  if (!targets || !targets.mean) return null

  const { low, high, mean, current } = targets
  const rangeMin = Math.min(low, currentPrice) * 0.97
  const rangeMax = Math.max(high, currentPrice) * 1.03
  const range    = rangeMax - rangeMin

  const pct = v => ((v - rangeMin) / range) * 100

  return (
    <div style={{ marginBottom: "16px" }}>
      <p style={{ fontSize: "11px", letterSpacing: "0.08em", color: "var(--text-secondary)", marginBottom: "10px" }}>
        ANALYST PRICE TARGETS
      </p>
      <div style={{ position: "relative", height: "4px", background: "var(--border)", borderRadius: "2px", margin: "20px 0" }}>
        {/* Range bar */}
        <div style={{
          position: "absolute",
          left: `${pct(low)}%`, width: `${pct(high) - pct(low)}%`,
          height: "100%", background: "var(--border)", borderRadius: "2px",
          opacity: 0.6,
        }} />
        {/* Mean marker */}
        <div title={`mean $${mean}`} style={{
          position: "absolute", left: `${pct(mean)}%`,
          width: "3px", height: "12px", top: "-4px",
          background: "var(--text-secondary)", borderRadius: "1px",
          transform: "translateX(-50%)",
        }} />
        {/* Current price marker */}
        <div title={`current $${currentPrice}`} style={{
          position: "absolute", left: `${pct(currentPrice)}%`,
          width: "3px", height: "16px", top: "-6px",
          background: "var(--text-primary)", borderRadius: "1px",
          transform: "translateX(-50%)",
        }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-secondary)" }}>
        <span>low ${low}</span>
        <span style={{ color: "var(--text-primary)" }}>mean ${mean}</span>
        <span>high ${high}</span>
      </div>
    </div>
  )
}