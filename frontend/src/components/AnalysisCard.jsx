// src/components/AnalysisCard.jsx
export default function AnalysisCard({ analysis, loading, onRefresh }) {
  if (loading) return (
    <div className="card">
      <p className="muted">running analysis...</p>
    </div>
  )

  if (!analysis) return null

  if (analysis.error) return (
    <div className="card">
      <p className="muted">analysis unavailable — {analysis.error}</p>
    </div>
  )

  const stanceClass = analysis.stance === "bull" ? "bull"
    : analysis.stance === "bear" ? "bear" : "neutral"

  const trendSign = analysis.trend_7d_pct > 0 ? "+" : ""

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px" }}>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ fontSize: "13px", fontWeight: "bold" }}>AI ANALYSIS</span>
          {analysis.cached && <span className="tag neutral">cached</span>}
        </div>
        <button className="btn outline" onClick={onRefresh} style={{ padding: "3px 10px", fontSize: "12px" }}>
          refresh
        </button>
      </div>

      <div style={{ display: "flex", gap: "12px", marginBottom: "14px", flexWrap: "wrap" }}>
        <span className={`tag ${stanceClass}`}>{analysis.stance}</span>
        <span className={`tag ${stanceClass}`}>{analysis.sentiment_signal}</span>
        <span className="tag neutral">confidence: {analysis.confidence}</span>
        <span className={analysis.trend_7d_pct > 0 ? "up" : "down"} style={{ fontSize: "13px" }}>
          {trendSign}{analysis.trend_7d_pct}% / 7d
        </span>
      </div>

      <p style={{ fontSize: "13px", lineHeight: "1.8", color: "var(--text-primary)" }}>
        {analysis.summary}
      </p>
    </div>
  )
}