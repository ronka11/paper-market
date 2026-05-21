import { useState, useEffect } from "react"
import { useParams, useSearchParams } from "react-router-dom"
import { useSession } from "../hooks/useSession"
import { fetchHistory, fetchAnalysis, fetchOrders} from "../api"
import { fetchTickerNews, fetchPriceTargets, fetchUpgradesDowngrades, fetchRecommendations } from "../api"
import { useLivePrice } from "../hooks/useLivePrice"
import RecommendationsBar from "../components/RecommendationsBar"
import PriceTargetBar from "../components/PriceTargetBar"
import PriceChart from "../components/PriceChart"
import AnalysisCard from "../components/AnalysisCard"
import OrderForm from "../components/OrderForm"

const PERIODS = ["1mo", "3mo", "6mo", "1y"]

export default function TickerView() {
  const { ticker }          = useParams()
  const [searchParams]      = useSearchParams()

  // Infer exchange from ticker suffix (.NS = NSE, .BO = BSE), fallback to search param
  let exchange = searchParams.get("exchange")
  if (!exchange) {
    if (ticker.endsWith(".NS")) exchange = "NSE"
    else if (ticker.endsWith(".BO")) exchange = "BSE"
    else exchange = "US"
  }

  const sessionKey          = useSession()
  const market              = exchange === "NSE" || exchange === "BSE" ? "IN" : "US"
  // Remove suffix for clean display if present
  const baseTicker          = ticker.replace(".NS", "").replace(".BO", "")
  const formattedTicker     = exchange === "NSE" ? `${baseTicker}.NS`
    : exchange === "BSE" ? `${baseTicker}.BO` : baseTicker
  const livePrice           = useLivePrice([formattedTicker])
  const live                = livePrice[formattedTicker]

  const [history, setHistory]     = useState([])
  const [analysis, setAnalysis]   = useState(null)
  const [orders, setOrders]       = useState([])
  const [period, setPeriod]       = useState("3mo")
  const [histLoading, setHistLoading]   = useState(true)
  const [analysisLoading, setAnalysisLoading] = useState(true)
  const [tickerNews, setTickerNews]   = useState([])
  const [targets, setTargets]         = useState(null)
  const [upgrades, setUpgrades]       = useState([])
  const [recs, setRecs]               = useState({})
    

  // Load full 1 year of price history once, period selector just filters
  useEffect(() => {
    if (!sessionKey) return
    setHistLoading(true)
    // Always fetch 1y data for full history, will be filtered by period
    fetchHistory(baseTicker, exchange, "1y", sessionKey)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setHistLoading(false))
  }, [baseTicker, exchange, sessionKey])

  // Apply period filter to already-loaded history
  const filteredHistory = period === "1y" ? history : (() => {
    if (!history.length) return []
    const periodDays = { "1mo": 30, "3mo": 90, "6mo": 180 }
    const days = periodDays[period] || 90
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - days)
    return history.filter(h => new Date(h.date) >= cutoffDate)
  })()

  // Load analysis + orders
  useEffect(() => {
    if (!sessionKey) return
    setAnalysisLoading(true)
    fetchAnalysis(baseTicker, exchange, false, sessionKey)
      .then(setAnalysis)
      .catch(() => setAnalysis({ error: "could not load" }))
      .finally(() => setAnalysisLoading(false))

    fetchOrders(sessionKey, market).then(all =>setOrders(all.filter(o => o.ticker === formattedTicker)))
    fetchTickerNews(baseTicker, exchange, sessionKey).then(setTickerNews).catch(() => [])
    fetchPriceTargets(baseTicker, exchange, sessionKey).then(setTargets).catch(() => null)
    fetchUpgradesDowngrades(baseTicker, exchange, sessionKey).then(setUpgrades).catch(() => [])
    fetchRecommendations(baseTicker, exchange, sessionKey).then(setRecs).catch(() => {})
  }, [baseTicker, exchange, sessionKey, formattedTicker, market])

  async function refreshAnalysis() {
    setAnalysisLoading(true)
    try {
      const result = await fetchAnalysis(baseTicker, exchange, true, sessionKey)
      setAnalysis(result)
    } finally {
      setAnalysisLoading(false)
    }
  }

  function reloadOrders() {
    fetchOrders(sessionKey, market).then(all =>
      setOrders(all.filter(o => o.ticker === formattedTicker))
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
          <h1 style={{ fontSize: "22px", fontWeight: "bold" }}>{baseTicker}</h1>
          <span className="tag neutral">{exchange}</span>
          {dayChange !== null && (
            <span className={dayChange >= 0 ? "up" : "down"} style={{ fontSize: "14px" }}>
              {dayChange >= 0 ? "+" : ""}{dayChange.toFixed(2)}% today
            </span>
          )}
        </div>
        {latest && (
          <p style={{ fontSize: "24px", marginTop: "4px" }}>
            {live?.price
              ? live.price.toLocaleString(undefined, { minimumFractionDigits: 2 })
              : latest?.close.toLocaleString(undefined, { minimumFractionDigits: 2 })
            }
            {live && (
              <span className={live.change_pct >= 0 ? "up" : "down"}
                style={{ fontSize: "14px", marginLeft: "10px" }}>
                {live.change_pct >= 0 ? "+" : ""}{live.change_pct?.toFixed(2)}% live
              </span>
            )}
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
        </div>

        {histLoading
          ? <p className="muted" style={{ padding: "60px 0", textAlign: "center" }}>loading chart...</p>
          : <PriceChart data={filteredHistory} height={280} mode="candle" />
        }
      </div>

      {/* ── Analysis + Order + Analyst ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "16px", alignItems: "start" }}>
        <div>
          <AnalysisCard analysis={analysis} loading={analysisLoading} onRefresh={refreshAnalysis} />

          {/* Recommendations + price targets */}
          {(Object.keys(recs).length > 0 || targets?.mean) && (
            <div className="card">
              <RecommendationsBar data={recs} />
              <PriceTargetBar targets={targets} currentPrice={live?.price || latest?.close} />
            </div>
          )}

          {/* Upgrades / downgrades */}
          {upgrades.length > 0 && (
            <div className="card">
              <p style={{ fontSize: "11px", letterSpacing: "0.08em", color: "var(--text-secondary)", marginBottom: "12px" }}>
                RECENT RATING CHANGES
              </p>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-secondary)" }}>
                    {["date", "firm", "from", "to", "action"].map(h => (
                      <th key={h} style={{ textAlign: "left", padding: "5px 0", fontWeight: "normal" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {upgrades.map((u, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "7px 0" }} className="muted">{u.date}</td>
                      <td>{u.firm}</td>
                      <td className="muted">{u.from_grade || "—"}</td>
                      <td className={u.action === "up" ? "up" : u.action === "down" ? "down" : ""}>
                        {u.to_grade}
                      </td>
                      <td className={u.action === "up" ? "up" : "down"}>{u.action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* yfinance news */}
          {tickerNews.length > 0 && (
            <div className="card">
              <p style={{ fontSize: "11px", letterSpacing: "0.08em", color: "var(--text-secondary)", marginBottom: "12px" }}>
                NEWS
              </p>
              {tickerNews.map((n, i) => (
                <div key={i} style={{ borderBottom: "1px solid var(--border)", paddingBottom: "10px", marginBottom: "10px" }}>
                  <a href={n.url} target="_blank" rel="noreferrer"
                    style={{ color: "var(--text-primary)", textDecoration: "none", fontSize: "13px" }}>
                    {n.title}
                  </a>
                  <p className="muted" style={{ fontSize: "11px", marginTop: "3px" }}>{n.publisher}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <OrderForm ticker={baseTicker} exchange={exchange} market={market} sessionKey={sessionKey} onOrderPlaced={reloadOrders} />
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