// src/pages/TickerView.jsx
import { useState, useEffect } from "react"
import { useParams, useSearchParams } from "react-router-dom"
import { useSession } from "../hooks/useSession"
import { fetchHistory, fetchAnalysis, fetchOrders, triggerScrape } from "../api"
import PriceChart from "../components/PriceChart"
import AnalysisCard from "../components/AnalysisCard"
import OrderForm from "../components/OrderForm"

const PERIODS = ["1mo", "3mo", "6mo", "1y"]

export default function TickerView() {
  const { ticker }          = useParams()
  const [searchParams]      = useSearchParams()
  const exchange            = searchParams.get("exchange") || "US"
  const sessionKey          = useSession()

  const [history, setHistory]     = useState([])
  const [analysis, setAnalysis]   = useState(null)
  const [orders, setOrders]       = useState([])
  const [period, setPeriod]       = useState("3mo")
  const [histLoading, setHistLoading]   = useState(true)
  const [analysisLoading, setAnalysisLoading] = useState(true)

  // Load price history
  useEffect(() => {
    if (!sessionKey) return
    setHistLoading(true)
    fetchHistory(ticker, exchange, period, sessionKey)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setHistLoading(false))
  }, [ticker, exchange, period, sessionKey])

  // Load analysis + orders
  useEffect(() => {
    if (!sessionKey) return
    setAnalysisLoading(true)
    fetchAnalysis(ticker, exchange, false, sessionKey)
      .then(setAnalysis)
      .catch(() => setAnalysis({ error: "could not load" }))
      .finally(() => setAnalysisLoading(false))

    fetchOrders(sessionKey).then(all =>
      setOrders(all.filter(o => o.ticker === ticker))
    )
  }, [ticker, exchange, sessionKey])

  async function refreshAnalysis() {
    setAnalysisLoading(true)
    try {
      const result = await fetchAnalysis(ticker, exchange, true, sessionKey)
      setAnalysis(result)
    } finally {
      setAnalysisLoading(false)
    }
  }

  async function handleScrape() {
    await triggerScrape(ticker, sessionKey)
    alert(`scrape queued for ${ticker} — check sentiment after a minute`)
  }

  function reloadOrders() {
    fetchOrders(sessionKey).then(all =>
      setOrders(all.filter(o => o.ticker === ticker))
    )
  }

  const latest = history[history.length - 1]
  const prev   = history[history.length - 2]
  const dayChange = latest && prev
    ? ((latest.close - prev.close) / prev.close) * 100
    : null

  return (
    <div>
      {/* ── Header ── */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: "12px" }}>
          <h1 style={{ fontSize: "22px", fontWeight: "bold" }}>{ticker}</h1>
          <span className="tag neutral">{exchange}</span>
          {dayChange !== null && (
            <span className={dayChange >= 0 ? "up" : "down"} style={{ fontSize: "14px" }}>
              {dayChange >= 0 ? "+" : ""}{dayChange.toFixed(2)}% today
            </span>
          )}
        </div>
        {latest && (
          <p style={{ fontSize: "24px", marginTop: "4px" }}>
            {latest.close.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        )}
      </div>

      {/* ── Price chart + period selector ── */}
      <div className="card">
        <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
          {PERIODS.map(p => (
            <button
              key={p}
              className={period === p ? "btn" : "btn outline"}
              onClick={() => setPeriod(p)}
              style={{ padding: "4px 12px", fontSize: "12px" }}
            >
              {p}
            </button>
          ))}
          <button
            className="btn outline"
            onClick={handleScrape}
            style={{ marginLeft: "auto", padding: "4px 12px", fontSize: "12px" }}
          >
            scrape reddit
          </button>
        </div>

        {histLoading
          ? <p className="muted" style={{ padding: "60px 0", textAlign: "center" }}>loading chart...</p>
          : <PriceChart data={history} height={280} color="auto" />
        }
      </div>

      {/* ── Analysis + Order form side by side ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "16px", alignItems: "start" }}>
        <AnalysisCard
          analysis={analysis}
          loading={analysisLoading}
          onRefresh={refreshAnalysis}
        />
        <OrderForm
          ticker={ticker}
          exchange={exchange}
          sessionKey={sessionKey}
          onOrderPlaced={reloadOrders}
        />
      </div>

      {/* ── Order history ── */}
      {orders.length > 0 && (
        <div className="card">
          <p style={{ fontWeight: "bold", fontSize: "13px", marginBottom: "14px" }}>ORDER HISTORY</p>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-secondary)" }}>
                {["side", "qty", "fill price", "status", "date"].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "6px 0", fontWeight: "normal" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "8px 0" }} className={o.side === "BUY" ? "up" : "down"}>{o.side}</td>
                  <td>{o.quantity}</td>
                  <td>{o.fill_price ?? "—"}</td>
                  <td className={o.status === "FILLED" ? "up" : "down"}>{o.status}</td>
                  <td className="muted">{new Date(o.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}