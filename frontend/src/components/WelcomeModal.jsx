import { useState, useEffect } from "react"

export default function WelcomeModal() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const seen = localStorage.getItem("pm_welcome_seen")
    if (!seen) setOpen(true)
  }, [])

  function dismiss() {
    localStorage.setItem("pm_welcome_seen", "1")
    setOpen(false)
  }

  if (!open) return null

  return (
    <div style={{
      position: "fixed", inset: 0,
      background: "rgba(0,0,0,0.7)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 1000,
    }}>
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        padding: "36px",
        maxWidth: "480px",
        width: "90%",
        fontFamily: "var(--font)",
      }}>
        <p style={{ fontSize: "11px", letterSpacing: "0.1em", color: "var(--text-secondary)", marginBottom: "16px" }}>
          WHY THIS EXISTS
        </p>
        <p style={{ fontSize: "15px", lineHeight: "1.9", marginBottom: "20px" }}>
          Paper Market is a personal learning project — built to get hands-on with
          backend engineering (FastAPI, PostgreSQL, async SQLAlchemy, Celery, Redis, LangGraph)
          and to understand financial markets without real money on the line.
        </p>
        <p style={{ fontSize: "13px", lineHeight: "1.8", color: "var(--text-secondary)", marginBottom: "28px" }}>
          Trade with virtual cash · AI-powered stock analysis · Reddit sentiment · 
          Real market data via yfinance · No account needed.
        </p>
        <button className="btn" onClick={dismiss} style={{ width: "100%" }}>
          got it, let me trade
        </button>
      </div>
    </div>
  )
}