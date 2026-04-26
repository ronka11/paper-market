// src/pages/Dashboard.jsx
import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { useSession } from "../hooks/useSession"
import { fetchIndices, fetchPortfolio } from "../api"
import PriceChart from "../components/PriceChart"

export default function Dashboard() {
  const sessionKey = useSession()
  const [indices, setIndices] = useState({ nifty50: [], nasdaq: [] })
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sessionKey) return
    async function load() {
      try {
        const [idx, port] = await Promise.all([
          fetchIndices(sessionKey),
          fetchPortfolio(sessionKey),
        ])
        setIndices(idx)
        setPortfolio(port)
      } catch (err) {
        console.error("dashboard load failed", err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [sessionKey])

  if (loading) return <p className="muted" style={{ marginTop: "40px" }}>loading...</p>

  const pnlTotal = portfolio
    ? portfolio.total_unrealised_pnl + portfolio.total_realised_pnl
    : 0
  const pnlClass = pnlTotal >= 0 ? "up" : "down"

  return (
    <div>
      {/* ── Indices ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "8px" }}>
        <IndexPanel title="NIFTY 50" data={indices.nifty50} />
        <IndexPanel title="NASDAQ"   data={indices.nasdaq}  />
      </div>

      {/* ── Portfolio snapshot ── */}
      {portfolio && (
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "16px" }}>
            <span style={{ fontWeight: "bold", fontSize: "13px" }}>PORTFOLIO</span>
            <span className="muted" style={{ fontSize: "12px" }}>
              starting ₹{portfolio.starting_cash.toLocaleString()}
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "20px" }}>
            <Stat label="cash"       value={`$${portfolio.cash_balance.toLocaleString()}`} />
            <Stat label="unrealised" value={`${portfolio.total_unrealised_pnl >= 0 ? "+" : ""}${portfolio.total_unrealised_pnl.toFixed(2)}`} cls={portfolio.total_unrealised_pnl >= 0 ? "up" : "down"} />
            <Stat label="realised"   value={`${portfolio.total_realised_pnl >= 0 ? "+" : ""}${portfolio.total_realised_pnl.toFixed(2)}`}   cls={portfolio.total_realised_pnl >= 0 ? "up" : "down"} />
          </div>

          {/* Positions table */}
          {portfolio.positions.length === 0 ? (
            <p className="muted" style={{ fontSize: "13px" }}>no open positions — search a ticker to start trading</p>
          ) : (
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-secondary)" }}>
                  {["ticker", "qty", "avg cost", "current", "unrealised"].map(h => (
                    <th key={h} style={{ textAlign: "left", padding: "6px 0", fontWeight: "normal" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {portfolio.positions.map(pos => (
                  <tr key={pos.ticker} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "8px 0" }}>
                      <Link to={`/ticker/${pos.ticker}`} style={{ color: "var(--text-primary)" }}>
                        {pos.ticker}
                      </Link>
                    </td>
                    <td>{pos.quantity}</td>
                    <td>{pos.avg_cost.toFixed(2)}</td>
                    <td>{pos.current_price.toFixed(2)}</td>
                    <td className={pos.unrealised_pnl >= 0 ? "up" : "down"}>
                      {pos.unrealised_pnl >= 0 ? "+" : ""}{pos.unrealised_pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

function IndexPanel({ title, data }) {
  if (!data.length) return (
    <div className="card">
      <p style={{ fontWeight: "bold", fontSize: "13px", marginBottom: "12px" }}>{title}</p>
      <p className="muted" style={{ fontSize: "12px" }}>no data — run fetch_index_data task first</p>
    </div>
  )

  const latest = data[data.length - 1]
  const first  = data[0]
  const change = ((latest.close - first.close) / first.close) * 100

  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "12px" }}>
        <span style={{ fontWeight: "bold", fontSize: "13px" }}>{title}</span>
        <span className={change >= 0 ? "up" : "down"} style={{ fontSize: "13px" }}>
          {change >= 0 ? "+" : ""}{change.toFixed(2)}%
        </span>
      </div>
      <PriceChart data={data} height={160} color="area" />
      <p className="muted" style={{ fontSize: "11px", marginTop: "8px", textAlign: "right" }}>
        last close {latest.close.toLocaleString()} · updated daily
      </p>
    </div>
  )
}

function Stat({ label, value, cls = "" }) {
  return (
    <div>
      <p className="muted" style={{ fontSize: "11px", marginBottom: "4px" }}>{label}</p>
      <p className={cls} style={{ fontSize: "16px" }}>{value}</p>
    </div>
  )
}